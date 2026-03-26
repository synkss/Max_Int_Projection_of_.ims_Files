#!/bin/bash
set -e

echo "====================================="
echo "Checking environment..."
echo "====================================="

if [ ! -f ".venv/bin/python" ]; then
    echo "No virtual environment found."
    echo "Run setup_env.sh first."
    exit 1
fi

echo ""
echo "====================================="
echo "Cleaning old builds..."
echo "====================================="

rm -rf build dist *.spec

echo ""
echo "====================================="
echo "Building executable..."
echo "====================================="

uv run --python .venv/bin/python pyinstaller \
    --onefile \
    --console \
    main.py

echo ""
echo "Build complete."
echo "Output:"
echo "dist/main"