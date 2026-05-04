# Azure Deployment Guide

This document describes how to deploy the Healthcare RAG Pipeline to Azure. Two options are covered: Azure Container Apps (recommended) and Azure Kubernetes Service (AKS).

## Prerequisites

- Azure CLI installed (`az`)
- Docker images pushed to GitHub Container Registry (GHCR) via CI pipeline
- Azure subscription with a resource group created

```bash
az login
az group create --name healthcare-rag-rg --location eastus
```

---

## Option A: Azure Container Apps (Recommended)

Azure Container Apps is serverless — you only pay when your app is processing requests. Simpler to manage than Kubernetes.

### 1. Create the Container Apps Environment

```bash
az containerapp env create \
  --name healthcare-rag-env \
  --resource-group healthcare-rag-rg \
  --location eastus
```

### 2. Deploy the Backend

```bash
az containerapp create \
  --name backend \
  --resource-group healthcare-rag-rg \
  --environment healthcare-rag-env \
  --image ghcr.io/ivan5355/health_care_rag_pipeline/backend:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    PINECONE_API_KEY=secretref:pinecone-key \
    BEDROCK_API_KEY=secretref:bedrock-key \
    AWS_DEFAULT_REGION=us-east-1 \
    JWT_SECRET=secretref:jwt-secret
```

### 3. Configure Secrets

```bash
az containerapp secret set \
  --name backend \
  --resource-group healthcare-rag-rg \
  --secrets \
    pinecone-key=<your-pinecone-api-key> \
    bedrock-key=<your-bedrock-api-key> \
    jwt-secret=<your-production-jwt-secret>
```

### 4. Deploy the Frontend

```bash
BACKEND_URL=$(az containerapp show --name backend --resource-group healthcare-rag-rg --query "properties.configuration.ingress.fqdn" -o tsv)

az containerapp create \
  --name frontend \
  --resource-group healthcare-rag-rg \
  --environment healthcare-rag-env \
  --image ghcr.io/ivan5355/health_care_rag_pipeline/frontend:latest \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.25 \
  --memory 0.5Gi
```

### 5. Configure Custom Domain (Optional)

```bash
az containerapp hostname add \
  --name frontend \
  --resource-group healthcare-rag-rg \
  --hostname your-domain.com
```

---

## Option B: Azure Kubernetes Service (AKS)

Use AKS if you need more control over networking, scaling policies, or multi-service orchestration.

### 1. Create AKS Cluster

```bash
az aks create \
  --resource-group healthcare-rag-rg \
  --name healthcare-rag-aks \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --generate-ssh-keys
```

### 2. Connect to Cluster

```bash
az aks get-credentials --resource-group healthcare-rag-rg --name healthcare-rag-aks
```

### 3. Create Kubernetes Secrets

```bash
kubectl create secret generic healthcare-rag-secrets \
  --from-literal=PINECONE_API_KEY=<your-key> \
  --from-literal=BEDROCK_API_KEY=<your-key> \
  --from-literal=JWT_SECRET=<your-secret>
```

### 4. Apply Deployment Manifests

Create `k8s/backend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: ghcr.io/ivan5355/health_care_rag_pipeline/backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: healthcare-rag-secrets
          resources:
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /api/health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: backend
  ports:
    - port: 8000
      targetPort: 8000
```

Create `k8s/frontend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: ghcr.io/ivan5355/health_care_rag_pipeline/frontend:latest
          ports:
            - containerPort: 80
          resources:
            limits:
              memory: "128Mi"
              cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 80
```

```bash
kubectl apply -f k8s/
```

---

## CI/CD Integration

The GitHub Actions CI pipeline (`.github/workflows/ci.yml`) automatically:
1. Builds Docker images on every push to `main`
2. Pushes them to GHCR with `latest` and commit SHA tags
3. To trigger a deployment, configure a webhook or add a deploy step that runs `az containerapp update` with the new image tag

---

## UHG/Optum Cloud Context

United Health Group (UHG) primarily uses Azure for cloud infrastructure. This deployment guide aligns with their technology stack:
- **Azure Container Apps** maps to their microservices platform
- **GHCR** can be replaced with Azure Container Registry (ACR) for enterprise use
- **Key Vault** should replace inline secrets for production compliance
- Network isolation via VNets would be required for PHI/HIPAA compliance
