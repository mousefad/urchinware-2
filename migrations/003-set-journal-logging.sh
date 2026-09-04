# Will be sourced from apply.sh. Can/should use functions from there

if [ -e /etc/alpine-release ]; then
    db "On Alpine linux - disable journal logging"
    echo "UPDATE configs SET journald_logging = 0;" > $TMP_SQL
else
    db "Not on Alpine linux - enable journal logging"
    echo "UPDATE configs SET journald_logging = 0;" > $TMP_SQL
fi

do_or_do_not sqlite3 "$DORCAS_DATABASE" "$TMP_SQL"

