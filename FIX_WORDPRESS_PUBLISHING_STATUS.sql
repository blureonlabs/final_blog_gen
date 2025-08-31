-- Fix WordPress Publishing Status Logic
-- This script updates the database to properly use the new is_published column

-- First, let's see the current state of published blogs
SELECT 
    id,
    status,
    wordpress_post_id,
    wordpress_url,
    created_at
FROM blogs 
WHERE status IN ('published', 'wordpress_published')
   OR wordpress_post_id IS NOT NULL
ORDER BY created_at DESC;

-- Update all blogs that have WordPress data to use the new logic:
-- 1. Set is_published = TRUE for blogs with WordPress data
-- 2. Change status back to 'ready' for the generation workflow

-- Step 1: Set is_published = TRUE for blogs with WordPress data
UPDATE blogs 
SET is_published = TRUE
WHERE wordpress_post_id IS NOT NULL 
   OR wordpress_url IS NOT NULL
   OR status IN ('published', 'wordpress_published');

-- Step 2: Change status back to 'ready' for published blogs
UPDATE blogs 
SET status = 'ready'
WHERE status IN ('published', 'wordpress_published');

-- Verify the changes
SELECT 
    id,
    status,
    is_published,
    wordpress_post_id,
    wordpress_url,
    created_at
FROM blogs 
WHERE is_published = TRUE
   OR wordpress_post_id IS NOT NULL
ORDER BY created_at DESC;

-- Show summary of the changes
SELECT 
    'Before Fix' as period,
    COUNT(*) as blog_count,
    status
FROM blogs 
WHERE status IN ('published', 'wordpress_published')
GROUP BY status

UNION ALL

SELECT 
    'After Fix' as period,
    COUNT(*) as blog_count,
    'ready (with is_published=TRUE)' as status
FROM blogs 
WHERE is_published = TRUE AND status = 'ready'

UNION ALL

SELECT 
    'After Fix' as period,
    COUNT(*) as blog_count,
    status
FROM blogs 
WHERE status = 'ready' AND is_published = FALSE;
