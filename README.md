# 🚀 Blog Generator - Bulk Blog Generation Dashboard

A modern, enterprise-grade bulk blog generation application built with Next.js 15, React 19, TypeScript, and Supabase. Generate, manage, and publish multiple blog posts across WordPress sites with AI-powered content creation.

## ✨ Features

### 🔐 **Authentication & User Management**
- **Role-based access control** (User, Moderator, Admin)
- **Subscription plans** (Free, Starter, Professional, Enterprise)
- **Secure Supabase authentication**
- **User profile management**

### 📝 **Blog Generation**
- **Bulk blog creation** with customizable parameters
- **AI-powered content generation** (OpenAI, Gemini integration)
- **Multiple content templates** and styles
- **Progress tracking** and status management

### 🌐 **WordPress Integration**
- **Multiple WordPress account management**
- **Automated publishing** to WordPress sites
- **Content synchronization** across platforms
- **Publishing status tracking**

### 🔑 **API Management**
- **Secure API key storage** for multiple services
- **Service integration** (OpenAI, Gemini, SERP, etc.)
- **Default key management** per service

### 📊 **Dashboard & Analytics**
- **Real-time project monitoring**
- **Usage statistics** and limits
- **Activity logging** and audit trails
- **Performance metrics**

### 🎨 **Modern UI/UX**
- **Responsive design** with Tailwind CSS
- **Dark/Light theme** support
- **shadcn/ui components** for consistent design
- **Mobile-optimized** interface

## 🛠️ Tech Stack

### **Frontend**
- **Next.js 15** - React framework with App Router
- **React 19** - Latest React with concurrent features
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful, accessible components

### **Backend & Database**
- **Supabase** - Open-source Firebase alternative
- **PostgreSQL** - Robust relational database
- **Row Level Security (RLS)** - Data protection
- **Real-time subscriptions** - Live updates

### **Authentication & Security**
- **Supabase Auth** - Secure user authentication
- **JWT tokens** - Stateless authentication
- **Role-based permissions** - Granular access control
- **Environment variables** - Secure configuration

## 🚀 Quick Start

### **Prerequisites**
- Node.js 18+ 
- npm, yarn, or pnpm
- Supabase account

### **1. Clone the Repository**
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
Create a `.env.local` file in the root directory:
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### **4. Database Setup**
Follow the [Supabase Setup Guide](./SUPABASE_SETUP.md) to:
- Create required database tables
- Set up Row Level Security policies
- Configure user roles and permissions

### **5. Run the Application**
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🗄️ Database Schema

The application uses the following main tables:

- **`users`** - User profiles, roles, and subscription data
- **`projects`** - Blog generation projects and metadata
- **`wordpress_accounts`** - WordPress site connections
- **`api_keys`** - Service API credentials
- **`blogs`** - Generated blog content and status
- **`activity_logs`** - User activity and audit trails

## 🔧 Configuration

### **Environment Variables**
```bash
# Required
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional
NEXT_PUBLIC_APP_NAME=Blog Generator
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### **Supabase Setup**
1. Create a new Supabase project
2. Run the SQL commands from [SUPABASE_SETUP.md](./SUPABASE_SETUP.md)
3. Configure authentication providers
4. Set up Row Level Security policies

## 📱 Usage

### **Getting Started**
1. **Sign up** for an account
2. **Add WordPress accounts** for your sites
3. **Configure API keys** for AI services
4. **Create your first project** for blog generation
5. **Monitor progress** and publish content

### **Creating Projects**
- Set project name and description
- Choose target WordPress account
- Configure blog parameters (count, style, topics)
- Monitor generation progress
- Review and publish content

### **Managing Content**
- **Draft management** - Review before publishing
- **Bulk operations** - Publish multiple blogs at once
- **Status tracking** - Monitor publishing progress
- **Error handling** - Retry failed operations

## 🔒 Security Features

- **Row Level Security (RLS)** - Data isolation per user
- **JWT authentication** - Secure token-based auth
- **Role-based access** - Granular permissions
- **API key encryption** - Secure credential storage
- **Activity logging** - Comprehensive audit trails

## 🚀 Deployment

### **Vercel (Recommended)**
```bash
npm install -g vercel
vercel
```

### **Netlify**
```bash
npm run build
# Deploy the `out` directory
```

### **Docker**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [SUPABASE_SETUP.md](./SUPABASE_SETUP.md)
- **Issues**: [GitHub Issues](https://github.com/blureonlabs/final_blog_gen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/blureonlabs/final_blog_gen/discussions)

## 🙏 Acknowledgments

- **Next.js team** for the amazing framework
- **Supabase** for the backend infrastructure
- **shadcn/ui** for the beautiful components
- **Tailwind CSS** for the utility-first styling

---

**Built with ❤️ by [blureonlabs](https://github.com/blureonlabs)**

*Transform your content creation workflow with AI-powered bulk blog generation!*
