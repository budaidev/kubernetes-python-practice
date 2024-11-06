# Selenium Setup Guide for Windows

## 1. Local Windows Setup

### Prerequisites Check
```powershell
# Verify Python installation
python --version

# Verify pip installation
pip --version

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate
```

### Install Dependencies
```powershell
# Install test requirements
pip install selenium==4.18.1
pip install webdriver-manager==4.0.1
pip install pytest==8.0.0
pip install pytest-html==4.1.1
pip install pytest-xdist==3.5.0  # Optional: for parallel testing

# Or use requirements file
pip install -r requirements-test.txt
```

### Project Structure
```
project_root/
├── tests/
│   ├── e2e/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_web_interface.py
│   └── __init__.py
├── scripts/
│   └── run-selenium-tests.bat
└── requirements-test.txt
```

### Test Runner Script (scripts/run-selenium-tests.bat)
```batch
@echo off
echo Running Selenium Tests...

REM Activate virtual environment
call venv\Scripts\activate

REM Ensure reports directory exists
mkdir reports 2>nul

REM Start the application in background (adjust port if needed)
start /B python app/main.py
timeout /t 5

REM Run tests
pytest tests/e2e/test_web_interface.py -v --html=reports/report.html

REM Store the exit code
set RESULT=%ERRORLEVEL%

REM Kill the application
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000"') do taskkill /F /PID %%a

REM Deactivate virtual environment
deactivate

exit /b %RESULT%
```

### Configuration Files

#### tests/e2e/conftest.py
```python
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

@pytest.fixture(scope="session")
def base_url():
    """Fixture for base URL of the application"""
    return os.getenv('APP_URL', 'http://localhost:5000')

@pytest.fixture(scope="function")
def driver():
    """Fixture for browser driver"""
    chrome_options = Options()
    
    # Check if running in CI
    if os.getenv('CI'):
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
    
    chrome_options.add_argument('--window-size=1920,1080')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()

@pytest.fixture(scope="function")
def wait(driver):
    """Fixture for WebDriverWait"""
    from selenium.webdriver.support.ui import WebDriverWait
    return WebDriverWait(driver, 10)
```

## 2. Local Test Execution

### Basic Commands
```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run all tests
pytest tests/e2e/test_web_interface.py

# Run with HTML report
pytest tests/e2e/test_web_interface.py --html=reports/report.html

# Run specific test
pytest tests/e2e/test_web_interface.py::test_add_book
```

### Using the Batch Script
```powershell
# Run all tests using the script
.\scripts\run-selenium-tests.bat
```

## 3. GitHub Actions Configuration

Create a new workflow file for Selenium tests:

### .github/workflows/selenium-tests.yml
```yaml
name: Selenium Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install Chrome
      run: |
        choco install googlechrome -y
        choco install chromedriver -y

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt
        pip install -r app/requirements.txt

    # If using Kind/Minikube
    - name: Create k8s Kind Cluster
      uses: helm/kind-action@v1.8.0

    - name: Deploy application
      run: |
        # Build and load image
        docker build -t python-webapp:latest ./app
        kind load docker-image python-webapp:latest

        # Deploy with helm
        helm upgrade --install python-webapp ./helm/python-webapp `
          --set image.repository=python-webapp `
          --set image.tag=latest

    - name: Wait for deployment
      run: |
        kubectl wait --timeout=300s --for=condition=available deployment/python-webapp-python-webapp
        kubectl port-forward service/python-webapp-service 5000:80 &
        Start-Sleep -Seconds 10

    - name: Run Selenium tests
      run: |
        mkdir reports -Force
        pytest tests/e2e/test_web_interface.py -v --html=reports/report.html

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: reports/

    - name: Debug Info on Failure
      if: failure()
      run: |
        Write-Host "=== Kubernetes Resources ==="
        kubectl get all -n default
        
        Write-Host "=== Pod Logs ==="
        kubectl logs -l app=python-webapp --tail=100
        
        Write-Host "=== Chrome Version ==="
        (Get-Item (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe').'(Default)').VersionInfo.ProductVersion
        
        Write-Host "=== ChromeDriver Version ==="
        chromedriver --version
```

### Additional Configuration for Act (Local GitHub Actions Testing)

Create `.actrc`:
```plaintext
-P windows-latest=catthehacker/ubuntu:act-latest
--privileged
--bind
```

Run with act:
```powershell
# Run selenium tests job
act -j test
```

## 4. Troubleshooting Common Issues

### ChromeDriver Issues
```powershell
# Check Chrome version
(Get-Item (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe').'(Default)').VersionInfo.ProductVersion

# Check ChromeDriver version
chromedriver --version

# Force specific ChromeDriver version in code
from webdriver_manager.chrome import ChromeDriverManager
ChromeDriverManager(version="specific_version").install()
```

### Port Already in Use
```powershell
# Find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Browser Not Closing
```powershell
# Force close Chrome
taskkill /F /IM chrome.exe /T
```

Would you like me to:
1. Add more Windows-specific troubleshooting steps?
2. Explain any part in more detail?
3. Add additional GitHub Actions configurations?