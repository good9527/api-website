# 通用静态数据API平台

一个模块化、可扩展的静态数据API平台，通过GitHub Actions定时采集多个公开数据源，经过清洗、校验后生成标准化JSON文件，通过EdgeOne Pages静态托管对外提供GET访问。

## 🚀 核心特性

- **模块化数据采集器**：支持油价、限行、政策、行政区划、价格表等多类数据源
- **数据质量保障**：Pydantic Schema校验 + 质量评分机制
- **失败不覆盖**：采集失败时保留旧数据，通过原子替换确保数据安全
- **版本回滚**：利用Git历史实现任意版本回滚
- **可视化仪表板**：现代化React前端，提供数据展示、监控、API文档等功能

## 📁 项目结构

```
api-website/
├── api/                    # 最终JSON数据输出目录
│   ├── v1/                 # API v1版本
│   │   ├── oil-price/      # 油价数据
│   │   ├── traffic-restrict/ # 限行数据
│   │   └── ...
│   └── metadata/           # 元数据
├── collectors/             # 数据采集器模块
├── processors/             # 数据处理模块
├── config/                 # 配置文件
├── scripts/                # 运行脚本
├── web/                    # 可视化网页前端
├── .github/workflows/      # GitHub Actions工作流
└── docs/                   # 项目文档
```

## 🛠️ 技术栈

### 后端 & 数据处理
- **Python 3.11+**：主要编程语言
- **Flask**：本地开发调试和处理管线编排
- **Pandas**：数据处理和分析
- **Pydantic**：数据校验和Schema定义
- **Requests**：HTTP请求库

### 前端 & UI
- **React 18 + TypeScript**：前端框架
- **Tailwind CSS**：样式方案
- **shadcn/ui**：UI组件库
- **Recharts**：图表库
- **Vite**：构建工具

### 部署 & 运维
- **GitHub Actions**：CI/CD和定时任务
- **EdgeOne Pages**：静态文件托管
- **SQLite**：本地数据存储

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd api-website
```

### 2. 安装依赖
```bash
# Python依赖
pip install -r requirements.txt

# 前端依赖
cd web
npm install
```

### 3. 本地开发
```bash
# 启动数据采集（模拟）
python scripts/run_collection.py --dry-run

# 启动前端开发服务器
cd web
npm run dev
```

### 4. 部署
项目通过GitHub Actions自动部署：
1. 推送代码到GitHub
2. 配置EdgeOne Pages
3. 设置GitHub Secrets（如需要）
4. 自动触发定时采集和部署

## 📊 API接口

### 数据接口
- `GET /api/v1/{数据类型}/latest.json` - 获取最新数据
- `GET /api/v1/{数据类型}/{日期}.json` - 获取历史数据
- `GET /api/health.json` - API健康状态
- `GET /api/metadata/sources.json` - 数据源状态

### 响应格式
```json
{
  "status": "success",
  "data": { ... },
  "metadata": {
    "source": "oil-price",
    "collected_at": "2026-05-24T12:00:00Z",
    "version": "20260524-120000",
    "quality_score": 0.95,
    "fields_count": 12,
    "records_count": 31
  }
}
```

## 🔧 配置说明

### 数据源配置 (`config/sources.yaml`)
```yaml
sources:
  oil-price:
    name: "国内油价"
    url: "https://api.example.com/oil-price"
    schedule: "0 9 * * *"  # 每天9点
    timeout: 30
    retries: 3
    schema: "oil_price.json"
```

### 全局设置 (`config/settings.yaml`)
```yaml
settings:
  quality_threshold: 0.8  # 数据质量阈值
  max_history_days: 30    # 历史数据保留天数
  staging_dir: "staging"
  live_dir: "api/v1"
```

## 📈 监控与告警

- **数据源状态监控**：实时显示各数据源健康状态
- **采集日志**：详细记录每次采集过程
- **质量评分**：自动评估数据完整性、准确性
- **失败告警**：GitHub Actions失败时自动创建Issue

## 🔒 安全与合规

- **数据源白名单**：仅从可信数据源采集
- **敏感信息过滤**：自动过滤个人身份信息
- **访问频率限制**：避免对目标网站造成压力
- **合规声明**：明确数据使用条款和免责说明

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 支持与反馈

- 提交Issue报告问题
- 创建Pull Request贡献代码
- 查看[项目文档](docs/)获取详细说明