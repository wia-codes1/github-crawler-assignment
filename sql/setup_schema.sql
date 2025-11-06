CREATE TABLE IF NOT EXISTS repo_summary (
  repo_id BIGINT PRIMARY KEY,
  full_name TEXT NOT NULL,
  owner_login TEXT NOT NULL,
  name TEXT NOT NULL,
  stars INTEGER NOT NULL,
  html_url TEXT,
  archived BOOLEAN DEFAULT FALSE,
  fetched_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS repo_changes (
  id BIGSERIAL PRIMARY KEY,
  repo_id BIGINT NOT NULL,
  field TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  changed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_repo_fetched_at ON repo_summary(fetched_at);
