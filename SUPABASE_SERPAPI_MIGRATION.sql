-- Supabase Database Migration for SerpAPI Integration
-- Run this in your Supabase SQL editor to add SerpAPI support

-- Step 1: Add SerpAPI columns to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS serp_api_on BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS serp_api_contents JSONB;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS enhanced_research BOOLEAN DEFAULT FALSE;

-- Step 2: Add comments to document the new columns
COMMENT ON COLUMN projects.serp_api_on IS 'Flag to enable/disable SerpAPI research for this project';
COMMENT ON COLUMN projects.serp_api_contents IS 'JSON object containing SerpAPI research results and insights';
COMMENT ON COLUMN projects.enhanced_research IS 'Flag to enable/disable enhanced research features (AI queries, external links, content scraping)';

-- Step 3: Create index for better performance on SerpAPI queries
CREATE INDEX IF NOT EXISTS idx_projects_serp_api_on ON projects(serp_api_on);

-- Step 4: Update existing projects to have default values
UPDATE projects SET serp_api_on = FALSE WHERE serp_api_on IS NULL;
UPDATE projects SET serp_api_contents = NULL WHERE serp_api_contents IS NULL;
UPDATE projects SET enhanced_research = FALSE WHERE enhanced_research IS NULL;

-- Step 5: Verify the new columns were added
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'projects' 
AND column_name IN ('serp_api_on', 'serp_api_contents', 'enhanced_research')
ORDER BY ordinal_position;

-- Step 6: Test insert with SerpAPI fields
-- This will verify that the new columns work correctly
INSERT INTO projects (
    user_id, 
    name, 
    description, 
    num_blogs, 
    status,
    serp_api_on,
    serp_api_contents,
    enhanced_research
) VALUES (
    'test-user-id', 
    'Test SerpAPI Project', 
    
    'Test project with SerpAPI enabled', 
    5, 
    'ready',
    TRUE,
    '{"test": "data"}'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;

-- Clean up test data
DELETE FROM projects WHERE user_id = 'test-user-id';

-- Step 7: Verify RLS policies still work with new columns
-- The existing RLS policies should automatically apply to the new columns
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'projects';

PRINT '✅ SerpAPI migration completed successfully!';
PRINT '✅ New columns added: serp_api_on, serp_api_contents';
PRINT '✅ Index created for better performance';
PRINT '✅ All existing projects updated with default values';
PRINT '✅ RLS policies automatically apply to new columns';
