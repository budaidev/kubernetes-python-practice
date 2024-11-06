# Prometheus Integration Guide

## Table of Contents
1. Setting Up Prometheus Locally
2. Adding Prometheus Metrics to Python Application
3. Helm Configuration for Prometheus
4. Monitoring Configuration
5. Accessing Prometheus UI
6. Common Metrics and Alerts

## 1. Setting Up Prometheus Locally

### Install Prometheus using Helm
```bash
cd prometheus-setup
docker compose up -d
```

### Verify Installation
```bash

# Default Grafana credentials
# localhost:3000
# Username: admin
# Password: admin
```

## 2. Adding Prometheus Metrics to Python Application

### Update Requirements
```txt
Flask==3.0.3
Flask-RESTful==0.3.10
Flask-SQLAlchemy==3.1.1
prometheus-client==0.20.0
```

### Updated Python Application
```python
from flask import Flask, render_template, request, redirect, url_for, jsonify
from prometheus_client import generate_latest, Counter, Histogram, Info
from prometheus_client import Counter, Histogram, Info
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
import time
import os

# Initialize app
app = Flask(__name__)
api = Api(app)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

DB_REQUEST_LATENCY = Histogram(
    'database_request_duration_seconds',
    'Database request latency in seconds',
    ['operation']
)

APP_INFO = Info('python_webapp_info', 'Application information')
APP_INFO.info({'version': '1.0.0', 'environment': os.getenv('APP_ENVIRONMENT', 'development')})

# Request latency middleware
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    latency = time.time() - request.start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.path
    ).observe(latency)
    return response

# Prometheus metrics endpoint
@app.route('/metrics')
def metrics():
    return generate_latest()

# Your existing application code...

# Add metrics to database operations
def add_book_with_metrics(book):
    start_time = time.time()
    try:
        db.session.add(book)
        db.session.commit()
        DB_REQUEST_LATENCY.labels(operation='add_book').observe(time.time() - start_time)
    except Exception as e:
        DB_REQUEST_LATENCY.labels(operation='add_book_error').observe(time.time() - start_time)
        raise e

# Update existing routes to use metrics
@app.route('/add', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    new_book = Book(title=title, author=author)
    add_book_with_metrics(new_book)
    return redirect(url_for('index'))
```

## 3. Helm Configuration for Prometheus

### Add ServiceMonitor to Helm Templates

#### helm/python-webapp/templates/servicemonitor.yaml
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ .Release.Name }}-servicemonitor
  labels:
    {{- include "python-webapp.labels" . | nindent 4 }}
    release: prometheus  # Must match Prometheus operator's serviceMonitorSelector
spec:
  selector:
    matchLabels:
      {{- include "python-webapp.labels" . | nindent 6 }}
  endpoints:
  - port: http  # Must match service port name
    path: /metrics
    interval: 15s
```

### Update Service Template

#### helm/python-webapp/templates/service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-service
  labels:
    {{- include "python-webapp.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
      name: http  # Added name for ServiceMonitor
  selector:
    app: {{ .Chart.Name }}
```

## 4. Monitoring Configuration

### Basic Prometheus Rules

#### helm/python-webapp/templates/prometheusrule.yaml
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: {{ .Release.Name }}-rules
  labels:
    {{- include "python-webapp.labels" . | nindent 4 }}
    release: prometheus
spec:
  groups:
  - name: python-webapp.rules
    rules:
    - alert: HighRequestLatency
      expr: rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]) > 0.5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: High request latency on {{ "{{" }} $labels.endpoint {{ "}}" }}
        description: Request latency is above 500ms (current value: {{ "{{" }} $value {{ "}}" }}s)
    
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: High error rate on {{ "{{" }} $labels.endpoint {{ "}}" }}
        description: Error rate is above 10% (current value: {{ "{{" }} $value {{ "}}" }})
```

## 5. Accessing and Using Prometheus

### Access Prometheus UI
```bash
# Get Prometheus URL
minikube service prometheus-operated -n monitoring --url

# Get Grafana URL
minikube service prometheus-grafana -n monitoring --url
```

### Basic PromQL Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Average latency
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# Database operation latency
rate(database_request_duration_seconds_sum[5m])
```

## 6. Creating Grafana Dashboards

### Basic Dashboard JSON
```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "auto",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "editorMode": "code",
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{method}} {{endpoint}}",
          "range": true,
          "refId": "A"
        }
      ],
      "title": "Request Rate",
      "type": "timeseries"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-15m",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "Python Web App Dashboard",
  "version": 0,
  "weekStart": ""
}
```

## 7. Troubleshooting

### Common Issues

#### 1. Metrics Not Showing Up
```bash
# Check ServiceMonitor
kubectl get servicemonitor -n default

# Verify endpoints
kubectl get endpoints -n default

# Check Prometheus targets
# Access Prometheus UI -> Status -> Targets
```

#### 2. Prometheus Operator Issues
```bash
# Check operator status
kubectl get pods -n monitoring | grep prometheus-operator

# Check operator logs
kubectl logs -n monitoring <prometheus-operator-pod> -f
```

#### 3. Service Discovery Problems
```bash
# Verify service labels
kubectl get service python-webapp-service -o yaml

# Check ServiceMonitor configuration
kubectl get servicemonitor python-webapp-servicemonitor -o yaml
```

### Verification Commands
```bash
# Test metrics endpoint
kubectl port-forward service/python-webapp-service 5000:80
curl localhost:5000/metrics

# Check Prometheus configuration
kubectl get secret -n monitoring prometheus-prometheus-kube-prometheus-prometheus -o yaml

# Verify Prometheus rules
kubectl get prometheusrules -n monitoring
```
