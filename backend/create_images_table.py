#!/usr/bin/env python3
"""
Script to create the missing images table in the database
"""

from core.supabase_client import supabase_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_images_table():
    """Create the missing images table"""
    
    # SQL commands to create the images table
    sql_commands = [
        # Create images table
        """
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
        """,
        
        # Create indexes
        """
        CREATE INDEX IF NOT EXISTS idx_images_project_id ON images(project_id);
        CREATE INDEX IF NOT EXISTS idx_images_blog_id ON images(blog_id);
        CREATE INDEX IF NOT EXISTS idx_images_status ON images(status);
        CREATE INDEX IF NOT EXISTS idx_images_image_number ON images(image_number);
        CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at);
        """,
        
        # Enable RLS
        """
        ALTER TABLE images ENABLE ROW LEVEL SECURITY;
        """,
        
        # Create RLS policies
        """
        CREATE POLICY "Users can view their own images" ON images
            FOR SELECT USING (project_id IN (
                SELECT id FROM projects WHERE user_id = auth.uid()
            ));
        """,
        
        """
        CREATE POLICY "Users can insert their own images" ON images
            FOR INSERT WITH CHECK (project_id IN (
                SELECT id FROM projects WHERE user_id = auth.uid()
            ));
        """,
        
        """
        CREATE POLICY "Users can update their own images" ON images
            FOR UPDATE USING (project_id IN (
                SELECT id FROM projects WHERE user_id = auth.uid()
            ));
        """,
        
        """
        CREATE POLICY "Users can delete their own images" ON images
            FOR DELETE USING (project_id IN (
                SELECT id FROM projects WHERE user_id = auth.uid()
            ));
        """,
        
        # Grant permissions
        """
        GRANT ALL ON images TO authenticated;
        """,
        
        # Add columns to existing tables if they don't exist
        """
        ALTER TABLE blogs 
        ADD COLUMN IF NOT EXISTS featured_image_url VARCHAR(500),
        ADD COLUMN IF NOT EXISTS featured_image_alt_text TEXT,
        ADD COLUMN IF NOT EXISTS featured_image_prompt TEXT;
        """,
        
        """
        ALTER TABLE projects 
        ADD COLUMN IF NOT EXISTS generate_images BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS num_images_per_blog INTEGER DEFAULT 1 CHECK (num_images_per_blog >= 1 AND num_images_per_blog <= 4),
        ADD COLUMN IF NOT EXISTS default_image_style VARCHAR(50) DEFAULT 'photographic',
        ADD COLUMN IF NOT EXISTS default_image_aspect_ratio VARCHAR(10) DEFAULT '16:9',
        ADD COLUMN IF NOT EXISTS default_image_quality VARCHAR(20) DEFAULT 'standard';
        """
    ]
    
    try:
        logger.info("🚀 Starting to create images table...")
        
        # Execute each SQL command
        for i, sql in enumerate(sql_commands, 1):
            logger.info(f"📝 Executing SQL command {i}/{len(sql_commands)}...")
            logger.debug(f"SQL: {sql.strip()}")
            
            # Execute the SQL command
            response = supabase_client.rpc('exec_sql', {'sql': sql}).execute()
            
            logger.info(f"✅ SQL command {i} executed successfully")
            
        logger.info("🎉 Images table creation completed successfully!")
        
        # Verify the table was created
        logger.info("🔍 Verifying table creation...")
        response = supabase_client.table('images').select('count').limit(1).execute()
        logger.info("✅ Images table exists and is accessible")
        
        # Check if the table has the expected structure
        logger.info("🔍 Checking table structure...")
        response = supabase_client.rpc('get_table_info', {'table_name': 'images'}).execute()
        logger.info(f"📊 Table structure: {response.data}")
        
    except Exception as e:
        logger.error(f"❌ Error creating images table: {e}")
        raise

if __name__ == "__main__":
    create_images_table()
