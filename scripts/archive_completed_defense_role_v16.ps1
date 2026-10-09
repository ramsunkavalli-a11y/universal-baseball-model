$ErrorActionPreference = 'Stop'
$taskSource = 'C:\Users\ramav\Documents\Codex\2026-09-13\wa\work\ubm-audit-v3\reports\generated\defense-role-v16'
$taskDestination = 'D:\UBMResearch\ubm-audit-v3\generated\defense-role-v16'
$taskReceipt = 'C:\Users\ramav\Documents\Codex\2026-09-13\wa\work\ubm-audit-v3\reports\model-evidence\hitter-2027-v1\storage-move-defense-role-v16.json'
if ((Resolve-Path -LiteralPath $taskSource).Path -cne $taskSource) { throw 'Unexpected source resolution' }
if ((Get-Item -LiteralPath $taskSource).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Already redirected' }
if (Test-Path -LiteralPath $taskDestination) { throw 'Archive target exists; do not overwrite' }
if (Test-Path -LiteralPath $taskReceipt) { throw 'Receipt exists; do not rerun' }
if ((Resolve-Path -LiteralPath 'D:\UBMResearch\ubm-audit-v3\generated').Path -cne 'D:\UBMResearch\ubm-audit-v3\generated') { throw 'Unexpected archive parent' }
$taskFiles = @(Get-ChildItem -LiteralPath $taskSource -Recurse -File)
if (@(Get-ChildItem -LiteralPath $taskSource -Recurse -Directory | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { throw 'Nested redirect' }
$taskManifest = @($taskFiles | ForEach-Object {
    [pscustomobject]@{ Relative = $_.FullName.Substring($taskSource.Length + 1); Bytes = $_.Length; SHA256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
})
$taskBytes = ($taskManifest | Measure-Object Bytes -Sum).Sum
if ((Get-PSDrive -Name D).Free -lt $taskBytes + 1GB) { throw 'Insufficient archive space' }
Copy-Item -LiteralPath $taskSource -Destination $taskDestination -Recurse
foreach ($taskFile in $taskManifest) {
    $taskCopy = Join-Path $taskDestination $taskFile.Relative
    if ((Get-Item -LiteralPath $taskCopy).Length -ne $taskFile.Bytes -or (Get-FileHash -LiteralPath $taskCopy -Algorithm SHA256).Hash -cne $taskFile.SHA256) { throw "Archive verification failed: $($taskFile.Relative)" }
}
if (@(Get-ChildItem -LiteralPath $taskDestination -Recurse -File).Count -ne $taskManifest.Count) { throw 'Archive file count mismatch' }
# Recheck the exact source and its contents immediately before removing the
# redundant C: copy. The verified D: copy is preserved and recoverable.
if ((Resolve-Path -LiteralPath $taskSource).Path -cne $taskSource -or (Get-Item -LiteralPath $taskSource).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Source changed' }
foreach ($taskFile in $taskManifest) {
    if ((Get-FileHash -LiteralPath (Join-Path $taskSource $taskFile.Relative) -Algorithm SHA256).Hash -cne $taskFile.SHA256) { throw 'Source changed during copy' }
}
if (@(Get-ChildItem -LiteralPath $taskSource -Recurse -File).Count -ne $taskManifest.Count) { throw 'Source file count changed' }
Remove-Item -LiteralPath $taskSource -Recurse -Force
New-Item -ItemType Junction -Path $taskSource -Target $taskDestination | Out-Null
foreach ($taskFile in $taskManifest) {
    if ((Get-FileHash -LiteralPath (Join-Path $taskSource $taskFile.Relative) -Algorithm SHA256).Hash -cne $taskFile.SHA256) { throw 'Redirected file verification failed' }
}
$taskReport = [ordered]@{ Source=$taskSource; Archive=$taskDestination; Bytes=$taskBytes; Files=$taskManifest.Count; AllHashesVerified=$true; OriginalPathsPreservedByJunction=$true; ResearchDeleted=$false; Manifest=$taskManifest }
[IO.File]::WriteAllText($taskReceipt, ($taskReport | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
Write-Output "Archived $taskBytes bytes across $($taskManifest.Count) files; checksums and original paths verified."
