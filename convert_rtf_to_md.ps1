# PowerShell script to convert RTF files to Markdown
# This script extracts plain text from RTF files and converts to Markdown format

param(
    [string]$SourceDir = "d:\git\srd\original",
    [string]$TargetDir = "d:\git\srd\markdown"
)

# Create target directory if it doesn't exist
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

# Function to extract text from RTF using regex fallback
function ConvertRTFToText {
    param([string]$rtfPath)
    
    $rtfContent = [System.IO.File]::ReadAllText($rtfPath, [System.Text.Encoding]::Default)
    
    # Remove font table
    $text = $rtfContent -replace '\{\\\*\\fonttbl[^}]*\}', ''
    # Remove color table
    $text = $text -replace '\{\\\*\\colortbl[^}]*\}', ''
    # Remove style sheet
    $text = $text -replace '\{\\\*\\stylesheet[^}]*\}', ''
    # Remove list tables
    $text = $text -replace '\{\\\*\\listtable[^}]*\}', ''
    # Remove list overrides
    $text = $text -replace '\{\\\*\\listoverridetable[^}]*\}', ''
    # Remove info section
    $text = $text -replace '\{\\info[^}]*\}', ''
    # Remove RTF headers and special sequences
    $text = $text -replace '^[^{]*\{\\rtf[^}]*\}', ''
    
    # Remove all RTF control sequences (backslash followed by letters and/or numbers)
    $text = $text -replace '\\[a-z]+[0-9]*\s?', ''
    # Remove escaped characters like \'xx
    $text = $text -replace "\\'[0-9a-f]{2}", ''
    # Remove curly braces
    $text = $text -replace '[{}]', ''
    # Remove asterisk commands
    $text = $text -replace '\\\*', ''
    # Remove any remaining backslashes
    $text = $text -replace '\\', ''
    
    # Clean up text replacements
    $text = $text -replace 'endash', '–'
    $text = $text -replace 'emdash', '—'
    $text = $text -replace 'rquote', "'"
    $text = $text -replace 'lquote', "'"
    $text = $text -replace 'ldblquote', '"'
    $text = $text -replace 'rdblquote', '"'
    
    # Clean up extra whitespace and newlines (but preserve some structure)
    $text = $text -replace '\s+', ' '
    # Add line breaks for common paragraph breaks (look for patterns)
    $text = $text -replace '([\.\?!])\s+([A-Z])', "`$1`n`n`$2"
    $text = $text -replace '\s+([\.;,!?])', '$1'
    $text = $text -replace '\s+\n', "`n"
    
    return $text.Trim()
}

# Get all RTF files
$rtfFiles = Get-ChildItem -Path $SourceDir -Filter "*.rtf" -File

Write-Host "Found $($rtfFiles.Count) RTF files to convert"

$count = 0
foreach ($rtfFile in $rtfFiles) {
    $count++
    $mdFileName = $rtfFile.BaseName + ".md"
    $mdPath = Join-Path -Path $TargetDir -ChildPath $mdFileName
    
    Write-Host "Converting [$count/$($rtfFiles.Count)] $($rtfFile.Name) -> $mdFileName"
    
    try {
        $text = ConvertRTFToText -rtfPath $rtfFile.FullName
        
        # Save as markdown
        [System.IO.File]::WriteAllText($mdPath, $text, [System.Text.Encoding]::UTF8)
        
        Write-Host "  OK: Successfully converted"
    }
    catch {
        Write-Host "  ERROR: $_"
    }
}

Write-Host "Conversion complete. Files saved to: $TargetDir"
