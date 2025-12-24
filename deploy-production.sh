#!/bin/bash
# deploy-production.sh

set -e  # Exit on error

echo "🚀 Deploying Self-Arguing Multi-Agent Analyst to Production..."

# Configuration
ENVIRONMENT=${1:-staging}
DOCKER_REGISTRY="your-registry"
IMAGE_TAG="latest"
NAMESPACE="self-arguing-analyst"

# Load environment-specific configuration
if [ "$ENVIRONMENT" == "production" ]; then
    export KUBECONFIG="$HOME/.kube/production-config"
    REPLICAS=3
    RESOURCES="--limits memory=1Gi,cpu=500m --requests memory=512Mi,cpu=250m"
else
    export KUBECONFIG="$HOME/.kube/staging-config"
    REPLICAS=2
    RESOURCES="--limits memory=512Mi,cpu=250m --requests memory=256Mi,cpu=100m"
fi

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $DOCKER_REGISTRY/self-arguing-analyst:$IMAGE_TAG .
docker push $DOCKER_REGISTRY/self-arguing-analyst:$IMAGE_TAG

# Update Kubernetes manifests
echo "📝 Updating Kubernetes manifests..."
sed -i.bak "s|image: .*|image: $DOCKER_REGISTRY/self-arguing-analyst:$IMAGE_TAG|" k8s/api-deployment.yaml
sed -i.bak "s|replicas: .*|replicas: $REPLICAS|" k8s/api-deployment.yaml

# Apply Kubernetes configuration
echo "🔧 Applying Kubernetes configuration..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/hpa.yaml

# Wait for rollout
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/api -n $NAMESPACE --timeout=300s
kubectl rollout status deployment/worker -n $NAMESPACE --timeout=300s

# Get service URL
SERVICE_URL=$(kubectl get svc api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL=$(kubectl get svc api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

echo "✅ Deployment complete!"
echo "🌐 API URL: http://$SERVICE_URL"
echo "📊 Metrics: http://$SERVICE_URL/metrics"
echo "📈 Grafana: http://$SERVICE_URL:3000"
echo "🔍 Prometheus: http://$SERVICE_URL:9090"

# Run smoke test
echo "🧪 Running smoke test..."
curl -f http://$SERVICE_URL/metrics || echo "Warning: Smoke test failed"