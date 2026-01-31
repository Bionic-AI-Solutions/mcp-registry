# MCP Registry Deployment Guide

## Prerequisites

- Kubernetes 1.25+
- kubectl configured with cluster access
- Docker registry access
- (Optional) cert-manager for TLS
- (Optional) Prometheus/Grafana for monitoring

## Quick Start

### 1. Build and Push Image

```bash
# Build
docker build -t your-registry/mcp-registry:v1.0.0 .

# Push
docker push your-registry/mcp-registry:v1.0.0

# Update k8s/05-deployment.yaml to use your image
