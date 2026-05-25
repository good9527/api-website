# 限行信息数据源配置指南

## 1. 寻找限行数据源

### 公开数据源选项

#### 1.1 政府官方数据
- **北京市交通委员会**：http://jtw.beijing.gov.cn/
- **上海市交通委员会**：https://jtw.sh.gov.cn/
- **广州市交通运输局**：https://jtys.gz.gov.cn/

#### 1.2 第三方数据平台
- **高德地图API**：https://lbs.amap.com/api/webservice/guide/api/traffic
- **百度地图API**：https://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-traffic
- **腾讯地图API**：https://lbs.qq.com/service/webService/webServiceGuide/webServiceTraffic

#### 1.3 开源数据项目
- **GitHub项目**：搜索 "traffic restriction api" 或 "限行数据"
- **数据聚合平台**：https://www.data.gov.cn/ (国家数据)

### 推荐方案：高德地图API

高德地图提供限行信息查询API，注册后可免费使用一定额度。

**注册步骤**：
1. 访问 https://lbs.amap.com/
2. 注册开发者账号
3. 创建应用，获取API Key
4. 申请限行信息查询权限

## 2. 配置数据源

### 2.1 修改配置文件

编辑 `config/sources.yaml`：

```yaml
sources:
  traffic-restrict:
    name: "限行信息"
    description: "各城市机动车限行规定"
    url: "https://restapi.amap.com/v5/direction/driving"  # 高德API示例
    schedule: "0 8 * * 1"  # 每周一8点执行
    timeout: 45
    retries: 2
    schema: "traffic_restrict.json"
    enabled: true
    headers:
      Accept: "application/json"
    params:
      key: "YOUR_AMAP_API_KEY"  # 替换为你的API Key
      origin: "116.397428,39.90923"  # 北京坐标
      destination: "116.407428,39.91923"
      strategy: 10  # 限行策略
```

### 2.2 创建采集器

如果需要自定义采集逻辑，修改 `collectors/traffic_restrict.py`：

```python
def _fetch_raw_data(self) -> Any:
    """
    获取限行数据
    这里可以实现具体的采集逻辑
    """
    # 示例：从高德API获取限行信息
    api_key = self.params.get('key', '')
    
    # 构建请求参数
    params = {
        'key': api_key,
        'origin': '116.397428,39.90923',
        'destination': '116.407428,39.91923',
        'strategy': 10
    }
    
    try:
        response = self.fetch_data(params=params)
        data = response.json()
        
        # 解析限行信息
        restrictions = []
        if 'route' in data and 'restriction' in data['route']:
            restriction_info = data['route']['restriction']
            restrictions.append({
                'city': '北京',
                'rule': restriction_info.get('rule', ''),
                'time_range': restriction_info.get('time', ''),
                'area': restriction_info.get('area', ''),
                'exceptions': [],
                'effective_date': datetime.now().strftime('%Y-%m-%d'),
                'end_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            })
        
        return {
            'update_time': datetime.now(timezone.utc).isoformat(),
            'restrictions': restrictions
        }
        
    except Exception as e:
        self.logger.error(f"获取限行数据失败: {e}")
        # 返回模拟数据作为备份
        return self._get_mock_data()
```

## 3. 本地测试

### 3.1 安装依赖

```bash
# 进入项目目录
cd h:\2026年项目\2.建立一个api网站

# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd web
npm install
cd ..
```

### 3.2 模拟运行

```bash
# 模拟运行，不实际采集数据
python scripts/run_collection.py --dry-run

# 查看输出
dir api\v1\traffic-restrict
```

### 3.3 实际采集测试

```bash
# 实际采集数据（需要配置好API Key）
python scripts/run_collection.py --sources traffic-restrict

# 检查采集结果
type api\v1\traffic-restrict\latest.json
```

### 3.4 启动前端

```bash
# 启动前端开发服务器
cd web
npm run dev
```

访问 http://localhost:3000 查看前端界面。

## 4. 数据验证

### 4.1 检查数据格式

采集完成后，检查 `api/v1/traffic-restrict/latest.json`：

```json
{
  "status": "success",
  "data": {
    "update_time": "2026-05-25T00:00:00Z",
    "restrictions": [
      {
        "city": "北京",
        "rule": "工作日早晚高峰时段限行",
        "time_range": "工作日7:00-9:00，17:00-20:00",
        "area": "五环路以内（不含五环）",
        "exceptions": ["新能源汽车"],
        "effective_date": "2026-05-25",
        "end_date": "2026-06-01"
      }
    ]
  },
  "metadata": {
    "source": "traffic-restrict",
    "collected_at": "2026-05-25T00:00:00Z",
    "version": "20260525-000000",
    "quality_score": 0.95,
    "fields_count": 2,
    "records_count": 1
  }
}
```

### 4.2 验证API接口

```bash
# 测试健康检查接口
curl http://localhost:5000/api/health.json

# 测试限行数据接口
curl http://localhost:5000/api/v1/traffic-restrict/latest.json
```

## 5. 常见问题

### 5.1 API调用失败

**问题**：调用限行API返回错误
**解决**：
1. 检查API Key是否正确
2. 检查API配额是否用完
3. 检查网络连接

### 5.2 数据格式错误

**问题**：采集的数据格式不符合Schema
**解决**：
1. 检查API返回的数据结构
2. 修改采集器的数据转换逻辑
3. 更新Schema定义

### 5.3 采集超时

**问题**：采集过程超时
**解决**：
1. 增加timeout配置
2. 检查API服务状态
3. 实现重试机制

## 6. 扩展建议

### 6.1 支持更多城市

修改采集器，支持多个城市的限行信息：

```python
cities = [
    {'name': '北京', 'origin': '116.397428,39.90923'},
    {'name': '上海', 'origin': '121.473701,31.230416'},
    {'name': '广州', 'origin': '113.264385,23.129112'},
    {'name': '深圳', 'origin': '114.085947,22.547000'}
]
```

### 6.2 定时更新

配置GitHub Actions，实现每日自动更新：

```yaml
# .github/workflows/collect-data.yml
schedule:
  - cron: '0 0 * * *'  # 每天UTC时间0点
```

### 6.3 数据可视化

在前端添加限行信息展示：

1. 在Dashboard页面添加限行状态卡片
2. 在Monitor页面显示限行数据源状态
3. 在ApiDocs页面添加限行API文档

## 7. 下一步

完成限行数据源配置后，可以：

1. **配置更多数据源**：油价、政策、行政区划等
2. **优化前端展示**：添加图表和地图可视化
3. **部署到生产环境**：配置GitHub Actions自动部署
4. **监控和告警**：设置采集失败通知

## 8. 联系支持

如有问题，请：

1. 查看项目文档：`docs/` 目录
2. 提交GitHub Issue
3. 查看采集日志：`logs/collection.log`