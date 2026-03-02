-- Advanced Meeting Features Database Schema
-- This schema supports video conferencing with AI-powered sign language recognition

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

-- Meetings table
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    host_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    is_locked BOOLEAN DEFAULT FALSE,
    waiting_room_enabled BOOLEAN DEFAULT FALSE,
    recording_enabled BOOLEAN DEFAULT FALSE,
    max_participants INTEGER DEFAULT 100,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Participants table
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    joined_at TIMESTAMP DEFAULT NOW(),
    left_at TIMESTAMP,
    is_host BOOLEAN DEFAULT FALSE,
    is_co_host BOOLEAN DEFAULT FALSE,
    audio_enabled BOOLEAN DEFAULT TRUE,
    video_enabled BOOLEAN DEFAULT TRUE
);

-- Recordings table
CREATE TABLE recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP NOT NULL,
    duration_seconds INTEGER NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    storage_url TEXT NOT NULL,
    thumbnail_url TEXT,
    status VARCHAR(50) DEFAULT 'processing'
);

-- Transcripts table
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recording_id UUID REFERENCES recordings(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    format VARCHAR(50) DEFAULT 'json',
    storage_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sign language captions table
CREATE TABLE sign_language_captions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    gesture TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    model_version VARCHAR(50) NOT NULL
);

-- ML experiments table (MLflow integration)
CREATE TABLE ml_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    description TEXT
);

-- ML runs table
CREATE TABLE ml_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES ml_experiments(id) ON DELETE CASCADE,
    run_name VARCHAR(255),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'running',
    hyperparameters JSONB NOT NULL,
    metrics JSONB NOT NULL,
    dataset_hash VARCHAR(64) NOT NULL,
    model_version VARCHAR(50)
);

-- Model versions table
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    run_id UUID REFERENCES ml_runs(id),
    created_at TIMESTAMP DEFAULT NOW(),
    deployment_status VARCHAR(50) DEFAULT 'experimental',
    performance_metrics JSONB NOT NULL,
    storage_url TEXT NOT NULL,
    UNIQUE(model_name, version)
);

-- Drift metrics table
CREATE TABLE drift_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version_id UUID REFERENCES model_versions(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Analytics events table
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_meetings_host_id ON meetings(host_id);
CREATE INDEX idx_participants_meeting_id ON participants(meeting_id);
CREATE INDEX idx_participants_user_id ON participants(user_id);
CREATE INDEX idx_recordings_meeting_id ON recordings(meeting_id);
CREATE INDEX idx_transcripts_recording_id ON transcripts(recording_id);
CREATE INDEX idx_sign_language_captions_meeting_id ON sign_language_captions(meeting_id);
CREATE INDEX idx_sign_language_captions_timestamp ON sign_language_captions(timestamp);
CREATE INDEX idx_ml_runs_experiment_id ON ml_runs(experiment_id);
CREATE INDEX idx_model_versions_deployment_status ON model_versions(deployment_status);
CREATE INDEX idx_drift_metrics_model_version_id ON drift_metrics(model_version_id);
CREATE INDEX idx_drift_metrics_timestamp ON drift_metrics(timestamp);
CREATE INDEX idx_analytics_events_meeting_id ON analytics_events(meeting_id);
CREATE INDEX idx_analytics_events_timestamp ON analytics_events(timestamp);
