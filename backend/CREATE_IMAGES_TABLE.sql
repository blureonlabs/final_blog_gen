-- Create the missing images table for image generation
-- This table is referenced in the code but missing from the database schema

-- Create images table
CREATE TABLE IF NOT EXISTS images (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    blog_id UUID NOT NULL REFERENCES blogs(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    alt_text TEXT,
    image_number INTEGER NOT NULL DEFAULT 1,
    s3_url VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'generated', 'failed')),
    error_message TEXT,
    wordpress_media_id VARCHAR(255),
    wordpress_media_url VARCHAR(500),
    generation_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_images_project_id ON images(project_id);
CREATE INDEX IF NOT EXISTS idx_images_blog_id ON images(blog_id);
CREATE INDEX IF NOT EXISTS idx_images_status ON images(status);
CREATE INDEX IF NOT EXISTS idx_images_image_number ON images(image_number);
CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at);

-- Enable RLS on images table
ALTER TABLE images ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for images
CREATE POLICY "Users can view their own images" ON images
    FOR SELECT USING (project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert their own images" ON images
    FOR INSERT WITH CHECK (project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can update their own images" ON images
    FOR UPDATE USING (project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can delete their own images" ON images
    FOR DELETE USING (project_id IN (
        SELECT id FROM projects WHERE user_id = auth.uid()
    ));

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_images_updated_at BEFORE UPDATE ON images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL ON images TO authenticated;

-- Add comments for documentation
COMMENT ON TABLE images IS 'Stores generated images for blog posts';
COMMENT ON COLUMN images.prompt IS 'The prompt used to generate the image';
COMMENT ON COLUMN images.alt_text IS 'Alt text for accessibility and SEO';
COMMENT ON COLUMN images.image_number IS 'Order of the image in the blog (1 = featured, 2+ = additional)';
COMMENT ON COLUMN images.s3_url IS 'URL of the generated image';
COMMENT ON COLUMN images.status IS 'Current status of the image generation';
COMMENT ON COLUMN images.wordpress_media_id IS 'WordPress media ID if published to WordPress';
COMMENT ON COLUMN images.wordpress_media_url IS 'WordPress media URL if published to WordPress';
COMMENT ON COLUMN images.generation_metadata IS 'Additional metadata about the image generation';

-- Update existing blogs to have image generation fields if they don't exist
ALTER TABLE blogs 
ADD COLUMN IF NOT EXISTS featured_image_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS featured_image_alt_text TEXT,
ADD COLUMN IF NOT EXISTS featured_image_prompt TEXT;

-- Update existing projects to have image generation settings if they don't exist
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS generate_images BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS num_images_per_blog INTEGER DEFAULT 1 CHECK (num_images_per_blog >= 1 AND num_images_per_blog <= 4),
ADD COLUMN IF NOT EXISTS default_image_style VARCHAR(50) DEFAULT 'photographic',
ADD COLUMN IF NOT EXISTS default_image_aspect_ratio VARCHAR(10) DEFAULT '16:9',
ADD COLUMN IF NOT EXISTS default_image_quality VARCHAR(20) DEFAULT 'standard';
