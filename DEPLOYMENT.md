# Web平台部署指南

## 🏠 本地运行

### 1. 安装依赖
```bash
# 创建虚拟环境（推荐）
python -m venv quant_web_env
source quant_web_env/bin/activate  # macOS/Linux
# 或
quant_web_env\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用
```bash
streamlit run app.py
```

### 3. 访问地址
- 默认地址: `http://localhost:8501`
- 应用会自动在浏览器中打开

## ☁️ 云服务器部署

### 选项A: Streamlit Community Cloud（免费）
1. 将项目推送到GitHub仓库
2. 访问 [https://share.streamlit.io/](https://share.streamlit.io/)
3. 连接GitHub仓库
4. 自动部署并获得公开URL

### 选项B: 自建服务器
```bash
# 在云服务器上
git clone your-repo-url
cd quant_web_platform
pip install -r requirements.txt

# 后台运行（使用nohup）
nohup streamlit run app.py --server.port=8501 --server.address=0.0.0.0 &

# 访问: http://your-server-ip:8501
```

### 选项C: Docker部署
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# 构建和运行
docker build -t quant-web-platform .
docker run -p 8501:8501 quant-web-platform
```

## 🔒 安全注意事项

### 数据安全
- ✅ 所有数据处理在服务器端完成
- ✅ 不存储用户输入的任何数据
- ✅ 每次会话独立，无持久化存储
- ✅ 使用HTTPS（生产环境建议）

### 合规性
- ✅ 仅用于个人研究学习
- ✅ 不提供投资建议
- ✅ 明确标注模拟交易性质
- ✅ 遵循证券法规要求

### 性能优化
- **缓存机制**: 可添加@st.cache_data装饰器优化重复计算
- **股票池限制**: 当前演示使用4只股票，可扩展但注意性能
- **回测周期**: 建议不超过2年以保证响应速度

## 🎯 功能验证清单

- [ ] 本地运行正常
- [ ] 参数调整功能正常  
- [ ] 回测结果显示正确
- [ ] ROI计算准确
- [ ] 图表显示正常
- [ ] 移动端适配良好

## 📱 移动端支持

Streamlit应用天然支持移动端：
- 响应式布局
- 触摸友好的控件
- 移动浏览器兼容

## 🚀 下一步优化建议

1. **增加策略类型**: 添加更多量化策略选项
2. **用户保存功能**: 允许保存最佳参数组合（需添加简单后端）
3. **实时数据**: 集成实时行情显示（需考虑API限制）
4. **多因子模型**: 支持自定义因子组合
5. **风险分析**: 添加VaR、最大回撤等风险指标

---
**记住：本平台仅为教育和研究目的，不构成投资建议**