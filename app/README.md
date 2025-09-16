# AI Agent Backend System

The `app/` directory contains the core backend system for the GKE-10 Hackathon AI Agent ecosystem. This Python-based microservices architecture implements intelligent AI agents using CrewAI framework, providing RESTful APIs, dynamic agent management, and RAG-powered knowledge base integration.

## 🏗️ Architecture Overview

```
app/
├── workers/                    # Agent Workers & API Endpoints
│   ├── orchestrator.py         # Main FastAPI server + Orchestrator Agent
│   ├── tech_analyst_worker.py  # Technical Analysis Agent
│   ├── architect_worker.py     # System Architecture Agent
│   ├── stylist_worker.py       # UI/UX Styling Agent
│   └── __init__.py
├── shared_crew_lib/            # Shared Libraries & Core Components
│   ├── agents/                 # CrewAI Agent Implementations
│   ├── base/                   # Enhanced Base Classes
│   ├── clients/                # GCP Service Clients
│   ├── schemas/                # Data Models & Schemas
│   └── services/               # Core Business Logic Services
├── services/                   # Application Services
│   └── crawler_service.py      # Website Crawling for RAG
└── scripts/                    # Deployment & Provisioning Scripts
    └── provision_agent_resources.py
```

## 🤖 Core Components

### Workers (Agent Microservices)

#### Orchestrator (`orchestrator.py`)
- **Primary Role**: Central coordination and API gateway
- **Responsibilities**:
  - FastAPI server hosting all REST endpoints
  - Intelligent conversation management
  - Task routing to specialized agents
  - Real-time WebSocket communication
- **Key Features**:
  - Multi-turn conversation handling
  - Intent analysis and agent selection
  - Dynamic agent discovery and creation
  - Comprehensive logging and monitoring

#### Specialized Agents
- **TechAnalystAgent**: Technical analysis, code review, architecture recommendations
- **ArchitectAgent**: System design, scalability planning, infrastructure advice
- **StylistAgent**: UI/UX design, fashion styling, visual recommendations

### Shared Libraries (`shared_crew_lib/`)

#### Enhanced Base Classes (`base/`)
- **EnhancedBaseAgent**: Abstract base with RAG integration, token monitoring, guardrails
- **BaseAgentWrapper**: Standardized agent lifecycle management
- **TaskGuardrailService**: Execution limits and safety controls

#### Agents (`agents/`)
- CrewAI-based agent implementations
- Role-specific prompts and capabilities
- Knowledge base integration
- Token consumption tracking

#### Clients (`clients/`)
- **FirestoreClient**: Real-time database operations
- **PubSubClient**: Asynchronous messaging
- **VertexAIClient**: LLM model access
- **VectorSearchClient**: RAG knowledge retrieval

#### Services (`services/`)
- **AgentRegistryService**: Dynamic agent management
- **KnowledgeBaseService**: RAG implementation
- **TaskExecutionService**: Workflow orchestration
- **TokenMonitoringService**: Cost tracking

## 🚀 Key Features

### Dynamic Agent Management
- **Runtime Agent Creation**: Create new agents through API calls
- **Capability Registration**: Auto-discovery of agent capabilities
- **Resource Provisioning**: Automatic Pub/Sub topic creation
- **State Persistence**: Agent configurations stored in Firestore

### RAG Knowledge Base
- **Website Crawling**: Automated content ingestion
- **Vector Embeddings**: Semantic search capabilities
- **Grounded Responses**: All answers constrained to knowledge base
- **Real-time Updates**: Dynamic knowledge base management

### Intelligent Guardrails
- **Retry Limits**: Prevent infinite execution loops
- **Token Monitoring**: Real-time cost tracking
- **Execution Logging**: Comprehensive audit trails
- **Error Handling**: Graceful failure recovery

## 🛠️ Technology Stack

### Core Frameworks
- **FastAPI**: High-performance async web framework
- **CrewAI**: Multi-agent orchestration framework
- **LangChain**: LLM application development
- **Pydantic**: Data validation and serialization

### Google Cloud Integration
- **Vertex AI**: Gemini model access
- **Firestore**: Real-time NoSQL database
- **Pub/Sub**: Asynchronous messaging
- **Cloud Storage**: File and asset storage
- **Vector Search**: Semantic knowledge retrieval

## 📋 API Endpoints

### Core Conversation API
```
POST /api/conversation
- Main endpoint for agent interactions
- Supports multi-turn conversations
- Automatic agent routing based on intent

GET /api/conversation/{conversation_id}
- Retrieve conversation history
- Real-time status updates
```

### Agent Management
```
GET /api/agents
- List all registered agents
- Include capabilities and status

POST /api/agents
- Create new agent dynamically
- Auto-provision required resources

PATCH /api/agents/{agent_id}
- Update agent configuration
- Modify capabilities and prompts

DELETE /api/agents/{agent_id}
- Remove agent and cleanup resources
```

### Knowledge Base Management
```
GET /api/knowledge-base
- List all knowledge entries
- Search and filter capabilities

POST /api/knowledge-base/index
- Add new website to knowledge base
- Trigger crawling and indexing

POST /api/knowledge-base/reindex/{entry_id}
- Re-crawl and update existing entry
- Refresh vector embeddings

DELETE /api/knowledge-base/{entry_id}
- Remove knowledge entry
- Cleanup associated vectors
```

### Health & Monitoring
```
GET /health
- Service health status
- Component availability check

GET /healthz
- Kubernetes health probe
- Ready/live status

GET /api/metrics
- Token consumption statistics
- Performance metrics
- Error rates
```

## 🔧 Configuration

### Environment Variables
```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./google-credentials.json

# Firestore Database
FIRESTORE_DATABASE_ID=your-database-id

# Vertex AI Configuration
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-pro

# Pub/Sub Configuration
PUBSUB_TOPIC_PREFIX=agent-tasks

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Agent Configuration
Agents are configured through Firestore documents in the `agents` collection:

```json
{
  "agent_id": "stylist-agent",
  "name": "Fashion Stylist",
  "description": "Provides fashion and styling advice",
  "capabilities": ["fashion", "styling", "ui-design"],
  "model_config": {
    "model": "gemini-1.5-pro",
    "temperature": 0.7,
    "max_tokens": 2048
  },
  "pubsub_topic": "agent-tasks-stylist",
  "status": "active",
  "created_at": "2024-01-15T10:00:00Z"
}
```

## 🚀 Getting Started

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your GCP configuration

# Run the orchestrator (main API server)
uvicorn app.workers.orchestrator:app --reload --host 0.0.0.0 --port 8000

# Or run individual agents
python -m app.workers.tech_analyst_worker
python -m app.workers.architect_worker
python -m app.workers.stylist_worker
```

### Docker Development
```bash
# Build and run all services
docker-compose up --build

# Run specific service
docker-compose up orchestrator
```

### Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Test API endpoints
curl -X POST http://localhost:8000/api/conversation \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "Help me design a modern e-commerce website"}'
```

## 📊 Monitoring & Observability

### Logging
- Structured JSON logging with correlation IDs
- Request/response tracing
- Agent execution timelines
- Error stack traces with context

### Metrics
- Token consumption per agent/conversation
- Response times and latency percentiles
- Error rates by endpoint and agent
- Resource utilization (CPU, memory)

### Health Checks
- Database connectivity
- External API availability
- Agent worker status
- Message queue health

## 🔐 Security

### Authentication
- Google Cloud IAM integration
- Service account-based authentication
- Workload Identity for GKE deployment

### Data Protection
- Input sanitization and validation
- Output filtering for sensitive data
- Audit logging for all operations
- Encryption at rest and in transit

## 🚢 Deployment

### Kubernetes
The backend is containerized and deployed on GKE:

```yaml
# Deployment configuration in k8s/
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator
  template:
    spec:
      containers:
      - name: orchestrator
        image: gcr.io/project/orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: GOOGLE_CLOUD_PROJECT
          value: "your-project-id"
```

### Scaling
- Horizontal Pod Autoscaling based on CPU/memory
- Pub/Sub message queue for load distribution
- Firestore for shared state management
- Stateless design for easy scaling

## 🤝 Contributing

### Development Guidelines
1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write comprehensive docstrings
4. Include unit tests for new features
5. Update API documentation

### Code Structure
- Keep agents focused on single responsibilities
- Use dependency injection for testability
- Implement proper error handling
- Log important events and decisions

### Testing Strategy
- Unit tests for individual components
- Integration tests for API endpoints
- End-to-end tests for complete workflows
- Performance tests for scalability
