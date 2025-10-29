-- createdb taskflow -U postgres
CREATE TABLE IF NOT EXISTS emails (
  id                 BIGSERIAL PRIMARY KEY,
  gmail_message_id   TEXT NOT NULL UNIQUE,
  gmail_thread_id    TEXT,
  subject            TEXT,
  sender             TEXT,
  received_at        TIMESTAMPTZ,
  snippet            TEXT,
  body               TEXT,
  processed          BOOLEAN NOT NULL DEFAULT FALSE,
  first_processed_at TIMESTAMPTZ,
  last_processed_at  TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
  id                BIGSERIAL PRIMARY KEY,
  email_id          BIGINT NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
  provider          TEXT   NOT NULL,
  provider_task_id  TEXT,
  provider_metadata JSONB,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (email_id, provider)  -- no duplicate tasks for the same email+provider
);

CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);
CREATE INDEX IF NOT EXISTS idx_tasks_provider      ON tasks(provider);

-- Keep emails.updated_at fresh
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_emails_updated_at ON emails;
CREATE TRIGGER trg_emails_updated_at
BEFORE UPDATE ON emails
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
