# Set console title
$Host.UI.RawUI.WindowTitle = "CEA Console"

# Set environment variable for micromamba
$env:MAMBA_ROOT_PREFIX = Join-Path $PSScriptRoot "micromamba"

# Get micromamba path
$micromambaPath = Join-Path $PSScriptRoot "micromamba.exe"

# Initialize micromamba shell integration
& $micromambaPath shell hook -s powershell | Out-String | Invoke-Expression

# Activate cea environment
micromamba activate cea

# Run any additional commands passed as arguments
if ($args) {
    & $args
}
