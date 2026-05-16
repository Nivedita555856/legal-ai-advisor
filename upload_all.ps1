$api = "https://legal-ai-advisor-sspd.onrender.com/api"
$dataDir = "C:\Users\admin\ProITBridge\Legal-AI-advisor\data\raw"

Write-Host ""
Write-Host "=== Step 1: Waking backend ===" -ForegroundColor Cyan
$awake = $false
for ($i = 1; $i -le 12; $i++) {
    try {
        $h = Invoke-RestMethod -Uri "$api/health" -TimeoutSec 30
        Write-Host "Backend is UP" -ForegroundColor Green
        $awake = $true
        break
    } catch {
        Write-Host "  Attempt $i of 12 - waiting 10s..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
}
if (-not $awake) {
    Write-Host "Backend not responding. Check Render dashboard." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Step 2: Uploading documents ===" -ForegroundColor Cyan
$files = Get-ChildItem -Path $dataDir -Filter "*.md" | Sort-Object Name
Write-Host "Found $($files.Count) files"
Write-Host ""

$ok = 0
$fail = 0
$total = $files.Count

foreach ($f in $files) {
    $num = $ok + $fail + 1
    Write-Host "[$num/$total] $($f.Name) ..." -NoNewline

    try {
        $boundary = [System.Guid]::NewGuid().ToString()
        $fileBytes = [System.IO.File]::ReadAllBytes($f.FullName)
        $enc = [System.Text.Encoding]::UTF8

        $part1 = "--$boundary`r`nContent-Disposition: form-data; name=`"doc_name`"`r`n`r`n$($f.Name)`r`n"
        $part2 = "--$boundary`r`nContent-Disposition: form-data; name=`"file`"; filename=`"$($f.Name)`"`r`nContent-Type: text/plain`r`n`r`n"
        $part3 = "`r`n--$boundary--`r`n"

        $bodyBytes = $enc.GetBytes($part1) + $enc.GetBytes($part2) + $fileBytes + $enc.GetBytes($part3)

        $r = Invoke-RestMethod -Uri "$api/upload" -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyBytes -TimeoutSec 120

        $chunks = $r.chunks
        Write-Host " OK - $chunks chunks" -ForegroundColor Green
        $ok++
    } catch {
        $msg = $_.Exception.Message
        Write-Host " FAILED: $msg" -ForegroundColor Red
        $fail++
    }

    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "=== Step 3: Verifying ===" -ForegroundColor Cyan

try {
    $stats = Invoke-RestMethod -Uri "$api/documents/stats" -TimeoutSec 30
    $vectorCount = $stats.stats.total_vector_count
    Write-Host "Pinecone vectors: $vectorCount" -ForegroundColor Green
} catch {
    Write-Host "Could not fetch stats" -ForegroundColor Yellow
}

try {
    $docs = Invoke-RestMethod -Uri "$api/documents" -TimeoutSec 30
    $docCount = $docs.count
    Write-Host "Supabase docs:    $docCount" -ForegroundColor Green
} catch {
    Write-Host "Could not fetch docs" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Result: $ok uploaded, $fail failed ===" -ForegroundColor Cyan

if ($ok -gt 0) {
    Write-Host ""
    Write-Host "Testing a query..." -ForegroundColor Cyan
    try {
        $body = '{"query":"What is the notice period in an employment contract in India?","jurisdiction":"India"}'
        $r = Invoke-RestMethod -Uri "$api/query" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 120
        $ans = $r.answer
        if ($ans.Length -gt 300) { $ans = $ans.Substring(0, 300) + "..." }
        Write-Host "Answer: $ans" -ForegroundColor White
    } catch {
        Write-Host "Query test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}
