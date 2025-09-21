# Online Boutique AI Management Dashboard

A comprehensive, multilingual management dashboard for Online Boutique's AI-driven e-commerce operations. Built with Vue 3, TypeScript, and modern web technologies to provide real-time monitoring and management of business operations across multiple departments.

## 🏢 Business Overview

The dashboard serves as the central command center for **Online Boutique Headquarters**, providing AI-driven management capabilities across four key business areas:

- **🧠 Strategy Department**: Business consulting and strategic planning
- **👥 HR Department**: AI agent management and workforce optimization  
- **🗄️ Knowledge Management**: Information indexing and knowledge base operations
- **📊 Operations Department**: Task monitoring and conversation management

## 🚀 Key Features

### 🌍 **Internationalization (i18n)**
- **Bilingual Support**: Complete English and Traditional Chinese (繁體中文) interface
- **Real-time Language Switching**: Instant language toggle with localStorage persistence
- **Professional Translations**: Business-grade translations for all interface elements
- **Scalable Architecture**: Easy addition of new languages

### 🎯 **Business Intelligence**
- **Strategy Consulting**: AI-powered business advisor with market analysis and capability expansion recommendations
- **Agent Performance Monitoring**: Real-time tracking of AI agent status, performance metrics, and resource utilization
- **Knowledge Base Management**: Centralized information repository with intelligent indexing and search capabilities
- **Operations Analytics**: Comprehensive task workflow monitoring and conversation history analysis

### 🔄 **Real-Time Operations**
- **Firebase Integration**: Live data synchronization across all business functions
- **Instant Updates**: Real-time status changes without page refreshes
- **Cross-Department Coordination**: Seamless information flow between business units
- **Performance Metrics**: Live dashboards with KPIs and operational statistics

## 📦 Technology Stack

- **Frontend Framework**: Vue 3 with Composition API
- **Language**: TypeScript with full type safety
- **Styling**: Sass (SCSS) with modular design system
- **Build Tool**: Vite for fast development and optimized builds
- **Database**: Firebase Firestore for real-time data synchronization
- **Internationalization**: Vue I18n 9.x with Composition API
- **State Management**: Vue 3 reactive system with composables
- **Deployment**: Docker + Nginx for production environments

## 🏗️ Application Architecture

### 🎛️ **Dashboard Modules**

#### 1. **Strategy Department (公司戰略)**
- **Business Consultant AI**: Interactive chat interface for strategic business advice
- **Market Analysis**: AI-powered insights on fashion trends and market opportunities
- **Capability Expansion**: Recommendations for organizational development and tool integration
- **Responsive Card Layout**: Three suggestion cards with optimized mobile display

#### 2. **HR Department (人事部) - Agent Management**
- **Agent Lifecycle Management**: Create, edit, enable/disable AI agents
- **Real-time Status Monitoring**: Live agent performance and health metrics
- **System Agent Protection**: Built-in safeguards for core agents (Orchestrator, Customer Service)
- **Capability Management**: Dynamic skill assignment and tool allocation
- **Bilingual Interface**: Full i18n support for agent status and operations

#### 3. **Knowledge Management (知識庫)**
- **Website Indexing**: Automated crawling and content indexing
- **Search Capabilities**: Intelligent information retrieval system
- **Status Tracking**: Real-time monitoring of indexing operations (Queued, Crawling, Active, Failed)
- **Content Management**: Centralized repository for business knowledge

#### 4. **Operations Department (營運部)**
- **Task Workflow Monitoring**: End-to-end task execution tracking
- **Conversation History**: Complete customer interaction logs with detailed analytics
- **Token Usage Analytics**: Cost tracking and resource optimization
- **Agent Performance Metrics**: Cross-departmental efficiency analysis

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+ with pnpm installed
- Firebase project with Firestore enabled
- Access to the backend API endpoints

### Install Dependencies

```bash
pnpm install
```

### Development Mode

```bash
pnpm run dev
```

Access the application at http://localhost:5173

### Type Checking

```bash
pnpm run type-check
```

### Build for Production

```bash
pnpm run build
```

### Preview Production Build

```bash
pnpm run preview
```

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t ai-agent-dashboard .
```

### Run Container

```bash
docker run -p 80:80 ai-agent-dashboard
```

### Multi-stage Build
The Dockerfile uses a multi-stage build process:
1. **Build Stage**: Compiles TypeScript and builds Vue app
2. **Production Stage**: Serves static files with Nginx

## 📁 Current Project Structure

```
dashboard/
├── src/
│   ├── components/              # Vue Components (6 active)
│   │   ├── AgentManagement.vue      # HR - Agent lifecycle management
│   │   ├── StrategyConsultant.vue   # Strategy - Business consulting AI
│   │   ├── KnowledgeBase.vue        # Knowledge - Content indexing
│   │   ├── OperationsCenter.vue     # Operations - Task & conversation monitoring
│   │   ├── LanguageSwitcher.vue     # i18n - Language toggle component
│   │   ├── LoadingSpinner.vue       # UI - Loading state indicator
│   │   └── ErrorMessage.vue         # UI - Error display component
│   ├── composables/             # Vue 3 Composables
│   │   ├── useFirebase.ts           # Firebase Firestore integration
│   │   ├── useAgents.ts             # Agent management logic
│   │   └── useConversations.ts      # Conversation data management
│   ├── i18n/                    # Internationalization
│   │   ├── index.ts                 # i18n configuration
│   │   └── locales/
│   │       ├── en.json              # English translations
│   │       └── zh-TW.json           # Traditional Chinese translations
│   ├── styles/                  # Sass Design System
│   │   ├── variables.scss           # Design tokens and variables
│   │   ├── global.scss              # Global styles and resets
│   │   └── components.scss          # Component-specific styles
│   ├── types/                   # TypeScript Definitions
│   │   ├── task.ts                  # Task workflow types
│   │   ├── agent.ts                 # Agent management types
│   │   └── knowledge.ts             # Knowledge base types
│   ├── App.vue                  # Root application component
│   └── main.ts                  # Application entry point with i18n
├── public/                      # Static assets
├── index.html                   # HTML template
├── vite.config.ts              # Vite build configuration
├── tsconfig.json               # TypeScript configuration
├── package.json                # Dependencies and scripts
└── Dockerfile                  # Production deployment
```

### 🗂️ **Component Architecture**

#### **Business Components**
- **AgentManagement.vue**: Complete HR management interface with CRUD operations, status monitoring, and system agent protection
- **StrategyConsultant.vue**: Interactive business consulting with AI-powered recommendations and responsive card layout
- **KnowledgeBase.vue**: Content indexing management with real-time status tracking and search capabilities
- **OperationsCenter.vue**: Dual-tab interface for task monitoring and conversation history with detailed analytics

#### **Infrastructure Components**
- **LanguageSwitcher.vue**: Elegant language toggle with globe icon and smooth transitions
- **LoadingSpinner.vue**: Consistent loading states with customizable messages
- **ErrorMessage.vue**: User-friendly error handling with retry mechanisms

## 🔧 Configuration

### 🌍 **Internationalization Configuration**

The dashboard implements Vue I18n 9.x with Composition API for comprehensive multilingual support:

```typescript
// src/i18n/index.ts
import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zhTW from './locales/zh-TW.json'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: { en, 'zh-TW': zhTW }
})
```

**Language Structure**:
- **150+ translation keys** per language
- **Hierarchical organization**: `app`, `navigation`, `agents`, `operations`, `common`
- **Dynamic content support**: Status messages, error handling, loading states
- **Persistent preferences**: Language choice saved in localStorage

### 🔥 **Firebase Configuration**

Real-time data integration configured in `src/composables/useFirebase.ts`:

```typescript
const firebaseConfig = {
  apiKey: "AIzaSyBQ8lOT39SnvFqlnnch9G_W8wa0jlfUg5E",
  authDomain: "gke-10-hackathon-471902.firebaseapp.com",
  projectId: "gke-10-hackathon-471902",
  storageBucket: "gke-10-hackathon-471902.firebasestorage.app",
  messagingSenderId: "679895434316",
  appId: "1:679895434316:web:9d1183ab38f168d24060e9"
}
```

**Collections**:
- `tasks`: Task workflow and execution logs
- `conversations`: Customer interaction history  
- `agents`: AI agent configurations and status
- `knowledge_base`: Indexed content and search data

### Vite Configuration

`vite.config.ts` includes:

- Vue plugin configuration with TypeScript support
- Path aliases (`@` points to `src`)
- Sass global variable imports
- Build optimization settings
- Development server proxy for API calls

### Environment Variables

```bash
# .env.local (for development)
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_PROJECT_ID=your-project-id
```

## 📊 Business Operations Status

### 🎯 **Task Workflow States**
- **PENDING**: Awaiting agent assignment and processing
- **RUNNING**: Active execution by assigned AI agent
- **COMPLETED**: Successfully processed with deliverables
- **FAILED**: Execution error requiring intervention

### 👥 **Agent Management States**
- **ACTIVE**: Agent operational and available for tasks
- **INACTIVE**: Agent temporarily disabled
- **CREATING**: Agent initialization in progress
- **FAILED**: Agent deployment or configuration error

### 🗄️ **Knowledge Base Operations**
- **QUEUED**: Content scheduled for indexing
- **CRAWLING**: Active website content extraction
- **INDEXING**: Processing and organizing extracted data
- **ACTIVE**: Content successfully indexed and searchable
- **FAILED**: Indexing error requiring manual review

### 💬 **Conversation Management**
- **Real-time Tracking**: Live customer interaction monitoring
- **Token Analytics**: Cost tracking per conversation
- **Agent Performance**: Response time and quality metrics
- **Historical Analysis**: Trend analysis and insights

## 🎨 Design System

The dashboard uses a comprehensive Sass-based design system defined in `src/styles/variables.scss`:

### Color Palette
```scss
// Primary colors
$primary-color: #3b82f6;
$secondary-color: #8b5cf6;
$success-color: #10b981;
$warning-color: #f59e0b;
$error-color: #ef4444;

// Dark theme
$bg-primary: #0f172a;
$bg-secondary: #1e293b;
$text-primary: #f8fafc;
$text-secondary: #cbd5e1;
```

### Spacing System
```scss
$spacing-xs: 0.25rem;   // 4px
$spacing-sm: 0.5rem;    // 8px
$spacing-md: 1rem;      // 16px
$spacing-lg: 1.5rem;    // 24px
$spacing-xl: 2rem;      // 32px
```

### Component Styling
- Consistent border radius (8px, 12px, 16px)
- Subtle shadow system for depth
- Smooth transitions (200ms ease-in-out)
- Responsive breakpoints

## 🔄 Real-Time Data Architecture

### 🔥 **Firebase Integration**

The dashboard implements comprehensive real-time data synchronization using Firebase Firestore:

```typescript
// Multi-collection real-time monitoring
export function useFirebase() {
  const tasks = ref<Task[]>([])
  const loading = ref(true)
  const error = ref<string | null>(null)
  
  const initFirebase = async () => {
    const db = getFirestore(app, "gke-10-hackathon")
    const tasksCollection = collection(db, 'tasks')
    const q = query(tasksCollection, orderBy('created_at', 'desc'))
    
    unsubscribe = onSnapshot(q, (querySnapshot) => {
      const taskList: Task[] = []
      querySnapshot.forEach((doc) => {
        // Process real-time updates
      })
      tasks.value = taskList
    })
  }
}
```

### 📡 **Real-Time Features**
- **Instant Synchronization**: Zero-delay updates across all connected clients
- **Cross-Department Coordination**: Live status updates between Strategy, HR, Knowledge, and Operations
- **Conversation Streaming**: Real-time customer interaction monitoring
- **Agent Health Monitoring**: Live performance metrics and status changes
- **Error Recovery**: Automatic reconnection and state restoration

## 🚨 Error Handling

### Connection Management
- Firebase connection error notifications
- Automatic network reconnection
- Graceful degradation when offline
- Loading state indicators throughout the UI

### User Experience
- Toast notifications for actions (success/error)
- Detailed error messages with actionable suggestions
- Retry mechanisms for failed operations
- Fallback UI states for missing data

## 📱 Responsive Design

### Breakpoint System
```scss
$mobile: 768px;
$tablet: 1024px;
$desktop: 1280px;
$wide: 1536px;
```

### Adaptive Features
- Desktop-first design approach
- Mobile-optimized navigation and interactions
- Horizontal scrolling tables on small screens
- Flexible grid system using CSS Grid and Flexbox
- Touch-friendly interface elements
- Collapsible sidebar on mobile devices

## 🚀 Production Features

### 🎯 **Current Implementation Status**

#### ✅ **Completed Features**
- **Full Internationalization**: English and Traditional Chinese with 150+ translation keys
- **Real-time Data Sync**: Firebase Firestore integration across all departments
- **Agent Management**: Complete CRUD operations with system agent protection
- **Business Intelligence**: Interactive strategy consulting with AI recommendations
- **Knowledge Management**: Content indexing with status tracking
- **Operations Analytics**: Task monitoring and conversation history
- **Responsive Design**: Mobile-optimized interface with adaptive layouts
- **Error Handling**: Comprehensive error states with retry mechanisms

#### 🔧 **System Architecture**
- **Component-Based**: 6 active Vue components with clear separation of concerns
- **Type Safety**: Full TypeScript implementation with strict type checking
- **State Management**: Reactive composables for cross-component data sharing
- **Performance**: Optimized builds with Vite and lazy loading
- **Scalability**: Modular design supporting easy feature additions

### 🏢 **Business Value**

#### **Operational Efficiency**
- **Centralized Management**: Single dashboard for all AI operations
- **Real-time Visibility**: Instant status updates across departments
- **Cost Optimization**: Token usage tracking and resource monitoring
- **Quality Assurance**: Agent performance metrics and conversation analytics

#### **User Experience**
- **Multilingual Support**: Seamless language switching for global teams
- **Intuitive Interface**: Business-focused design with clear navigation
- **Mobile Accessibility**: Full functionality on all device sizes
- **Professional Aesthetics**: Modern design system with consistent branding

## 🧪 Testing

### Unit Testing
```bash
# Run unit tests
pnpm run test

# Run tests with coverage
pnpm run test:coverage

# Run tests in watch mode
pnpm run test:watch
```

### E2E Testing
```bash
# Run end-to-end tests
pnpm run test:e2e

# Run E2E tests in headless mode
pnpm run test:e2e:headless
```

## 🚀 Performance Optimization

### Build Optimization
- Tree shaking for unused code elimination
- Code splitting for lazy loading
- Asset optimization (images, fonts)
- Gzip compression in production

### Runtime Performance
- Vue 3 reactivity system for efficient updates
- Virtual scrolling for large data sets
- Debounced search and filtering
- Memoized computed properties

## 🔐 Security

### Firebase Security
- Firestore security rules for data access control
- Authentication integration (future enhancement)
- Input sanitization and validation

### Content Security Policy
- Strict CSP headers in production
- XSS protection mechanisms
- Secure cookie handling

## 🚢 Deployment

### Production Build
```bash
# Build for production
pnpm run build

# Preview production build locally
pnpm run preview
```

### Docker Deployment
```dockerfile
# Multi-stage build
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN pnpm install
COPY . .
RUN pnpm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
```

## 📈 Future Enhancements

### 🔮 **Planned Features**
- **Advanced Analytics**: Machine learning insights for business optimization
- **Custom Dashboards**: User-configurable widgets and layouts
- **API Integration**: Extended backend connectivity for enhanced functionality
- **Authentication**: Role-based access control and user management
- **Notifications**: Real-time alerts and notification system
- **Export Capabilities**: Data export and reporting functionality

### 🌐 **Scalability Roadmap**
- **Multi-tenant Support**: Organization-level data isolation
- **Plugin Architecture**: Extensible module system for custom features
- **Advanced i18n**: Support for additional languages and locales
- **Performance Optimization**: Advanced caching and data virtualization
- **Mobile App**: Native mobile application development

---

## 🎯 **Project Summary**

The **Online Boutique AI Management Dashboard** represents a comprehensive, enterprise-grade solution for managing AI-driven e-commerce operations. With its multilingual interface, real-time data synchronization, and modular architecture, it provides a scalable foundation for business intelligence and operational excellence.

**Key Achievements**:
- ✅ **100% Internationalized** interface with professional translations
- ✅ **Real-time Firebase integration** across all business functions  
- ✅ **Responsive design** optimized for all device sizes
- ✅ **Type-safe architecture** with comprehensive error handling
- ✅ **Production-ready** with Docker deployment capabilities

The dashboard successfully bridges the gap between technical AI operations and business management, providing stakeholders with the tools needed to monitor, analyze, and optimize their AI-driven e-commerce ecosystem.
