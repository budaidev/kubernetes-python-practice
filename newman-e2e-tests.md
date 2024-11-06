First, let's create the Postman collection for testing our API endpoints.

### postman/collection.json
```json
{
  "info": {
    "name": "Python Web App API Tests",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test('Status code is 200', function () {",
              "    pm.response.to.have.status(200);",
              "});",
              "pm.test('Response has correct structure', function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData).to.have.property('status');",
              "    pm.expect(jsonData.status).to.eql('healthy');",
              "});"
            ],
            "type": "text/javascript"
          }
        }
      ],
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/health",
          "host": ["{{baseUrl}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "List Books",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test('Status code is 200', function () {",
              "    pm.response.to.have.status(200);",
              "});",
              "pm.test('Response is an array', function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData).to.be.an('array');",
              "});"
            ],
            "type": "text/javascript"
          }
        }
      ],
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/api/books",
          "host": ["{{baseUrl}}"],
          "path": ["api", "books"]
        }
      }
    },
    {
      "name": "Create Book",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test('Status code is 201', function () {",
              "    pm.response.to.have.status(201);",
              "});",
              "pm.test('Book created successfully', function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData).to.have.property('id');",
              "    pm.expect(jsonData).to.have.property('title');",
              "    pm.expect(jsonData).to.have.property('author');",
              "    pm.globals.set('bookId', jsonData.id);",
              "});"
            ],
            "type": "text/javascript"
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n    \"title\": \"Test Book\",\n    \"author\": \"Test Author\"\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/api/books",
          "host": ["{{baseUrl}}"],
          "path": ["api", "books"]
        }
      }
    },
    {
      "name": "Get Book",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test('Status code is 200', function () {",
              "    pm.response.to.have.status(200);",
              "});",
              "pm.test('Book details are correct', function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData).to.have.property('id');",
              "    pm.expect(jsonData).to.have.property('title');",
              "    pm.expect(jsonData.title).to.eql('Test Book');",
              "});"
            ],
            "type": "text/javascript"
          }
        }
      ],
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/api/books/{{bookId}}",
          "host": ["{{baseUrl}}"],
          "path": ["api", "books", "{{bookId}}"]
        }
      }
    }
  ]
}
```

### postman/environment.json
```json
{
  "id": "test-env",
  "name": "Test Environment",
  "values": [
    {
      "key": "baseUrl",
      "value": "http://localhost:5000",
      "enabled": true
    }
  ]
}
```

Now, let's update the GitHub Actions workflow to include Newman tests:

```yaml
name: Deploy and Test

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy-and-test:
    runs-on: ubuntu-latest
    
    steps:
    # ... previous steps ...

    - name: Wait for deployment
      run: |
        kubectl wait --timeout=300s --for=condition=available deployment/python-webapp-python-webapp || true
        kubectl get pods -l app=python-webapp

    - name: Setup Port Forward
      run: |
        kubectl port-forward service/python-webapp-service 5000:80 &
        # Wait for port-forward to establish
        sleep 10
        curl http://localhost:5000/health || true

    - name: Install Newman
      run: |
        npm install -g newman

    - name: Run API Tests
      run: |
        newman run postman/collection.json \
          --environment postman/environment.json \
          --reporters cli,junit \
          --reporter-junit-export results/newman-results.xml

    - name: Upload Test Results
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: newman-test-results
        path: results/newman-results.xml

    # Optional: Publish Test Results
    - name: Publish Test Results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always()
      with:
        files: results/newman-results.xml
```

For local testing, create a helper script:

### scripts/run-tests.sh
```bash
#!/bin/bash

# Start port forwarding
kubectl port-forward service/python-webapp-service 5000:80 &
PF_PID=$!

# Wait for port-forward to establish
echo "Waiting for service to be available..."
sleep 10

# Run Newman tests
echo "Running API tests..."
newman run postman/collection.json \
  --environment postman/environment.json \
  --reporters cli,htmlextra \
  --reporter-htmlextra-export results/newman-report.html

# Capture test result
TEST_EXIT_CODE=$?

# Cleanup
kill $PF_PID

# Exit with test result
exit $TEST_EXIT_CODE
```

For Windows users, create a PowerShell version:

### scripts/run-tests.ps1
```powershell
# Start port forwarding
$portForward = Start-Process -FilePath "kubectl" -ArgumentList "port-forward service/python-webapp-service 5000:80" -PassThru

# Wait for port-forward to establish
Write-Host "Waiting for service to be available..."
Start-Sleep -Seconds 10

# Run Newman tests
Write-Host "Running API tests..."
newman run postman/collection.json `
  --environment postman/environment.json `
  --reporters cli,htmlextra `
  --reporter-htmlextra-export results/newman-report.html

# Capture test result
$testResult = $LASTEXITCODE

# Cleanup
Stop-Process -Id $portForward.Id -Force

# Exit with test result
exit $testResult
```

To run the tests locally:

```bash
# Linux/Mac
chmod +x scripts/run-tests.sh
./scripts/run-tests.sh

# Windows PowerShell
.\scripts\run-tests.ps1
```

### Debugging the Tests

Add this to the workflow for better debugging:

```yaml
    - name: Debug Service
      if: failure()
      run: |
        echo "Checking service status..."
        kubectl get services
        kubectl describe service python-webapp-service
        
        echo "Checking endpoints..."
        kubectl get endpoints
        
        echo "Checking pods..."
        kubectl get pods
        kubectl describe pods -l app=python-webapp
        
        echo "Checking logs..."
        kubectl logs -l app=python-webapp --tail=100
        
        echo "Testing connection..."
        curl -v http://localhost:5000/health || true
```

For more detailed Newman reporting, you can add HTML reports:

```yaml
    - name: Install Newman HTML Reporter
      run: npm install -g newman-reporter-htmlextra

    - name: Run API Tests with HTML Report
      run: |
        newman run postman/collection.json \
          --environment postman/environment.json \
          --reporters cli,htmlextra,junit \
          --reporter-htmlextra-export results/newman-report.html \
          --reporter-junit-export results/newman-results.xml

    - name: Upload HTML Report
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: newman-html-report
        path: results/newman-report.html
```

Would you like me to explain any part of the Newman tests or help with creating additional test cases?