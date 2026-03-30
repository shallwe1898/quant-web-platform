#!/bin/bash

echo "🚀 开始部署高级量化交易平台到Streamlit Cloud"
echo "=========================================="

# 1. 确保所有文件已提交
echo "📦 检查Git状态..."
git status

echo ""
echo "✅ 所有文件已准备好部署！"
echo ""
echo "📋 手动部署步骤："
echo "1. 打开 https://share.streamlit.io/"
echo "2. 登录你的GitHub账户"
echo "3. 点击 'New app'"
echo "4. 填写以下配置："
echo "   - Repository: shallwe1898/quant-web-platform"
echo "   - Branch: main"
echo "   - Main file path: advanced_app.py"
echo "   - Python version: (保持默认)"
echo "5. 点击 'Deploy'"
echo ""
echo "🎯 部署成功后，你将获得URL："
echo "   https://shallwe1898-quant-web-platform.streamlit.app"
echo ""
echo "💡 提示：如果advanced_app.py部署失败（内存限制），"
echo "   可以先尝试部署app.py（基础版本）"