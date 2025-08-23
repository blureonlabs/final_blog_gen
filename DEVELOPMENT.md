# 🚀 Development Workflow Guide

## 👥 **Team Structure**
- **Repository Owner**: blureonlabs (main account)
- **Team Size**: 3 developers
- **Workflow**: Feature Branch + Pull Request

## 🌿 **Branching Strategy**

### **Main Branches**
- **`main`** - Production branch (protected)
- **`develop`** - Integration/staging branch

### **Feature Branches**
- **`feature/feature-name`** - New features
- **`hotfix/bug-description`** - Critical bug fixes
- **`refactor/component-name`** - Code refactoring

## 📋 **Development Workflow**

### **1. Starting New Work**

#### **For New Features**
```bash
# Ensure you're on develop and it's up to date
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on your feature...
# Make commits with clear messages
git add .
git commit -m "feat: add blog generation API endpoint"

# Push feature branch
git push origin feature/your-feature-name
```

#### **For Bug Fixes**
```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/authentication-error

# Fix the bug...
git add .
git commit -m "fix: resolve user authentication issue"

# Push hotfix branch
git push origin hotfix/authentication-error
```

### **2. Commit Message Convention**

Use conventional commit format:
```bash
# Feature
git commit -m "feat: add WordPress account management"

# Bug fix
git commit -m "fix: resolve API key validation error"

# Documentation
git commit -m "docs: update README with setup instructions"

# Refactoring
git commit -m "refactor: improve authentication flow"

# Testing
git commit -m "test: add unit tests for blog generation"
```

### **3. Pull Request Process**

#### **Creating a PR**
1. **Push your branch** to GitHub
2. **Go to GitHub** and click "Compare & pull request"
3. **Fill PR template**:
   - **Title**: Clear description of changes
   - **Description**: What was changed and why
   - **Type**: Feature, Bug Fix, Refactor, etc.
   - **Testing**: How to test the changes
   - **Screenshots**: If UI changes

#### **PR Review Process**
1. **Self-review** your code before requesting review
2. **Request review** from team members
3. **Address feedback** and push updates
4. **Get approval** from at least 1 team member
5. **Merge** when approved

### **4. Merging Strategy**

#### **Feature Branches**
- **Target**: `develop` branch
- **Requirement**: At least 1 approval
- **Method**: Squash and merge (clean history)

#### **Hotfix Branches**
- **Target**: `main` branch
- **Requirement**: At least 2 approvals
- **Method**: Merge commit (preserve hotfix history)

## 🔧 **Local Development Setup**

### **1. Clone Repository**
```bash
git clone https://github.com/blureonlabs/final_blog_gen.git
cd final_blog_gen
```

### **2. Install Dependencies**
```bash
npm install
# or
yarn install
# or
pnpm install
```

### **3. Environment Setup**
```bash
# Copy environment template
cp .env.example .env.local

# Fill in your Supabase credentials
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### **4. Database Setup**
Follow the [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) guide to set up your local database.

## 🚀 **Running the Application**

### **Development Mode**
```bash
npm run dev
# Open http://localhost:3000
```

### **Build & Test**
```bash
# Build the application
npm run build

# Run linting
npm run lint

# Run tests (when available)
npm test
```

## 📝 **Code Standards**

### **TypeScript**
- Use strict TypeScript configuration
- Define proper interfaces for all data structures
- Avoid `any` type - use proper typing

### **React Components**
- Use functional components with hooks
- Follow naming convention: `PascalCase` for components
- Keep components focused and single-responsibility

### **Styling**
- Use Tailwind CSS classes
- Follow design system patterns
- Ensure responsive design

### **Error Handling**
- Use try-catch blocks for async operations
- Log errors appropriately
- Provide user-friendly error messages

## 🔍 **Testing Strategy**

### **Unit Tests**
- Test utility functions
- Test React components
- Test API endpoints

### **Integration Tests**
- Test complete user flows
- Test database operations
- Test authentication flows

### **Manual Testing**
- Test on different browsers
- Test responsive design
- Test accessibility features

## 🚨 **Emergency Procedures**

### **Critical Bug in Production**
1. **Create hotfix branch** from main
2. **Fix the issue** immediately
3. **Test thoroughly** on hotfix branch
4. **Create PR** to main (bypass develop)
5. **Get emergency approval** from team lead
6. **Deploy to production**

### **Rollback Procedure**
```bash
# If you need to rollback
git checkout main
git revert <commit-hash>
git push origin main
```

## 📚 **Useful Commands**

### **Git Workflow**
```bash
# Check current branch
git branch

# See all branches
git branch -a

# Switch to main
git checkout main

# Switch to develop
git checkout develop

# Update local branches
git fetch origin
git pull origin main
git pull origin develop

# Delete local feature branch after merge
git branch -d feature/feature-name

# See commit history
git log --oneline --graph
```

### **Development**
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Check for linting issues
npm run lint

# Format code (if prettier is configured)
npm run format
```

## 🤝 **Team Collaboration Tips**

1. **Communicate early** - Let team know what you're working on
2. **Keep branches small** - One feature per branch
3. **Review code thoroughly** - Don't rush PR reviews
4. **Test your changes** - Don't assume it works
5. **Document changes** - Update README/docs when needed
6. **Ask for help** - Don't get stuck for too long

## 📞 **Getting Help**

- **Git Issues**: Check git documentation or ask team
- **Code Problems**: Create issue on GitHub
- **Database Issues**: Check Supabase documentation
- **UI/UX Questions**: Discuss with team in PR comments

---

**Happy Coding! 🎉**

*Remember: Good code is code that your teammates can understand and maintain.*
