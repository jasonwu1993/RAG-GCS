#!/bin/bash
# Quick commit script for RAG-GCS
# Usage: ./quick-commit.sh "Your message"

if [ -z "$1" ]; then
    echo "💬 Enter commit message:"
    read -r MSG
else
    MSG="$1"
fi

echo "🔍 Checking for secrets..."
if git diff --name-only | grep -E '\.env$|service-account\.json$'; then
    echo "⚠️  WARNING: Sensitive files detected!"
    read -p "Continue? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled"
        exit 1
    fi
fi

echo "📦 Staging changes..."
git add .

echo "💾 Committing..."
git commit -m "$MSG

📅 $(date '+%Y-%m-%d %H:%M:%S')
🏷️  Auto-commit"

echo "📡 Pushing to GitHub..."
git push origin main

echo "✅ Done! https://github.com/jasonwu1993/RAG-GCS"
