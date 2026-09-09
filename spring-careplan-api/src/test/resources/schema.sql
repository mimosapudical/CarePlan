CREATE TABLE IF NOT EXISTS careplans_careplan (
    id uuid PRIMARY KEY,
    status varchar(20) NOT NULL,
    history jsonb NOT NULL,
    payload jsonb NOT NULL,
    care_plan jsonb NULL,
    error text NULL,
    queued_at timestamp with time zone NULL,
    manual_retry_count integer NOT NULL DEFAULT 0,
    last_manual_retry_at timestamp with time zone NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);
