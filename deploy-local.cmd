@echo off
echo Starting Minikube deployment...

:: Start Minikube if not running
minikube status || minikube start

:: Set Docker environment
@FOR /f "tokens=*" %%i IN ('minikube -p minikube docker-env --shell cmd') DO @%%i

:: Build image
echo Building Docker image...
docker build -t python-webapp:latest ./app

:: Verify image
echo Verifying image...
docker images | findstr python-webapp

:: Deploy with Terraform
echo Deploying with Terraform...
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan

:: Verify deployment
echo Verifying deployment...
kubectl get pods
kubectl get services python-webapp-service

:: Get service URL
echo Getting service URL...
minikube service python-webapp-service --url

echo Deployment complete!