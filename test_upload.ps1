# Test script to upload image and check status
param(
    [string]$ImagePath = "test_assets/tasks_photo.jpg"
)

$apiUrl = "http://localhost:8000/api"

Write-Host "=== Testing Task OCR API ===" -ForegroundColor Cyan
Write-Host ""

# Check if file exists
if (-not (Test-Path $ImagePath)) {
    Write-Host "Error: Image file not found at $ImagePath" -ForegroundColor Red
    exit 1
}

$fileSize = (Get-Item $ImagePath).Length
Write-Host "Found image: $ImagePath ($([math]::Round($fileSize/1KB, 2)) KB)" -ForegroundColor Green
Write-Host ""

# Upload image
Write-Host "Step 1: Uploading image..." -ForegroundColor Yellow
try {
    $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $ImagePath))
    $fileEnc = [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBytes)
    $boundary = [System.Guid]::NewGuid().ToString()

    $LF = "`r`n"
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"image`"; filename=`"tasks_photo.jpg`"",
        "Content-Type: image/jpeg$LF",
        $fileEnc,
        "--$boundary--$LF"
    ) -join $LF

    $response = Invoke-RestMethod -Uri "$apiUrl/upload/" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyLines

    $transactionId = $response.transaction_id
    $status = $response.status

    Write-Host "✓ Upload successful!" -ForegroundColor Green
    Write-Host "  Transaction ID: $transactionId" -ForegroundColor Cyan
    Write-Host "  Status: $status" -ForegroundColor Cyan
    Write-Host ""

} catch {
    Write-Host "✗ Upload failed!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Poll for results
Write-Host "Step 2: Polling for results..." -ForegroundColor Yellow
$maxAttempts = 30
$pollInterval = 2
$attempt = 0

while ($attempt -lt $maxAttempts) {
    $attempt++

    try {
        $statusResponse = Invoke-RestMethod -Uri "$apiUrl/status/$transactionId/" -Method Get
        $currentStatus = $statusResponse.status

        Write-Host "  Attempt $attempt/$maxAttempts - Status: $currentStatus" -ForegroundColor Gray

        if ($currentStatus -eq "completed") {
            Write-Host ""
            Write-Host "✓ Processing completed!" -ForegroundColor Green
            Write-Host ""

            # Display results
            Write-Host "=== Results ===" -ForegroundColor Cyan
            Write-Host "Processing Duration: $($statusResponse.processing_duration) seconds" -ForegroundColor White
            Write-Host "OCR Confidence: $($statusResponse.ocr_confidence)" -ForegroundColor White
            Write-Host "Tasks Extracted: $($statusResponse.extracted_tasks.Count)" -ForegroundColor White
            Write-Host ""

            if ($statusResponse.extracted_tasks.Count -gt 0) {
                Write-Host "=== Extracted Tasks ===" -ForegroundColor Cyan
                $taskNum = 1
                foreach ($task in $statusResponse.extracted_tasks) {
                    Write-Host ""
                    Write-Host "Task #$taskNum" -ForegroundColor Yellow
                    Write-Host "  Name: $($task.task_name)" -ForegroundColor White
                    if ($task.description) {
                        Write-Host "  Description: $($task.description)" -ForegroundColor Gray
                    }
                    if ($task.assignee) {
                        Write-Host "  Assignee: $($task.assignee)" -ForegroundColor White
                    }
                    if ($task.due_date) {
                        Write-Host "  Due Date: $($task.due_date)" -ForegroundColor White
                    }
                    Write-Host "  Priority: $($task.priority)" -ForegroundColor White
                    Write-Host "  Confidence: $($task.confidence_score)" -ForegroundColor Gray
                    $taskNum++
                }
            }

            Write-Host ""
            Write-Host "=== Full JSON Response ===" -ForegroundColor Cyan
            $statusResponse | ConvertTo-Json -Depth 10

            exit 0

        } elseif ($currentStatus -eq "failed") {
            Write-Host ""
            Write-Host "✗ Processing failed!" -ForegroundColor Red
            Write-Host "  Error: $($statusResponse.error_message)" -ForegroundColor Red
            exit 1

        } elseif ($currentStatus -in @("pending", "processing")) {
            Start-Sleep -Seconds $pollInterval

        } else {
            Write-Host "  Unknown status: $currentStatus" -ForegroundColor Yellow
            Start-Sleep -Seconds $pollInterval
        }

    } catch {
        Write-Host "  Error checking status: $_" -ForegroundColor Red
        Start-Sleep -Seconds $pollInterval
    }
}

Write-Host ""
Write-Host "✗ Timeout waiting for results after $($maxAttempts * $pollInterval) seconds" -ForegroundColor Red
exit 1
