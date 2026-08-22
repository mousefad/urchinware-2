#!/bin/bash

PROG="${0##*/}"
FAILS=0
DEV=""
MOUNTED=n
MOUNT_CREATED=n
MOUNT_PATH="mount"

main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        usage 0
    elif [ "$#" -gt 1 ]; then
        usage 1
    fi

    check_prereq
    check_root

    DEV="$1"
    if [ -z "$DEV" ]; then
        # Prompt for device is not already specified
        read -p "Insert SD card into reader and press RETURN" _
        DEV="$(guess_dev)"
        read -p "Guessed device = $DEV, ok? [RETURN to accept, else enter device] > " d
        if [ "$d" != "" ]; then
            DEV="$d"
        fi
    fi

    if [ "${DEV#/dev/}" = "$DEV" ]; then
        # does not include /dev prefix
        DEV="/dev/$DEV"
    fi

    partition="$(lsblk "$DEV" --pairs | awk '/TYPE="part"/ { print $1 }' | head -1)"
    if [ "${partition#/dev/}" = "$partition" ]; then
        # does not include /dev prefix
        partition="/dev/$partition"
    fi

    # FSTYPE="vfat"
    # FSVER="FAT32"
    # LABEL="PIBOOT"
    # PARTTYPE="0xc"
    # PTTYPE="dos"
    # PARTFLAGS="0x80"
    kv_pairs="$(lsblk --pairs --output FSTYPE,FSVER,LABEL,PARTTYPE,PTTYPE,PARTFLAGS "$DEV")"
    eval "$kv_pairs"

    # Check first partition has correct type (FAT32 / c)
    check_value FSTYPE vfat "$FSTYPE"
    check_value FSVER FAT32 "$FSVER"
    check_value PARTTYPE 0xc "$PARTTYPE"
    check_value PTTYPE dos "$PTTYPE"
    check_value LABEL PIBOOT "$LABEL"
    check_value PARTFLAGS 0x80 "$PARTFLAGS"

    if [ "$FAILS" -gt 0 ]; then
        erex "device checks failed"
    fi

    trap cleanup EXIT

    SRC_DIR="$(realpath .)" || exit 1
    MOUNT_PATH="$SRC_DIR/mount"

    if [ ! -e "$MOUNT_PATH" ]; then
        echo -n "creating mount dir $MOUNT_PATH... "
        mkdir "$MOUNT_PATH" || exit 1
        echo ok
        MOUNT_CREATED=y
    fi

    echo -n "mounting $DEV... "
    mount "$DEV" mount || exit 1
    MOUNTED=y
    echo ok

    echo -n "checking if empty... "
    if [ "$(ls "$MOUNT_PATH" | wc -l)" = "0" ]; then
        echo ok
    else
        erex "device $dev is not empty"
    fi

    echo -n "changing into mount dir... "
    cd "$MOUNT_PATH" || exit 1
    echo ok

    echo -n "extracting base system tarball... "
    tar zxf "$SRC_DIR/alpine.tar.gz" || exit 1
    cp "$SRC_DIR/copy-to-install/"* ./
    cd -
}

usage() {
    echo "Copies the Alpine base system to the first partition of 'dev', whose first partition"
    echo "should be formatted with a FAT32 partition and labelled PIBOOT."
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
    for prog in mount tar lsblk realpath; do
        is_installed $prog || erex "not found in PATH: $prog"
    done
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

guess_dev() {
    d=$(guess_dev_mmc)
    [ "$d" = "" ] && d=$(guess_dev_sd)
    echo "$d"
}

guess_dev_mmc() {
    d=$(dmesg | grep -E '^\[[ 0-9\.]*] mmcblk[0-9]:' | sed -e 's/^.*mmcblk/mmcblk/' -e 's/:.*//' | tail -1)
    if [ "$d" = "" ]; then
        return 1
    else
        echo "${d}p1"
        return 1
    fi
}

guess_dev_sd() {
    d=$(dmesg | grep "Write Protect is off" | tail -1 | grep -o '\[sd.\]' | grep -o 'sd.')
    if [ "$d" = "" ]; then
        # make sure we're not talking about root dev
        return 1
    else
        rd=$(mount | sed -n '/on \/ / { s/[0-9].*//; p }' | tail -1)
        rd="${rd#/dev/}"
        if [ "$rd" = "$d" ]; then
            # The device we found is the root device. Derp. Not OK
            return 1
        fi
        echo "${d}1"
        return 1
    fi
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
    if [ "$MOUNTED" = y ]; then
        echo -n "cleanup: unmounting $DEV... "
        if ! umount "$DEV"; then
            echo "failed"
        else
            echo "ok"
            MOUNTED=n
        fi
    fi

    if [ "$MOUNTED" = n ] && [ "$MOUNT_CREATED" = y ]; then
        echo -n "cleanup: removing mount dir $MOUNT_PATH... "
        rmdir mount && echo ok
    fi
}

main "$@"
