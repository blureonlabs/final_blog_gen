-- Fix image URL length issues in the images table
-- This script increases the VARCHAR length for URL fields to handle longer URLs

-- Update s3_url field to handle longer URLs (Supabase Storage URLs can be long)
ALTER TABLE images ALTER COLUMN s3_url TYPE VARCHAR(2000);

-- Update wordpress_media_url field as well
ALTER TABLE images ALTER COLUMN wordpress_media_url TYPE VARCHAR(2000);

-- Add comment to document the change
COMMENT ON COLUMN images.s3_url IS 'Supabase Storage URL for generated image (increased to VARCHAR(2000) to handle long URLs)';
COMMENT ON COLUMN images.wordpress_media_url IS 'WordPress media URL (increased to VARCHAR(2000) to handle long URLs)';

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'images' 
AND column_name IN ('s3_url', 'wordpress_media_url')
ORDER BY column_name;
