ALTER TABLE blackout DROP COLUMN app_name;
ALTER TABLE blackout ADD COLUMN app_names JSONB NOT NULL DEFAULT '[]';

DROP INDEX IF EXISTS idx_blackout_app_name;
CREATE INDEX idx_blackout_app_names ON blackout USING GIN (app_names);
