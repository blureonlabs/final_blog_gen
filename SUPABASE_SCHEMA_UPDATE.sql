-- Migration script to update projects table field names for consistency
-- Run this in your Supabase SQL editor after running the main schema

-- Update projects table to rename total_blogs to num_blogs
ALTER TABLE projects RENAME COLUMN total_blogs TO num_blogs;

-- Update any existing data if needed (optional)
-- UPDATE projects SET num_blogs = COALESCE(num_blogs, 0) WHERE num_blogs IS NULL;

-- Verify the change
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'projects' 
AND column_name IN ('num_blogs', 'completed_blogs');

-- Add comment to document the change
COMMENT ON COLUMN projects.num_blogs IS 'Number of blogs to generate for this project (renamed from total_blogs for consistency)';
