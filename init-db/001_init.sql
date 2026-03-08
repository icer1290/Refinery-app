-- Initialize pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- News Articles Table (shared by both services)
-- =====================================================
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(255) NOT NULL,
    source_url VARCHAR(2048) UNIQUE NOT NULL,
    original_title TEXT NOT NULL,
    original_description TEXT,
    chinese_title TEXT,
    chinese_summary TEXT,
    full_content TEXT,
    total_score FLOAT,
    industry_impact_score FLOAT,
    milestone_score FLOAT,
    attention_score FLOAT,
    published_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reflection_retries INTEGER DEFAULT 0,
    reflection_passed BOOLEAN DEFAULT FALSE,
    reflection_feedback TEXT,
    is_published BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

-- =====================================================
-- Article Embeddings Table (with vector support)
-- =====================================================
CREATE TABLE IF NOT EXISTS article_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID UNIQUE NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    embedding vector(1536),
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- RSS Feed Sources Table
-- =====================================================
CREATE TABLE IF NOT EXISTS rss_feed_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(2048) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_fetched_at TIMESTAMP WITH TIME ZONE,
    fetch_error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Workflow Runs Table
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'running',
    total_feeds_fetched INTEGER DEFAULT 0,
    total_articles_found INTEGER DEFAULT 0,
    total_articles_after_dedup INTEGER DEFAULT 0,
    total_articles_after_scoring INTEGER DEFAULT 0,
    total_articles_stored INTEGER DEFAULT 0,
    errors JSONB,
    metadata JSONB
);

-- =====================================================
-- Users Table (api-server)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- User Preferences Table (api-server)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE REFERENCES users(id),
    preferred_categories JSONB,
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- Favorites Table (api-server)
-- =====================================================
CREATE TABLE IF NOT EXISTS favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    article_id UUID NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, article_id)
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Vector index for similarity search (IVFFlat)
CREATE INDEX IF NOT EXISTS ix_article_embeddings_embedding ON article_embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- News articles indexes
CREATE INDEX IF NOT EXISTS ix_news_articles_source_url ON news_articles(source_url);
CREATE INDEX IF NOT EXISTS ix_news_articles_published_at ON news_articles(published_at);
CREATE INDEX IF NOT EXISTS ix_news_articles_total_score ON news_articles(total_score);

-- Article embeddings indexes
CREATE INDEX IF NOT EXISTS ix_article_embeddings_article_id ON article_embeddings(article_id);
CREATE INDEX IF NOT EXISTS ix_article_embeddings_content_hash ON article_embeddings(content_hash);

-- RSS feed sources indexes
CREATE INDEX IF NOT EXISTS ix_rss_feed_sources_url ON rss_feed_sources(url);
CREATE INDEX IF NOT EXISTS ix_rss_feed_sources_is_active ON rss_feed_sources(is_active);

-- Workflow runs index
CREATE INDEX IF NOT EXISTS ix_workflow_runs_started_at ON workflow_runs(started_at);

-- Users index
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);