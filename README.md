# 店铺业绩分析工具

一个用于分析店铺业绩构成的Python工具，可以分析产品、尺寸、销量、销售额、运费等数据，并支持月度对比分析。

## 🌟 功能特点

- ✅ **Web界面**：基于Streamlit的可视化Web应用
- ✅ **自动识别**：自动识别Excel中的产品、尺寸、数量、金额、运费等列
- ✅ **数据分析**：按产品分析业绩构成，按产品+尺寸分析业绩构成
- ✅ **占比计算**：计算销售额占比、销量占比
- ✅ **月度对比**：支持月度对比分析，找出增长和下降的产品
- ✅ **数据可视化**：柱状图、饼图等图表展示
- ✅ **报告导出**：生成分析报告（Excel格式）
- ✅ **云端部署**：支持部署到Streamlit Cloud，公开访问

## 🚀 快速开始

### 方法1：Web版本（推荐）

#### 本地运行
```bash
# 安装依赖
pip install -r requirements.txt

# 启动Web应用
streamlit run app.py
```

浏览器会自动打开 http://localhost:8501

#### 云端部署（Streamlit Cloud）

1. **准备GitHub仓库**
   - 确保代码已推送到GitHub
   - 仓库应包含：`app.py`、`shop_analyzer.py`、`requirements.txt`

2. **部署到Streamlit Cloud**
   - 访问 [Streamlit Cloud](https://share.streamlit.io/)
   - 使用GitHub账号登录
   - 点击 "New app" 或访问 https://share.streamlit.io/new
   - 选择你的GitHub仓库
   - 设置主文件路径：`app.py`
   - 点击 "Deploy!" 完成部署

3. **访问应用**
   - 部署成功后获得公开URL（如：`https://your-app.streamlit.app`）
   - 可以分享给任何人使用

详细部署说明请查看 [DEPLOY.md](DEPLOY.md)

### 方法2：命令行版本

#### 分析单个Excel文件
```bash
python quick_analyze.py "d:\208管家\工作簿2.xlsx"
```

#### 对比两个月份的业绩
```bash
python compare_months.py "上月.xlsx" "本月.xlsx"
```

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install pandas openpyxl numpy streamlit plotly
```

## 📖 使用说明

### Web版本使用

1. **单文件分析**
   - 选择"单文件分析"模式
   - 上传Excel文件
   - 查看产品业绩、产品+尺寸、数据可视化
   - 下载分析报告

2. **月度对比分析**
   - 选择"月度对比分析"模式
   - 分别上传上月和本月的Excel文件
   - 查看对比结果、增长产品、下降产品
   - 下载对比报告

### 命令行版本使用

详细说明请查看 [README.md](README.md)（命令行部分）

## 📊 Excel文件格式要求

工具会自动识别以下列名（支持中英文）：

- **产品列**: 产品、品名、商品、货品、名称、product、item
- **尺寸列**: 尺寸、规格、size、规格尺寸
- **数量列**: 数量、件数、销量、quantity、qty、数量(件)
- **金额列**: 金额、销售额、收入、amount、sales、金额(元)、销售额(元)
- **运费列**: 运费、邮费、快递费、shipping、运费(元)
- **日期列**: 日期、时间、date、月份、month

## 📁 项目结构

```
shop_analyzer/
├── app.py                 # Streamlit Web应用主文件
├── shop_analyzer.py       # 分析工具核心模块
├── quick_analyze.py       # 快速分析脚本
├── compare_months.py      # 月度对比脚本
├── requirements.txt       # Python依赖包
├── .streamlit/
│   └── config.toml       # Streamlit配置
├── .gitignore            # Git忽略文件
├── DEPLOY.md             # 部署指南
├── README.md             # 本文件
└── README_WEB.md         # Web版本详细说明
```

## 🔧 常见问题

**Q: 如何部署到Streamlit Cloud？**
A: 查看 [DEPLOY.md](DEPLOY.md) 获取详细部署指南

**Q: 提示"无法自动识别列名"怎么办？**
A: 检查Excel文件中的列名是否包含"产品"、"金额"等关键词，或者修改 `shop_analyzer.py` 中的列名映射

**Q: Web应用可以离线使用吗？**
A: 可以，在本地运行 `streamlit run app.py` 即可

**Q: 数据会上传到服务器吗？**
A: 本地运行时数据不会上传。部署到Streamlit Cloud时，上传的文件会临时存储在服务器上

## 📚 相关文档

- [Web版本详细说明](README_WEB.md)
- [部署指南](DEPLOY.md)
- [Streamlit文档](https://docs.streamlit.io/)
- [Streamlit Cloud文档](https://docs.streamlit.io/streamlit-cloud)

## 📝 许可证

本项目采用 MIT 许可证

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**享受数据分析的乐趣！** 📊✨
