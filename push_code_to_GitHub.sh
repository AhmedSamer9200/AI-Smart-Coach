#!/bin/bash

echo "🚀 Preparing to push updates to GitHub..."

# 1. تجهيز كل الملفات اللي اتعدلت
git add .

# 2. عمل رسالة الحفظ أوتوماتيك بالتاريخ والوقت بتاع جهازك
COMMIT_MSG="🔄 Auto-update: $(date +'%Y-%m-%d %I:%M %p')"
git commit -m "$COMMIT_MSG"

# 3. الرفع للسحابة
echo "☁️ Pushing code to GitHub..."
git push

echo "========================================="
echo "✅ Code successfully pushed and secured!"
echo "========================================="