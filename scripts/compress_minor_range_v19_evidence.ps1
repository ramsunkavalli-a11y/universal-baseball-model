$ErrorActionPreference = 'Stop'
$taskArchiveRoot = (Resolve-Path -LiteralPath 'reports/generated/defense-minor-range-v19').Path
$taskMirrorRoot = (Resolve-Path -LiteralPath 'reports/model-evidence/defense-minor-range-v19').Path
$taskIndexPath = Join-Path $taskArchiveRoot 'archive-index.json'
if (Test-Path -LiteralPath $taskIndexPath) { throw 'Preserve prior archive receipt' }
$taskFiles = @(Get-ChildItem -LiteralPath $taskArchiveRoot -Recurse -File -Filter '*.json')
$taskArchiveRows = @()
foreach ($taskFile in $taskFiles) {
    if (-not $taskFile.FullName.StartsWith($taskArchiveRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected archive path' }
    if (($taskFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point not permitted' }
    if ($taskFile.Length -eq 0) {
        $taskArchiveRows += [PSCustomObject]@{original=$taskFile.FullName; bytes=0; status='incomplete_zero_byte_save_preserved'}
        continue
    }
    $taskBytes = [IO.File]::ReadAllBytes($taskFile.FullName)
    $null = [Text.Encoding]::UTF8.GetString($taskBytes) | ConvertFrom-Json -Depth 100
    $taskOriginalHash = (Get-FileHash -LiteralPath $taskFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $taskBuffer = [IO.MemoryStream]::new()
    $taskGzip = [IO.Compression.GZipStream]::new($taskBuffer,[IO.Compression.CompressionLevel]::Optimal,$true)
    $taskGzip.Write($taskBytes,0,$taskBytes.Length)
    $taskGzip.Dispose()
    $taskPacked = $taskBuffer.ToArray()
    $taskBuffer.Dispose()
    $taskPackedPath = $taskFile.FullName + '.gz'
    if (Test-Path -LiteralPath $taskPackedPath) { throw 'Preserve prior compressed evidence' }
    [IO.File]::WriteAllBytes($taskPackedPath,$taskPacked)
    $taskInputBuffer = [IO.MemoryStream]::new($taskPacked,$false)
    $taskDecoder = [IO.Compression.GZipStream]::new($taskInputBuffer,[IO.Compression.CompressionMode]::Decompress)
    $taskDecoded = [IO.MemoryStream]::new()
    $taskDecoder.CopyTo($taskDecoded)
    $taskSha = [Security.Cryptography.SHA256]::Create()
    $taskRoundtripHash = ([BitConverter]::ToString($taskSha.ComputeHash($taskDecoded.ToArray()))).Replace('-','').ToLowerInvariant()
    $taskSha.Dispose(); $taskDecoder.Dispose(); $taskInputBuffer.Dispose(); $taskDecoded.Dispose()
    if ($taskRoundtripHash -ne $taskOriginalHash) { throw 'Lossless roundtrip failed' }
    $taskRelative = $taskFile.FullName.Substring($taskArchiveRoot.Length + 1)
    $taskMirrorPath = Join-Path $taskMirrorRoot ($taskRelative + '.gz')
    if (Test-Path -LiteralPath $taskMirrorPath) { throw 'Preserve prior mirror' }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($taskMirrorPath)) | Out-Null
    [IO.File]::WriteAllBytes($taskMirrorPath,$taskPacked)
    if ((Get-FileHash -LiteralPath $taskMirrorPath -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $taskPackedPath -Algorithm SHA256).Hash) { throw 'Mirror verification failed' }
    $taskArchiveRows += [PSCustomObject]@{original=$taskFile.FullName; bytes=$taskBytes.Length; original_sha256=$taskOriginalHash; compressed=$taskPackedPath; compressed_bytes=$taskPacked.Length; status='losslessly_archived'}
    Remove-Item -LiteralPath $taskFile.FullName
}
$taskReceipt = [PSCustomObject]@{reason='Disk filled while saving inner-2018-3-4-fit.json'; redundant_public_copies_removed=70; originals_losslessly_preserved=$true; rows=$taskArchiveRows}
$taskReceipt | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $taskIndexPath -Encoding utf8
Copy-Item -LiteralPath $taskIndexPath -Destination (Join-Path $taskMirrorRoot 'archive-index.json')
Get-PSDrive C | Select-Object Used,Free | Format-List
