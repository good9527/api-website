#!/usr/bin/env python3
"""
启动Flask API服务器
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("启动Flask API服务器")
    print("=" * 50)
    print(f"访问地址: http://localhost:5000")
    print(f"API健康检查: http://localhost:5000/api/health.json")
    print(f"数据源列表: http://localhost:5000/api/metadata/sources.json")
    print(f"限行数据: http://localhost:5000/api/v1/traffic-restrict/latest.json")
    print("=" * 50)
    print("按Ctrl+C停止服务器")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )