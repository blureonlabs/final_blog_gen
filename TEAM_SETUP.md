# 🚀 Team Development Setup Guide

## 👥 **For Team Members (Harp0859, etc.)**

### **Step 1: Fork the Repository**
1. **Go to**: `https://github.com/blureonlabs/final_blog_gen`
2. **Click "Fork"** (top right button)
3. **Fork to your personal account** (e.g., `Harp0859/final_blog_gen`)

### **Step 2: Clone Your Fork**
```bash
# Clone your fork (NOT the original)
git clone https://github.com/YOUR_USERNAME/final_blog_gen.git
cd final_blog_gen

# Add the main repo as upstream (for syncing)
git remote add upstream https://github.com/blureonlabs/final_blog_gen.git
```

### **Step 3: Set Up Environment**
```bash
# Install dependencies
npm install

# Copy environment template
cp env.template .env.local

# Edit .env.local with your Supabase credentials
# Ask @blureonlabs for the credentials
```

### **Step 4: Start Development**
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Start development server
npm run dev

# Your app will run on http://localhost:3000
```

## 🔄 **Daily Development Workflow**

### **Morning Sync**
```bash
# Get latest changes from main repo
git fetch upstream
git checkout main
git merge upstream/main

# Update your feature branch
git checkout feature/your-feature-name
git merge main
```

### **Development**
```bash
# Make changes, then:
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### **Submit PR**
1. **Go to your fork** on GitHub
2. **Click "Compare & pull request"**
3. **Set base**: `blureonlabs:main` ← `YOUR_USERNAME:feature/your-feature-name`
4. **Add description** and create PR

## 📋 **Branch Naming Convention**
```
feature/user-authentication
feature/blog-editor
feature/admin-dashboard
bugfix/login-error
hotfix/critical-bug
```

## 📝 **Commit Message Format**
```
feat(auth): add OAuth login support
fix(api): resolve user data fetching issue
docs(readme): update installation instructions
refactor(components): simplify user card component
```

## 🔒 **Important Rules**
- **Never push directly** to main branch
- **Always create feature branches**
- **Test locally** before submitting PR
- **Ask for help** if stuck

## 🆘 **Need Help?**
- **Technical issues**: Create GitHub issue
- **Setup problems**: Ask @blureonlabs
- **Team coordination**: Use your team chat

## ✅ **You're Ready When:**
- [ ] Repository forked to your account
- [ ] Fork cloned locally
- [ ] Dependencies installed
- [ ] Development server running
- [ ] Feature branch created

---

**Happy coding! 🚀**

**Remember**: Keep it simple, communicate with the team, and have fun building!
