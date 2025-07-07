#!/bin/bash

echo "🔍 DEPENDENCY ANALYSIS - What imports what"
echo "=========================================="

FILES_TO_CHECK=(
    "app/api/auth.py"
    "app/api/consultations.py" 
    "app/api/users.py"
    "app/services/consultation_service.py"
    "app/services/user_service.py"
)

for file in "${FILES_TO_CHECK[@]}"; do
    echo ""
    echo "📁 Checking if $file is imported anywhere..."
    
    # Convert file path to import path
    import_path=$(echo $file | sed 's/app\///g' | sed 's/\.py//g' | sed 's/\//./g')
    
    # Search for imports
    found=$(grep -r "from app.${import_path#app.} import\|import app.${import_path#app.}" app/ 2>/dev/null || true)
    
    if [ -z "$found" ]; then
        echo "✅ $file - NOT imported anywhere (SAFE TO DELETE)"
    else
        echo "❌ $file - IMPORTED by:"
        echo "$found"
        echo "🚨 NOT SAFE TO DELETE"
    fi
done
