# Kubernetes Deployment Manifests

This directory contains all Kubernetes manifests for deploying the GKE-10 Hackathon AI Agent ecosystem on Google Kubernetes Engine (GKE). The deployment includes the backend API services, frontend dashboard, and supporting infrastructure.

## 🏗️ Architecture Overview

```
k8s/
├── namespace.yaml                 # Kubernetes namespace
├── ksa.yaml                      # Kubernetes Service Account
├── orchestrator-deployment.yaml  # Main API server deployment
├── tech-analyst-deployment.yaml  # Technical Analyst Agent
├── architect-deployment.yaml     # Architect Agent
├── dashboard.yaml                # Frontend dashboard deployment
├── backend-config.yaml          # BackendConfig for load balancing
└── ingress.yaml                 # HTTP(S) load balancer configuration
```

## 🚀 Deployment Components

### Core Services

#### Orchestrator Service (`orchestrator-deployment.yaml`)
- **Purpose**: Main FastAPI server and intelligent orchestrator agent
- **Replicas**: 3 for high availability
- **Resources**: 1 CPU, 2Gi memory per pod
- **Ports**: 8000 (HTTP API)
- **Health Checks**: Liveness and readiness probes
- **Features**:
  - Workload Identity integration
  - Environment-based configuration
  - Horizontal Pod Autoscaling ready

#### Specialist Agent Services
- **Tech Analyst** (`tech-analyst-deployment.yaml`): Technical analysis and recommendations
- **Architect** (`architect-deployment.yaml`): System architecture design and optimization
- **Configuration**: Similar to orchestrator with agent-specific environment variables

#### Dashboard Service (`dashboard.yaml`)
- **Purpose**: Vue 3 frontend for monitoring and management
- **Technology**: Nginx serving static files
- **Replicas**: 2 for redundancy
- **Resources**: 0.5 CPU, 1Gi memory per pod

### Infrastructure Components

#### Namespace (`namespace.yaml`)
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-agents
  labels:
    name: ai-agents
```

#### Service Account (`ksa.yaml`)
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-agent-ksa
  namespace: ai-agents
  annotations:
    iam.gke.io/gcp-service-account: ai-agent-gsa@PROJECT_ID.iam.gserviceaccount.com
```

#### Ingress Configuration (`ingress.yaml`)
- **Load Balancer**: Google Cloud Load Balancer
- **SSL**: Automatic SSL certificate provisioning
- **Routing**: Path-based routing to services
- **Backend Configuration**: Custom health checks and timeouts

## 🔧 Configuration Management

### Environment Variables
All services use environment variables for configuration:

```yaml
env:
- name: GOOGLE_CLOUD_PROJECT
  value: "your-project-id"
- name: FIRESTORE_DATABASE_ID
  value: "your-database-id"
- name: VERTEX_AI_LOCATION
  value: "us-central1"
- name: PUBSUB_TOPIC_PREFIX
  value: "agent-tasks"
- name: LOG_LEVEL
  value: "INFO"
```

### Secrets Management
Sensitive configuration is managed through Kubernetes secrets:

```bash
# Create secrets for API keys and credentials
kubectl create secret generic ai-agent-secrets \
  --from-literal=firebase-api-key=your-api-key \
  --from-literal=vertex-ai-key=your-vertex-key \
  -n ai-agents
```

### ConfigMaps
Non-sensitive configuration through ConfigMaps:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-agent-config
  namespace: ai-agents
data:
  api-timeout: "30s"
  max-retries: "3"
  log-format: "json"
```

## 🛡️ Security Configuration

### Workload Identity
Secure access to Google Cloud services without storing service account keys:

```yaml
# Kubernetes Service Account
apiVersion: v1
kind: ServiceAccount
metadata:
  annotations:
    iam.gke.io/gcp-service-account: ai-agent-gsa@PROJECT_ID.iam.gserviceaccount.com
  name: ai-agent-ksa
  namespace: ai-agents
```

### Network Policies
Restrict network traffic between pods:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-agent-network-policy
  namespace: ai-agents
spec:
  podSelector:
    matchLabels:
      app: orchestrator
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: dashboard
    ports:
    - protocol: TCP
      port: 8000
```

### Pod Security Standards
Enforce security policies:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-agents
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## 📊 Monitoring & Observability

### Health Checks
All services include comprehensive health checks:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### Resource Monitoring
Resource requests and limits for optimal performance:

```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 1000m
    memory: 2Gi
```

### Logging Configuration
Structured logging for better observability:

```yaml
env:
- name: LOG_LEVEL
  value: "INFO"
- name: LOG_FORMAT
  value: "json"
- name: LOG_OUTPUT
  value: "stdout"
```

## 🚀 Deployment Instructions

### Prerequisites
- GKE cluster with Workload Identity enabled
- `kubectl` configured to access your cluster
- Required Google Cloud APIs enabled:
  - Kubernetes Engine API
  - Vertex AI API
  - Firestore API
  - Pub/Sub API

### Step 1: Create Namespace and Service Account
```bash
kubectl apply -f namespace.yaml
kubectl apply -f ksa.yaml
```

### Step 2: Set up Workload Identity
```bash
# Create Google Service Account
gcloud iam service-accounts create ai-agent-gsa \
  --display-name="AI Agent Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:ai-agent-gsa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:ai-agent-gsa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Bind Kubernetes and Google Service Accounts
gcloud iam service-accounts add-iam-policy-binding \
  ai-agent-gsa@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[ai-agents/ai-agent-ksa]"
```

### Step 3: Deploy Backend Services
```bash
# Deploy orchestrator (main API)
kubectl apply -f orchestrator-deployment.yaml

# Deploy specialist agents
kubectl apply -f tech-analyst-deployment.yaml
kubectl apply -f architect-deployment.yaml

# Configure backend settings
kubectl apply -f backend-config.yaml
```

### Step 4: Deploy Frontend Dashboard
```bash
kubectl apply -f dashboard.yaml
```

### Step 5: Configure Load Balancer
```bash
kubectl apply -f ingress.yaml
```

### Step 6: Verify Deployment
```bash
# Check pod status
kubectl get pods -n ai-agents

# Check services
kubectl get services -n ai-agents

# Check ingress
kubectl get ingress -n ai-agents

# View logs
kubectl logs -f deployment/orchestrator -n ai-agents
```

## 🔄 Scaling Configuration

### Horizontal Pod Autoscaler
Automatic scaling based on CPU and memory usage:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestrator-hpa
  namespace: ai-agents
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orchestrator
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaler
Automatic resource adjustment:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: orchestrator-vpa
  namespace: ai-agents
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orchestrator
  updatePolicy:
    updateMode: "Auto"
```

## 🔧 Troubleshooting

### Common Issues

#### Pod Startup Failures
```bash
# Check pod events
kubectl describe pod <pod-name> -n ai-agents

# View container logs
kubectl logs <pod-name> -c <container-name> -n ai-agents

# Check resource constraints
kubectl top pods -n ai-agents
```

#### Service Discovery Issues
```bash
# Test service connectivity
kubectl exec -it <pod-name> -n ai-agents -- curl http://orchestrator:8000/health

# Check service endpoints
kubectl get endpoints -n ai-agents

# Verify DNS resolution
kubectl exec -it <pod-name> -n ai-agents -- nslookup orchestrator.ai-agents.svc.cluster.local
```

#### Workload Identity Problems
```bash
# Verify service account annotation
kubectl describe sa ai-agent-ksa -n ai-agents

# Check Google Service Account binding
gcloud iam service-accounts get-iam-policy ai-agent-gsa@PROJECT_ID.iam.gserviceaccount.com

# Test authentication from pod
kubectl exec -it <pod-name> -n ai-agents -- curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

### Debugging Commands
```bash
# Get cluster information
kubectl cluster-info

# Check node status
kubectl get nodes

# View resource usage
kubectl top nodes
kubectl top pods -n ai-agents

# Check events
kubectl get events -n ai-agents --sort-by='.lastTimestamp'

# Port forward for local testing
kubectl port-forward service/orchestrator 8000:8000 -n ai-agents
```

## 🔄 Updates and Rollbacks

### Rolling Updates
```bash
# Update deployment image
kubectl set image deployment/orchestrator \
  orchestrator=gcr.io/PROJECT_ID/orchestrator:v2.0.0 \
  -n ai-agents

# Check rollout status
kubectl rollout status deployment/orchestrator -n ai-agents

# View rollout history
kubectl rollout history deployment/orchestrator -n ai-agents
```

### Rollback Strategy
```bash
# Rollback to previous version
kubectl rollout undo deployment/orchestrator -n ai-agents

# Rollback to specific revision
kubectl rollout undo deployment/orchestrator --to-revision=2 -n ai-agents

# Pause rollout
kubectl rollout pause deployment/orchestrator -n ai-agents

# Resume rollout
kubectl rollout resume deployment/orchestrator -n ai-agents
```

## 📋 Maintenance Tasks

### Regular Maintenance
```bash
# Update cluster
gcloud container clusters upgrade CLUSTER_NAME --zone=ZONE

# Update node pools
gcloud container node-pools upgrade POOL_NAME --cluster=CLUSTER_NAME --zone=ZONE

# Clean up unused resources
kubectl delete pod --field-selector=status.phase==Succeeded -n ai-agents
kubectl delete pod --field-selector=status.phase==Failed -n ai-agents
```

### Backup and Recovery
```bash
# Backup configurations
kubectl get all -n ai-agents -o yaml > ai-agents-backup.yaml

# Export secrets (be careful with sensitive data)
kubectl get secrets -n ai-agents -o yaml > secrets-backup.yaml

# Restore from backup
kubectl apply -f ai-agents-backup.yaml
```

## 🔐 Security Best Practices

### Image Security
- Use minimal base images (distroless, alpine)
- Scan images for vulnerabilities
- Use specific image tags, not `latest`
- Implement image signing and verification

### Runtime Security
- Run containers as non-root users
- Use read-only root filesystems
- Implement Pod Security Standards
- Regular security audits and updates

### Network Security
- Implement Network Policies
- Use TLS for all communications
- Restrict ingress and egress traffic
- Monitor network traffic patterns

## 📊 Cost Optimization

### Resource Optimization
- Right-size resource requests and limits
- Use Spot/Preemptible instances for non-critical workloads
- Implement cluster autoscaling
- Monitor and optimize resource usage

### Storage Optimization
- Use appropriate storage classes
- Implement data lifecycle policies
- Regular cleanup of unused volumes
- Monitor storage costs

## 🤝 Contributing

### Deployment Guidelines
1. Test all changes in a development cluster first
2. Use proper resource limits and requests
3. Include comprehensive health checks
4. Document any new configuration options
5. Follow Kubernetes best practices

### Security Guidelines
1. Never commit secrets to version control
2. Use Workload Identity instead of service account keys
3. Implement least privilege access
4. Regular security reviews and updates

### Monitoring Guidelines
1. Include proper logging configuration
2. Set up alerting for critical metrics
3. Monitor resource usage and costs
4. Implement distributed tracing for complex workflows
