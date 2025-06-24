#!/bin/sh
set -e

echo "🐍 Backend pre-commit running..."

# Auto-activate venv if not already activated
if [ -f venv/scripts/activate ]; then
  . venv/scripts/activate
fi

isort . && black . && flake8 .
