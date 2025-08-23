# 🛠️ Development Environment Setup

## 🚀 Quick Start for Team Members

### **Prerequisites**
- Node.js 18+ installed
- Git installed and configured
- GitHub account with access to the repository
- Code editor (VS Code recommended)

### **1. Clone the Repository**
```bash
# Clone using HTTPS (recommended for collaborators)
git clone https://github.com/blureonlabs/final_blog_gen.git

# Or using SSH (if you have SSH keys set up)
git clone git@github.com:blureonlabs/final_blog_gen.git

# Navigate to project directory
cd final_blog_gen
```

### **2. Install Dependencies**
```bash
# Using npm (recommended)
npm install

# Or using pnpm
pnpm install

# Or using yarn
yarn install
```

### **3. Environment Configuration**
```bash
# Copy environment template
cp .env.example .env.local

# Edit .env.local with your local values
nano .env.local
# or
code .env.local
```

**Required Environment Variables:**
```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional: Development overrides
NEXT_PUBLIC_APP_NAME=Blu Blog Gen (Dev)
NEXT_PUBLIC_APP_VERSION=1.0.0-dev
```

### **4. Database Setup**
1. **Access Supabase Dashboard**
   - Go to [supabase.com](https://supabase.com)
   - Sign in with your credentials
   - Select the project

2. **Run Database Migrations**
   - Follow instructions in [SUPABASE_SETUP.md](./SUPABASE_SETUP.md)
   - Ensure all tables are created
   - Verify Row Level Security policies

### **5. Start Development Server**
```bash
# Start development server
npm run dev

# Or using pnpm
pnpm dev

# Or using yarn
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🔧 Development Tools

### **VS Code Extensions (Recommended)**
```json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "ms-vscode.vscode-json"
  ]
}
```

### **Browser Extensions**
- **React Developer Tools** - For React debugging
- **Redux DevTools** - For state management (if using Redux)
- **Tailwind CSS IntelliSense** - For Tailwind classes

## 📁 Project Structure

```
final_blog_gen/
├── app/                    # Next.js app directory
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/             # Reusable components
│   ├── ui/                # shadcn/ui components
│   ├── auth-form.tsx      # Authentication forms
│   ├── dashboard.tsx      # Main dashboard
│   └── ...                # Other components
├── lib/                    # Utility functions
│   ├── supabase.ts        # Supabase client
│   ├── auth.ts            # Authentication utilities
│   └── utils.ts           # Helper functions
├── hooks/                  # Custom React hooks
├── public/                 # Static assets
├── styles/                 # Additional styles
└── docs/                   # Documentation
```

## 🧪 Testing

### **Run Tests**
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- --testPathPattern=auth
```

### **Testing Guidelines**
- Write tests for new features
- Ensure tests pass before creating PRs
- Use descriptive test names
- Mock external dependencies

## 📝 Code Quality

### **Linting and Formatting**
```bash
# Run ESLint
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Run Prettier
npm run format

# Check TypeScript types
npm run type-check
```

### **Pre-commit Hooks**
```bash
# Install husky (if not already installed)
npm install -g husky

# Set up pre-commit hooks
npx husky install
npx husky add .husky/pre-commit "npm run lint && npm run type-check"
```

## 🚀 Development Workflow

### **Daily Routine**
1. **Morning Sync**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Development**
   - Make changes
   - Test locally
   - Commit frequently with clear messages

4. **Push and PR**
   ```bash
   git push origin feature/your-feature-name
   # Create Pull Request on GitHub
   ```

### **Commit Message Convention**
```
type(scope): description

Examples:
feat(auth): add OAuth login support
fix(api): resolve user data fetching issue
docs(readme): update installation instructions
refactor(components): simplify user card component
style(ui): improve button hover states
test(auth): add login form tests
chore(deps): update dependencies
```

## 🔒 Security Best Practices

### **Never Commit**
- API keys
- Database credentials
- Private keys
- Environment files (.env)
- User data
- Access tokens

### **Always Use**
- Environment variables
- .env.local for local development
- .env.example for documentation
- Supabase Row Level Security

## 🆘 Troubleshooting

### **Common Issues**

#### **Port Already in Use**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

#### **Dependencies Issues**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### **Supabase Connection Issues**
- Verify environment variables
- Check Supabase project status
- Ensure IP is not blocked
- Verify API keys are correct

### **Getting Help**
1. **Check documentation** first
2. **Search existing issues** for similar problems
3. **Ask in team chat** for quick questions
4. **Create GitHub issue** for bugs/features
5. **Request code review** for complex changes

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Supabase Documentation](https://supabase.com/docs)

---

**Happy coding! 🚀**

If you have any questions or need help, don't hesitate to ask the team!
