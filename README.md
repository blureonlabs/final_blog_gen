# Blu Blog Gen

A modern blog generation application built with Next.js and Supabase, designed for team collaboration and scalable content management.

## 🚀 Quick Start

```bash
# Install dependencies
npm install
# or
pnpm install

# Run development server
npm run dev
# or
pnpm dev

# Build for production
npm run build
# or
pnpm build
```

## 👥 Team Development Structure

### Repository Access
- **Main Account**: `@blureonlabs` (Repository Owner)
- **Collaborators**: Personal GitHub accounts with write access
- **Branch Protection**: Enabled on `main` branch

### Development Workflow

#### 1. **Feature Development**
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: your feature description"

# Push feature branch
git push origin feature/your-feature-name
```

#### 2. **Pull Request Process**
1. Create PR from `feature/your-feature-name` → `main`
2. Request review from team members
3. Address review comments
4. Merge only after approval

#### 3. **Release Process**
```bash
# Create release branch
git checkout main
git checkout -b release/v1.x.x

# Make release-specific changes
git add .
git commit -m "chore: prepare release v1.x.x"

# Push and create PR
git push origin release/v1.x.x
```

### 🏗️ Branch Strategy

- **`main`** - Production-ready code (protected)
- **`develop`** - Integration branch for features
- **`feature/*`** - Individual feature development
- **`release/*`** - Release preparation
- **`hotfix/*`** - Critical production fixes

### 📋 Commit Convention

```
type(scope): description

Types:
- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting, missing semicolons, etc.
- refactor: code refactoring
- test: adding tests
- chore: maintenance tasks

Examples:
- feat(auth): add OAuth login support
- fix(api): resolve user data fetching issue
- docs(readme): update installation instructions
```

### 🔒 Security & Access

- **Personal Access Tokens**: Required for authentication
- **Branch Protection**: Prevents direct pushes to main
- **Code Review**: Mandatory for all PRs
- **Environment Variables**: Never commit sensitive data

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS, shadcn/ui components
- **Backend**: Supabase (PostgreSQL, Auth, Storage)
- **Package Manager**: npm/pnpm

## 📁 Project Structure

```
final_blog_gen/
├── app/                 # Next.js app directory
├── components/          # Reusable UI components
│   └── ui/             # shadcn/ui components
├── lib/                 # Utility functions & configs
├── hooks/               # Custom React hooks
├── public/              # Static assets
├── styles/              # Global styles
└── docs/                # Documentation
```

## 🌐 Environment Setup

Copy `env.template` to `.env.local` and configure:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## 📚 Documentation

- [Supabase Setup Guide](./SUPABASE_SETUP.md)
- [Component Library](./components/README.md)
- [API Documentation](./docs/API.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Follow the commit convention
4. Submit a pull request
5. Ensure all tests pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create GitHub issues for bugs/features
- **Discussions**: Use GitHub Discussions for questions
- **Team Chat**: Internal communication channel

---

**Team**: Blu Blog Gen Development Team  
**Maintainer**: @blureonlabs  
**Last Updated**: $(date)
