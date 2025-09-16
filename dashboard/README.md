# AI Agent Management Dashboard

A modern, real-time monitoring dashboard built with Vue 3, TypeScript, and Sass for managing and monitoring AI agent tasks in the GKE-10 Hackathon ecosystem.

## 🚀 Key Features

- **Real-Time Data Updates**: Firebase Firestore real-time listeners for instant task status changes
- **Responsive Design**: Optimized for both desktop and mobile devices
- **TypeScript Support**: Full type safety and IntelliSense
- **Sass Styling**: Modular CSS preprocessing with design system
- **Component Architecture**: Maintainable Vue 3 Composition API structure
- **Three-Tab Interface**: Task Monitoring, Agent Management, Knowledge Base Management

## 📦 Technology Stack

- **Frontend Framework**: Vue 3 with Composition API
- **Language**: TypeScript
- **Styling**: Sass (SCSS) with CSS modules
- **Build Tool**: Vite for fast development and optimized builds
- **Database**: Firebase Firestore for real-time data
- **Deployment**: Docker + Nginx for production
- **State Management**: Vue 3 reactive system with composables

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

## 📁 Project Structure

```
dashboard/
├── src/
│   ├── components/          # Vue Components
│   │   ├── LoadingSpinner.vue    # Loading state indicator
│   │   ├── ErrorMessage.vue      # Error display component
│   │   ├── TaskTable.vue         # Task monitoring table
│   │   ├── AgentCard.vue         # Agent status cards
│   │   └── KnowledgeBaseList.vue # Knowledge base management
│   ├── composables/         # Vue 3 Composables
│   │   ├── useFirebase.ts        # Firebase integration
│   │   ├── useTasks.ts           # Task management logic
│   │   └── useAgents.ts          # Agent management logic
│   ├── styles/              # Sass Stylesheets
│   │   ├── variables.scss        # Design system variables
│   │   ├── global.scss           # Global styles
│   │   └── components.scss       # Component-specific styles
│   ├── types/               # TypeScript Type Definitions
│   │   ├── task.ts              # Task-related types
│   │   ├── agent.ts             # Agent-related types
│   │   └── api.ts               # API response types
│   ├── views/               # Page Components
│   │   ├── TaskMonitoring.vue    # Main task monitoring view
│   │   ├── AgentManagement.vue   # Agent management interface
│   │   └── KnowledgeBase.vue     # Knowledge base management
│   ├── App.vue             # Root Component
│   └── main.ts             # Application Entry Point
├── public/                  # Static Assets
├── index.html              # HTML Template
├── vite.config.ts          # Vite Configuration
├── tsconfig.json           # TypeScript Configuration
├── package.json            # Dependency Management
└── Dockerfile              # Docker Configuration
```

## 🔧 Configuration

### Firebase Configuration

Firebase configuration is located in `src/composables/useFirebase.ts`:

```typescript
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};
```

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

## 📊 Task Status Definitions

- **PENDING**: Waiting to be processed
- **RUNNING**: Currently executing
- **TECH_ANALYST_RUNNING**: Technical Analyst Agent processing
- **ARCHITECT_RUNNING**: Architect Agent processing
- **STYLIST_RUNNING**: Stylist Agent processing
- **ORCHESTRATOR_RUNNING**: Orchestrator Agent coordinating
- **COMPLETED**: Successfully completed
- **FAILED**: Execution failed with error
- **TIMEOUT**: Exceeded maximum execution time
- **CANCELLED**: Manually cancelled by user

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

## 🔄 Real-Time Updates

Implemented using Firebase Firestore's `onSnapshot` API for instant data synchronization:

### Task Monitoring
```typescript
// Real-time task updates
const unsubscribe = onSnapshot(
  query(collection(db, 'tasks'), orderBy('created_at', 'desc')),
  (snapshot) => {
    const tasks = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));
    // Update reactive state
  }
);
```

### Features
- Automatic listening to `tasks`, `agents`, and `knowledge_base` collections
- Sorted by creation time (newest first)
- Error handling and automatic reconnection
- Optimistic updates for better UX

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

## 🔌 API Integration

### Backend Communication
The dashboard communicates with the backend API for:

```typescript
// Agent management
GET    /api/agents              // List all agents
POST   /api/agents              // Create new agent
PATCH  /api/agents/{id}         // Update agent
DELETE /api/agents/{id}         // Delete agent

// Knowledge base
GET    /api/knowledge-base      // List knowledge entries
POST   /api/knowledge-base/index // Add new entry
DELETE /api/knowledge-base/{id} // Remove entry

// Task management
POST   /api/conversation        // Create new task
GET    /api/conversation/{id}   // Get task details
```

### Error Handling
- HTTP error status code handling
- Request timeout management
- Retry logic for failed requests
- Loading states during API calls

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

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dashboard
  template:
    spec:
      containers:
      - name: dashboard
        image: gcr.io/project/dashboard:latest
        ports:
        - containerPort: 80
```
