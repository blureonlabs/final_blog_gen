-- Supabase Storage Setup for Blu Blog Gen
-- Run this in your Supabase SQL editor

-- First, create the storage bucket for blog content
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'blog-content',
    'blog-content',
    true,  -- Make bucket public for easy access
    52428800,  -- 50MB file size limit
    ARRAY['application/json', 'text/plain', 'text/markdown']
) ON CONFLICT (id) DO NOTHING;

-- Create storage policies for the blog-content bucket
-- Allow authenticated users to upload files
CREATE POLICY "Allow authenticated users to upload blog content" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'blog-content' 
        AND auth.role() = 'authenticated'
    );

-- Allow users to view their own blog content
CREATE POLICY "Allow users to view their own blog content" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'blog-content' 
        AND (
            -- Allow public read access for published blogs
            (storage.foldername(name))[1] = 'blogs' 
            OR auth.role() = 'authenticated'
        )
    );

-- Allow users to update their own blog content
CREATE POLICY "Allow users to update their own blog content" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'blog-content' 
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'blogs'
    );

-- Allow users to delete their own blog content
CREATE POLICY "Allow users to delete their own blog content" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'blog-content' 
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'blogs'
    );

-- Create a function to ensure storage bucket exists
CREATE OR REPLACE FUNCTION ensure_storage_bucket(bucket_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if bucket exists
    IF EXISTS (SELECT 1 FROM storage.buckets WHERE id = bucket_name) THEN
        RETURN TRUE;
    ELSE
        -- Create bucket if it doesn't exist
        INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        VALUES (
            bucket_name,
            bucket_name,
            true,
            52428800,  -- 50MB
            ARRAY['application/json', 'text/plain', 'text/markdown']
        );
        RETURN TRUE;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION ensure_storage_bucket(TEXT) TO authenticated;

-- Create a function to get storage URL for a blog
CREATE OR REPLACE FUNCTION get_blog_storage_url(blog_id UUID)
RETURNS TEXT AS $$
DECLARE
    blog_record RECORD;
    storage_url TEXT;
BEGIN
    -- Get blog storage info
    SELECT storage_path, storage_bucket INTO blog_record
    FROM blogs WHERE id = blog_id;
    
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    -- Construct storage URL
    storage_url := 'https://' || current_setting('app.settings.supabase_url') || 
                   '/storage/v1/object/public/' || 
                   blog_record.storage_bucket || '/' || 
                   blog_record.storage_path;
    
    RETURN storage_url;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION get_blog_storage_url(UUID) TO authenticated;

-- Create a function to clean up orphaned storage files
CREATE OR REPLACE FUNCTION cleanup_orphaned_storage_files()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    orphaned_file RECORD;
BEGIN
    -- Find files in storage that don't have corresponding blog records
    FOR orphaned_file IN 
        SELECT o.name, o.bucket_id
        FROM storage.objects o
        WHERE o.bucket_id = 'blog-content'
        AND (storage.foldername(o.name))[1] = 'blogs'
        AND NOT EXISTS (
            SELECT 1 FROM blogs b 
            WHERE b.storage_path = o.name
        )
    LOOP
        -- Delete orphaned file
        DELETE FROM storage.objects 
        WHERE name = orphaned_file.name 
        AND bucket_id = orphaned_file.bucket_id;
        
        deleted_count := deleted_count + 1;
    END LOOP;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the cleanup function
GRANT EXECUTE ON FUNCTION cleanup_orphaned_storage_files() TO authenticated;

-- Create a view for storage usage statistics
CREATE OR REPLACE VIEW storage_usage_stats AS
SELECT 
    b.storage_bucket,
    COUNT(*) as file_count,
    SUM(b.content_size_bytes) as total_bytes,
    ROUND(SUM(b.content_size_bytes) / 1024.0 / 1024.0, 2) as total_mb,
    ROUND(AVG(b.content_size_bytes) / 1024.0, 2) as avg_kb
FROM blogs b
WHERE b.storage_path IS NOT NULL
GROUP BY b.storage_bucket;

-- Grant access to the view
GRANT SELECT ON storage_usage_stats TO authenticated;

-- Create indexes for better storage performance
CREATE INDEX IF NOT EXISTS idx_storage_objects_bucket_name ON storage.objects(bucket_id, name);
CREATE INDEX IF NOT EXISTS idx_storage_objects_created_at ON storage.objects(created_at);

-- Insert default storage bucket if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM storage.buckets WHERE id = 'blog-content') THEN
        INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
        VALUES (
            'blog-content',
            'blog-content',
            true,
            52428800,
            ARRAY['application/json', 'text/plain', 'text/markdown']
        );
    END IF;
END $$;
