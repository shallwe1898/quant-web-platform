#!/bin/bash

# A股量化交易平台 - Streamlit部署脚本
echo "🚀 开始部署A股量化交易Web平台到Streamlit Cloud"

# 1. 初始化Git仓库
echo "📦 初始化Git仓库..."
git init
git add .
git commit -m "A股量化交易Web平台 - 初始提交"

# 2. 创建GitHub仓库（你需要手动操作）
echo ""
echo "📋 下一步操作："
echo "1. 登录 https://github.com"
echo "2. 创建新仓库，名称：quant-web-platform"
echo "3. 复制仓库的HTTPS地址（格式：https://github.com/你的用户名/quant-web-platform.git）"
echo ""

read -p "请输入你的GitHub仓库HTTPS地址: " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ 错误：必须提供GitHub仓库地址"
    exit 1
fi

# 4. 推送到GitHub
echo "📤 推送到GitHub..."
git branch -M main
git remote add origin $REPO_URL
git push -u origin main

echo ""
echo "✅ GitHub推送完成！"
echo ""
echo "🌐 现在部署到Streamlit Cloud："
echo "1. 打开 https://share.streamlit.io/"
echo "2. 点击 'New app'"
echo "3. 选择你的仓库: quant-web-platform"
echo "4. Main file path: app.py"
echo "5. 点击 'Deploy'"
echo ""
echo "⏳ 几分钟后你将获得公开URL，格式类似："
echo "   https://你的用户名-quant-web-platform.streamlit.app"
echo ""
echo "🎯 部署完成后，你就可以通过该URL访问你的量化交易平台了！"