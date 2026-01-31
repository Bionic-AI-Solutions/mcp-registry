# Deployment Guide - MCP Registry

**Generated:** 2026-01-31
**Project:** mcp-registry
**Type:** Kubernetes Deployment

---

## Prerequisites

### Infrastructure Requirements

- **Kubernetes:** 1.25 or higher
- **kubectl:** Configured with cluster access
- **Docker Registry:** For storing container images (Docker Hub, GCR, ECR, or private registry)
- **Persistent Storage:** StorageClass for PostgreSQL PVCs
- **Load Balancer:** For external access (cloud provider or MetalLB)

### Optional Components

- **cert-manager:** For automatic TLS certificate management
- **Prometheus:** For metrics collection
- **Grafana:** For metrics visualization
- **Ingress Controller:** NGINX, Traefik, or cloud-specific

### Access Requirements

- Cluster admin permissions for initial setup
- Container registry push access
- DNS management (for domain configuration)

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Load Balancer / Ingress         │
│    (External traffic entry point)       │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│      MCP Registry Service               │
│      (ClusterIP or LoadBalancer)        │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │  MCP Registry Pods  │
        │  (HPA: 2-10 pods)   │
        │  ┌──────────────┐   │
        │  │ FastAPI      │   │
        │  │ Uvicorn      │   │
        │  │ Health check │   │
        │  └──────────────┘   │
        └──────┬─────┬────────┘
               │     │
          ┌────┴─┐ ┌─┴────┐
          │ PG   │ │ Redis│
          │ DB   │ │Cache │
          │(PVC) │ │      │
          └──────┘ └──────┘
```

---

## Deployment Steps

### Step 1: Build Container Image

#### Build Multi-stage Docker Image

```bash
# Navigate to project root
cd /workspaces/mcp-registry

# Build image
docker build -t <your-registry>/mcp-registry:v1.0.0 .

# Example for Docker Hub
docker build -t yourusername/mcp-registry:v1.0.0 .

# Example for GCR
docker build -t gcr.io/your-project/mcp-registry:v1.0.0 .

# Example for ECR
docker build -t <account-id>.dkr.ecr.<region>.amazonaws.com/mcp-registry:v1.0.0 .
```

#### Dockerfile Breakdown

**Stage 1: Builder**
- Base: `python:3.11-slim`
- Installs build dependencies (gcc, postgresql-client)
- Installs Python packages from `pyproject.toml`

**Stage 2: Production**
- Base: `python:3.11-slim`
- Creates non-root user `mcp`
- Copies Python dependencies from builder
- Sets environment variables
- Configures health check on `/health` endpoint
- Exposes port 8000
- Runs as non-root user for security

#### Push to Registry

```bash
# Login to registry
docker login

# Push image
docker push <your-registry>/mcp-registry:v1.0.0

# Tag as latest (optional)
docker tag <your-registry>/mcp-registry:v1.0.0 <your-registry>/mcp-registry:latest
docker push <your-registry>/mcp-registry:latest
```

---

### Step 2: Configure Kubernetes Manifests

#### Update Image Reference

Edit `k8s/05-deployment.yaml`:

```yaml
spec:
  template:
    spec:
      containers:
      - name: mcp-registry
        image: <your-registry>/mcp-registry:v1.0.0  # Update this line
        imagePullPolicy: IfNotPresent
```

#### Configure Secrets

Edit `k8s/02-secret.yaml` with base64-encoded values:

```bash
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Base64 encode values
echo -n "postgresql://user:password@postgres:5432/mcp_registry" | base64
echo -n "redis://redis:6379/0" | base64
echo -n "<your-fernet-key>" | base64
echo -n "<your-bootstrap-secret>" | base64
```

Update `k8s/02-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcp-registry-secret
  namespace: mcp-registry
type: Opaque
data:
  DATABASE_URL: <base64-encoded-postgres-url>
  REDIS_URL: <base64-encoded-redis-url>
  ENCRYPTION_KEY: <base64-encoded-fernet-key>
  ADMIN_CREATION_SECRET: <base64-encoded-bootstrap-secret>
  LANGFUSE_PUBLIC_KEY: <base64-encoded-langfuse-public-key>  # Optional
  LANGFUSE_SECRET_KEY: <base64-encoded-langfuse-secret-key>  # Optional
```

#### Configure Application Settings

Edit `k8s/01-configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-registry-config
  namespace: mcp-registry
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  HOST: "0.0.0.0"
  PORT: "8000"
  WORKERS: "4"
  CORS_ORIGINS: '["https://yourdomain.com"]'
  RATE_LIMIT_ENABLED: "true"
  LANGFUSE_HOST: "https://cloud.langfuse.com"  # Optional
```

#### Configure Ingress (Optional)

Edit `k8s/07-ingress.yaml` for custom domain:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mcp-registry-ingress
  namespace: mcp-registry
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod  # If using cert-manager
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - mcp-registry.yourdomain.com
    secretName: mcp-registry-tls
  rules:
  - host: mcp-registry.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mcp-registry-service
            port:
              number: 80
```

---

### Step 3: Deploy to Kubernetes

#### Apply Manifests in Order

```bash
# Create namespace
kubectl apply -f k8s/00-namespace.yaml

# Create ConfigMap and Secrets
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml

# Deploy PostgreSQL
kubectl apply -f k8s/03-postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n mcp-registry --timeout=120s

# Deploy Redis
kubectl apply -f k8s/04-redis.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis -n mcp-registry --timeout=60s

# Create ServiceAccount (if exists)
kubectl apply -f k8s/09-serviceaccount.yaml

# Deploy application
kubectl apply -f k8s/05-deployment.yaml

# Wait for application pods
kubectl wait --for=condition=ready pod -l app=mcp-registry -n mcp-registry --timeout=180s

# Create service
kubectl apply -f k8s/06-service.yaml

# Apply Ingress (optional)
kubectl apply -f k8s/07-ingress.yaml

# Apply HPA (Horizontal Pod Autoscaler)
kubectl apply -f k8s/08-hpa.yaml
```

#### Or Apply All at Once

```bash
# Apply all manifests
kubectl apply -f k8s/

# Note: May need to reapply if dependencies aren't ready
```

---

### Step 4: Run Database Migrations

#### Option A: Kubernetes Job (Recommended)

Create `k8s/10-migration-job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: mcp-registry-migration
  namespace: mcp-registry
spec:
  template:
    spec:
      containers:
      - name: migration
        image: <your-registry>/mcp-registry:v1.0.0
        command: ["alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: mcp-registry-secret
        - configMapRef:
            name: mcp-registry-config
      restartPolicy: OnFailure
  backoffLimit: 3
```

```bash
# Run migration
kubectl apply -f k8s/10-migration-job.yaml

# Check status
kubectl logs -f job/mcp-registry-migration -n mcp-registry

# Clean up job after success
kubectl delete job mcp-registry-migration -n mcp-registry
```

#### Option B: Manual from Pod

```bash
# Exec into running pod
kubectl exec -it deployment/mcp-registry -n mcp-registry -- bash

# Run migrations
alembic upgrade head

# Exit pod
exit
```

---

### Step 5: Verify Deployment

#### Check Pod Status

```bash
# View pods
kubectl get pods -n mcp-registry

# Expected output:
# NAME                            READY   STATUS    RESTARTS   AGE
# mcp-registry-<hash>-<id>        1/1     Running   0          2m
# postgres-<hash>-<id>            1/1     Running   0          5m
# redis-<hash>-<id>               1/1     Running   0          4m

# Check pod logs
kubectl logs -f deployment/mcp-registry -n mcp-registry

# Check all resources
kubectl get all -n mcp-registry
```

#### Health Check

```bash
# Port-forward for testing
kubectl port-forward -n mcp-registry service/mcp-registry-service 8000:80

# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2026-01-31T..."}
```

#### Test API Access

```bash
# Get LoadBalancer external IP (if using LoadBalancer service)
kubectl get service mcp-registry-service -n mcp-registry

# Or get Ingress URL
kubectl get ingress -n mcp-registry

# Test bootstrap endpoint
curl -X POST http://<external-ip>/api/v1/admin/bootstrap \
  -H "Content-Type: application/json" \
  -H "X-Bootstrap-Secret: <your-secret>" \
  -d '{
    "name": "Admin Tenant",
    "contact_email": "admin@example.com"
  }'
```

---

## Manifest Details

### 00-namespace.yaml
Creates isolated namespace `mcp-registry` for all resources.

### 01-configmap.yaml
Non-sensitive configuration:
- Debug mode
- Log level
- Host/port settings
- Worker count
- CORS origins
- Rate limiting toggle
- Observability endpoints

### 02-secret.yaml
Sensitive configuration:
- Database connection string
- Redis connection string
- Fernet encryption key
- Admin bootstrap secret
- Langfuse API keys (optional)

### 03-postgres.yaml
PostgreSQL StatefulSet:
- **Image:** `postgres:16-alpine`
- **Storage:** 10Gi PVC (configurable)
- **Service:** `postgres:5432` (ClusterIP)
- **Environment:** Database name, user, password from Secret

### 04-redis.yaml
Redis Deployment:
- **Image:** `redis:7-alpine`
- **Service:** `redis:6379` (ClusterIP)
- **Persistence:** Optional (configure volume if needed)

### 05-deployment.yaml
Application Deployment:
- **Replicas:** 3 (managed by HPA)
- **Image:** Your container image
- **Resources:**
  - Requests: 256Mi memory, 100m CPU
  - Limits: 512Mi memory, 500m CPU
- **Health Checks:**
  - Liveness: `/health` every 30s
  - Readiness: `/health` every 10s
- **Environment:** From ConfigMap and Secret
- **Security:** Non-root user, read-only root filesystem

### 06-service.yaml
Service exposing application:
- **Type:** LoadBalancer (or ClusterIP if using Ingress)
- **Port:** 80 → 8000 (container)
- **Selector:** `app: mcp-registry`

### 07-ingress.yaml
Ingress for external access:
- **Class:** nginx (configurable)
- **TLS:** cert-manager integration
- **Host:** Custom domain
- **Path:** `/` → service:80

### 08-hpa.yaml
Horizontal Pod Autoscaler:
- **Min Replicas:** 2
- **Max Replicas:** 10
- **Metrics:** CPU 70%, Memory 80%
- **Scale down:** Stabilization 300s

### 09-serviceaccount.yaml
ServiceAccount for pods:
- Identity for Kubernetes API access
- RBAC permissions (if needed)

---

## Scaling and Performance

### Horizontal Pod Autoscaling (HPA)

```bash
# View HPA status
kubectl get hpa -n mcp-registry

# Expected output:
# NAME           REFERENCE                 TARGETS         MINPODS   MAXPODS   REPLICAS
# mcp-registry   Deployment/mcp-registry   50%/70% CPU     2         10        3

# Describe HPA for details
kubectl describe hpa mcp-registry -n mcp-registry
```

### Manual Scaling

```bash
# Scale to specific number
kubectl scale deployment mcp-registry -n mcp-registry --replicas=5

# HPA will override manual scaling based on metrics
```

### Resource Tuning

Edit `k8s/05-deployment.yaml`:

```yaml
resources:
  requests:
    memory: "512Mi"   # Increase for heavy loads
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### PostgreSQL Performance

For production workloads, consider:
- Increase PVC size in `k8s/03-postgres.yaml`
- Use cloud-managed databases (RDS, Cloud SQL, Azure Database)
- Configure connection pooling in application
- Add read replicas for heavy read workloads

---

## Monitoring and Observability

### Logs

```bash
# View application logs
kubectl logs -f deployment/mcp-registry -n mcp-registry

# View logs from all pods
kubectl logs -l app=mcp-registry -n mcp-registry --tail=100

# View PostgreSQL logs
kubectl logs -l app=postgres -n mcp-registry --tail=50

# View Redis logs
kubectl logs -l app=redis -n mcp-registry --tail=50
```

### Metrics (Prometheus)

Application exposes Prometheus metrics at `/metrics` endpoint:

```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mcp-registry
  namespace: mcp-registry
spec:
  selector:
    matchLabels:
      app: mcp-registry
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

**Available Metrics:**
- HTTP request duration
- Request count by endpoint
- Active connections
- Database connection pool stats
- Redis cache hit/miss rates

### Health Checks

```bash
# Liveness probe (is container alive?)
curl http://<pod-ip>:8000/health

# Readiness probe (is container ready for traffic?)
curl http://<pod-ip>:8000/health

# Both use same endpoint, return 200 OK when healthy
```

### Observability with Langfuse

If Langfuse is configured in ConfigMap and Secret:
- LLM interactions are logged to Langfuse
- Traces include request context, tenant ID, API calls
- Access Langfuse dashboard to view telemetry

---

## Security Hardening

### Network Policies

Create `k8s/11-networkpolicy.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-registry-netpol
  namespace: mcp-registry
spec:
  podSelector:
    matchLabels:
      app: mcp-registry
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-nginx  # Only from ingress
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector: {}  # External APIs (Langfuse, etc.)
    ports:
    - protocol: TCP
      port: 443
```

### Pod Security Standards

Add to `k8s/05-deployment.yaml`:

```yaml
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: mcp-registry
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

### TLS/HTTPS

Use cert-manager for automatic certificate management:

```bash
# Install cert-manager (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

Update Ingress with cert-manager annotations (already in `k8s/07-ingress.yaml`).

---

## Backup and Disaster Recovery

### PostgreSQL Backups

#### Option A: pg_dump via CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: mcp-registry
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16-alpine
            command:
            - /bin/sh
            - -c
            - pg_dump $DATABASE_URL | gzip > /backup/mcp-registry-$(date +%Y%m%d).sql.gz
            envFrom:
            - secretRef:
                name: mcp-registry-secret
            volumeMounts:
            - name: backup
              mountPath: /backup
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: postgres-backup-pvc
          restartPolicy: OnFailure
```

#### Option B: Cloud Provider Snapshots

Use automated snapshots if using cloud-managed databases:
- AWS RDS: Automated backups with point-in-time recovery
- Google Cloud SQL: Automated backups
- Azure Database: Automated backups

### Restore from Backup

```bash
# Exec into PostgreSQL pod
kubectl exec -it deployment/postgres -n mcp-registry -- bash

# Restore from backup
gunzip -c /backup/mcp-registry-20260131.sql.gz | psql $DATABASE_URL
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n mcp-registry

# Common issues:
# - Image pull errors: Verify registry access and image name
# - CrashLoopBackOff: Check logs for application errors
# - Pending: Check resource constraints and node capacity
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity from app pod
kubectl exec -it deployment/mcp-registry -n mcp-registry -- \
  python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect(dsn='$DATABASE_URL'))"

# Check PostgreSQL service
kubectl get service postgres -n mcp-registry

# Check PostgreSQL logs
kubectl logs -l app=postgres -n mcp-registry
```

### Redis Connection Issues

```bash
# Test Redis connectivity from app pod
kubectl exec -it deployment/mcp-registry -n mcp-registry -- \
  python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()"

# Check Redis service
kubectl get service redis -n mcp-registry
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress mcp-registry-ingress -n mcp-registry

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Verify DNS points to LoadBalancer IP
nslookup mcp-registry.yourdomain.com
```

### Migration Failures

```bash
# Check migration job logs
kubectl logs job/mcp-registry-migration -n mcp-registry

# Manually run migration from pod
kubectl exec -it deployment/mcp-registry -n mcp-registry -- alembic upgrade head

# Check current migration version
kubectl exec -it deployment/mcp-registry -n mcp-registry -- alembic current
```

---

## Updating the Application

### Rolling Update

```bash
# Build new image
docker build -t <your-registry>/mcp-registry:v1.1.0 .
docker push <your-registry>/mcp-registry:v1.1.0

# Update deployment
kubectl set image deployment/mcp-registry \
  mcp-registry=<your-registry>/mcp-registry:v1.1.0 \
  -n mcp-registry

# Or edit deployment directly
kubectl edit deployment mcp-registry -n mcp-registry

# Watch rollout status
kubectl rollout status deployment/mcp-registry -n mcp-registry

# Check rollout history
kubectl rollout history deployment/mcp-registry -n mcp-registry
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/mcp-registry -n mcp-registry

# Rollback to specific revision
kubectl rollout undo deployment/mcp-registry -n mcp-registry --to-revision=2
```

### Database Migrations with Updates

```bash
# After deploying new version, run migration job
kubectl apply -f k8s/10-migration-job.yaml

# Wait for migration to complete
kubectl wait --for=condition=complete job/mcp-registry-migration -n mcp-registry --timeout=300s

# If migration fails, rollback application
kubectl rollout undo deployment/mcp-registry -n mcp-registry
```

---

## Multi-Environment Strategy

### Environment Separation

Use namespaces or separate clusters:

```bash
# Development
kubectl apply -f k8s/ --namespace=mcp-registry-dev

# Staging
kubectl apply -f k8s/ --namespace=mcp-registry-staging

# Production
kubectl apply -f k8s/ --namespace=mcp-registry
```

### Kustomize for Environment Management

```
k8s/
├── base/                # Base manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/             # Development overrides
│   │   ├── kustomization.yaml
│   │   └── patches.yaml
│   ├── staging/         # Staging overrides
│   │   ├── kustomization.yaml
│   │   └── patches.yaml
│   └── prod/            # Production overrides
│       ├── kustomization.yaml
│       └── patches.yaml
```

```bash
# Deploy to dev
kubectl apply -k k8s/overlays/dev/

# Deploy to production
kubectl apply -k k8s/overlays/prod/
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Kubernetes
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build and push Docker image
      run: |
        docker build -t ${{ secrets.REGISTRY }}/mcp-registry:${{ github.sha }} .
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push ${{ secrets.REGISTRY }}/mcp-registry:${{ github.sha }}

    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        kubeconfig: ${{ secrets.KUBE_CONFIG }}

    - name: Run database migrations
      run: |
        kubectl apply -f k8s/10-migration-job.yaml
        kubectl wait --for=condition=complete job/mcp-registry-migration -n mcp-registry --timeout=300s

    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/mcp-registry mcp-registry=${{ secrets.REGISTRY }}/mcp-registry:${{ github.sha }} -n mcp-registry
        kubectl rollout status deployment/mcp-registry -n mcp-registry
```

---

## Production Checklist

- [ ] Container image built and pushed to registry
- [ ] Secrets configured with secure values
- [ ] ConfigMap configured for production
- [ ] PostgreSQL persistent storage configured
- [ ] Database migrations completed successfully
- [ ] Application pods running and healthy
- [ ] Health checks passing
- [ ] Service and Ingress configured
- [ ] TLS certificates issued (if using HTTPS)
- [ ] DNS records pointing to LoadBalancer/Ingress
- [ ] HPA configured and tested
- [ ] Resource limits set appropriately
- [ ] Monitoring and logging configured
- [ ] Backup strategy implemented
- [ ] Network policies applied (if required)
- [ ] Security policies enforced
- [ ] Documentation updated with production URLs

---

## Support and Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Review logs for errors
- Check resource usage and scaling events
- Verify backup completion

**Monthly:**
- Update container images for security patches
- Review and optimize resource requests/limits
- Test disaster recovery procedures

**Quarterly:**
- Update Kubernetes cluster
- Review and update security policies
- Performance testing and optimization

---

**Last Updated:** 2026-01-31
**Deployment Type:** Kubernetes
**Minimum Cluster Version:** 1.25
