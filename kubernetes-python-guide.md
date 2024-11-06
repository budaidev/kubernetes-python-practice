# Practical Guide: Deploying Python Web App on Kubernetes

## Table of Contents
1. Project Structure
2. Python Web Application
3. Docker Configuration
4. Kubernetes Manifests
5. Deployment Process
6. Testing and Verification

## 0. Installing Minikube


```
New-Item -Path 'c:\' -Name 'minikube' -ItemType Directory -Force
Invoke-WebRequest -OutFile 'c:\minikube\minikube.exe' -Uri 'https://github.com/kubernetes/minikube/releases/latest/download/minikube-windows-amd64.exe' -UseBasicParsing
```

Add to path
```
$oldPath = [Environment]::GetEnvironmentVariable('Path', [EnvironmentVariableTarget]::Machine)
if ($oldPath.Split(';') -inotcontains 'C:\minikube'){
  [Environment]::SetEnvironmentVariable('Path', $('{0};C:\minikube' -f $oldPath), [EnvironmentVariableTarget]::Machine)
}
```

## 1. Project Structure

```
python-k8s-app/
├── app/
│   ├── static/
│   │   └── style.css
│   ├── templates/
│   │   └── index.html
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
├── k8s/
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── kubernetes-python-guide.md
```

## 2. Python Web Application

### requirements.txt
```txt
Flask==3.0.3
Flask-RESTful==0.3.10
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.36
Werkzeug==3.1.2
pytest==8.3.3

```

### main.py
```python
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize app
app = Flask(__name__)
api = Api(app)

# Configure the SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'books.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Book {self.title}>"

# Create an application context
with app.app_context():
    # Create the database and tables
    db.create_all()

# RESTful API
book_parser = reqparse.RequestParser()
book_parser.add_argument('title', type=str, required=True, help='Title cannot be blank!')
book_parser.add_argument('author', type=str, required=True, help='Author cannot be blank!')

class BookResource(Resource):
    def get(self, book_id):
        book = Book.query.get(book_id)
        if not book:
            return {'message': 'Book not found'}, 404
        return {'id': book.id, 'title': book.title, 'author': book.author}

    def delete(self, book_id):
        book = Book.query.get(book_id)
        if not book:
            return {'message': 'Book not found'}, 404
        db.session.delete(book)
        db.session.commit()
        return {'message': 'Book deleted'}

class BookListResource(Resource):
    def get(self):
        books = Book.query.all()
        return [{'id': book.id, 'title': book.title, 'author': book.author} for book in books]

    def post(self):
        args = book_parser.parse_args()
        new_book = Book(title=args['title'], author=args['author'])
        db.session.add(new_book)
        db.session.commit()
        return {'id': new_book.id, 'title': new_book.title, 'author': new_book.author}, 201

# Add API routes
api.add_resource(BookListResource, '/api/books')
api.add_resource(BookResource, '/api/books/<int:book_id>')

# Web frontend
@app.route('/')
def index():
    with app.app_context():
        books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/add', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    new_book = Book(title=title, author=author)
    db.session.add(new_book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:book_id>', methods=['GET'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if book:
        db.session.delete(book)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    try:
        # Try to query the database to verify connection
        Book.query.first()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "database": str(e)}), 500
    
# Run the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

```


### templates/index.html
```html
{% extends "base.html" %}

{% block content %}
<h1>Welcome to Kubernetes Demo App</h1>
<div class="form-container">
    <h2>Add New Item</h2>
    <form id="itemForm">
        <input type="text" id="name" placeholder="Item Name" required>
        <input type="text" id="description" placeholder="Description" required>
        <button type="submit">Add Item</button>
    </form>
</div>

<script>
document.getElementById('itemForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('name', document.getElementById('name').value);
    formData.append('description', document.getElementById('description').value);
    
    await fetch('/items', {
        method: 'POST',
        body: formData
    });
    
    window.location.href = '/items';
});
</script>
{% endblock %}
```


## 3. Docker Configuration

### Dockerfile
```dockerfile
# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt requirements.txt

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create directory for SQLite database and set permissions
RUN mkdir -p /app/instance && \
    chmod 777 /app/instance

# Set environment variable for Python to run unbuffered
ENV PYTHONUNBUFFERED=1

# Expose the port that the app runs on
EXPOSE 5000

# Command to run the application directly with Python
CMD ["python", "main.py"]
```

## 4. Kubernetes Manifests

**configmap.yaml**: Stores configuration data in key-value pairs that can be consumed by pods as environment variables or configuration files.
**secret.yaml**: Stores sensitive data such as passwords, OAuth tokens, and SSH keys, which can be used by pods securely.
**deployment.yaml**: Manages the deployment of application pods, ensuring the desired number of replicas are running and handling updates.
**service.yaml**: Exposes the application running on a set of pods as a network service, enabling communication within the cluster or from external sources.
**ingress.yaml**: Manages external access to the services in a cluster, typically HTTP and HTTPS, by providing load balancing, SSL termination, and name-based virtual hosting.

### k8s/configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: webapp-config
data:
  DATABASE_URL: "sqlite:///./books.db"
  APP_ENVIRONMENT: "production"
```

### k8s/secret.yaml
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: webapp-secret
type: Opaque
stringData:
  API_KEY: "your-secret-key"
```

### k8s/deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-webapp
  labels:
    app: python-webapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: python-webapp
  template:
    metadata:
      labels:
        app: python-webapp
    spec:
      containers:
      - name: python-webapp
        image: python-webapp:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: webapp-config
        - secretRef:
            name: webapp-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### k8s/service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: python-webapp-service
spec:
  selector:
    app: python-webapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer

```

### k8s/ingress.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: python-webapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: python-webapp-service
            port:
              number: 80
```

## 5. Deployment Process

### Build and Deploy Commands
```bash
#First, point your Docker CLI to Minikube's Docker daemon. In Windows Command Prompt:
@FOR /f "tokens=*" %i IN ('minikube -p minikube docker-env --shell cmd') DO @%i

eval $(minikube docker-env)

# Build Docker image
docker build -t python-webapp:latest ./app

# Apply Kubernetes configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get pods
kubectl get services
kubectl get ingress
```

## 6. Testing and Verification

### Check deployment status
```bash
# Check pods status
kubectl get pods

# Check logs
kubectl logs -l app=python-webapp

# Port forward for local testing
kubectl port-forward svc/python-webapp-service 8000:80
```

### Access the application
- Open browser and navigate to `http://localhost:8000`
- Test the health endpoint: `http://localhost:8000/health`
- Create and view items through the web interface

### Troubleshooting Commands
```bash
# Get detailed pod information
kubectl describe pod <pod-name>

# Get pod logs
kubectl logs <pod-name>

# Execute commands in pod
kubectl exec -it <pod-name> -- /bin/bash

# Check service details
kubectl describe service python-webapp-service

# Check ingress status
kubectl describe ingress python-webapp-ingress
```

This guide provides a complete setup for deploying a Python web application on Kubernetes. The application includes basic CRUD operations, a clean UI, and proper Kubernetes configurations. The setup can be extended later with Helm charts, Terraform configurations, and Minikube-specific optimizations.

The application uses SQLite for simplicity, but in a production environment, you would want to use a proper database service like PostgreSQL with persistent volumes.
