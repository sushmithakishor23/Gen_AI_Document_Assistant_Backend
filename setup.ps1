# Setup script for Gen AI Document Assistant Backend
# Run this script to set up the development environment

Write-Host "Setting up Gen AI Document Assistant Backend..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    py -m venv venv
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "`n.env file already exists." -ForegroundColor Yellow
} else {
    Write-Host "`nCreating .env file from template..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env and add your API keys!" -ForegroundColor Yellow
}

Write-Host "`n" + "="*50 -ForegroundColor Green
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green
Write-Host "`nTo start the server, run:" -ForegroundColor Cyan
Write-Host "  python main.py" -ForegroundColor White
Write-Host "`nOr:" -ForegroundColor Cyan
Write-Host "  uvicorn main:app --reload" -ForegroundColor White
Write-Host "`nDon't forget to add your OpenAI API key to the .env file!" -ForegroundColor Yellow
