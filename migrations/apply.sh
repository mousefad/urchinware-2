#!/usr/bin/env sh

PROGRAM="$0"
MIGRATION_DIR="$(realpath "$PROGRAM")"
MIGRATION_DIR="${MIGRATION_DIR%/*}"
CONFIRM=n
DEBUG=n
BACKED_UP=n
RUN_DATE=$(date +%Y-%m-%dT%T)
TMP_SQL=""

usage () {
    cat <<-EOD
	Usage:
	
	  ${PROGRAM##*/} [options] [migration-dir]
	
	Applies all migrations in migration-dir or dir where this program is found if
	migration-dir not specified as argument.
	
	Options:
	
	-D : debug output
	-h : this cruft
	-v : print version and exit
	-y : confirm yes to changes (else will just preview)
	
	EOD
    exit "${1:-0}"
}

main () {
    set -- $(getopt Dhvy $@)
    [ $? -eq 0 ] || erex "incorrect using. For help run with -h option"
    while [ $# -gt 0 ]; do
        case $1 in
        -D)
            DEBUG=y
            shift
            ;;
        -h)
            usage 0
            shift
            ;;
        -v)
            echo "$PROGNAME version $VERSION"
            echo "(C) $YEAR, $AUTHOR"
            exit 0
            ;;
        -y)
            CONFIRM=y
            shift
            ;;
        --)
            shift
            break
            ;;
        esac
    done

    check_prereq

    if [ -n "$1" ]; then
        MIGRATION_DIR="$1"
        shift
    fi

    db "MIGRATION_DIR=$MIGRATION_DIR"
    get_tmp_sql
    db "TMP_SQL=$TMP_SQL"

    for f in "$MIGRATION_DIR/"[0-9][0-9][0-9]-*; do
        migrate "$f"
    done
}

check_prereq() {
    local prog
    for prog in realpath sqlite3 date tr; do
        is_installed $prog || erex "not found in PATH: $prog"
        db "pre-req $prog found"
    done

    [ -r "${DORCAS_DATABASE?ERROR - DORCAS_DATABASE env var must be set}" ] || erex "database $DORCAS_DATABASE not readable"
    db "database set and readable: $DORCAS_DATABASE"
}

is_installed() {
    which $1 >/dev/null 2>&1
}

migrate () {
    local migration_id
    if ! migration_id="$(get_migration_id "$1")"; then
        erex "could not get migration ID for $1"
    fi

    local applied_date
    if applied_date=$(applied_on "$migration_id"); then
        db "id=$migration_id was already applied @ $applied_date"
        return 0
    fi

    db "\e[1mWill apply $migration_id $1\e[m"

    case "$1" in 
        *.sql)
            do_or_do_not sqlite3 "$DORCAS_DATABASE" "$1" || exit 1
            ;;
        *.sh)
            source "$1" || exit 1 
            ;;
        *)
            err "don't know how to handle: $1"
            exit 1
            ;;
    esac

    echo "INSERT INTO migrations (id, path, applied_at) VALUES ( $migration_id, '$1', '$RUN_DATE' );" > "$TMP_SQL"
    do_or_do_not sqlite3 "$DORCAS_DATABASE" "$TMP_SQL"
}

get_migration_id () {
    local s="${1##*/}" # basename
    # remove leading zeros
    while [ "${s}" != "0" ] && [ "${s#[0-9]}" != "${s}" ]; do
        case "$s" in
            0*) s="${s#0}" ;;
            *)  break ;;
        esac
    done
    # find index of first non-digit
    local i=0
    while [ $i -lt ${#s} ]; do
        case ${s:$i:1} in
            [0-9]) echo nop > /dev/null ;;
            *) break ;;
        esac
        let i+=1
    done
    s="${s:0:$i}"
    if [ -z "$s" ]; then
        case "${1##*/}" in
            0*) s=0 ;;
            *) return 1 ;;
        esac
    fi
    db "get_migration_id: $1 -> $s"
    echo "$s"
}

applied_on () {
    local ts="$(echo -e ".mode ascii\nselect applied_at from migrations where id = $1;" | sqlite3 "$DORCAS_DATABASE" 2> /dev/null)"
    if [ -z "$ts" ]; then
        return 1
    else
        echo "$ts"
    fi
}

get_tmp_sql () {
    [ -n "$TMP_SQL" ] && return 0
    local f
    local limit=100
    while true; do
        # Alpine / busybox mktemp doesn't support templates with a suffix, so we'll 
        # generate the oursleves with _get_tmp_sql
        f="$(_get_tmp_sql)"
        if [ ! -e "$f" ]; then
            TMP_SQL="$f"
            touch "$TMP_SQL" || exit 1
            trap 'rm -f $TMP_SQL' EXIT
            return 0
        fi
        let limit-=1
        [ $limit -eq 0 ] && erex "get_tmp_sql: failed too many tries"
    done
}

_get_tmp_sql () {
    echo "/tmp/$RUN_DATE-$RANDOM$RANDOM.sql"
}


# e.g. 
#   exact:                find_migration 001-whatever.sh
#   prefix only:          find_migration 001-whatever
#   prefix and extension: find_migration 000 sql
find_migration () {
    local prefix="$1"
    local ext="$2"
    [ -n "$ext" ] && ext=".$ext"

    if [ -e "$MIGRATION_DIR/$prefix$ext" ]; then
        # case 1 - exact patch
        echo "$MIGRATION_DIR/$prefix$ext"
        return 0
    else
        local found=""
        local f
        for f in "$MIGRATION_DIR/$prefix"*"$ext"; do
            if [ -n "$found" ]; then
                err "find_migration_path: too many matches for $prefix*$ext"
                return 1
            fi
            found="$f"
        done
        if [ -z "$found" ]; then
            err "find_migration_path: no matches for $prefix*$ext"
            return 1
        fi
        echo "$found"
        return 0
    fi
}

do_or_do_not () {
    if [ "$CONFIRM" = y ]; then
        if [ "$BACKED_UP" != y ]; then
            local name="$DORCAS_DATABASE-$RUN_DATE"
            db "backing up database to $name.gz"
            cp -p "$DORCAS_DATABASE" "$name" || exit 1
            gzip -9 "$name"
            BACKED_UP=y
        fi
        db "RUN: $*"
        if [ "$1" = sqlite3 ] && [ -r "$3" ]; then
            db_cat "$3 contents:" < "$3"
        fi
        "$@"
        return $?
    else
        echo "DRY-RUN: $*"
        if [ "$1" = sqlite3 ] && [ -r "$3" ]; then
            db_cat "$3 contains:" < "$3"
        fi
        return 0
    fi
}

err () {
    echo -e "ERROR: $*" 1>&2
}

db () {
    [ "$DEBUG" = y ] || return
    echo -e "DEBUG: $*" 1>&2
}

db_cat () {
    [ "$DEBUG" = y ] || return
    db "$@"
    cat 1>&2
}

erex () {
    err "$@"
    exit 1
}

main "$@"
