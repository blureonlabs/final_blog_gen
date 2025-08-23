# Supabase Setup Guide

## 🔧 **Database Tables Setup**

### **Step 1: Create Users Table**
```sql
-- Drop existing table if it exists
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255),
  role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'moderator', 'admin')),
  is_active BOOLEAN DEFAULT true,
  subscription_plan VARCHAR(50) DEFAULT 'free',
  subscription_expires_at TIMESTAMP WITH TIME ZONE,
  api_usage_limit INTEGER DEFAULT 1000,
  api_usage_current INTEGER DEFAULT 0,
  last_login TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  features_enabled JSONB DEFAULT '{"blog_generation": true, "wordpress_accounts": false, "ai_image_generation": false, "advanced_features": false}'::jsonb,
  feature_limits JSONB DEFAULT '{"blogs_limit": 50, "wordpress_accounts_limit": 10, "images_limit": 100}'::jsonb,
  pricing_tier VARCHAR(50) DEFAULT 'free'
);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can read own profile" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can read all users" ON users
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Admins can update all users" ON users
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- Insert admin user (replace with your email)
INSERT INTO users (id, email, full_name, role, features_enabled, feature_limits, pricing_tier)
VALUES (
  'your-admin-user-id-here', -- Replace with your actual user ID from auth.users
  'your-email@example.com',  -- Replace with your email
  'Admin User',
  'admin',
  '{"blog_generation": true, "wordpress_accounts": true, "ai_image_generation": true, "advanced_features": true}'::jsonb,
  '{"blogs_limit": 999999, "wordpress_accounts_limit": 999, "images_limit": 9999}'::jsonb,
  'internal'
);
```

### **Step 2: Create Activity Logs Table**
```sql
-- Drop existing table if it exists
DROP TABLE IF EXISTS activity_logs CASCADE;

-- Create activity_logs table
CREATE TABLE activity_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  action VARCHAR(255) NOT NULL,
  level VARCHAR(20) DEFAULT 'info' CHECK (level IN ('debug', 'info', 'warn', 'error')),
  category VARCHAR(50) DEFAULT 'general',
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB
);

-- Enable RLS
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can read own logs" ON activity_logs
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own logs" ON activity_logs
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM users 
    WHERE id = auth.uid() AND role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Admin can read all logs
CREATE POLICY "Admins can read all logs" ON activity_logs
  FOR SELECT USING (is_admin());
```

### **Step 3: Create WordPress Accounts Table**
```sql
-- Create wordpress_accounts table
CREATE TABLE wordpress_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  site_url VARCHAR(500) NOT NULL,
  username VARCHAR(255) NOT NULL,
  password VARCHAR(500) NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE wordpress_accounts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can manage own WordPress accounts" ON wordpress_accounts
  FOR ALL USING (auth.uid() = user_id);

-- Admin can see all WordPress accounts
CREATE POLICY "Admins can read all WordPress accounts" ON wordpress_accounts
  FOR SELECT USING (is_admin());
```

### **Step 4: Create API Keys Table**
```sql
-- Create api_keys table
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  service VARCHAR(100) NOT NULL,
  api_key VARCHAR(1000) NOT NULL,
  is_default BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can manage own API keys" ON api_keys
  FOR ALL USING (auth.uid() = user_id);

-- Admin can see all API keys
CREATE POLICY "Admins can read all API keys" ON api_keys
  FOR SELECT USING (is_admin());
```

### **Step 5: Create Projects Table**
```sql
-- Create projects table
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  total_blogs INTEGER NOT NULL,
  completed_blogs INTEGER DEFAULT 0,
  status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
  wordpress_account_id UUID REFERENCES wordpress_accounts(id),
  api_keys JSONB, -- Store array of API key IDs
  settings JSONB, -- Store project settings
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can manage own projects" ON projects
  FOR ALL USING (auth.uid() = user_id);

-- Admin can see all projects
CREATE POLICY "Admins can read all projects" ON projects
  FOR SELECT USING (is_admin());
```

### **Step 6: Create Blogs Table**
```sql
-- Create blogs table
CREATE TABLE blogs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(500) NOT NULL,
  content TEXT NOT NULL,
  status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'failed')),
  wordpress_post_id VARCHAR(255), -- Store WordPress post ID if published
  metadata JSONB, -- Store generation parameters, images, etc.
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE blogs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can manage own blogs" ON blogs
  FOR ALL USING (auth.uid() = user_id);

-- Admin can see all blogs
CREATE POLICY "Admins can read all blogs" ON blogs
  FOR SELECT USING (is_admin());
```

### **Step 7: Update Existing Users to Internal Tier**
```sql
-- Update all existing users to internal tier with unlimited access
UPDATE users 
SET 
  features_enabled = '{"blog_generation": true, "wordpress_accounts": true, "ai_image_generation": true, "advanced_features": true}'::jsonb,
  feature_limits = '{"blogs_limit": 999999, "wordpress_accounts_limit": 999, "images_limit": 9999}'::jsonb,
  pricing_tier = 'internal'
WHERE pricing_tier IS NULL OR pricing_tier = 'free';
```

### **Step 8: Fix Admin Access for Existing Tables**
If you already have the tables created, run these SQL commands to add admin access:

```sql
-- Add admin access to wordpress_accounts table
CREATE POLICY "Admins can read all WordPress accounts" ON wordpress_accounts
  FOR SELECT USING (is_admin());

-- Add admin access to api_keys table  
CREATE POLICY "Admins can read all API keys" ON api_keys
  FOR SELECT USING (is_admin());

-- Add admin access to projects table
CREATE POLICY "Admins can read all projects" ON projects
  FOR SELECT USING (is_admin());

-- Add admin access to blogs table
CREATE POLICY "Admins can read all blogs" ON blogs
  FOR SELECT USING (is_admin());
```

**Note:** Make sure the `is_admin()` function exists. If it doesn't, create it first:

```sql
-- Create function to check if user is admin (if not already exists)
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM users 
    WHERE id = auth.uid() AND role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 🔐 **Environment Variables**

Create a `.env.local` file in your project root:

```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## ✅ **Verification**

After running the SQL:

1. **Check tables exist:**
   ```sql
   \dt
   ```

2. **Check RLS policies:**
   ```sql
   SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
   FROM pg_policies 
   WHERE schemaname = 'public';
   ```

3. **Test admin access:**
   ```sql
   SELECT * FROM users WHERE role = 'admin';
   ```

## 🚀 **Next Steps**

1. **Run the SQL commands** in Supabase SQL Editor
2. **Test the system** - create projects, add WordPress accounts
3. **Verify RLS policies** are working correctly
4. **Test admin features** - user management, system health

---

**Your internal team will have unlimited access to all features!** 🎉
