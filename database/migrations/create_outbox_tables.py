"""Create event_outbox and processed_events tables in the local test database."""
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:password@localhost:5433/healthcare")
conn = engine.connect()

conn.execute(text("""
    CREATE TABLE IF NOT EXISTS event_outbox (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_type VARCHAR(100) NOT NULL,
        event_version INTEGER DEFAULT 1 NOT NULL,
        aggregate_type VARCHAR(100) NOT NULL,
        aggregate_id UUID NOT NULL,
        payload JSONB NOT NULL,
        tenant_id UUID,
        actor_id UUID NOT NULL,
        correlation_id UUID,
        causation_id UUID,
        status VARCHAR(20) DEFAULT 'pending' NOT NULL,
        published_at TIMESTAMPTZ,
        retry_count INTEGER DEFAULT 0 NOT NULL,
        max_retries INTEGER DEFAULT 5 NOT NULL,
        last_error TEXT,
        next_retry_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
        deleted_at TIMESTAMPTZ
    )
"""))

conn.execute(text("""
    CREATE TABLE IF NOT EXISTS processed_events (
        event_id UUID NOT NULL,
        worker VARCHAR(100) NOT NULL,
        processed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
        PRIMARY KEY (event_id, worker)
    )
"""))

conn.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_outbox_pending_poll
    ON event_outbox (status, created_at)
    WHERE status = 'pending'
"""))

conn.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_outbox_failed
    ON event_outbox (status)
    WHERE status = 'failed'
"""))

conn.commit()
conn.close()
print("event_outbox and processed_events tables created successfully")
