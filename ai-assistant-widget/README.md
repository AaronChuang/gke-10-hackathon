# AI Assistant Widget

An injectable JavaScript widget built with Preact that provides AI-powered customer service and product assistance for e-commerce websites. This widget integrates seamlessly with the Online Boutique sample application for the GKE-10 Hackathon, demonstrating non-invasive AI enhancement.

## 🌟 Key Features

- **Non-Invasive Integration**: Single `<script>` tag injection into any e-commerce site
- **AI-Powered Assistance**: Intelligent product recommendations and customer support using Google's Gemini models
- **Real-Time Chat Interface**: Interactive conversation with AI assistant agent
- **Product Context Awareness**: Automatically detects and analyzes current product page
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Zero Dependencies**: Self-contained widget with no external requirements
- **GKE Integration**: Uses Google Kubernetes Engine ingress for scalable backend services

## 🏗️ Architecture Overview

```
stylist-widget/
├── src/
│   ├── components/           # Preact Components
│   │   ├── ChatWidget.tsx    # Main chat interface
│   │   ├── MessageList.tsx   # Chat message display
│   │   ├── MessageInput.tsx  # User input component
│   │   └── ProductContext.tsx # Product information display
│   ├── services/            # Business Logic
│   │   ├── api.ts           # Backend API communication
│   │   ├── productDetector.ts # Product page analysis
│   │   └── storage.ts       # Local storage management
│   ├── types/               # TypeScript Definitions
│   │   ├── api.ts           # API response types
│   │   ├── product.ts       # Product-related types
│   │   └── widget.ts        # Widget configuration types
│   ├── styles/              # CSS Styles
│   │   ├── widget.css       # Main widget styles
│   │   └── themes.css       # Color themes and variants
│   ├── app.tsx             # Root Application Component
│   └── main.ts             # Entry Point & Widget Initialization
├── public/                  # Static Assets
│   └── widget.js           # Compiled widget bundle
├── dist/                   # Build Output
└── vite.config.ts          # Build Configuration
```

## 🚀 Technology Stack

### Core Technologies
- **Preact**: Lightweight React alternative (3KB)
- **TypeScript**: Type-safe JavaScript development
- **Vite**: Fast build tool and development server
- **CSS Modules**: Scoped styling to prevent conflicts

### Integration Features
- **DOM Injection**: Dynamic widget insertion
- **Event Handling**: Cross-frame communication
- **Local Storage**: Conversation persistence
- **Responsive CSS**: Mobile-first design approach

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+ with pnpm installed
- Access to the GKE backend services (proxy-agent and orchestrator)
- Modern web browser for testing

### Install Dependencies
```bash
cd stylist-widget
pnpm install
```

### Development Mode
```bash
pnpm run dev
```
Access the development server at http://localhost:4173

### Build for Production
```bash
# Build the widget
pnpm run build

# Output will be in dist/stylist-widget.js
ls -la dist/
```

### Preview Production Build
```bash
# Preview locally
pnpm run preview

# Test the built widget
open http://localhost:4173
```

## 📦 Widget Integration

### Basic Integration
Add this single script tag to any e-commerce website:

```html
<script 
  async 
  src="https://storage.googleapis.com/gke-10-hackathon-assets/ai-assistant-widget.js">
</script>
```

The widget will automatically initialize and render on the page without any additional configuration required.

### Configuration Options (Optional)
The widget can be customized by setting global configuration before loading:

```html
<script>
  window.AIAssistantWidgetConfig = {
    apiUrl: 'http://34.160.253.241',        // GKE ingress endpoint
    theme: 'light',                         // 'light' | 'dark' | 'auto'
    position: 'bottom-right',               // 'bottom-right' | 'bottom-left'
    autoOpen: false,                        // Auto-open chat on load
    productSelector: '.product-container'   // Custom product detection
  };
</script>
<script 
  async 
  src="https://storage.googleapis.com/gke-10-hackathon-assets/ai-assistant-widget.js">
</script>
```

### Advanced Integration
For custom product context and enhanced features:

```javascript
// Set custom product information
window.AIAssistantWidgetConfig = {
  productContext: {
    name: 'Premium Cotton T-Shirt',
    price: '$29.99',
    category: 'Clothing',
    description: 'Comfortable cotton t-shirt...',
    images: ['image1.jpg', 'image2.jpg'],
    colors: ['red', 'blue', 'green'],
    sizes: ['S', 'M', 'L', 'XL']
  }
};

// Load the widget
<script 
  async 
  src="https://storage.googleapis.com/gke-10-hackathon-assets/ai-assistant-widget.js">
</script>
```

## 🎨 Styling & Theming

### CSS Custom Properties
The widget uses CSS custom properties for easy theming:

```css
:root {
  --widget-primary-color: #3b82f6;
  --widget-secondary-color: #8b5cf6;
  --widget-background: #ffffff;
  --widget-text-color: #1f2937;
  --widget-border-radius: 12px;
  --widget-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  --widget-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
}
```

### Dark Theme Support
```css
[data-theme="dark"] {
  --widget-background: #1f2937;
  --widget-text-color: #f9fafb;
  --widget-border-color: #374151;
}
```

### Responsive Design
```css
/* Mobile-first approach */
.widget-container {
  width: 100%;
  max-width: 400px;
  height: 600px;
}

@media (max-width: 768px) {
  .widget-container {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }
}
```

## 🔌 API Integration

### Backend Communication
The widget communicates with the orchestrator service:

```typescript
interface ConversationRequest {
  user_prompt: string;
  conversation_id?: string;
  product_context?: ProductContext;
}

interface ConversationResponse {
  response: string;
  conversation_id: string;
  agent_used: string;
  status: 'completed' | 'running' | 'failed';
}
```

### Error Handling
```typescript
class ApiService {
  async sendMessage(message: string, context?: ProductContext) {
    try {
      const response = await fetch(`${this.apiUrl}/api/conversation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_prompt: message,
          conversation_id: this.conversationId,
          product_context: context
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw new ApiError('Failed to send message', error);
    }
  }
}
```

## 🕵️ Product Detection

### Automatic Product Analysis
The widget automatically detects product information from the current page:

```typescript
class ProductDetector {
  detectProduct(): ProductContext | null {
    // Try multiple detection strategies
    const strategies = [
      this.detectFromStructuredData,
      this.detectFromOpenGraph,
      this.detectFromSelectors,
      this.detectFromHeuristics
    ];
    
    for (const strategy of strategies) {
      const result = strategy();
      if (result) return result;
    }
    
    return null;
  }
  
  private detectFromStructuredData(): ProductContext | null {
    const jsonLd = document.querySelector('script[type="application/ld+json"]');
    if (jsonLd) {
      try {
        const data = JSON.parse(jsonLd.textContent || '');
        if (data['@type'] === 'Product') {
          return this.parseStructuredData(data);
        }
      } catch (e) {
        console.warn('Failed to parse structured data:', e);
      }
    }
    return null;
  }
}
```

### Custom Product Selectors
For specific e-commerce platforms:

```typescript
const PLATFORM_SELECTORS = {
  shopify: {
    name: '.product-single__title',
    price: '.price',
    description: '.product-single__description',
    images: '.product-single__photo img'
  },
  woocommerce: {
    name: '.product_title',
    price: '.price .amount',
    description: '.woocommerce-product-details__short-description',
    images: '.woocommerce-product-gallery__image img'
  },
  online_boutique: {
    name: 'h2',
    price: '.price',
    description: '.product-info p',
    images: '.product-image img'
  }
};
```

## 💬 Chat Interface

### Message Types
```typescript
interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  agent?: string;
  metadata?: {
    product_context?: ProductContext;
    confidence_score?: number;
    suggestions?: string[];
  };
}
```

### Real-Time Features
- **Typing Indicators**: Shows when AI is processing
- **Message Status**: Delivery and read receipts
- **Auto-Scroll**: Smooth scrolling to new messages
- **Message Persistence**: Local storage for conversation history

## 🔐 Security & Privacy

### Data Protection
- **No Personal Data Storage**: Only conversation context is stored locally
- **Secure API Communication**: HTTPS-only requests
- **Content Security Policy**: Strict CSP headers
- **Input Sanitization**: XSS protection for user inputs

### Privacy Features
- **Local Storage Only**: No server-side user tracking
- **Conversation Cleanup**: Automatic cleanup of old conversations
- **Opt-out Support**: Easy widget removal and data clearing

## 📊 Analytics & Monitoring

### Usage Tracking
```typescript
interface WidgetAnalytics {
  widget_loaded: Date;
  conversations_started: number;
  messages_sent: number;
  product_contexts_detected: number;
  errors_encountered: string[];
  user_agent: string;
  page_url: string;
}
```

### Performance Monitoring
- **Load Time Tracking**: Widget initialization performance
- **API Response Times**: Backend communication metrics
- **Error Rate Monitoring**: Failed requests and exceptions
- **User Engagement**: Conversation length and frequency

## 🚢 Deployment

### Build and Deploy to Google Cloud Storage
```bash
# Build the widget for production
pnpm run build

# Upload to Google Cloud Storage
gcloud storage cp dist/stylist-widget.js gs://gke-10-hackathon-assets/stylist-widget.js

# Verify deployment
curl -I https://storage.googleapis.com/gke-10-hackathon-assets/stylist-widget.js
```

### Automated Deployment
For CI/CD integration:

```bash
#!/bin/bash
# deploy.sh
set -e

echo "Building widget..."
pnpm run build

echo "Uploading to GCS..."
gcloud storage cp dist/stylist-widget.js gs://gke-10-hackathon-assets/stylist-widget.js

echo "Setting cache headers..."
gcloud storage objects update gs://gke-10-hackathon-assets/stylist-widget.js \
  --cache-control="public, max-age=3600"

echo "Deployment complete!"
echo "Widget available at: https://storage.googleapis.com/gke-10-hackathon-assets/stylist-widget.js"
```

### Version Management
```bash
# Deploy with version tag
gcloud storage cp dist/stylist-widget.js gs://gke-10-hackathon-assets/stylist-widget-v1.0.0.js

# Update latest version
gcloud storage cp dist/stylist-widget.js gs://gke-10-hackathon-assets/stylist-widget.js

# Development version
gcloud storage cp dist/stylist-widget.js gs://gke-10-hackathon-assets/stylist-widget-dev.js
```

```html
<!-- Specific version -->
<script async src="https://storage.googleapis.com/gke-10-hackathon-assets/stylist-widget-v1.0.0.js"></script>

<!-- Latest stable (recommended) -->
<script async src="https://storage.googleapis.com/gke-10-hackathon-assets/stylist-widget.js"></script>

<!-- Development version -->
<script async src="https://storage.googleapis.com/gke-10-hackathon-assets/stylist-widget-dev.js"></script>
```

### Rollback Strategy
```bash
# Backup current version before deployment
gcloud storage cp gs://gke-10-hackathon-assets/stylist-widget.js \
  gs://gke-10-hackathon-assets/stylist-widget-backup.js

# Rollback to previous version if needed
gcloud storage cp gs://gke-10-hackathon-assets/stylist-widget-v1.0.0.js \
  gs://gke-10-hackathon-assets/stylist-widget.js
```
```

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

### Integration Testing
```bash
# Test widget integration
pnpm run test:integration

# Test across different browsers
pnpm run test:cross-browser
```

### E2E Testing
```typescript
// Playwright test example
test('widget loads and responds to user input', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Wait for widget to load
  await page.waitForSelector('.stylist-widget');
  
  // Open chat
  await page.click('.widget-trigger');
  
  // Send message
  await page.fill('.message-input', 'Help me style this outfit');
  await page.click('.send-button');
  
  // Verify response
  await page.waitForSelector('.assistant-message');
  const response = await page.textContent('.assistant-message:last-child');
  expect(response).toContain('style');
});
```

## 🔧 Configuration Reference

### Widget Configuration
```typescript
interface WidgetConfig {
  apiUrl?: string;                   // Backend API endpoint (default: built-in)
  theme?: 'light' | 'dark' | 'auto'; // Visual theme (default: 'light')
  position?: 'bottom-right' | 'bottom-left'; // Widget position (default: 'bottom-right')
  autoOpen?: boolean;                // Auto-open on page load (default: false)
  productSelector?: string;          // CSS selector for product detection
  conversationTimeout?: number;      // Conversation timeout in minutes (default: 30)
  maxMessages?: number;              // Maximum messages per conversation (default: 50)
  enableAnalytics?: boolean;         // Enable usage analytics (default: true)
  customStyles?: Record<string, string>; // Custom CSS properties
  productContext?: ProductContext;   // Manual product information
}

// Usage example
window.StylistWidgetConfig = {
  theme: 'dark',
  position: 'bottom-left',
  autoOpen: true
};
```

### Build Environment Variables
```bash
# .env.production
VITE_API_BASE_URL=https://your-orchestrator-api.com
VITE_WIDGET_VERSION=1.0.0
VITE_ENABLE_DEBUG=false
VITE_GCS_BUCKET=gke-10-hackathon-assets

# .env.development  
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_DEBUG=true
```

### Build Configuration
The widget is built using Vite with the following configuration:

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    lib: {
      entry: 'src/main.ts',
      name: 'StylistWidget',
      fileName: 'stylist-widget',
      formats: ['iife'] // Self-contained bundle
    },
    rollupOptions: {
      output: {
        inlineDynamicImports: true // Single file output
      }
    }
  }
});
```

## 🤝 Contributing

### Development Guidelines
1. Follow Preact best practices and patterns
2. Use TypeScript for all new code
3. Write comprehensive unit tests
4. Test across multiple browsers and devices
5. Update documentation for new features

### Code Style
- Use ESLint and Prettier for consistent formatting
- Follow semantic commit message conventions
- Keep components small and focused
- Use meaningful variable and function names

### Pull Request Process
1. Create feature branch from `main`
2. Implement changes with tests
3. Test widget integration manually
4. Update documentation if needed
5. Submit PR with detailed description

## 📋 Browser Support

### Supported Browsers
- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+
- **Mobile Safari**: 14+
- **Chrome Mobile**: 90+

### Polyfills Included
- **Fetch API**: For older browsers
- **Promise**: ES6 Promise support
- **Object.assign**: Object merging
- **Array.from**: Array utilities

## 🚀 Performance Optimization

### Bundle Size
- **Preact**: ~3KB gzipped
- **Widget Code**: ~15KB gzipped
- **Total Bundle**: <20KB gzipped

### Loading Strategy
- **Async Loading**: Non-blocking script loading
- **Lazy Initialization**: Widget loads only when needed
- **Code Splitting**: Separate chunks for different features
- **Tree Shaking**: Remove unused code

### Runtime Performance
- **Virtual DOM**: Efficient rendering with Preact
- **Event Delegation**: Optimized event handling
- **Debounced Input**: Reduced API calls
- **Memory Management**: Proper cleanup on unmount
