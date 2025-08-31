-- Update published blog statuses back to 'ready'
-- This separates generation status from publishing status

-- First, let's see what blogs currently have 'published' status
SELECT 
    id,
    status,
    project_id,
    created_at
FROM blogs 
WHERE status IN ('published', 'wordpress_published')
ORDER BY created_at DESC;

-- Update the status to 'ready' for all published blogs
UPDATE blogs 
SET status = 'ready'
WHERE status IN ('published', 'wordpress_published');

-- Verify the changes
SELECT 
    id,
    status,
    project_id,
    created_at
FROM blogs 
WHERE status = 'ready'
ORDER BY created_at DESC;

-- Show summary of the changes
SELECT 
    'Before Update' as period,
    COUNT(*) as blog_count,
    status
FROM blogs 
WHERE status IN ('published', 'wordpress_published')
GROUP BY status

UNION ALL

SELECT 
    'After Update' as period,
    COUNT(*) as blog_count,
    status
FROM blogs 
WHERE status = 'ready'
GROUP BY status;
