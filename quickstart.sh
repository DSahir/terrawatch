#!/bin/bash

# TerraWatch Quick Start Guide
# Automated setup and launch script

set -e

echo "🌍 TerraWatch - Quick Start Setup"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${BLUE}[1/5]${NC} Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Step 2: Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo -e "${BLUE}[2/5]${NC} Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${BLUE}[2/5]${NC} Virtual environment already exists"
fi

# Step 3: Activate and install dependencies
echo -e "${BLUE}[3/5]${NC} Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"

# Step 4: Check for .env file
echo -e "${BLUE}[4/5]${NC} Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC}  .env file not found"
    cp .env.example .env
    echo -e "${YELLOW}⚠${NC}  Created .env from .env.example"
    echo ""
    echo -e "${YELLOW}⚠${NC}  IMPORTANT: Edit .env and add your FEATHERLESS_API_KEY"
    echo -e "${YELLOW}⚠${NC}  Get one from: https://featherless.ai"
    echo ""
else
    if grep -q "your_api_key_here" .env; then
        echo -e "${YELLOW}⚠${NC}  FEATHERLESS_API_KEY not configured in .env"
        echo -e "${YELLOW}⚠${NC}  Please edit .env and add your API key"
    else
        echo -e "${GREEN}✓${NC} .env file configured"
    fi
fi

# Step 5: Test imports
echo -e "${BLUE}[5/5]${NC} Testing imports..."
python3 -c "
from backend.config import FEATHERLESS_API_KEY, BASE_URL
from backend.models import RiskResponse, NarrateResponse
from backend.risk_engine import get_risk_data
from backend.insurance_engine import InsuranceEngine
from backend.ai_client import FeatherlessAIClient
print('✓ All imports successful')
" || {
    echo "❌ Import test failed"
    exit 1
}

echo ""
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Edit .env and add your FEATHERLESS_API_KEY:"
echo "   Get one from: https://featherless.ai"
echo ""
echo "2. Start the API server:"
echo "   uvicorn backend.main:app --reload"
echo ""
echo "3. In another terminal, test the API:"
echo "   python scripts/test_api.py"
echo ""
echo "4. API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Full project overview"
echo "   - IMPLEMENTATION.md - Detailed task breakdown"
echo "   - scripts/test_api.py - Comprehensive test suite"
echo ""
