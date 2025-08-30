-- Migration: Add Image Generation and SerpAPI fields to projects table
-- Date: 2024-12-19

-- First, rename total_blogs to num_blogs to match frontend expectations
ALTER TABLE projects 
RENAME COLUMN IF EXISTS total_blogs TO num_blogs;

-- Add new columns to projects table
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS generate_images BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS num_images_per_blog INTEGER DEFAULT 1 CHECK (num_images_per_blog >= 1 AND num_images_per_blog <= 4),
ADD COLUMN IF NOT EXISTS serp_api_on BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS enhanced_research BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS serp_api_contents TEXT;

-- Add comment to explain the new fields
COMMENT ON COLUMN projects.generate_images IS 'Enable image generation for blogs';
COMMENT ON COLUMN projects.num_images_per_blog IS 'Number of images per blog (1-4)';
COMMENT ON COLUMN projects.serp_api_on IS 'Enable SerpAPI research for content generation';
COMMENT ON COLUMN projects.enhanced_research IS 'Enable enhanced research features';
COMMENT ON COLUMN projects.serp_api_contents IS 'Stored SerpAPI research content';

-- Update existing projects to have default values
UPDATE projects 
SET 
    generate_images = FALSE,
    num_images_per_blog = 1,
    serp_api_on = FALSE,
    enhanced_research = FALSE
WHERE generate_images IS NULL 
   OR num_images_per_blog IS NULL 
   OR serp_api_on IS NULL 
   OR enhanced_research IS NULL;

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'projects' 
  AND column_name IN ('generate_images', 'num_images_per_blog', 'serp_api_on', 'enhanced_research', 'serp_api_contents')
ORDER BY column_name;
