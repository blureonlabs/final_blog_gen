-- Supabase Database Schema with Storage Integration for Blu Blog Gen
-- Run this in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create blogs table with storage references
CREATE TABLE IF NOT EXISTS blogs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    -- Content is now stored in Supabase Storage, not in this table
    -- content TEXT NOT NULL, -- REMOVED: Content stored in storage
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    word_count INTEGER DEFAULT 0,
    prompt TEXT,
    ai_model VARCHAR(100),
    
    -- Storage references
    storage_path VARCHAR(500) NOT NULL,           -- Path to content in storage
    storage_bucket VARCHAR(100) DEFAULT 'blog-content',
    content_size_bytes INTEGER,                   -- Size of content in bytes
    content_hash VARCHAR(64),                     -- MD5 hash for deduplication
    
    -- SEO and publishing
    seo_meta JSONB,
    wordpress_url VARCHAR(500),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create projects table (if not exists)
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    num_blogs INTEGER NOT NULL DEFAULT 0,
    completed_blogs INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    wordpress_account_id VARCHAR(255),
    api_keys JSONB,
    draft_creation_model VARCHAR(50) DEFAULT 'openai',
    content_vetting_model VARCHAR(50) DEFAULT 'openai',
    model_settings JSONB,
    workflow_preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create api_keys table (if not exists)
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

-- Create wordpress_accounts table (if not exists)
CREATE TABLE IF NOT EXISTS wordpress_accounts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
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
CREATE INDEX IF NOT EXISTS idx_blogs_project_id ON blogs(project_id);
CREATE INDEX IF NOT EXISTS idx_blogs_status ON blogs(status);
CREATE INDEX IF NOT EXISTS idx_blogs_created_at ON blogs(created_at);
CREATE INDEX IF NOT EXISTS idx_blogs_storage_path ON blogs(storage_path);
CREATE INDEX IF NOT EXISTS idx_blogs_content_hash ON blogs(content_hash);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_service ON api_keys(service);
CREATE INDEX IF NOT EXISTS idx_wordpress_accounts_user_id ON wordpress_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_project_id ON logs(project_id);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);

-- Create RLS (Row Level Security) policies
ALTER TABLE blogs ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE wordpress_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- Blogs policies
CREATE POLICY "Users can view their own blogs" ON blogs
    FOR SELECT USING (project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert their own blogs" ON blogs
    FOR INSERT WITH CHECK (project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can update their own blogs" ON blogs
    FOR UPDATE USING (project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can delete their own blogs" ON blogs
    FOR DELETE USING (project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    ));

-- Projects policies
CREATE POLICY "Users can view their own projects" ON projects
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own projects" ON projects
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own projects" ON projects
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own projects" ON projects
    FOR DELETE USING (user_id = auth.uid());

-- API Keys policies
CREATE POLICY "Users can view their own API keys" ON api_keys
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own API keys" ON api_keys
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own API keys" ON api_keys
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own API keys" ON api_keys
    FOR DELETE USING (user_id = auth.uid());

-- WordPress Accounts policies
CREATE POLICY "Users can view their own WordPress accounts" ON wordpress_accounts
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own WordPress accounts" ON wordpress_accounts
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own WordPress accounts" ON wordpress_accounts
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own WordPress accounts" ON wordpress_accounts
    FOR DELETE USING (user_id = auth.uid());

-- Logs policies
CREATE POLICY "Users can view their own logs" ON logs
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own logs" ON logs
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Create functions for automatic timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_blogs_updated_at BEFORE UPDATE ON blogs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wordpress_accounts_updated_at BEFORE UPDATE ON wordpress_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for blog statistics with storage info
CREATE OR REPLACE VIEW blog_stats AS
SELECT 
    p.id as project_id,
    p.name as project_name,
            p.num_blogs,
    COUNT(b.id) as blogs_generated,
    COUNT(CASE WHEN b.status = 'ready' THEN 1 END) as blogs_ready,
    COUNT(CASE WHEN b.status = 'generating' THEN 1 END) as blogs_generating,
    COUNT(CASE WHEN b.status = 'failed' THEN 1 END) as blogs_failed,
    AVG(b.word_count) as avg_word_count,
    SUM(b.content_size_bytes) as total_storage_bytes,
    ROUND(SUM(b.content_size_bytes) / 1024.0 / 1024.0, 2) as total_storage_mb
FROM projects p
LEFT JOIN blogs b ON p.id = b.project_id
GROUP BY p.id, p.name, p.num_blogs;

-- Create a function to get blog content from storage
CREATE OR REPLACE FUNCTION get_blog_content(blog_id UUID)
RETURNS JSON AS $$
DECLARE
    blog_record RECORD;
    content_url TEXT;
BEGIN
    -- Get blog metadata
    SELECT storage_path, storage_bucket INTO blog_record
    FROM blogs WHERE id = blog_id;
    
    IF NOT FOUND THEN
        RETURN json_build_object('error', 'Blog not found');
    END IF;
    
    -- Construct storage URL (this would be used by your application)
    content_url := 'https://your-project.supabase.co/storage/v1/object/public/' || 
                   blog_record.storage_bucket || '/' || blog_record.storage_path;
    
    RETURN json_build_object(
        'blog_id', blog_id,
        'storage_path', blog_record.storage_path,
        'storage_bucket', blog_record.storage_bucket,
        'content_url', content_url
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT ALL ON blogs TO authenticated;
GRANT ALL ON projects TO authenticated;
GRANT ALL ON api_keys TO authenticated;
GRANT ALL ON wordpress_accounts TO authenticated;
GRANT ALL ON logs TO authenticated;
GRANT EXECUTE ON FUNCTION get_blog_content(UUID) TO authenticated;

-- Grant access to the view
GRANT SELECT ON blog_stats TO authenticated;

-- Insert sample data for testing (optional)
-- INSERT INTO api_keys (user_id, name, service, api_key, is_default) VALUES 
-- (auth.uid(), 'OpenAI Default', 'openai', 'your-openai-key-here', true),
-- (auth.uid(), 'Gemini Default', 'gemini', 'your-gemini-key-here', true);
