ALTER TABLE configs ADD COLUMN journald_logging BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE configs SET journald_logging = 0 WHERE id = 'irchin';
