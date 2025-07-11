#!/bin/bash
echo "🇸🇦 Saudi Legal Crawler - Unix Runner"
echo "===================================="

cd "$(dirname "$0")/backend"

echo "🔧 Activating virtual environment (if exists)..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️ No virtual environment found - using system Python"
fi

echo "🚀 Starting crawler..."
python run_saudi_legal_crawler.py

echo "✅ Crawler execution completed"
read -p "Press Enter to continue..."
