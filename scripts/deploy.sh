kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml
kubectl apply -f k8s/03-postgres.yaml
kubectl apply -f k8s/04-redis.yaml

kubectl wait --for=condition=ready pod -l app=mcp-postgres -n mcp-registry --timeout=120s
kubectl wait --for=condition=ready pod -l app=mcp-redis -n mcp-registry --timeout=120s

# If running manually:
kubectl run migration --rm -i --restart=Never \
  --image=your-registry/mcp-registry:v1.0.0 \
  --env="DATABASE_URL=postgresql+asyncpg://..." \
  -- alembic upgrade head

kubectl apply -f k8s/05-deployment.yaml
kubectl apply -f k8s/06-service.yaml
kubectl apply -f k8s/07-ingress.yaml
kubectl apply -f k8s/08-hpa.yaml

# Check pods
kubectl get pods -n mcp-registry

# Check logs
kubectl logs -l app=mcp-registry -n mcp-registry --tail=100

# Test health endpoint
kubectl port-forward svc/mcp-registry 8080:80 -n mcp-registry
curl http://localhost:8080/health
