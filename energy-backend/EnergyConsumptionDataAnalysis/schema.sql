CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS energy_history (
    id BIGSERIAL PRIMARY KEY,
    username TEXT REFERENCES users(username) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    temperature DOUBLE PRECISION NOT NULL,
    humidity DOUBLE PRECISION NOT NULL,
    squarefootage DOUBLE PRECISION NOT NULL,
    occupancy DOUBLE PRECISION NOT NULL,
    renewableenergy DOUBLE PRECISION NOT NULL DEFAULT 0,
    hvacusage SMALLINT NOT NULL DEFAULT 0,
    lightingusage SMALLINT NOT NULL DEFAULT 0,
    holiday SMALLINT NOT NULL DEFAULT 0,
    energyconsumption DOUBLE PRECISION NOT NULL CHECK (energyconsumption >= 0)
);

ALTER TABLE energy_history ADD COLUMN IF NOT EXISTS username TEXT REFERENCES users(username) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS energy_history_user_timestamp_idx ON energy_history(username, timestamp DESC);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (username, source_name, chunk_index)
);
CREATE INDEX IF NOT EXISTS knowledge_chunks_user_idx ON knowledge_chunks(username);
CREATE INDEX IF NOT EXISTS knowledge_chunks_search_idx ON knowledge_chunks USING GIN (to_tsvector('english', content));
