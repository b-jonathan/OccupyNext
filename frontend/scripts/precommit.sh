#!/bin/sh
set -e
echo "🔧 Running frontend checks..."
cd "$(dirname "$0")/.."  # Go to frontend/
npm run lint-check
