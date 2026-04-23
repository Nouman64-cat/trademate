# TradeMate Admin Portal

Admin dashboard for managing the TradeMate trade intelligence platform. Built with Next.js 16, TypeScript, and Tailwind CSS.

## ✨ Features

### 🎨 UI/UX
- **Dark/Light Theme** - Automatic theme switching with system preference detection
- **Responsive Design** - Mobile-first approach with collapsible sidebar
- **Modern Interface** - Clean, professional dashboard with intuitive navigation

### 🏗️ Architecture
- **Singleton API Service** - Centralized HTTP client with axios
- **Type-Safe** - Full TypeScript coverage with shared type definitions
- **Component-Based** - Reusable components with consistent styling
- **Utility-First CSS** - Tailwind CSS with custom utility functions

### 📊 Core Modules

#### 1. Dashboard (`/dashboard`)
- Overview statistics (users, conversations, messages)
- Recent activity feed
- Quick action buttons
- Real-time metrics

#### 2. User Management (`/users`)
- User list with pagination
- Advanced filtering (role, status, verification)
- Search functionality
- User actions (edit, delete, ban)
- Export to CSV

#### 3. Chatbot Configuration (`/chatbot/config`)
- LLM Settings (model, temperature, tokens, top_p)
- Agent Configuration (tools, router, max calls)
- Rate Limiting (messages/hour, conversations/day)
- Feature Flags (document search, recommendations, tracking)

## 🚀 Getting Started

### Prerequisites
- Node.js 20+
- npm or yarn
- TradeMate API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Run development server
npm run dev

# Open browser at http://localhost:3000
# Will redirect to /dashboard automatically
```

### Build

```bash
# Production build
npm run build

# Start production server
npm start
```

## 📁 Project Structure

```
admin-portal/
├── app/
│   ├── components/         # Reusable UI components
│   │   ├── dashboard-layout.tsx
│   │   ├── sidebar.tsx
│   │   ├── header.tsx
│   │   ├── theme-provider.tsx
│   │   └── theme-toggle.tsx
│   │
│   ├── constants/          # Configuration
│   │   └── navigation.tsx
│   │
│   ├── services/           # API services
│   │   └── api.ts          # Axios singleton
│   │
│   ├── types/              # TypeScript types
│   │   └── index.ts
│   │
│   ├── utils/              # Utilities
│   │   └── cn.ts
│   │
│   ├── dashboard/          # Dashboard pages
│   ├── users/              # User management
│   ├── chatbot/            # Chatbot config
│   ├── analytics/          # Analytics (future)
│   ├── settings/           # Settings (future)
│   │
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Home
│
├── .env.example
├── package.json
└── README.md
```

## 🔧 API Service Usage

```typescript
import api from '@/app/services/api';

// GET
const users = await api.get('/v1/admin/users');

// POST
const user = await api.post('/v1/admin/users', data);

// PUT
await api.put(`/v1/admin/users/${id}`, data);

// DELETE
await api.delete(`/v1/admin/users/${id}`);

// Auth
api.setAuthToken('jwt-token');
api.clearAuthToken();
```

## 🎯 Next Steps

- [ ] Connect to real API endpoints
- [ ] Add authentication/login
- [ ] Implement analytics dashboard
- [ ] Add system settings
- [ ] Create audit logs
- [ ] Add toast notifications
- [ ] Unit/E2E testing

## 🛠️ Tech Stack

- Next.js 16.2.4
- TypeScript 5
- Tailwind CSS 4
- Axios
- Lucide Icons
- next-themes

## 📄 License

Private - TradeMate Project
