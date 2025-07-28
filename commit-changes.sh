#!/bin/bash

# 🚀 Clair Backend - Quick Commit Script
# Usage: ./commit-changes.sh "Your commit message"

set -e  # Exit on any error

echo "🔍 Checking repository status..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check for unstaged changes
if ! git diff-index --quiet HEAD --; then
    echo "📝 Found unstaged changes"
else
    echo "ℹ️  No changes to commit"
    exit 0
fi

# Show current status
echo "📊 Current repository status:"
git status --short

echo ""
echo "📁 Changed files:"
git diff --name-only

echo ""
echo "🔍 Security check - ensuring no secrets are being committed..."

# Check for potential secrets
SECRETS_FOUND=false

# Check for .env files (except .env.example)
if git diff --cached --name-only | grep -E '\.env
