# This script automates the full CiteCrawl pipeline:
# 1. Extracts and enriches URLs from a CSV file.
# 2. Generates and appends citations to the bibliography file.

# --- Configuration ---
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"
$csvPath = "data\csv_with_links\Recursos guia - Género e inclusión en la IA.csv"
$outputDir = "data\extracted_pages\genero_e_inclusion_en_la_ia"

# --- Execution ---
Write-Host "Starting the CiteCrawl pipeline..."
Write-Host "Input file: $csvPath"
Write-Host "Output folder: $outputDir"
Write-Host ""

try {
    Write-Host "[Step 1/2] Running extraction and enrichment..."
    uv run python -m citecrawl extract $csvPath --output $outputDir
    Write-Host "Extraction complete."
    Write-Host ""

    Write-Host "[Step 2/2] Running citation generation..."
    uv run python -m citecrawl cite $csvPath
    Write-Host "Citation generation complete."
    Write-Host ""

    Write-Host "Pipeline finished successfully."
}
catch {
    Write-Error "An error occurred during the pipeline execution: $_"
    exit 1
}