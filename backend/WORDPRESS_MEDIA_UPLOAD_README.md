# WordPress Media Upload Service

This service automatically uploads generated blog images to WordPress sites and updates the database with WordPress media URLs.

## 🚀 Features

- **Automatic Image Upload**: Upload images from Supabase Storage to WordPress media library
- **Batch Processing**: Process multiple images for a blog simultaneously
- **Database Integration**: Automatically update `wordpress_media_url` field in images table
- **Error Handling**: Comprehensive error handling and retry mechanisms
- **Background Processing**: Celery tasks for non-blocking uploads
- **REST API**: Full API endpoints for triggering and monitoring uploads

## 📁 File Structure

```
backend/
├── services/
│   └── wordpress_media_service.py      # Core WordPress media upload service
├── tasks/
│   └── wordpress_media_upload.py       # Celery tasks for background processing
├── routers/
│   └── wordpress_media.py              # API endpoints for WordPress media operations
└── test_wordpress_media_upload.py      # Test script for functionality verification
```

## 🔧 Setup Requirements

### 1. WordPress Account Configuration

Ensure you have a WordPress account configured in the `wordpress_accounts` table:

```sql
-- Check existing WordPress accounts
SELECT id, name, site_url, username, is_active 
FROM wordpress_accounts 
WHERE is_active = true;
```

### 2. Database Schema

The `images` table must include these fields:

```sql
-- Required fields for WordPress media upload
wordpress_media_url VARCHAR(2000),    -- WordPress media URL after upload
wordpress_media_id INTEGER,           -- WordPress media ID
```

### 3. Image Prerequisites

Images must meet these criteria before WordPress upload:

- **Status**: `generated` (successfully processed by Fal AI)
- **S3 URL**: Must have a valid `s3_url` from Supabase Storage
- **No WordPress URL**: `wordpress_media_url` must be NULL

## 📡 API Endpoints

### Upload Blog Images to WordPress

```http
POST /api/wordpress-media/upload-blog-images/{blog_id}
```

**Request Body:**
```json
{
  "wordpress_account_id": "uuid-of-wordpress-account"
}
```

**Response:**
```json
{
  "success": true,
  "message": "WordPress media upload started for 3 images",
  "task_id": "celery-task-id",
  "blog_id": "blog-uuid",
  "wordpress_account": "My WordPress Site",
  "images_count": 3,
  "status": "processing"
}
```

### Upload Single Image to WordPress

```http
POST /api/wordpress-media/upload-single-image/{image_id}
```

**Request Body:**
```json
{
  "wordpress_account_id": "uuid-of-wordpress-account"
}
```

### Get Blog Images Status

```http
GET /api/wordpress-media/blog-images/{blog_id}
```

**Response:**
```json
{
  "blog_id": "blog-uuid",
  "images": [...],
  "total_count": 3,
  "ready_for_wordpress": 2,
  "uploaded_to_wordpress": 1,
  "summary": {
    "total_images": 3,
    "generated": 2,
    "pending": 1,
    "failed": 0,
    "wordpress_ready": 2,
    "wordpress_uploaded": 1
  }
}
```

### Get WordPress Accounts

```http
GET /api/wordpress-media/wordpress-accounts
```

### Retry Failed Uploads

```http
POST /api/wordpress-media/retry-failed-uploads/{blog_id}
```

## 🔄 Workflow

### 1. Image Generation (Existing)
```
Blog Content → Image Placeholders → Fal AI Generation → Supabase Storage
```

### 2. WordPress Upload (New)
```
Supabase Storage → Download Image → WordPress REST API → Media Library → Database Update
```

### 3. Complete Flow
```
Blog Generation → Image Processing → WordPress Upload → Ready for Publishing
```

## 🎯 Usage Examples

### Python Script Example

```python
import requests

# Upload all images for a blog to WordPress
response = requests.post(
    "http://localhost:8000/api/wordpress-media/upload-blog-images/blog-uuid",
    json={"wordpress_account_id": "wp-account-uuid"}
)

print(response.json())
```

### Frontend Integration

```typescript
// Upload blog images to WordPress
const uploadImages = async (blogId: string, wordpressAccountId: string) => {
  const response = await fetch(`/api/wordpress-media/upload-blog-images/${blogId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ wordpress_account_id: wordpressAccountId })
  });
  
  return response.json();
};
```

## 🧪 Testing

### Run Test Script

```bash
cd backend
python test_wordpress_media_upload.py
```

### Test Endpoints

1. **Check WordPress accounts**: `GET /api/wordpress-media/wordpress-accounts`
2. **Check image status**: `GET /api/wordpress-media/blog-images/{blog_id}`
3. **Test upload**: `POST /api/wordpress-media/upload-blog-images/{blog_id}`

## ⚠️ Important Notes

### WordPress Requirements

- **REST API Enabled**: WordPress site must have REST API enabled
- **Authentication**: Uses Application Passwords (generate from WP user profile)
- **Permissions**: User must have media upload permissions
- **HTTPS**: Recommended for production use

### Setting Up Application Passwords

1. **Go to WordPress Admin** → Users → Profile
2. **Scroll down to "Application Passwords"**
3. **Add New Application Password**:
   - Name: "Blog Generator API"
   - Click "Add New Application Password"
4. **Copy the generated password** (it will only show once!)
5. **Use this password** in your WordPress account configuration

**Important**: Application passwords are more secure than regular passwords and can be revoked individually.

### Rate Limiting

- **Batch Processing**: Includes 0.5s delay between uploads
- **WordPress Limits**: Respects WordPress server limits
- **Error Handling**: Automatic retry for failed uploads

### Security Considerations

- **Credentials**: WordPress passwords stored in database
- **HTTPS**: All communications should use HTTPS
- **Access Control**: API endpoints should be protected

## 🚨 Troubleshooting

### Common Issues

1. **"WordPress account not found"**
   - Check if account exists and is active
   - Verify account ID in request

2. **"No images ready for WordPress upload"**
   - Ensure images have status `generated`
   - Check if images have S3 URLs
   - Verify `wordpress_media_url` is NULL

3. **"WordPress upload failed"**
   - Check WordPress site accessibility
   - Verify username/password credentials
   - Check user permissions for media upload

4. **"Database update failed"**
   - Verify database connection
   - Check table schema includes required fields

### Debug Steps

1. **Check image status**:
   ```sql
   SELECT id, status, s3_url, wordpress_media_url 
   FROM images 
   WHERE blog_id = 'your-blog-id';
   ```

2. **Verify WordPress account**:
   ```sql
   SELECT * FROM wordpress_accounts 
   WHERE id = 'your-account-id' AND is_active = true;
   ```

3. **Test WordPress connectivity**:
   - Visit `{site_url}/wp-json/wp/v2/media`
   - Check if REST API responds

## 🔮 Future Enhancements

- **Image Optimization**: Compress images before upload
- **Bulk Operations**: Upload images across multiple blogs
- **Scheduling**: Scheduled uploads at specific times
- **Webhooks**: Notify external systems on completion
- **Analytics**: Track upload success rates and performance

## 📚 Related Documentation

- [WordPress REST API Documentation](https://developer.wordpress.org/rest-api/)
- [Fal AI Image Generation](../FAL_AI_README.md)
- [Blog Image Processing](../BLOG_IMAGE_PROCESSING_README.md)
- [WordPress Publishing](../WORDPRESS_PUBLISHING_FIXES.md)
