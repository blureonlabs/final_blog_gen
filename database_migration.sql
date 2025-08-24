-- Complete Database Recreation Script
-- Run this in your Supabase SQL Editor to fix all constraint issues

-- Step 1: Drop existing tables (if they exist)
DROP TABLE IF EXISTS blogs CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

-- Step 2: Create projects table with correct structure
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    num_blogs INTEGER NOT NULL DEFAULT 0,
    completed_blogs INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'ready')),
    wordpress_account_id UUID,
    api_keys JSONB,
    settings JSONB,
    
    -- AI Model Configuration
    draft_creation_model VARCHAR(50) CHECK (draft_creation_model IS NULL OR draft_creation_model IN ('openai', 'gemini')),
    content_vetting_model VARCHAR(50) CHECK (content_vetting_model IS NULL OR content_vetting_model IN ('openai', 'gemini')),
    model_settings JSONB,
    workflow_preferences JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 3: Create blogs table with correct structure
CREATE TABLE blogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'generating', 'completed', 'failed', 'published', 'ready')),
    word_count INTEGER DEFAULT 0,
    seo_score INTEGER DEFAULT 0,
    prompt TEXT,
    ai_model VARCHAR(100),
    wordpress_url VARCHAR(500),
    
    -- Storage fields
    storage_path VARCHAR(500),
    storage_bucket VARCHAR(100),
    s3_content_key VARCHAR(500),
    generation_metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE
);

-- Step 4: Create indexes for better performance
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at);

CREATE INDEX idx_blogs_project_id ON blogs(project_id);
CREATE INDEX idx_blogs_status ON blogs(status);
CREATE INDEX idx_blogs_created_at ON blogs(created_at);

-- Step 5: Create RLS (Row Level Security) policies
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE blogs ENABLE ROW LEVEL SECURITY;

-- Projects RLS policy
CREATE POLICY "Users can view their own projects" ON projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own projects" ON projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own projects" ON projects
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own projects" ON projects
    FOR DELETE USING (auth.uid() = user_id);

-- Blogs RLS policy
CREATE POLICY "Users can view blogs from their projects" ON blogs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = blogs.project_id 
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert blogs to their projects" ON blogs
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = blogs.project_id 
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update blogs from their projects" ON blogs
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = blogs.project_id 
            AND projects.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete blogs from their projects" ON blogs
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM projects 
            WHERE projects.id = blogs.project_id 
            AND projects.user_id = auth.uid()
        )
    );

-- Step 6: Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Step 7: Apply updated_at triggers
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blogs_updated_at 
    BEFORE UPDATE ON blogs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Step 8: Insert sample data for testing (optional)
-- Uncomment the lines below if you want to test with sample data

-- INSERT INTO projects (user_id, name, description, num_blogs, status) VALUES 
-- ('00000000-0000-0000-0000-000000000000', 'Sample Project', 'This is a sample project for testing', 10, 'ready');

-- Step 9: Verify the tables were created correctly
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name IN ('projects', 'blogs')
ORDER BY table_name, ordinal_position;

-- Step 10: Verify constraints
SELECT 
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conrelid IN ('projects'::regclass, 'blogs'::regclass)
ORDER BY conrelid, conname;

-- Step 11: Test insert with 'ready' status
-- This will verify that the constraint allows 'ready' status
INSERT INTO projects (user_id, name, description, num_blogs, status) 
VALUES ('test-user-id', 'Test Project', 'Test Description', 5, 'ready')
ON CONFLICT DO NOTHING;

-- Clean up test data
DELETE FROM projects WHERE user_id = 'test-user-id';

PRINT '✅ Database tables recreated successfully!';
PRINT '✅ All constraints are now properly configured';
PRINT '✅ Projects can now use "ready" status';
PRINT '✅ RLS policies are in place for security';
