#!/bin/bash

# Check for debug code that shouldn't be in production
EXIT_CODE=0

# Check for console.log in non-test JS files
echo "Checking for console.log in production code..."
if grep -r "console\.log" apps/shopify-app/app \
    --include="*.js" \
    --include="*.jsx" \
    --include="*.ts" \
    --include="*.tsx" \
    --exclude-dir=tests \
    --exclude-dir=__tests__ \
    2>/dev/null; then
    echo "❌ Found console.log statements in production code"
    EXIT_CODE=1
fi

# Check for print statements in Python production code
echo "Checking for print statements in Python code..."
for service in services/*/src; do
    if [ -d "$service" ]; then
        if grep -r "print(" "$service" --include="*.py" 2>/dev/null | grep -v "# noqa: T201"; then
            echo "❌ Found print statements in $service"
            EXIT_CODE=1
        fi
    fi
done

# Check for debugger statements
echo "Checking for debugger statements..."
if grep -r "debugger" apps/shopify-app/app \
    --include="*.js" \
    --include="*.jsx" \
    --include="*.ts" \
    --include="*.tsx" \
    2>/dev/null; then
    echo "❌ Found debugger statements"
    EXIT_CODE=1
fi

# Check for Python breakpoints
echo "Checking for Python breakpoints..."
if grep -r "breakpoint()\|import pdb\|pdb.set_trace()" services/*/src \
    --include="*.py" \
    2>/dev/null; then
    echo "❌ Found Python breakpoints"
    EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ No debug code found"
fi

exit $EXIT_CODE
