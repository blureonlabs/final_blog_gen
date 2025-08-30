# Blog Image Processing Service

This service automatically processes blog content, extracts image placeholders, and generates images using Fal AI FLUX.1 model.

## Overview

The Blog Image Processing Service provides a complete workflow for:

1. **Extracting** `[image:description]` placeholders from blog content
2. **Storing** image metadata in the `images` table
3. **Generating** images using Fal AI FLUX.1 model
4. **Updating** the database with generated image URLs

## API Endpoints

### 1. Process Blog for Images
**POST** `/api/blog-images/process-blog`

Extracts image placeholders from blog content and stores them in the database.

**Request Body:**
```json
{
  "blog_id": "uuid",
  "project_id": "uuid", 
  "title": "Blog Title",
  "content": "Blog content with [image:description] placeholders",
  "style": "photographic",           // optional, default: photographic
  "aspect_ratio": "16:9",           // optional, default: 16:9
  "quality": "standard"              // optional, default: standard
}
```

**Response:**
```json
{
  "success": true,
  "message": "Processed 2 image placeholders",
  "blog_id": "uuid",
  "project_id": "uuid",
  "images_processed": 2,
  "stored_images": [...]
}
```

### 2. Generate Images for Blog
**POST** `/api/blog-images/generate-images`

Generates images for all pending image placeholders in a blog.

**Request Body:**
```json
{
  "blog_id": "uuid",
  "project_id": "uuid",
  "style": "photographic",           // optional
  "aspect_ratio": "16:9",           // optional
  "quality": "standard"              // optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Generated 2 images, 0 failed",
  "blog_id": "uuid",
  "project_id": "uuid",
  "images_generated": 2,
  "images_failed": 0,
  "generated_images": [...],
  "failed_images": [...]
}
```

### 3. Complete Workflow
**POST** `/api/blog-images/process-and-generate`

Runs the complete workflow: process blog content and generate images in one call.

**Request Body:**
```json
{
  "blog_id": "uuid",
  "project_id": "uuid",
  "title": "Blog Title",
  "content": "Blog content with [image:description] placeholders",
  "style": "photographic",           // optional
  "aspect_ratio": "16:9",           // optional
  "quality": "standard"              // optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Complete workflow completed: 2 processed, 2 generated",
  "blog_id": "uuid",
  "project_id": "uuid",
  "workflow_summary": {
    "total_images_processed": 2,
    "total_images_generated": 2,
    "total_images_failed": 0
  },
  "workflow_details": {...}
}
```

### 4. Get Blog Image Status
**GET** `/api/blog-images/blog/{blog_id}/status`

Get the current status of image generation for a specific blog.

**Response:**
```json
{
  "success": true,
  "blog_id": "uuid",
  "blog_title": "Blog Title",
  "total_images": 2,
  "status_summary": {
    "pending": 0,
    "generating": 0,
    "generated": 2,
    "failed": 0
  },
  "images": [...]
}
```

## Image Placeholder Format

The service recognizes image placeholders in the following format:

```
[image:Description of what the image should show]
```

**Examples:**
- `[image:Modern office workspace with productivity tools and organized desk setup]`
- `[image:Team collaboration meeting with whiteboard and digital displays]`
- `[image:Data visualization dashboard showing analytics and metrics]`

## Database Schema

The service uses the following `images` table structure:

```sql
CREATE TABLE IF NOT EXISTS images (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    blog_id UUID NOT NULL REFERENCES blogs(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    image_number INTEGER NOT NULL,
    s3_url VARCHAR(500),
    wordpress_media_id VARCHAR(100),
    wordpress_media_url VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'generating',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Status Values

- **`pending`**: Image placeholder extracted, waiting for generation
- **`generating`**: Image is currently being generated
- **`generated`**: Image successfully generated and stored
- **`failed`**: Image generation failed

## Prerequisites

1. **Fal AI API Key**: User must have an active Fal AI API key configured
2. **Project Settings**: Project must have `generate_images: true`
3. **Blog Content**: Blog must contain `[image:description]` placeholders

## Usage Flow

### Step 1: Generate Blog with Image Placeholders
First, generate a blog using the content generation service with `generate_images: true` and `num_images_per_blog: 1-4`. The AI will include image placeholders like:

```
[image:Header image showing the main topic]
... content ...
[image:Illustration of key concept]
... content ...
[image:Example or case study visualization]
```

### Step 2: Process and Generate Images
Call the `/api/blog-images/process-and-generate` endpoint with the blog content to:

1. Extract all `[image:description]` placeholders
2. Store them in the `images` table with status `pending`
3. Generate images using Fal AI FLUX.1 model
4. Update the database with generated image URLs

### Step 3: Monitor Status
Use `/api/blog-images/blog/{blog_id}/status` to monitor the progress of image generation.

## Error Handling

The service includes comprehensive error handling:

- **Validation**: Checks for required fields and user permissions
- **API Key Validation**: Ensures Fal AI API key is available
- **Status Tracking**: Tracks success/failure for each image
- **Logging**: Detailed logging for debugging and monitoring
- **Fallback**: Continues processing even if individual images fail

## Configuration

### Image Styles
- `photographic`, `cinematic`, `anime`, `digital-art`, `oil-painting`, `watercolor`, `sketch`, `cartoon`, `3d-render`, `minimalist`, `vintage`, `modern`, `abstract`, `realistic`, `fantasy`

### Aspect Ratios
- `16:9` (landscape widescreen), `4:3` (landscape standard), `1:1` (square), `3:4` (portrait standard), `9:16` (portrait mobile)

### Quality Levels
- `standard` (28 inference steps), `high` (35 inference steps), `ultra` (50 inference steps)

## Testing

Run the test script to verify the service works correctly:

```bash
python3 test_blog_image_processor.py
```

This will test:
- Image placeholder extraction from various content formats
- Handling of malformed placeholders
- Edge cases and error scenarios

## Integration

The service integrates with:
- **Blog Generation Service**: Receives blogs with image placeholders
- **Fal AI Service**: Generates images using FLUX.1 model
- **Database**: Stores image metadata and URLs
- **Logging System**: Tracks all operations and errors

## Security

- **User Authentication**: All endpoints require valid JWT tokens
- **Ownership Validation**: Users can only access their own projects and blogs
- **API Key Management**: Secure handling of Fal AI API keys
- **Input Validation**: Comprehensive validation of all input parameters
