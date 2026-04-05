#!/bin/bash

# Bash script to run frontend in development mode

echo "Starting Sign Language Video Call Frontend..."
echo "=============================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed or not in PATH"
    exit 1
fi

# Check Node version
echo "Node version: $(node --version)"
echo "npm version: $(npm --version)"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "node_modules not found. Installing dependencies..."
    npm ci
fi

echo ""
echo "Frontend starting on http://localhost:5173"
echo "Press Ctrl+C to stop"
echo ""

# Run dev server
npm run dev
