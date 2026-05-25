# 部署指南

本文档详细说明如何部署通用静态数据API平台到EdgeOne Pages。

## 前置条件

1. **GitHub账户**：用于托管代码和运行GitHub Actions
2. **EdgeOne Pages账户**：用于静态文件托管
3. **Node.js 18+**：用于构建前端
4. **Python 3.11+**：用于运行数据采集脚本

## 部署步骤

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd api-website
```

### 2. 配置GitHub Secrets

在GitHub仓库的Settings > Secrets and variables > Actions中添加以下Secrets：

- `EDGEONE_TOKEN`：EdgeOne Pages API Token
- `EDGEONE_ZONE_ID`：EdgeOne Zone ID

### 3. 配置EdgeOne Pages

1. 登录EdgeOne控制台
2. 创建新的Pages项目
3. 配置构建设置：
   - **构建命令**：`cd web && npm install && npm run build`
   - **输出目录**：`web/dist`
   - **安装命令**：`npm install`

### 4. 配置GitHub Actions

项目已包含两个GitHub Actions工作流：

1. **collect-data.yml**：定时采集数据
   - 默认每天UTC时间0点（北京时间8点）运行
   - 可手动触发

2. **deploy.yml**：自动部署到EdgeOne Pages
   - 当数据采集成功后自动触发
   - 可手动触发

### 5. 配置数据源

编辑 `config/sources.yaml` 文件，配置要采集的数据源：

```yaml
sources:
  oil-price:
    name: "国内油价"
    url: "https://your-api-endpoint.com/oil-price"
    schedule: "0 9 * * *"  # 每天9点
    timeout: 30
    retries: 3
    enabled: true
```

### 6. 本地测试

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd web
npm install

# 模拟运行数据采集
python scripts/run_collection.py --dry-run

# 启动前端开发服务器
npm run dev
```

### 7. 部署到生产环境

1. 推送代码到GitHub的main分支
2. GitHub Actions会自动运行数据采集
3. 采集成功后自动部署到EdgeOne Pages

## 验证部署

### 检查API健康状态

```bash
curl https://your-domain.com/api/health.json
```

预期响应：

```json
{
  "status": "success",
  "timestamp": "2026-05-24T15:00:00Z",
  "sources": {
    "oil-price": { "status": "healthy" },
    "traffic-restrict": { "status": "healthy" }
  }
}
```

### 检查前端页面

访问 `https://your-domain.com/web/` 查看可视化界面。

## 监控和维护

### 查看采集日志

在GitHub仓库的Actions页面查看采集日志。

### 手动触发采集

在GitHub Actions页面手动运行"Collect Data"工作流。

### 回滚数据

数据存储在Git历史中，可以通过Git回滚：

```bash
git log --oneline
git checkout <commit-hash> -- api/
git commit -m "rollback: revert to previous data"
git push
```

## 故障排除

### 采集失败

1. 检查数据源URL是否可访问
2. 检查网络连接
3. 查看GitHub Actions日志

### 部署失败

1. 检查EdgeOne Token是否正确
2. 检查构建命令是否正确
3. 查看EdgeOne Pages构建日志

### 数据不更新

1. 检查GitHub Actions是否正常运行
2. 检查数据源配置是否正确
3. 检查数据质量阈值设置

## 性能优化

### 启用CDN缓存

EdgeOne Pages自动提供CDN加速，可以在EdgeOne控制台配置缓存策略。

### 压缩数据

可以在数据采集时启用gzip压缩：

```python
import gzip
import json

data = {"key": "value"}
compressed = gzip.compress(json.dumps(data).encode())
```

### 数据分页

对于大量数据，考虑实现分页加载。

## 安全建议

1. **API密钥**：为API访问设置密钥
2. **速率限制**：配置请求频率限制
3. **CORS**：配置跨域访问策略
4. **HTTPS**：确保使用HTTPS访问

## 扩展功能

### 添加新数据源

1. 在 `collectors/` 目录创建新的采集器
2. 在 `config/sources.yaml` 添加配置
3. 在 `config/schemas/` 添加数据Schema
4. 推送代码，GitHub Actions会自动采集

### 自定义前端

1. 修改 `web/src/pages/` 中的页面组件
2. 添加新的图表组件到 `web/src/components/charts/`
3. 修改主题配置 `web/tailwind.config.js`

## 联系支持

如有问题，请通过以下方式联系：

- GitHub Issues：提交问题
- 邮件：support@example.com
- 文档：查看项目README