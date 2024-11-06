### 1. First, let's check existing resources:
```bash
# Check existing services
kubectl get services -n default

# Check existing deployments
kubectl get deployments -n default

# Check existing pods
kubectl get pods -n default

# Check existing configmaps
kubectl get configmaps -n default

# Check existing secrets
kubectl get secrets -n default
```

### 2. Delete existing resources:
```bash
# Delete service
kubectl delete service python-webapp-service -n default

# Delete deployment
kubectl delete deployment python-webapp -n default

# Delete configmap if exists
kubectl delete configmap webapp-config -n default

# Delete secret if exists
kubectl delete secret webapp-secret -n default

# Or delete everything at once (be careful with this in production!)
kubectl delete all -l app=python-webapp -n default
```

### 3. Verify cleanup:
```bash
# Check if resources are gone
kubectl get all -l app=python-webapp -n default
```

### 4. Then retry Terraform:
```bash
# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

If you want to completely start fresh, you can also:

```bash
# Delete everything in terraform state
terraform destroy

# Remove the terraform state files
rm -f terraform.tfstate*

# Reinitialize terraform
terraform init

# Create new plan
terraform plan -out=tfplan

# Apply new configuration
terraform apply tfplan
```

The error occurred because:
1. There were existing Kubernetes resources that weren't managed by Helm
2. Helm requires specific labels and annotations on resources it manages
3. The existing resources didn't have these required Helm management labels

This cleanup process will allow Helm to create and manage the resources properly.
