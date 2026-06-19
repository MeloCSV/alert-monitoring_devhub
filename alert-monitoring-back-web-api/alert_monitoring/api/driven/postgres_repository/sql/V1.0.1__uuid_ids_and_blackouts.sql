-- Migrate alert_app to UUID primary key
ALTER TABLE alert_app ADD COLUMN uid UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE alert_app DROP CONSTRAINT alert_app_pkey;
ALTER TABLE alert_app DROP COLUMN id;
ALTER TABLE alert_app RENAME COLUMN uid TO id;
ALTER TABLE alert_app ADD CONSTRAINT alert_app_pkey PRIMARY KEY (id);

-- Migrate default_alert_app to UUID primary key
ALTER TABLE default_alert_app ADD COLUMN uid UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE default_alert_app DROP CONSTRAINT default_alert_app_pkey;
ALTER TABLE default_alert_app DROP COLUMN id;
ALTER TABLE default_alert_app RENAME COLUMN uid TO id;
ALTER TABLE default_alert_app ADD CONSTRAINT default_alert_app_pkey PRIMARY KEY (id);

-- Migrate catalog_apps to UUID primary key
ALTER TABLE catalog_apps ADD COLUMN uid UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE catalog_apps DROP CONSTRAINT catalog_apps_pkey;
ALTER TABLE catalog_apps DROP COLUMN id;
ALTER TABLE catalog_apps RENAME COLUMN uid TO id;
ALTER TABLE catalog_apps ADD CONSTRAINT catalog_apps_pkey PRIMARY KEY (id);

-- Migrate catalog_app_api to UUID primary key
ALTER TABLE catalog_app_api ADD COLUMN uid UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE catalog_app_api DROP CONSTRAINT catalog_app_api_pkey;
ALTER TABLE catalog_app_api DROP COLUMN id;
ALTER TABLE catalog_app_api RENAME COLUMN uid TO id;
ALTER TABLE catalog_app_api ADD CONSTRAINT catalog_app_api_pkey PRIMARY KEY (id);

-- Migrate alert_api to UUID primary key
ALTER TABLE alert_api ADD COLUMN uid UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE alert_api DROP CONSTRAINT alert_api_pkey;
ALTER TABLE alert_api DROP COLUMN id;
ALTER TABLE alert_api RENAME COLUMN uid TO id;
ALTER TABLE alert_api ADD CONSTRAINT alert_api_pkey PRIMARY KEY (id);

-- Migrate default_alert_api to UUID primary key
ALTER TABLE default_alert_api ADD COLUMN uid UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE default_alert_api DROP CONSTRAINT default_alert_api_pkey;
ALTER TABLE default_alert_api DROP COLUMN id;
ALTER TABLE default_alert_api RENAME COLUMN uid TO id;
ALTER TABLE default_alert_api ADD CONSTRAINT default_alert_api_pkey PRIMARY KEY (id);

-- Create blackout table for persisting AlertManager silences
CREATE TABLE blackout (
    id               UUID         NOT NULL DEFAULT gen_random_uuid(),
    alertmanager_id  VARCHAR(255) NOT NULL,
    matchers         JSONB        NOT NULL DEFAULT '[]',
    starts_at        TIMESTAMPTZ  NULL,
    ends_at          TIMESTAMPTZ  NULL,
    created_by       VARCHAR(255) NULL,
    comment          TEXT         NULL,
    state            VARCHAR(50)  NOT NULL DEFAULT 'active',
    source           VARCHAR(255) NULL,
    app_name         VARCHAR(255) NULL,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT blackout_pkey PRIMARY KEY (id),
    CONSTRAINT blackout_alertmanager_id_key UNIQUE (alertmanager_id)
);

CREATE INDEX idx_blackout_state ON blackout (state);
CREATE INDEX idx_blackout_source ON blackout (source);
CREATE INDEX idx_blackout_app_name ON blackout (app_name);
