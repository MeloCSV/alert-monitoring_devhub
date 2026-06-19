CREATE TABLE alert_app (
    id                   UUID            NOT NULL DEFAULT gen_random_uuid(),
    name                 VARCHAR(255)    NOT NULL,
    description          TEXT            NOT NULL,
    source_tool          VARCHAR(255)    NULL,
    severity             VARCHAR(50)     NOT NULL,
    chips                JSONB           NOT NULL DEFAULT '[]',
    environments         JSONB           NOT NULL DEFAULT '[]',
    solution             VARCHAR(255)    NULL,
    notification_channel VARCHAR(255)    NULL,
    CONSTRAINT alert_app_pkey PRIMARY KEY (id)
);

CREATE INDEX ix_alert_app_name ON alert_app (name);


CREATE TABLE default_alert_app (
    id                   UUID            NOT NULL DEFAULT gen_random_uuid(),
    raw_name             VARCHAR(255)    NOT NULL,
    display_name         VARCHAR(500)    NOT NULL,
    raw_description      TEXT,
    display_description  TEXT,
    severity             VARCHAR(50),
    notification_channel VARCHAR(100),
    excluded_namespaces  JSONB           NOT NULL DEFAULT '[]',
    included_namespaces  JSONB           NOT NULL DEFAULT '[]',
    excluded_jobs        JSONB           NOT NULL DEFAULT '[]',
    CONSTRAINT default_alert_app_pkey PRIMARY KEY (id),
    CONSTRAINT default_alert_app_raw_name_key UNIQUE (raw_name)
);


CREATE TABLE catalog_apps (
    id        UUID            NOT NULL DEFAULT gen_random_uuid(),
    object_id VARCHAR(50)     NOT NULL,
    name      VARCHAR(500)    NOT NULL,
    csw_code  VARCHAR(100)    NOT NULL,
    CONSTRAINT catalog_apps_pkey PRIMARY KEY (id),
    CONSTRAINT catalog_apps_object_id_key UNIQUE (object_id)
);

CREATE INDEX idx_catalog_apps_name ON catalog_apps (name);


CREATE TABLE catalog_app_api (
    id           UUID         NOT NULL DEFAULT gen_random_uuid(),
    app          VARCHAR(500) NOT NULL,
    microservice VARCHAR(500) NOT NULL,
    apis         JSONB        NOT NULL DEFAULT '[]',
    CONSTRAINT catalog_app_api_pkey PRIMARY KEY (id),
    CONSTRAINT catalog_app_api_microservice_key UNIQUE (microservice)
);

CREATE INDEX idx_catalog_app_api_app ON catalog_app_api (app);


CREATE TABLE alert_api (
    id                   UUID            NOT NULL DEFAULT gen_random_uuid(),
    rule_id              VARCHAR(100)    NOT NULL,
    name                 VARCHAR(500)    NOT NULL,
    severity             VARCHAR(50),
    notification_channel VARCHAR(100),
    apis_alertadas       JSONB           NOT NULL DEFAULT '[]',
    message              TEXT,
    CONSTRAINT alert_api_pkey PRIMARY KEY (id),
    CONSTRAINT alert_api_rule_id_key UNIQUE (rule_id)
);


CREATE TABLE default_alert_api (
    id                   UUID         NOT NULL DEFAULT gen_random_uuid(),
    raw_name             VARCHAR(255) NOT NULL,
    display_name         VARCHAR(500) NOT NULL,
    raw_description      TEXT,
    display_description  TEXT,
    severity             VARCHAR(50),
    notification_channel VARCHAR(100),
    excluded_apis        JSONB        NOT NULL DEFAULT '[]',
    CONSTRAINT default_alert_api_pkey PRIMARY KEY (id),
    CONSTRAINT default_alert_api_raw_name_key UNIQUE (raw_name)
);


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
