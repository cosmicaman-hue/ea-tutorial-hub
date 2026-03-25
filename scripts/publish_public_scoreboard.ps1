param(
    [string]$PublicSitePath = "public_site",
    [switch]$Push
)

$ErrorActionPreference = 'Stop'

function Resolve-AbsolutePath {
    param([string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

$siteDir = Resolve-AbsolutePath -Path $PublicSitePath
if (-not (Test-Path -LiteralPath $siteDir)) {
    throw "Public site directory not found: $siteDir"
}

$scoresPath = Join-Path $siteDir 'scores.json'
if (-not (Test-Path -LiteralPath $scoresPath)) {
    throw "scores.json not found at $scoresPath. Run Force Publish in LAN admin first."
}

Write-Host "Public site snapshot detected: $scoresPath"

if (-not $Push) {
    Write-Host "Push not requested. Use -Push to commit and push public_site changes."
    exit 0
}

$repoRoot = Resolve-AbsolutePath -Path '.'
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git'))) {
    throw "No git repository found at: $repoRoot"
}

$repoUri = New-Object System.Uri(($repoRoot.TrimEnd('\') + '\'))
$siteUri = New-Object System.Uri(($siteDir.TrimEnd('\') + '\'))
$siteRel = [System.Uri]::UnescapeDataString($repoUri.MakeRelativeUri($siteUri).ToString()).Replace('/', '\').TrimEnd('\')
if ([string]::IsNullOrWhiteSpace($siteRel) -or $siteRel.StartsWith('..')) {
    throw "Public site directory must be inside repository root. repo=$repoRoot site=$siteDir"
}
$paths = @(
    "$siteRel\index.html",
    "$siteRel\README.md",
    "$siteRel\_headers",
    "$siteRel\scores.json"
)

git -C $repoRoot add -- $paths
git -C $repoRoot diff --cached --quiet -- $paths
if ($LASTEXITCODE -eq 0) {
    Write-Host "No public_site changes to commit."
    exit 0
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
git -C $repoRoot commit -m "Publish public scoreboard ($timestamp)" -- $paths
git -C $repoRoot push origin HEAD
Write-Host "Pushed latest public scoreboard for Cloudflare Pages deployment."
