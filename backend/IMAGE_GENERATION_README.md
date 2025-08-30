# Image Generation Backend

This document describes the image generation backend for the Blu Blog Gen application, which provides AI-powered image generation for blog posts using Fal AI's FLUX.1 model.

## Overview

The image generation backend consists of several components:

- **FalAIService**: Direct integration with Fal AI's FLUX.1 model
- **ImageGenerationService**: High-level service for blog image generation
- **Image Generation Router**: FastAPI endpoints for image generation
- **Database Schema**: Storage for image metadata and generation logs

## Features

### 🎨 Image Generation
- Generate 1-4 images per blog post
- Multiple artistic styles (photographic, cinematic, anime, digital-art, etc.)
- Various aspect ratios (16:9, 4:3, 1:1, 3:4, 9:16)
- Quality levels (standard, high, ultra)
- Automatic prompt optimization based on blog content

### 🔧 Technical Features
- Async/await support for non-blocking operations
- Comprehensive error handling and logging
- API key validation and management
- Rate limiting and cost control
- Image metadata storage and retrieval

## Setup

### 1. Environment Variables

Add the following to your `.env` file:

```bash
FAL_AI_API_KEY=your_fal_ai_api_key_here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Migration

Run the SQL migration script in your Supabase SQL editor:

```sql
-- Run the contents of ADD_IMAGE_GENERATION_FIELDS.sql
```

## API Endpoints

### Get Available Options

```http
GET /api/images/styles
GET /api/images/aspect-ratios
GET /api/images/qualities
```

### Generate Images

```http
POST /api/images/generate
```

**Request Body:**
```json
{
  "blog_id": "uuid",
  "title": "Blog Title",
  "content": "Blog content...",
  "seo_meta": {
    "keywords": ["keyword1", "keyword2"]
  },
  "num_images": 2,
  "style": "photographic",
  "aspect_ratio": "16:9",
  "quality": "standard"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Generated 2 images successfully",
  "blog_id": "uuid",
  "images": [
    {
      "url": "https://...",
      "prompt": "Generated prompt...",
      "style": "photographic",
      "aspect_ratio": "16:9",
      "quality": "standard",
      "generated_at": "2024-01-01T00:00:00Z",
      "variation": 1
    }
  ],
  "total_generated": 2,
  "requested_count": 2
}
```

### Manage Images

```http
GET /api/images/blog/{blog_id}
DELETE /api/images/blog/{blog_id}/image/{image_index}
```

### Utility Endpoints

```http
POST /api/images/generate-placeholder
POST /api/images/validate-api-key
```

## Usage Examples

### Python Service Usage

```python
from services.image_generation_service import ImageGenerationService

# Initialize service
image_service = ImageGenerationService()
image_service.set_fal_api_key("your_api_key")

# Generate images for a blog
result = await image_service.generate_blog_images(
    blog_id="blog-uuid",
    title="Your Blog Title",
    content="Your blog content...",
    num_images=2,
    style="digital-art",
    aspect_ratio="16:9",
    quality="high"
)

if result["success"]:
    print(f"Generated {result['total_generated']} images")
    for img in result["images"]:
        print(f"Image URL: {img['url']}")
```

### Direct Fal AI Usage

```python
from services.fal_ai_service import FalAIService

# Initialize Fal AI service
fal_service = FalAIService("your_api_key")

# Generate single image
result = await fal_service.generate_image(
    prompt="A beautiful landscape",
    style="photographic",
    aspect_ratio="16:9",
    quality="standard"
)

if result["success"]:
    print(f"Image URL: {result['image_url']}")
```

## Configuration

### Available Styles

- `photographic` - Realistic photographic style
- `cinematic` - Movie-like dramatic style
- `anime` - Japanese anime style
- `digital-art` - Digital artwork style
- `oil-painting` - Traditional oil painting style
- `watercolor` - Watercolor painting style
- `sketch` - Hand-drawn sketch style
- `cartoon` - Cartoon/comic style
- `3d-render` - 3D rendered style
- `minimalist` - Clean, minimal style
- `vintage` - Retro/vintage style
- `modern` - Contemporary design style
- `abstract` - Abstract artistic style
- `realistic` - Hyper-realistic style
- `fantasy` - Fantasy/magical style

### Available Aspect Ratios

- `16:9` - Widescreen landscape (1280x720)
- `4:3` - Standard landscape (1280x960)
- `1:1` - Square (1024x1024)
- `3:4` - Standard portrait (960x1280)
- `9:16` - Mobile portrait (720x1280)

### Available Qualities

- `standard` - 28 inference steps (faster, lower cost)
- `high` - 35 inference steps (balanced)
- `ultra` - 50 inference steps (highest quality, highest cost)

## Error Handling

The service provides comprehensive error handling:

- **API Key Issues**: Invalid or missing API keys
- **Rate Limiting**: Fal AI rate limit exceeded
- **Network Issues**: Timeout or connection errors
- **Content Issues**: Inappropriate content detection
- **Resource Issues**: Insufficient credits or quota

## Cost Management

### Fal AI Pricing
- **Standard Quality**: ~$0.01 per image
- **High Quality**: ~$0.015 per image  
- **Ultra Quality**: ~$0.02 per image

### Cost Control Features
- Maximum 4 images per blog post
- Sequential generation to avoid rate limits
- Quality level selection for cost optimization
- Batch processing for efficiency

## Testing

Run the test script to verify functionality:

```bash
cd backend
python test_image_generation.py
```

This will test:
- Fal AI service connectivity
- Image generation functionality
- Service integration
- Error handling

## Monitoring and Logging

### Database Logs
All image generation activities are logged in the `logs` table with:
- User ID and project ID
- Generation parameters
- Success/failure status
- Error messages and metadata

### Image Metadata
Generated images include:
- Original prompt used
- Generation parameters
- Timestamp and variation info
- Fal AI response metadata

## Troubleshooting

### Common Issues

1. **API Key Invalid**
   - Verify your Fal AI API key
   - Check if the key has sufficient credits
   - Ensure the key is active

2. **Generation Fails**
   - Check the error message in logs
   - Verify content appropriateness
   - Check network connectivity

3. **Slow Generation**
   - Higher quality settings take longer
   - Multiple images are generated sequentially
   - Consider using standard quality for faster results

### Debug Mode

Enable detailed logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security

- All endpoints require authentication
- Row-level security (RLS) enabled
- User can only access their own images
- API keys are stored securely in database

## Performance

### Optimization Tips
- Use standard quality for bulk generation
- Generate images in parallel when possible
- Cache generated images for reuse
- Monitor API usage and costs

### Rate Limits
- Fal AI: ~10 requests per minute
- Sequential processing to avoid limits
- Automatic retry with exponential backoff

## Future Enhancements

- **Multiple AI Providers**: DALL-E, Stable Diffusion, Midjourney
- **Image Editing**: Inpainting, outpainting, style transfer
- **Batch Processing**: Generate images for multiple blogs
- **Smart Cropping**: Automatic aspect ratio optimization
- **Image Analytics**: Usage statistics and cost tracking

## Support

For issues or questions:
1. Check the logs for error details
2. Verify your API key and credits
3. Test with the provided test script
4. Review the error handling documentation

## License

This image generation backend is part of the Blu Blog Gen project and follows the same licensing terms.
