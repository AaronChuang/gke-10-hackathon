# GKE-10 Hackathon: Dynamic AI Agentic Ecosystem

[![AI Agent Dashboard](https://img.shields.io/badge/AI-Agent%20Dashboard-blue?style=for-the-badge&logo=probot)](https://your-dashboard-url.com)
[![Vue 3](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=for-the-badge&logo=vue.js)](https://vuejs.org/)
[![GKE Autopilot](https://img.shields.io/badge/GKE-Autopilot-4285F4?style=for-the-badge&logo=google-kubernetes-engine)](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)
[![Gemini](https://img.shields.io/badge/Powered%20by-Gemini-8E77D3?style=for-the-badge&logo=google-gemini)](https://deepmind.google/technologies/gemini/)

A dynamic, manageable AI agent ecosystem built on Google Cloud for the GKE Turns 10 Hackathon. This platform features a decoupled microservices architecture with a management dashboard, an injectable customer-facing widget, and a backend powered by multiple AI agents. The entire system is orchestrated on GKE, supporting intelligent task routing, dynamic agent management, and a Retrieval-Augmented Generation (RAG) knowledge base.

**Live Demo URL:** `[Your Deployed Dashboard URL Here]`

## 🌟 About This Project (GKE Turns 10 Hackathon)

This project was created for the **GKE Turns 10 Hackathon** (September 12 - September 22, 2025). Our goal was to enhance the **Online Boutique** sample application with Agentic AI capabilities without modifying its core source code. We achieved this by building an independent, injectable JavaScript widget powered by a robust, GKE-hosted AI microservices backend.

* **Non-Invasive Integration:** A single `<script>` tag injects an "AI Stylist" into the Online Boutique product pages, demonstrating a clean, decoupled, and scalable integration pattern.
* **Powered by GKE:** The entire backend, from the intelligent orchestrator to the specialized AI agents and the management dashboard, is containerized and runs on a GKE Autopilot cluster for hands-off, optimized infrastructure management.
* **Leveraging Google AI:** The system's intelligence is powered by Google's Gemini models via Vertex AI, with a RAG implementation using Vector Search to provide grounded, context-aware responses.

### Challenges We Ran Into

*   **State Management in a Serverless World:** Coordinating state across multiple serverless GKE services and asynchronous agents was complex. We solved this by using Firestore as a centralized, real-time state database, providing a single source of truth for all components.
*   **Preventing Agent Loops:** Early prototypes occasionally resulted in agents getting stuck in infinite loops. We implemented a guardrails system with a two-retry termination policy and detailed logging to prevent this and ensure system stability.

### Accomplishments & Learnings

*   **Decoupled Architecture is Key:** The microservices approach was highly effective. It allowed us to develop, deploy, and scale the dashboard, orchestrator, and agents independently. GKE Autopilot made managing this complex setup surprisingly straightforward.
*   **The Power of Human-AI Collaboration:** Pairing a human architect with AI assistants for coding and analysis proved to be a massive productivity multiplier. This hybrid team model allowed us to build a sophisticated system in a fraction of the time.
*   **Non-Invasive Integration Works:** The injectable widget strategy successfully enhanced an existing application without touching its source code, demonstrating a powerful pattern for modernizing legacy systems.

## 👥 Our Team: A Human-AI Collaboration

This project was brought to life through a unique development methodology, pairing a human developer with a team of advanced AI assistants. This hybrid approach allowed for rapid prototyping, complex problem-solving, and sophisticated code generation.

* **Human Developer (Aaron Chen):** Acted as the project lead, architect, and strategist. Responsible for defining the vision, making key architectural decisions, and performing final code implementation and debugging.
* **AI Partner (Google's Gemini 2.5 Pro):** Served as the primary co-programmer and systems analyst. Responsible for generating complex code blocks (Kubernetes YAML, Python backend logic, Preact/Vue components), writing detailed technical specifications, and providing in-depth debugging suggestions.
* **AI Partner (Anthropic's Claude 3 Sonnet):** Acted as a conceptual sparring partner and code refactoring specialist, responsible for brainstorming alternative approaches and improving code readability.

## ✨ Core Features

* **🤖 Decoupled Microservices:** The backend is split into an **Orchestrator** for management and a **Proxy Agent** for conversations, allowing independent scaling and development.
* **🧠 Dynamic Agent Management:** A comprehensive Vue 3 dashboard allows for the creation, monitoring, and management of AI agents in real-time via a direct Firebase connection.
* **🗣️ Conversational AI Widget:** A lightweight, injectable Preact widget provides AI-powered customer assistance on any website, connecting to the backend via a GKE Ingress.
* **🧠 Retrieval-Augmented Generation (RAG):** Agent responses are grounded in a knowledge base created by ingesting external websites, ensuring answers are relevant and factually based.
* **🛡️ Intelligent Guardrails:** The system includes mechanisms like retry limits to prevent infinite loops and tracks token consumption for cost analysis.
* **🔄 Agent-to-Agent (A2A) Communication:** Our architecture supports both inter-service **Agent-to-Agent (A2A)** communication via Pub/Sub and intra-service collaboration using the CrewAI framework, enabling complex, multi-agent workflows.

## 🏗️ System Architecture

A high-level overview of the component relationships and data flow within the ecosystem.


![System Architecture Diagram for the AI Agentic Ecosystem](./docs/images/system-architecture.png)

### System Flow
1.  **Access Site:** The user visits the Online Boutique application.
2.  **Inject JS:** Cloud Storage serves the `widget.js` file, which is injected into the site.
3.  **Interact:** The user interacts with the AI Widget or the Admin Dashboard, sending requests to the GKE Ingress.
4.  **Publish Task:** The `Proxy Agent` receives the request and publishes a task to Pub/Sub for asynchronous processing.
5.  **Trigger Agent:** Pub/Sub triggers the appropriate `Agent Worker Pod`.
6.  **Execute & Write State:** The agent completes the task and writes the result and status to Firestore.
7.  **Calls for Intelligence:** Throughout the process, agents call Vertex AI for LLM and RAG capabilities.
(Real-time updates are pushed from Firestore back to the user's browser.)



### Core Workflow Sequence

This sequence diagram illustrates the end-to-end flow of a conversational AI request, from initial user interaction to complex, asynchronous task delegation between agents.


![Core Workflow Sequence Diagram](./docs/images/core-workflow-sequence.png)


### "AI as a Company": Our Architectural Philosophy

To achieve a truly scalable and manageable system, we architected our entire AI ecosystem based on a powerful metaphor: **AI as a Company**. Each component has a clearly defined corporate role, enabling a sophisticated and decoupled collaboration model.

* **The Front Desk (`Proxy Agent`):** This is the company's sole public-facing department. It directly handles all initial customer conversations via the injectable widget. It is trained to manage simple interactions and answer basic questions on its own.

* **The General Manager (`Orchestrator Agent`):** This is the company's internal decision-making core. It does not interact with customers directly. When the `Proxy Agent` encounters a complex request it cannot handle, it submits an "internal work ticket" (a task) to the `Orchestrator`. The `Orchestrator`'s job is to analyze this complex task, break it down if necessary, and delegate it to the most appropriate specialist department.

* **Specialist Departments (`Agent Workers`):** These are the company's expert teams (e.g., `Styling Dept.`, `Market Analysis Dept.`). Each is a specialized AI agent that receives tasks from the `Orchestrator` and executes them. These departments can be dynamically created, configured, and managed through the dashboard.

* **Corporate Communication Channels:** Our "company" utilizes a hybrid communication model:
    * **Inter-Departmental Memos (`Google Cloud Pub/Sub`):** For asynchronous, decoupled communication *between* major departments (e.g., from `Proxy Agent` to `Orchestrator`, or `Orchestrator` to `Stylist Agent`). This ensures the system is resilient and scalable.
    * **Intra-Departmental Teamwork (`CrewAI`):** For synchronous, complex collaboration *within* a single department. For example, to fulfill one task, the `Styling Agent` might internally coordinate a small crew of sub-agents (a "trend researcher," a "copywriter," etc.) to produce the final output.


## 🚀 Core Technology Stack

### **Backend Technologies**
-   **FastAPI**: High-performance Python web framework for the API layer and orchestrator service
-   **CrewAI**: Framework for orchestrating role-playing, autonomous AI agents with specialized capabilities
-   **Google Cloud Firestore**: NoSQL document database for real-time state management and task tracking
-   **Google Cloud Pub/Sub**: Asynchronous messaging queue, acting as the **Message Coordination Platform (MCP)** for inter-agent communication
-   **Google Vertex AI**: Serves the Gemini family of Large Language Models for AI processing
-   **LangChain**: Framework for developing LLM-powered applications with RAG capabilities
-   **Python 3.9+**: Core backend language with comprehensive type hints

### **Frontend Technologies**
-   **Vue 3 with Composition API**: Modern reactive framework for the management dashboard
-   **Preact**: Lightweight React alternative (3KB) for the injectable widget
-   **TypeScript**: Type-safe JavaScript for robust development across all frontend components
-   **Firebase SDK**: Client-side library for real-time data synchronization with Firestore
-   **Sass/SCSS**: CSS pre-processor with design system and component-scoped styling
-   **Vite**: Next-generation frontend tooling for fast development and optimized builds
-   **CSS Modules**: Scoped styling to prevent conflicts in widget integration

### **Cloud & DevOps Infrastructure**
-   **Google Kubernetes Engine (GKE)**: Container orchestration with Autopilot for managed scaling
-   **Google Cloud Storage**: Object storage for hosting the injectable JavaScript widget
-   **Google Artifact Registry**: Private Docker container registry for secure image storage
-   **Google Cloud Build**: Serverless CI/CD pipeline for automated container builds
-   **Workload Identity**: Secure, keyless authentication for GKE applications accessing GCP services
-   **Docker & Docker Compose**: Containerization for development and production deployment
-   **Google Cloud Load Balancer**: HTTP(S) load balancing with SSL termination and health checks

## **🛠️ Getting Started**

### Prerequisites
-   Python 3.9+
-   Node.js 18+ (with `pnpm` installed)
-   Docker & Docker Compose
-   Google Cloud SDK (`gcloud`)
-   A Google Cloud Platform project with billing enabled

### 1. Clone the Project
```bash
git clone <repository-url>
cd gke-10-hackathon
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit the .env file and fill in your GCP project details
```

### 3. Set Up Google Cloud Credentials
For local development, you'll need a service account key.
```bash
# Place your GCP service account key in the project root
cp path/to/your/google-credentials.json ./google-credentials.json
```

### 4. Launch Backend Services (Local)
```bash
# Use Docker Compose to start all services
docker-compose up --build
```

### 5. Launch Frontend Dashboard (Local)
```bash
cd dashboard
pnpm install
pnpm run dev
```

### 6. Access the Application
- **API (via Orchestrator):** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Management Dashboard:** http://localhost:5173
- **Widget Preview:** http://localhost:4173 (stylist-widget dev server)

## **🚢 Deployment Guide**

The entire system is configured for deployment on GKE.

### 1. Set Up Cloud Resources
Ensure you have:
- A GKE cluster with Workload Identity enabled
- Pub/Sub topics for each agent
- A Firestore database
- An Artifact Registry repository

### 2. Configure Workload Identity
Follow the guide to create a GSA, KSA, and bind them together to provide secure access to GCP APIs.

### 3. Build & Push Images
```bash
# Build the main application image
gcloud builds submit --tag asia-east1-docker.pkg.dev/[PROJECT-ID]/[REPO]/ai-agent-base:latest .
# Build and push other images (dashboard, widget) as needed
```

### 4. Deploy to GKE
Apply the Kubernetes manifests in the `k8s/` directory. The recommended order ensures that dependencies like namespaces and configurations are created first.
```bash
# 1. Namespace and Service Account
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/ksa.yaml

# 2. Backend Configurations
kubectl apply -f k8s/backend-config.yaml

# 3. Deployments
kubectl apply -f k8s/orchestrator-deployment.yaml
kubectl apply -f k8s/proxy-agent-deployment.yaml
kubectl apply -f k8s/omni-agent-deployment.yaml
kubectl apply -f k8s/agent-registry-listener-deployment.yaml
kubectl apply -f k8s/dashboard.yaml

# 4. Expose Services with Ingress
kubectl apply -f k8s/ingress.yaml

# 5. Verify Deployment
kubectl get pods,services,ingress -n ai-agents
```

### 5. Deploy Widget to Cloud Storage
```bash
# Build and deploy the AI assistant widget
cd stylist-widget
pnpm run build
gcloud storage cp dist/stylist-widget.js gs://gke-10-hackathon-assets/ai-assistant-widget.js

# Verify widget deployment
curl -I https://storage.googleapis.com/gke-10-hackathon-assets/ai-assistant-widget.js
```

## **🤝 Contributing**

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## **📄 License**

Distributed under the MIT License. See LICENSE for more information.

## **🙏 Acknowledgements**

* **Google Cloud Platform** for providing the robust and scalable cloud infrastructure that made this project possible.  
* **The CrewAI Team** for their excellent agentic framework, which formed the backbone of our agent collaboration.  
* **The** Vue.js & Preact **Communities** for their outstanding frontend tools and documentation.  
* Our invaluable **AI Development Partners**, Google's Gemini 2.5 Pro and Anthropic's Claude 3 Sonnet, for their exceptional assistance in code generation and problem-solving.