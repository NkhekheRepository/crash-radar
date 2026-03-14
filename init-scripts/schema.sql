-- Raw Tables (populated by Airbyte)
CREATE TABLE IF NOT EXISTS raw_coingecko (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    price DECIMAL(20, 8),
    market_cap DECIMAL(20, 2),
    volume DECIMAL(20, 2),
    rsi_24h DECIMAL(10, 2),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_coinglass (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    open_interest DECIMAL(20, 2),
    oi_change_pct DECIMAL(10, 4),
    funding_rate DECIMAL(10, 6),
    funding_change DECIMAL(10, 6),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_alternative_me (
    id SERIAL PRIMARY KEY,
    fear_greed_index INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_fred (
    id SERIAL PRIMARY KEY,
    cpi DECIMAL(10, 4),
    dxy DECIMAL(10, 4),
    interest_rate DECIMAL(10, 4),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_news (
    id SERIAL PRIMARY KEY,
    headline TEXT,
    sentiment_score DECIMAL(5, 2),
    source VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Normalized Tables
CREATE TABLE IF NOT EXISTS normalized_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20, 8),
    rsi_24h DECIMAL(10, 2),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS normalized_leverage (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    open_interest DECIMAL(20, 2),
    oi_change_pct DECIMAL(10, 4),
    funding_rate DECIMAL(10, 6),
    funding_change DECIMAL(10, 6),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS normalized_sentiment (
    id SERIAL PRIMARY KEY,
    fear_greed_index INTEGER,
    news_count INTEGER,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS normalized_macro (
    id SERIAL PRIMARY KEY,
    cpi DECIMAL(10, 4),
    dxy DECIMAL(10, 4),
    interest_rate DECIMAL(10, 4),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS normalized_regulation (
    id SERIAL PRIMARY KEY,
    threat_level VARCHAR(20),
    source VARCHAR(100),
    description TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS normalized_cycle (
    id SERIAL PRIMARY KEY,
    phase VARCHAR(20),
    confidence DECIMAL(5, 2),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Signals Table
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    score INTEGER NOT NULL,
    signal_type VARCHAR(20) NOT NULL,
    btc_price DECIMAL(20, 2),
    rsi DECIMAL(10, 2),
    oi_pct DECIMAL(10, 4),
    fear_index INTEGER,
    cycle_phase VARCHAR(20),
    macro_indicator VARCHAR(20),
    regulation_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);

-- AI Predictions Table
CREATE TABLE IF NOT EXISTS signals_predicted (
    id SERIAL PRIMARY KEY,
    crash_probability DECIMAL(5, 4),
    prediction VARCHAR(10),
    confidence DECIMAL(5, 4),
    signal_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_predicted_created ON signals_predicted(created_at DESC);

-- Config table for thresholds
CREATE INDEX IF NOT EXISTS idx_normalized_leverage_timestamp ON normalized_leverage(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_normalized_sentiment_timestamp ON normalized_sentiment(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_normalized_macro_timestamp ON normalized_macro(timestamp DESC);

-- Config table for thresholds
CREATE TABLE IF NOT EXISTS config (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- System logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    component VARCHAR(50),
    status VARCHAR(20),
    message TEXT,
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_event_type ON system_logs(event_type);

-- Sync tracking
CREATE TABLE IF NOT EXISTS airbyte_sync_log (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    last_sync TIMESTAMP,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
