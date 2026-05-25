#!/usr/bin/env python3
"""
项目结构测试脚本
验证项目目录和文件是否完整
"""

import os
import sys
from pathlib import Path

def test_structure():
    """测试项目结构"""
    base_dir = Path(__file__).parent.parent
    
    # 必要目录
    required_dirs = [
        "api/v1/oil-price",
        "api/v1/traffic-restrict",
        "api/v1/policy",
        "api/v1/admin-division",
        "api/v1/price-table",
        "api/metadata",
        "collectors",
        "processors",
        "config",
        "config/schemas",
        "scripts",
        "web/public",
        "web/src/components/layout",
        "web/src/components/charts",
        "web/src/components/common",
        "web/src/pages",
        "web/src/services",
        "web/src/hooks",
        "web/src/types",
        ".github/workflows",
        "docs"
    ]
    
    # 必要文件
    required_files = [
        "requirements.txt",
        "pyproject.toml",
        ".gitignore",
        "README.md",
        "collectors/__init__.py",
        "collectors/base.py",
        "collectors/registry.py",
        "collectors/oil_price.py",
        "collectors/traffic_restrict.py",
        "processors/__init__.py",
        "processors/pipeline.py",
        "processors/cleaner.py",
        "processors/validator.py",
        "processors/quality.py",
        "config/__init__.py",
        "config/settings.yaml",
        "config/sources.yaml",
        "config/schemas/oil_price.json",
        "config/schemas/traffic_restrict.json",
        "config/schemas/policy.json",
        "config/schemas/admin_division.json",
        "config/schemas/price_table.json",
        "scripts/run_collection.py",
        ".github/workflows/collect-data.yml",
        ".github/workflows/deploy.yml",
        "web/package.json",
        "web/vite.config.ts",
        "web/tsconfig.json",
        "web/tailwind.config.js",
        "web/index.html",
        "web/src/main.tsx",
        "web/src/App.tsx",
        "web/src/index.css"
    ]
    
    print("测试项目结构...")
    print("=" * 50)
    
    # 检查目录
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        else:
            print(f"目录存在: {dir_path}")
    
    # 检查文件
    missing_files = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"文件存在: {file_path}")
    
    print("=" * 50)
    
    # 输出结果
    if missing_dirs:
        print(f"缺少 {len(missing_dirs)} 个目录:")
        for dir_path in missing_dirs:
            print(f"  - {dir_path}")
    
    if missing_files:
        print(f"缺少 {len(missing_files)} 个文件:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    if not missing_dirs and not missing_files:
        print("项目结构完整！")
        return True
    else:
        print("项目结构不完整")
        return False

def main():
    """主函数"""
    success = test_structure()
    
    if success:
        print("\n项目结构测试通过！")
        sys.exit(0)
    else:
        print("\n项目结构测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()