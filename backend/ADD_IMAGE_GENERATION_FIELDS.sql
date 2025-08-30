-- Add Image Generation Fields to Existing Database
-- Run this in your Supabase SQL editor after the main schema

-- Add image generation fields to blogs table
ALTER TABLE blogs 
ADD COLUMN IF NOT EXISTS featured_image_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS featured_image_alt_text TEXT,
ADD COLUMN IF NOT EXISTS featured_image_prompt TEXT,
ADD COLUMN IF NOT EXISTS image_generation_logs JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS image_generation_settings JSONB DEFAULT '{}';

-- Add image generation fields to projects table (if not already present)
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS generate_images BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS num_images_per_blog INTEGER DEFAULT 1 CHECK (num_images_per_blog >= 1 AND num_images_per_blog <= 4),
ADD COLUMN IF NOT EXISTS default_image_style VARCHAR(50) DEFAULT 'photographic',
ADD COLUMN IF NOT EXISTS default_image_aspect_ratio VARCHAR(10) DEFAULT '16:9',
ADD COLUMN IF NOT EXISTS default_image_quality VARCHAR(20) DEFAULT 'standard';

-- Create image_generations table for tracking image generation history
CREATE TABLE IF NOT EXISTS image_generations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    blog_id UUID NOT NULL REFERENCES blogs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    prompt TEXT NOT NULL,
    style VARCHAR(50) NOT NULL,
    aspect_ratio VARCHAR(10) NOT NULL,
    quality VARCHAR(20) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    alt_text TEXT,
    generation_metadata JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'generated',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for image_generations table
CREATE INDEX IF NOT EXISTS idx_image_generations_blog_id ON image_generations(blog_id);
CREATE INDEX IF NOT EXISTS idx_image_generations_user_id ON image_generations(user_id);
CREATE INDEX IF NOT EXISTS idx_image_generations_created_at ON image_generations(created_at);

-- Enable RLS on image_generations table
ALTER TABLE image_generations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for image_generations
CREATE POLICY "Users can view their own image generations" ON image_generations
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own image generations" ON image_generations
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own image generations" ON image_generations
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own image generations" ON image_generations
    FOR DELETE USING (user_id = auth.uid());

-- Create trigger for automatic timestamp updates on image_generations
CREATE TRIGGER update_image_generations_updated_at BEFORE UPDATE ON image_generations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL ON image_generations TO authenticated;

-- Create a view for image generation statistics
CREATE OR REPLACE VIEW image_generation_stats AS
SELECT 
    u.id as user_id,
    COUNT(ig.id) as total_images_generated,
    COUNT(DISTINCT ig.blog_id) as blogs_with_images,
    AVG(CASE WHEN ig.status = 'generated' THEN 1 ELSE 0 END) as success_rate,
    MAX(ig.created_at) as last_generation
FROM auth.users u
LEFT JOIN image_generations ig ON u.id = ig.user_id
GROUP BY u.id;

-- Grant access to the view
GRANT SELECT ON image_generation_stats TO authenticated;

-- Add comments for documentation
COMMENT ON TABLE image_generations IS 'Tracks individual image generation requests and results';
COMMENT ON COLUMN blogs.featured_image_url IS 'URL of the featured image for the blog post';
COMMENT ON COLUMN blogs.featured_image_alt_text IS 'Alt text for accessibility and SEO';
COMMENT ON COLUMN blogs.featured_image_prompt IS 'The prompt used to generate the featured image';
COMMENT ON COLUMN blogs.image_generation_logs IS 'JSON array of image generation logs and metadata';
COMMENT ON COLUMN blogs.image_generation_settings IS 'Settings used for image generation (style, aspect ratio, quality)';
COMMENT ON COLUMN projects.generate_images IS 'Whether to automatically generate images for blogs in this project';
COMMENT ON COLUMN projects.num_images_per_blog IS 'Number of images to generate per blog (1-4)';
COMMENT ON COLUMN projects.default_image_style IS 'Default image style for blogs in this project';
COMMENT ON COLUMN projects.default_image_aspect_ratio IS 'Default aspect ratio for images in this project';
COMMENT ON COLUMN projects.default_image_quality IS 'Default quality level for images in this project';

-- Update existing blogs to have default values
UPDATE blogs 
SET 
    image_generation_logs = '[]'::jsonb,
    image_generation_settings = '{}'::jsonb
WHERE image_generation_logs IS NULL;

-- Update existing projects to have default values
UPDATE projects 
SET 
    generate_images = FALSE,
    num_images_per_blog = 1,
    default_image_style = 'photographic',
    default_image_aspect_ratio = '16:9',
    default_image_quality = 'standard'
WHERE generate_images IS NULL;
