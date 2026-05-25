# ──────────────────────────────────────────────────────────────────────────────
#  export-diagrams.ps1
#  Exports every PlantUML diagram found in .md files to outDiagrams/<subfolder>/
#  Usage:  .\scripts\export-diagrams.ps1
# ──────────────────────────────────────────────────────────────────────────────

$Root     = Split-Path $PSScriptRoot -Parent
$Jar      = "C:\Users\hiayg\.vscode\extensions\jebbs.plantuml-2.18.1\plantuml.jar"
$OutRoot  = Join-Path $Root "outDiagrams"

# Add more source folders here as the project grows
$SourceDirs = @("Analysis", "Implementation")

# ── sanity checks ─────────────────────────────────────────────────────────────
if (-not (Test-Path $Jar)) {
    Write-Error "PlantUML jar not found at: $Jar"; exit 1
}

# ── discover & export ─────────────────────────────────────────────────────────
$count = 0

foreach ($dir in $SourceDirs) {
    $srcDir = Join-Path $Root $dir
    if (-not (Test-Path $srcDir)) { continue }

    Get-ChildItem -Path $srcDir -Filter "*.md" -Recurse | ForEach-Object {
        $file = $_

        # Skip files that have no @startuml block
        if ((Get-Content $file.FullName -Raw) -notmatch '@startuml') { return }

        # Mirror source subfolder under outDiagrams/
        $relative = $file.DirectoryName.Substring($Root.Length).TrimStart('\', '/')
        $outDir   = Join-Path $OutRoot $relative

        if (-not (Test-Path $outDir)) {
            New-Item -ItemType Directory -Force -Path $outDir | Out-Null
            Write-Host "  Created  outDiagrams\$relative" -ForegroundColor DarkGray
        }

        Write-Host "Exporting  $($file.FullName.Substring($Root.Length + 1))" -ForegroundColor Cyan
        java -DPLANTUML_LIMIT_SIZE=16384 -jar $Jar -tpng -charset UTF-8 -o $outDir $file.FullName

        if ($LASTEXITCODE -eq 0) {
            Write-Host "       --> outDiagrams\$relative\$($file.BaseName).png" -ForegroundColor Green
        } else {
            Write-Warning "Export failed for $($file.Name)"
        }

        $count++
    }
}

if ($count -eq 0) {
    Write-Host "No diagrams found in: $($SourceDirs -join ', ')" -ForegroundColor Yellow
} else {
    Write-Host "`nDone - $count diagram(s) exported to outDiagrams\" -ForegroundColor Green
}
