# Build a sideload-ready zip for the Roku web installer.
#
# The installer requires `manifest` at the archive root (no wrapper
# folder) and forward-slash path separators. Compress-Archive on Windows
# PowerShell 5.1 writes backslashes, which some Roku firmware rejects, so
# this builds the zip entry-by-entry with System.IO.Compression.

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$out = Join-Path $PSScriptRoot 'now-playing-vinyl.zip'
if (Test-Path $out) { Remove-Item $out }

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$zip = [System.IO.Compression.ZipFile]::Open($out, 'Create')
try {
    $files = Get-ChildItem -Recurse -File -Path 'manifest', 'source', 'components'
    foreach ($f in $files) {
        $entry = (Resolve-Path -Relative $f.FullName) -replace '^\.[\\/]', '' -replace '\\', '/'
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip, $f.FullName, $entry) | Out-Null
        Write-Host "  + $entry"
    }
}
finally {
    $zip.Dispose()
}

Write-Host "wrote $out"
