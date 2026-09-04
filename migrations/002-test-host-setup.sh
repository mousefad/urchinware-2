# Will be sourced from apply.sh. Can/should use functions from there

host="$(hostname)"
if [ "$(echo "SELECT count(1) FROM configs WHERE id = '$host';" | sqlite3 "$DORCAS_DATABASE")" -eq 1 ]; then
    db "Already have a configs records for id=$host"
else
    db "Adding configs record for id=$host..."
    cat > "$TMP_SQL" <<-EOD 
	INSERT INTO configs (
	    id, 
	    broker_id, 
	    voice_id, 
	    mqtt_prefix, 
	    instrument_id, 
	    time_interval, 
	    journal_interval, 
	    boredom_minimum,
	    boredom_amount, 
	    door_open_seconds, 
	    mute_switch
	) VALUES (
	    '$host', 
	    'tunnel', 
	    'default',
	    'nh/urchin', 
	    'Creept Urchin Test Rig', 
	    1.0, 
	    1.0, 
	    60,
	    0.0005, 
	    15, 
	    0
	);
	EOD
    do_or_do_not sqlite3 "$DORCAS_DATABASE" "$TMP_SQL"
fi


