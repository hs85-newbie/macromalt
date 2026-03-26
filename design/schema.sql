-- ============================================================
-- macromalt SaaS — PostgreSQL 스키마 (Phase 24 M0)
-- 로컬 개발: SQLite 호환 (CREATE TABLE IF NOT EXISTS)
-- 프로덕션: Railway PostgreSQL
-- ============================================================

-- ── 1. users ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(100),
    plan          VARCHAR(20) NOT NULL DEFAULT 'free',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ── 2. subscriptions ─────────────────────────────────────────
-- Toss Payments 구독 (Type B 월정액)
CREATE TABLE IF NOT EXISTS subscriptions (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    toss_billing_key  VARCHAR(255),
    toss_customer_key VARCHAR(255),
    plan              VARCHAR(20) NOT NULL DEFAULT 'pro',
    status            VARCHAR(20) NOT NULL DEFAULT 'inactive',
    amount            INTEGER NOT NULL DEFAULT 49900,
    next_billing_at   TIMESTAMP,
    cancelled_at      TIMESTAMP,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);

-- ── 3. user_api_keys ─────────────────────────────────────────
-- BYOK API 키 (AES-256-GCM 암호화 저장)
CREATE TABLE IF NOT EXISTS user_api_keys (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider       VARCHAR(30) NOT NULL,
    key_enc        TEXT NOT NULL,
    iv             VARCHAR(64) NOT NULL,
    is_valid       BOOLEAN NOT NULL DEFAULT TRUE,
    last_tested_at TIMESTAMP,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

-- ── 4. user_wp_settings ──────────────────────────────────────
-- WordPress 연결 정보 (비밀번호 AES-256-GCM 암호화)
CREATE TABLE IF NOT EXISTS user_wp_settings (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    site_url          VARCHAR(500) NOT NULL,
    username          VARCHAR(100) NOT NULL,
    password_enc      TEXT NOT NULL,
    iv                VARCHAR(64) NOT NULL,
    category_analysis INTEGER DEFAULT 2,
    category_picks    INTEGER DEFAULT 3,
    category_default  INTEGER DEFAULT 1,
    is_connected      BOOLEAN NOT NULL DEFAULT FALSE,
    last_tested_at    TIMESTAMP,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── 5. user_pipeline_settings ────────────────────────────────
-- 파이프라인 실행 설정
CREATE TABLE IF NOT EXISTS user_pipeline_settings (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    enabled           BOOLEAN NOT NULL DEFAULT FALSE,
    slot              VARCHAR(20) DEFAULT 'morning',
    max_posts_per_run INTEGER DEFAULT 3,
    language          VARCHAR(10) DEFAULT 'ko',
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── 6. run_logs ──────────────────────────────────────────────
-- 파이프라인 실행 이력
CREATE TABLE IF NOT EXISTS run_logs (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status        VARCHAR(20) NOT NULL,
    slot          VARCHAR(20),
    triggered_by  VARCHAR(20) DEFAULT 'manual',
    started_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at   TIMESTAMP,
    error_message TEXT,
    cost_usd      NUMERIC(10, 6) DEFAULT 0,
    cost_krw      INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_run_logs_user_id ON run_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_run_logs_started_at ON run_logs(started_at DESC);

-- ── 7. published_posts ───────────────────────────────────────
-- WordPress 발행 포스트 이력
CREATE TABLE IF NOT EXISTS published_posts (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    run_log_id   INTEGER REFERENCES run_logs(id),
    wp_post_id   INTEGER,
    wp_post_url  TEXT,
    title        TEXT NOT NULL,
    category     VARCHAR(50),
    published_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_published_posts_user_id ON published_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_published_posts_published_at ON published_posts(published_at DESC);
