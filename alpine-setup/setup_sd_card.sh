#!/bin/bash

PROG="${0##*/}"
PRIMARY_PARTITION_MB=250
FALLOW_PERCENT=10
DEV=""
PARTITION_SETUP_FILE=""
FAILS=0
MOUNTED=n
MOUNT_CREATED=n
MOUNT_PATH="mount"
P1LABEL="PIBOOT"
P2LABEL="PERSIST"
ALPINE_TARBALL="${ALPINE_TARBALL:-alpine.tar.gz}"

main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        usage 0
    elif [ "$#" -gt 1 ]; then
        usage 1
    fi

    check_prereq
    check_root
    set_device "$@"
    calculate_partitions
    preview_and_confirm

    wipe_old_partitions
    sync

    make_partitions
    sync

    format_partitions
    sync

    copy_base_system
    sync
}

usage() {
    echo "Installs Alpine Linux on an SD card as follows:"
    echo "+ Wipes all existing partitions"
    echo "+ Creates partition 1 as $PRIMARY_PARTITION_MB MiB / DOS / bootable"
    echo "+ Formats partition 1 with DOS FAT32, label=$P1LABEL"
    echo "+ Creates partition 2 as [remaining space - 10%] MiB / Linux"
    echo "+ Formats partition 2 with f2fs, label=$P2LABEL"
    echo "+ Copies base Alpine system from ${ALPINE_TARBALL} to partition 1"
    echo "+ Copies files from install/ to partition 1"
    echo
    echo "Usage:"
    echo
    echo "  $PROG [dev]"
    echo
    echo "e.g."
    echo
    echo "  $PROG /dev/sdb"
    echo
    echo "If dev is not specified, the device will be guessed by looking at recently connected"
    echo "block devices, and the user prompted to confirm the guess."
    exit "${1:-0}"
}

check_prereq() {
    local prog
    for prog in dd dc sfdisk lsblk awk mount realpath tar; do
        is_installed $prog || erex "not found in PATH: $prog"
    done

    if [ ! -r "${ALPINE_TARBALL}" ]; then
        erex "not readable: '${ALPINE_TARBALL}'"
    fi
}

is_installed() {
    which $1 >/dev/null 2>&1
}

erex() {
    echo "ERROR: $*" 1>&2
    exit 1
}

# checks to see if the user is executing program with root perms,
# if not, exits with error message
check_root() {
    if [ "$(id -u)" != "0" ]; then
        erex "should be run as root"
        exit 2
    fi
}

set_device() {
    DEV="$1"
    if [ -z "$DEV" ]; then
        # Prompt for device if not already specified
        read -p "Insert SD card into reader and press RETURN" _
        DEV="$(guess_dev)"
        read -p "Guessed device = '$DEV', ok? [RETURN to accept, else enter device] > " d
        if [ -n "$d" ]; then
            DEV="$d"
        fi
    fi

    if [ "${DEV#/dev/}" = "$DEV" ]; then
        # does not include /dev prefix
        DEV="/dev/$DEV"
    fi

    if [ ! -e "$DEV" ]; then
        erex "device does not exist: $DEV"
    fi

    if lsblk -rno MOUNTPOINT "$DEV" | grep -q /; then
        erex "$DEV has mounted partitions"
    fi
}

guess_dev() {
    if guess_dev_mmc; then
        return 0
    elif guess_dev_sd; then
        return 0
    else
        return 1
    fi
}

guess_dev_mmc() {
    d="$(dmesg | grep -E '^\[[ 0-9\.]*] mmcblk[0-9]:' | sed -e 's/^.*mmcblk/mmcblk/' -e 's/:.*//' | tail -1)"
    if [ -z "$d" ]; then
        return 1
    fi
    echo "$d"
}

guess_dev_sd() {
    d=$(dmesg | grep "Write Protect is off" | tail -1 | grep -o '\[sd.\]' | grep -o 'sd.')
    if [ -z "$d" ]; then
        return 1
    fi
    echo "$d"
}

calculate_partitions() {
    local -i total_size_bytes="$(lsblk --noheadings --nodeps --output SIZE --bytes "$DEV")"

    # sanity 1
    [ "$total_size_bytes" -gt 0 ] || erex "failed to determine size of device $DEV"

    # calculate size with FALLOW_PERCENT left out
    local -i usable_size_mb=$(dc <<<"100 $FALLOW_PERCENT - $total_size_bytes * 100 / 1024 1024 * / p")

    # sanity 2
    [ "$usable_size_mb" -gt "$PRIMARY_PARTITION_MB" ] || erex "not enough space for primary partition of $PRIMARY_PARTITION_MB MiB"

    secondary_size_mb=$((usable_size_mb - PRIMARY_PARTITION_MB))

    # sanity 3
    [ "$secondary_size_mb" -gt 0 ] || erex "no space for secondary partition"

    PARTITION_SETUP_FILE=$(mktemp) || exit 1
    trap 'cleanup' EXIT

    cat >"$PARTITION_SETUP_FILE" <<-EOD
	start=2048, size=${PRIMARY_PARTITION_MB}M, type=c, bootable
	size=${secondary_size_mb}M, type=83
	EOD
}

preview_and_confirm() {
    echo -e "\e[1;4;5mWARNING: About to re-partition and re-format device $DEV\e[m"
    echo
    echo "Partition Scheme"
    echo "----------------"
    nl <"$PARTITION_SETUP_FILE" | sed 's/^ *\([0-9][0-9]*\)[ 	]*/Partition #\1: /'
    echo
    echo "Formatting"
    echo "----------"
    echo "Partition 1 will be formatted with FAT32 filesystem, label=$P1LABEL"
    echo "Partition 2 will be formatted with f2fs  filesystem, label=$P2LABEL"
    echo
    echo "Install"
    echo "-------"
    echo "Will un-tar alpine.tar.gz to partition 1"
    echo "Will copy files from install/ to partition 1"
    echo
    echo -e "If you proceed now, all data on \e[1m$DEV\e[m will be DELETED"
    local conf
    read -p "'yes' to proceed, anything else to abort> " conf
    if [ "$conf" != "yes" ]; then
        echo "Aborted" 1>&2
        exit 1
    fi
}

# If we don't blank out data at the start of all the existing partitions
# we get a lot of scary warnings when we reformat them, and can even
# end up with old data visible after the format in some cases...
wipe_old_partitions() {
    local -a devices=()
    local partition
    local d
    while read partition; do
        if [ "${partition#/dev/}" = "$partition" ]; then
            # does not include /dev prefix
            partition="/dev/$partition"
        fi
        devices+=("$partition")
    done < <(lsblk "$DEV" --pairs --output NAME,TYPE | awk -F '"' '/TYPE="part"/ { print $2 }')
    devices+=("$DEV")
    for d in "${devices[@]}"; do
        dd_part "$d"
    done
}

dd_part() {
    local -a cmd=(dd if=/dev/zero of="$1" bs=1M count=10 conv=fsync status=none)
    echo "wiping:$(printf " %q" "${cmd[@]}")..."
    "${cmd[@]}"
}

make_partitions() {
    echo "Partitioning..."
    sfdisk --quiet --wipe always "$DEV" <"$PARTITION_SETUP_FILE"
}

format_partitions() {
    echo -n "Formatting partitions..."
    local -a partitions
    local partition
    while IFS='"' read _ partition _; do
        if [ "${partition#/dev/}" = "$partition" ]; then
            # does not include /dev prefix
            partition="/dev/$partition"
        fi
        partitions+=("$partition")
    done < <(lsblk "$DEV" -P | awk '/TYPE="part"/ { print $1 }')

    # sanity
    [ "${#partitions[@]}" -eq 2 ] || erex "expected to find 2 partitions, found ${#partitions[@]}"

    echo "formatting patition 1..."
    mkfs.vfat -n "$P1LABEL" -F 32 "${partitions[0]}"

    echo "formatting patition 2..."
    mkfs.f2fs -l "$P2LABEL" "${partitions[1]}"
}

copy_base_system() {
    # Get the first partition (not base blockdev)
    local partition="$(lsblk "$DEV" --pairs --output NAME,TYPE | awk -F '"' '/TYPE="part"/ { print $2 ; exit; }')"
    if [ "${partition#/dev/}" = "$partition" ]; then
        # does not include /dev prefix
        partition="/dev/$partition"
    fi

    local kv_pairs="$(lsblk --pairs --output FSTYPE,FSVER,LABEL,PARTTYPE,PTTYPE,PARTFLAGS "$partition")"
    eval "$kv_pairs"

    # Check first partition has correct type (FAT32 / c)
    # increment FAILS on errors
    check_value FSTYPE vfat "$FSTYPE"
    check_value FSVER FAT32 "$FSVER"
    check_value PARTTYPE 0xc "$PARTTYPE"
    check_value PTTYPE dos "$PTTYPE"
    check_value LABEL PIBOOT "$LABEL"
    check_value PARTFLAGS 0x80 "$PARTFLAGS"

    if [ "$FAILS" -gt 0 ]; then
        erex "device checks failed"
    fi

    SRC_DIR="$(realpath .)" || exit 1
    MOUNT_PATH="$(realpath "$SRC_DIR/mount")"

    # prepare install/root.tar
    if [ ! -e "$MOUNT_PATH" ]; then
        echo -n "creating mount dir $MOUNT_PATH... "
        mkdir "$MOUNT_PATH" || exit 1
        echo ok
        MOUNT_CREATED=y
    fi

    echo -n "mounting $DEV... "
    mount "$partition" "$MOUNT_PATH" || exit 1
    MOUNTED=y
    echo ok

    echo -n "checking if empty... "
    if [ "$(ls "$MOUNT_PATH" | wc -l)" = "0" ]; then
        echo ok
    else
        erex "device $partition is not empty"
    fi

    echo -n "changing into mount dir... "
    cd "$MOUNT_PATH" || exit 1
    echo ok

    echo "extracting base system tarball..."
    tar zxf "$SRC_DIR/alpine.tar.gz" || exit 1

    echo "copying files from $SRC_DIR/install..."
    cp "$SRC_DIR/install/"* ./
    if [ -e "$SRC_DIR/root" ]; then
        echo "creating root.tar..."
        tar -c -f ./root.tar -C "$SRC_DIR" --owner root --group root root
    fi

    cd "$SRC_DIR"
}

check_value() {
    local varname="$1"
    local expect="$2"
    local got="$3"

    echo -n "checking $varname (expect '$expect')... "
    if [ "$expect" = "$got" ]; then
        echo "ok"
    else
        echo "error: got '$got'"
        let FAILS+=1
    fi
}

cleanup() {
    if [ -n "$PARTITION_SETUP_FILE" ] && [ -f "$PARTITION_SETUP_FILE" ]; then
        rm "$PARTITION_SETUP_FILE"
    fi

    if [ "$MOUNTED" = y ]; then
        echo -n "cleanup: unmounting $MOUNT_PATH... "
        if ! umount "$MOUNT_PATH"; then
            echo "failed"
        else
            echo "ok"
            MOUNTED=n
        fi
    fi

    if [ "$MOUNTED" = n ] && [ "$MOUNT_CREATED" = y ]; then
        echo -n "cleanup: removing mount dir $MOUNT_PATH... "
        rmdir "$MOUNT_PATH" && echo ok
    fi
}

main "$@"
