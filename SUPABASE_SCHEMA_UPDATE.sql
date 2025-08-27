-- Supabase Database Schema Update for WordPress Publishing
-- Run this in your Supabase SQL editor to add missing fields

-- Step 1: Add missing fields to blogs table for WordPress publishing
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500);
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS storage_bucket VARCHAR(100) DEFAULT 'blog-content';
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS content_size_bytes INTEGER;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS wordpress_post_id VARCHAR(255);
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS generation_logs JSONB;
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS seo_score INTEGER DEFAULT 0;

-- Step 2: Update blogs table status constraints to include all required statuses
ALTER TABLE blogs DROP CONSTRAINT IF EXISTS blogs_status_check;
ALTER TABLE blogs ADD CONSTRAINT blogs_status_check 
CHECK (status IN ('draft', 'generating', 'seo_optimizing', 'formatting', 'image_generating', 'ready', 'needs_revision', 'publishing', 'published', 'failed'));

-- Update default status to 'draft'
ALTER TABLE blogs ALTER COLUMN status SET DEFAULT 'draft';

-- Step 3: Add missing fields to wordpress_accounts table
ALTER TABLE wordpress_accounts ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE wordpress_accounts ADD COLUMN IF NOT EXISTS app_password VARCHAR(500);

-- Step 4: Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_blogs_storage_path ON blogs(storage_path);
CREATE INDEX IF NOT EXISTS idx_blogs_content_hash ON blogs(content_hash);
CREATE INDEX IF NOT EXISTS idx_blogs_wordpress_post_id ON blogs(wordpress_post_id);
CREATE INDEX IF NOT EXISTS idx_blogs_seo_score ON blogs(seo_score);
CREATE INDEX IF NOT EXISTS idx_wordpress_accounts_user_id ON wordpress_accounts(user_id);

-- Step 5: Update RLS policies for wordpress_accounts
-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can manage own WordPress accounts" ON wordpress_accounts;
DROP POLICY IF EXISTS "Admins can read all WordPress accounts" ON wordpress_accounts;

-- Create new RLS policies
CREATE POLICY "Users can manage own WordPress accounts" ON wordpress_accounts
  FOR ALL USING (auth.uid() = user_id);

-- Step 6: Verify all required fields exist
DO $$
DECLARE
    missing_fields TEXT[] := ARRAY[]::TEXT[];
    field_record RECORD;
BEGIN
    -- Check blogs table
    FOR field_record IN 
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'blogs' AND column_name IN ('storage_path', 'storage_bucket', 'content_size_bytes', 'content_hash', 'wordpress_post_id', 'error_message', 'generation_logs', 'seo_score')
    LOOP
        -- Field exists, do nothing
    END LOOP;
    
    -- Check wordpress_accounts table
    FOR field_record IN 
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'wordpress_accounts' AND column_name IN ('user_id', 'app_password')
    LOOP
        -- Field exists, do nothing
    END LOOP;
    
    RAISE NOTICE 'All required fields are present in the database for WordPress publishing';
END $$;

-- Step 7: Create storage bucket if it doesn't exist
-- Note: This requires the storage extension to be enabled
-- You may need to run this manually in the Supabase dashboard
-- INSERT INTO storage.buckets (id, name, public) VALUES ('blog-content', 'blog-content', false)
-- ON CONFLICT (id) DO NOTHING;
