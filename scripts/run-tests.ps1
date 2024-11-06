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