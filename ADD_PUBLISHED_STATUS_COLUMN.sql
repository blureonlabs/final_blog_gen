-- Add separate published status column to blogs table
-- This allows tracking generation progress and publishing status independently

-- Add the new column
ALTER TABLE blogs ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE;

-- Add an index for better query performance
CREATE INDEX IF NOT EXISTS idx_blogs_is_published ON blogs(is_published);

-- Update existing blogs to set is_published based on current status
-- Assuming blogs with status 'published' or 'wordpress_published' are already published
UPDATE blogs 
SET is_published = TRUE 
WHERE status IN ('published', 'wordpress_published');

-- Add a comment to document the column
COMMENT ON COLUMN blogs.is_published IS 'Indicates whether the blog has been published to WordPress (separate from generation status)';

-- Show the updated table structure
\d blogs;
