# AI Agent Backend System

The `app/` directory contains the core backend system for the GKE-10 Hackathon AI Agent ecosystem. This Python-based microservices architecture implements intelligent AI agents using CrewAI framework, providing RESTful APIs, dynamic agent management, and RAG-powered knowledge base integration.

## 🏗️ Architecture Overview

```
app/
├── workers/                    # Agent Workers & API Endpoints
│   ├── orchestrator.py         # Main FastAPI server + Orchestrator Agent
│   ├── proxy.py                # Proxy Agent for conversation handling
│   ├── omni_agent_worker.py    # Multi-purpose Omni Agent
│   └── __init__.py
├── shared_crew_lib/            # Shared Libraries & Core Components
│   ├── agents/                 # CrewAI Agent Implementations
│   │   ├── base.py             # Base agent class
│   │   ├── orchestrator_agent.py # Orchestrator agent implementation
│   │   ├── proxy_agent.py      # Proxy agent for conversations
│   │   └── omni_agent.py       # Multi-purpose agent
│   ├── clients/                # GCP Service Clients
│   │   └── gcp_clients.py      # Firestore, Pub/Sub clients
│   ├── schemas/                # Data Models & Schemas
│   │   ├── conversation.py     # Conversation data models
│   │   ├── agent_registry.py   # Agent registry schemas
│   │   └── knowledge_base.py   # Knowledge base schemas
│   └── services/               # Core Business Logic Services
│       ├── conversation_service.py # Conversation management
│       ├── agent_registry_service.py # Agent lifecycle management
│       └── rag_service.py      # RAG implementation
├── services/                   # Application Services
│   └── crawler_service.py      # Website Crawling for RAG
└── scripts/                    # Deployment & Provisioning Scripts
    └── provision_agent_resources.py
```

## 🤖 Core Components

### Workers (Agent Microservices)

#### Orchestrator (`orchestrator.py`)
- **Primary Role**: Central coordination and management API
- **Responsibilities**:
  - FastAPI server hosting management REST endpoints
  - Agent lifecycle management (create, update, delete agents)
  - Knowledge base management (indexing, search)
  - Task coordination and routing
- **Key Features**:
  - Agent registry management
  - Knowledge base CRUD operations
  - System initialization and health checks
  - Comprehensive logging and monitoring

#### Proxy Agent (`proxy.py`)
- **Primary Role**: Customer conversation handling
- **Responsibilities**:
  - FastAPI server for conversation API
  - Customer interaction processing
  - Task delegation to specialist agents
  - Session management and history
- **Key Features**:
  - Multi-turn conversation handling
  - Intent analysis and response generation
  - Firebase integration for real-time updates
  - Direct replies and task delegation

#### Omni Agent (`omni_agent_worker.py`)
- **Primary Role**: Multi-purpose task processing
- **Responsibilities**:
  - Flexible task execution
  - Pub/Sub message processing
  - Dynamic capability handling
- **Key Features**:
  - Adaptable to various task types
  - Event-driven processing
  - Scalable worker architecture

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

### Conversation API (Proxy Agent - Port 8001)
```
POST /api/conversation
- Main endpoint for customer interactions
- Supports multi-turn conversations
- Session management and history
- Direct replies and task delegation

GET /api/conversation/{session_id}
- Retrieve conversation history
- Real-time status updates
- Session summary and related tasks

POST /api/task
- Create asynchronous tasks
- Task delegation to specialist agents

GET /api/task/{task_id}
- Get task status and results
- Real-time progress monitoring
```

### Management API (Orchestrator - Port 8000)
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

POST /api/start-task
- Start orchestrated tasks
- Legacy task initiation endpoint
```

### Knowledge Base Management (Orchestrator - Port 8000)
```
GET /api/knowledge-base
- List all knowledge entries
- Search and filter capabilities

POST /api/knowledge-base/index
- Add new website to knowledge base
- Trigger crawling and indexing

POST /api/knowledge-base/reindex/{kb_id}
- Re-crawl and update existing entry
- Refresh vector embeddings

DELETE /api/knowledge-base/{kb_id}
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
GCP_PROJECT_ID=gke-10-hackathon-471902
GCP_FIRESTORE_NAME=gke-10-hackathon
GOOGLE_API_KEY=your-gemini-api-key

# Pub/Sub Configuration
PROXY_AGENT_SUBSCRIPTION_ID=proxy-agent-sub
AGENT_REGISTRY_SUBSCRIPTION_ID=agent-registry-updates-sub

# API Configuration
PYTHONPATH=/workspace
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

# Run the orchestrator (management API server)
uvicorn app.workers.orchestrator:app --reload --host 0.0.0.0 --port 8000

# Run the proxy agent (conversation API server)
uvicorn app.workers.proxy:app --reload --host 0.0.0.0 --port 8001

# Run the omni agent worker
python -m app.workers.omni_agent_worker
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

# Test conversation API (proxy agent)
curl -X POST http://localhost:8001/api/conversation \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "Tell me about this product", "user_id": "test-user"}'

# Test management API (orchestrator)
curl -X GET http://localhost:8000/api/agents
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
