# Helm and Terraform Deployment Guide for Python Web Application

## Table of Contents
1. Prerequisites and Setup
2. Helm Chart Configuration
3. Terraform Configuration
4. Deployment Process
5. Accessing the Application
6. Troubleshooting Guide
7. Maintenance and Updates

## 1. Prerequisites and Setup

### Initial Setup
```bash
# Start Minikube with sufficient resources
minikube start --cpus 2 --memory 4096 --disk-size 20g

# Enable Ingress addon
minikube addons enable ingress

# Configure Docker to use Minikube's daemon
# For Windows CMD:
@FOR /f "tokens=*" %i IN ('minikube -p minikube docker-env --shell cmd') DO @%i
# For PowerShell:
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Verify Minikube status
minikube status
```

### Build Application Image
```bash
# Navigate to application directory
cd ../app

# Build the image
docker build -t python-webapp:latest .

# Verify image
docker images | grep python-webapp
```

## 2. Helm Chart Configuration

### Chart Structure
```
helm/
└── python-webapp/
    ├── Chart.yaml           # Chart metadata
    ├── values.yaml          # Default configuration
    └── templates/
        ├── _helpers.tpl     # Template helpers
        ├── configmap.yaml   # Config data
        ├── secret.yaml      # Sensitive data
        ├── deployment.yaml  # Application deployment
        └── service.yaml     # Service definition
```

### Chart.yaml
```yaml
apiVersion: v2
name: python-webapp
description: A Helm chart for Python Web Application
version: 0.1.0
appVersion: "1.0.0"
```

### values.yaml
```yaml
image:
  repository: python-webapp
  tag: latest
  pullPolicy: IfNotPresent

replicaCount: 1

service:
  type: LoadBalancer
  port: 80
  targetPort: 5000

probes:
  liveness:
    path: /health
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
  readiness:
    path: /health
    initialDelaySeconds: 20
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

config:
  database_url: "sqlite:///./books.db"
  app_environment: "production"

secrets:
  api_key: "your-secret-key"
```

## 3. Terraform Configuration

### Directory Structure
```
terraform/
├── main.tf          # Main configuration
├── variables.tf     # Variable definitions
├── outputs.tf       # Output definitions
└── versions.tf      # Version constraints
```

### main.tf
```hcl
provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "minikube"
  }
}

resource "kubernetes_namespace" "app" {
  count = var.namespace != "default" ? 1 : 0
  
  metadata {
    name = var.namespace
  }
}

resource "helm_release" "python_webapp" {
  name       = var.app_name
  chart      = "../helm/python-webapp"
  namespace  = var.namespace
  
  force_update  = true
  replace       = true
  recreate_pods = true
  
  set {
    name  = "namespace"
    value = var.namespace
  }

  set {
    name  = "replicaCount"
    value = var.replica_count
  }

  set {
    name  = "image.repository"
    value = var.image_repository
  }

  set {
    name  = "image.tag"
    value = var.image_tag
  }

  depends_on = [kubernetes_namespace.app]
}
```

### variables.tf
```hcl
variable "minikube_context" {
  description = "Minikube context name"
  type        = string
  default     = "minikube"
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "python-webapp"
}

variable "replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 1
}

variable "image_repository" {
  description = "Docker image repository"
  type        = string
  default     = "python-webapp"
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}
```

### outputs.tf
```hcl
data "kubernetes_service" "app" {
  metadata {
    name      = "${var.app_name}-service"
    namespace = var.namespace
  }
  depends_on = [helm_release.python_webapp]
}

output "app_url" {
  description = "Application URL"
  value       = "http://localhost:${data.kubernetes_service.app.spec.0.port.0.port}"
}

output "minikube_url" {
  description = "Minikube service URL"
  value       = "Run: minikube service ${var.app_name}-service -n ${var.namespace}"
}
```

## 4. Deployment Process

### Initial Deployment
```bash
# Initialize Terraform
cd terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply deployment
terraform apply tfplan
```

### Updating Deployment
```bash
# Make changes to configuration
# Then plan and apply
terraform plan -out=tfplan
terraform apply tfplan
```

## 5. Accessing the Application

### Method 1: Minikube Service (Recommended)
```bash
# Get URL and open in browser
minikube service python-webapp-service

# Get URL only
minikube service python-webapp-service --url
```

### Method 2: Port Forwarding
```bash
# Forward local port
kubectl port-forward deployment/python-webapp-python-webapp 5000:5000
```

## 6. Troubleshooting Guide

### Common Issues and Solutions

#### 1. Helm Release Already Exists
```bash
Error: cannot re-use a name that is still in use

# Solution:
# List existing releases
helm list -n default

# Delete existing release
helm uninstall python-webapp -n default

# Or update Terraform configuration with force_update (already included in our config)
```

#### 2. Pod Health Check Failures
```bash
# Check pod status
kubectl get pods
kubectl describe pod <pod-name>

# Check logs
kubectl logs deployment/python-webapp-python-webapp

# Common causes and solutions:
# 1. Missing /health endpoint - Add endpoint to Flask app
# 2. Database connection issues - Check connection string
# 3. Timing issues - Adjust probe timing in values.yaml
```

#### 3. Image Pull Issues
```bash
# Verify Minikube Docker environment
eval $(minikube docker-env)

# Check image exists
docker images | grep python-webapp

# Rebuild if needed
docker build -t python-webapp:latest .

# Force pod recreation
kubectl delete pod <pod-name>
```

#### 4. Terraform Provider Configuration
```bash
Error: Provider configuration: cannot load Kubernetes client config

# Solutions:
# 1. Check Minikube status
minikube status

# 2. Verify context
kubectl config get-contexts
kubectl config use-context minikube

# 3. Update provider configuration if needed
```

#### 5. Service Access Issues
```bash
# Check service status
kubectl get svc python-webapp-service

# Verify endpoints
kubectl get endpoints python-webapp-service

# Check pod readiness
kubectl describe pod <pod-name> | grep -A 5 Conditions
```

## 7. Maintenance and Updates

### Update Application
```bash
# 1. Update application code
# 2. Rebuild Docker image
eval $(minikube docker-env)
docker build -t python-webapp:latest .

# 3. Update deployment
terraform apply -auto-approve
```

### Monitor Deployment
```bash
# Watch pod status
kubectl get pods -w

# Check rollout status
kubectl rollout status deployment/python-webapp-python-webapp

# View logs
kubectl logs -f deployment/python-webapp-python-webapp
```

### Cleanup
```bash
# Delete Helm release
helm uninstall python-webapp -n default

# Delete with Terraform
terraform destroy

# Clean Terraform files
rm -f terraform.tfstate*
rm -f .terraform.lock.hcl
rm -rf .terraform/

# Stop Minikube (optional)
minikube stop
```

### Environment-Specific Deployments

#### dev.tfvars
```hcl
namespace     = "dev"
replica_count = 1
image_tag     = "dev"
```

#### prod.tfvars
```hcl
namespace     = "prod"
replica_count = 3
image_tag     = "prod"
```

Apply environment-specific configuration:
```bash
# Development
terraform plan -var-file="dev.tfvars" -out=tfplan
terraform apply tfplan

# Production
terraform plan -var-file="prod.tfvars" -out=tfplan
terraform apply tfplan
```