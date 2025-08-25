-- Comprehensive Database Schema for Blu Blog Gen
-- This schema matches the expected project JSON structure

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create projects table with all required fields
CREATE TABLE IF NOT EXISTS projects (
    idx SERIAL PRIMARY KEY,  -- Auto-incrementing index
    id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,  -- UUID for the project
    user_id UUID NOT NULL,  -- User who owns the project
    name VARCHAR(255) NOT NULL,  -- Project name
    description TEXT,  -- Project description
    num_blogs INTEGER NOT NULL DEFAULT 0,  -- Number of blogs to generate
    completed_blogs INTEGER NOT NULL DEFAULT 0,  -- Number of completed blogs
    status VARCHAR(50) NOT NULL DEFAULT 'ready',  -- Project status (ready, in_progress, completed, failed)
    wordpress_account_id UUID,  -- WordPress account ID (nullable)
    api_keys JSONB,  -- API keys configuration as JSON
    settings JSONB,  -- Project settings as JSON
    draft_creation_model VARCHAR(50),  -- Model for draft creation
    content_vetting_model VARCHAR(50),  -- Model for content vetting
    model_settings JSONB,  -- Model-specific settings as JSON
    workflow_preferences JSONB,  -- Workflow preferences as JSON
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create blogs table
CREATE TABLE IF NOT EXISTS blogs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    word_count INTEGER DEFAULT 0,
    prompt TEXT,
    ai_model VARCHAR(100),
    seo_meta JSONB,
    wordpress_url VARCHAR(500),
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    service VARCHAR(50) NOT NULL CHECK (service IN ('openai', 'gemini', 'serp', 'other')),
    api_key TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create wordpress_accounts table
CREATE TABLE IF NOT EXISTS wordpress_accounts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    site_url VARCHAR(500) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create logs table for tracking blog generation
CREATE TABLE IF NOT EXISTS logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    blog_id UUID REFERENCES blogs(id) ON DELETE SET NULL,
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    category VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_projects_idx ON projects(idx);
CREATE INDEX IF NOT EXISTS idx_projects_id ON projects(id);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

CREATE INDEX IF NOT EXISTS idx_blogs_project_id ON blogs(project_id);
CREATE INDEX IF NOT EXISTS idx_blogs_status ON blogs(status);
CREATE INDEX IF NOT EXISTS idx_blogs_created_at ON blogs(created_at);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_service ON api_keys(service);

CREATE INDEX IF NOT EXISTS idx_wordpress_accounts_user_id ON wordpress_accounts(user_id);

CREATE INDEX IF NOT EXISTS idx_logs_project_id ON logs(project_id);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);

-- Create RLS (Row Level Security) policies
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE blogs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE wordpress_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (you may want to customize these)
CREATE POLICY "Users can view their own projects" ON projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own projects" ON projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own projects" ON projects
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own projects" ON projects
    FOR DELETE USING (auth.uid() = user_id);

-- Insert sample data for testing (optional)
-- INSERT INTO projects (user_id, name, description, num_blogs, status) 
-- VALUES (
--     '00000000-0000-0000-0000-000000000000',
--     'Test Project',
--     'Test Description',
--     5,
--     'ready'
-- );

-- Verify the schema
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'projects' 
ORDER BY ordinal_position;
