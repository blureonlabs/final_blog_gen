# WordPress Setup Guide

## 🔑 Setting Up Application Passwords

### Step 1: Access WordPress Admin
1. Go to your WordPress site: `https://yoursite.com/wp-admin`
2. Log in with your admin account

### Step 2: Generate Application Password
1. Go to **Users** → **Profile**
2. Scroll down to **"Application Passwords"** section
3. In the **"Add New Application Password"** field:
   - Name: `Blog Generator API`
   - Click **"Add New Application Password"**
4. **Copy the generated password** (it will only show once!)

### Step 3: Configure in Your System
1. Go to your project settings
2. Add WordPress account with:
   - **Site URL**: `https://yoursite.com`
   - **Username**: Your WordPress username
   - **Password**: The application password you just generated

## 🧪 Testing Your Setup

### Run the Simple Test
```bash
cd backend
python3 test_wordpress_upload_simple.py
```

This will test:
- ✅ WordPress site connectivity
- ✅ REST API access
- ✅ Authentication with application password
- ✅ User permissions for media upload

### Expected Output
```
✅ WordPress REST API is accessible
✅ WordPress authentication successful!
✅ User has media upload permissions
✅ Found X images ready for upload
```

## 🚨 Common Issues

### 1. "Cannot connect to WordPress site"
- Check if site URL is correct
- Ensure site is accessible from your server
- Verify REST API is enabled

### 2. "WordPress authentication failed"
- Username is correct
- Application password is correct (not regular password)
- Application password was generated from WP user profile

### 3. "User may not have media upload permissions"
- User role should be: author, editor, or administrator
- Check user capabilities in WordPress

## 🔗 WordPress REST API Endpoints

- **Media Upload**: `https://yoursite.com/wp-json/wp/v2/media`
- **Posts**: `https://yoursite.com/wp-json/wp/v2/posts`
- **Users**: `https://yoursite.com/wp-json/wp/v2/users`

## 📚 Additional Resources

- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Application Passwords Documentation](https://wordpress.org/support/article/using-application-passwords/)
- [Media Endpoints Reference](https://developer.wordpress.org/rest-api/reference/media/)

## 🎯 Next Steps

Once setup is complete:
1. **New blogs** will automatically upload images to WordPress
2. **Existing blogs** can be manually triggered for upload
3. **Monitor progress** using the status endpoints
4. **Images** will be available in your WordPress media library

Your WordPress integration is now ready! 🚀
