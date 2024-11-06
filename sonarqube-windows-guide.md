# Local SonarQube Integration with GitHub Actions for Python Flask Projects (Windows)

## Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Windows-Specific Installation](#windows-specific-installation)
- [Configuration Files](#configuration-files)
- [Running Locally on Windows](#running-locally-on-windows)
- [Troubleshooting Windows Issues](#troubleshooting-windows-issues)
- [Best Practices](#best-practices)

## Prerequisites

For Windows, you'll need:
- Docker Desktop for Windows
- Git for Windows
- Python 3.x
- Windows PowerShell or Command Prompt
- WSL2 (Windows Subsystem for Linux) - Required for Docker Desktop
- Act for Windows

## Windows-Specific Installation

### 1. Install WSL2
```powershell
# Open PowerShell as Administrator and run:
wsl --install
```
Restart your computer after installation.

### 2. Install Docker Desktop
1. Download Docker Desktop from [Docker Hub](https://hub.docker.com/editions/community/docker-ce-desktop-windows)
2. Enable WSL2 integration in Docker Desktop settings
3. Verify installation:
```powershell
docker --version
```

### 3. Install Act for Windows
```powershell
# Using Chocolatey (recommended)
choco install act-cli

# Alternative: Download from GitHub releases
# Visit https://github.com/nektos/act/releases
```

### 4. Set Up Python Environment
```powershell
# Install Python from Microsoft Store or python.org
python --version

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install flask pytest pytest-cov coverage
```

## Project Structure

Windows path structure:
```
YourFlaskProject\
├── .github\
│   └── workflows\
│       └── sonarqube.yml
├── your_flask_app\
│   ├── __init__.py
│   └── app.py
├── tests\
│   └── test_app.py
├── sonar-project.properties
├── requirements.txt
└── .secrets
```

## Configuration Files

### GitHub Actions Workflow (`.github\workflows\sonarqube.yml`)
```yaml
name: SonarQube Analysis

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  sonarqube:
    name: SonarQube Scan
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install coverage pytest pytest-cov

      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=xml:coverage.xml

      - name: SonarQube Scan
        uses: sonarsource/sonarqube-scan-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
        with:
          args: >
            -Dsonar.projectKey=flask-project
            -Dsonar.python.coverage.reportPaths=coverage.xml
            -Dsonar.sources=.
            -Dsonar.test.inclusions=**/test_*.py
            -Dsonar.python.version=3
```

### Windows PowerShell Script for Secrets (`set-secrets.ps1`)
```powershell
# Create this script to handle secrets more easily on Windows
$Env:SONAR_TOKEN="your_token_here"
$Env:SONAR_HOST_URL="http://localhost:9000"
```

## Running Locally on Windows

### 1. Start SonarQube Container
```powershell
# Run in PowerShell
docker run -d --name sonarqube `
    -p 9000:9000 `
    -p 9092:9092 `
    sonarqube:latest
```

### 2. Initial SonarQube Setup
1. Open http://localhost:9000 in your browser
2. Login with default credentials (admin/admin)
3. Create new project and generate token
4. Update `set-secrets.ps1` with your token

### 3. Run Tests and Generate Coverage
```powershell
# Activate virtual environment if not activated
.\venv\Scripts\activate

# Run tests with coverage
pytest --cov=. --cov-report=xml:coverage.xml
```

### 4. Run GitHub Actions Locally
```powershell
# Source secrets
. .\set-secrets.ps1

# Run act (PowerShell)
act -s SONAR_TOKEN="$Env:SONAR_TOKEN" `
    -s SONAR_HOST_URL="$Env:SONAR_HOST_URL" `
    -P ubuntu-latest=nektos/act-environments-ubuntu:18.04
```

## Troubleshooting Windows Issues

### Common Windows-Specific Problems

1. **WSL2 Issues**
   ```powershell
   # Check WSL version
   wsl --status
   
   # Update WSL if needed
   wsl --update
   ```

2. **Docker Desktop Problems**
   - Ensure Hyper-V is enabled
   - Check WSL2 integration in Docker Desktop settings
   - Verify memory allocation in WSL2

3. **Path Issues**
   ```powershell
   # Check if Python is in PATH
   $Env:Path -split ';'
   
   # Add Python to PATH if needed
   $Env:Path += ";C:\Python3x\Scripts\;C:\Python3x\"
   ```

4. **Permission Issues**
   - Run PowerShell as Administrator when needed
   - Check file permissions in project directory
   - Ensure Docker has necessary permissions

### File Path Fixes
```powershell
# Convert Windows paths to Unix-style for act
$Env:ACT_FORCE_UNIX_PATHS=1
```

## Best Practices for Windows

1. **Environment Setup**
   - Use virtual environments consistently
   - Keep paths short to avoid Windows path length limits
   - Use PowerShell Core for better Unicode support

2. **Docker Configuration**
   - Allocate sufficient resources in Docker Desktop
   - Use WSL2 backend for better performance
   - Regular cleanup of Docker resources
   ```powershell
   # Clean up unused Docker resources
   docker system prune -a
   ```

3. **Python Project Structure**
   - Use `.gitignore` appropriate for Windows
   - Configure line endings (git config core.autocrlf true)
   - Use `pathlib` for cross-platform path handling

## Additional Windows Resources

- [Docker Desktop WSL2 Backend](https://docs.docker.com/desktop/windows/wsl/)
- [Windows Python Setup Guide](https://docs.python.org/3/using/windows.html)
- [PowerShell Core Documentation](https://docs.microsoft.com/en-us/powershell/)
- [WSL2 Documentation](https://docs.microsoft.com/en-us/windows/wsl/)

## License

This guide is available under the MIT License. Feel free to modify and distribute as needed.
