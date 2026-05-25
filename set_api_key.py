#!/usr/bin/env python3
"""
安全设置小米MiMo API密钥
"""

import os
import sys
import json
import getpass
from pathlib import Path


def set_api_key():
    """设置API密钥"""
    print("=== 设置小米MiMo API密钥 ===")
    print("注意：API密钥是敏感信息，请勿在对话中明文提供")
    print()
    
    # 方法1：从环境变量读取
    current_key = os.environ.get("MIMO_API_KEY")
    if current_key:
        print(f"当前环境变量中已设置MIMO_API_KEY: {current_key[:8]}...{current_key[-4:]}")
        print()
    
    # 方法2：安全输入
    print("请选择设置方式：")
    print("1. 设置环境变量（推荐）")
    print("2. 保存到配置文件（不推荐，仅用于测试）")
    print("3. 退出")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        print("\n=== 设置环境变量 ===")
        print("请在PowerShell中运行以下命令：")
        print()
        print("$env:MIMO_API_KEY='your-api-key-here'")
        print()
        print("或者永久设置（需要管理员权限）：")
        print("[System.Environment]::SetEnvironmentVariable('MIMO_API_KEY', 'your-api-key-here', 'User')")
        print()
        
        # 验证环境变量
        api_key = input("或者直接在这里输入API密钥（不会保存到文件）: ").strip()
        if api_key:
            os.environ["MIMO_API_KEY"] = api_key
            print(f"✅ 环境变量已设置: {api_key[:8]}...{api_key[-4:]}")
            print("现在可以运行测试脚本了：python test_mimo_vision.py")
        
    elif choice == "2":
        print("\n=== 保存到配置文件 ===")
        print("⚠️  警告：配置文件可能被他人访问，请勿在生产环境使用")
        
        api_key = input("请输入API密钥: ").strip()
        if not api_key:
            print("❌ 未输入API密钥")
            return
        
        # 保存到配置文件
        config_file = Path(__file__).parent / "config" / "api_keys.json"
        config_file.parent.mkdir(exist_ok=True)
        
        config = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                config = {}
        
        config["mimo_api_key"] = api_key
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ API密钥已保存到: {config_file}")
        print("现在可以运行测试脚本了：python test_mimo_vision.py")
        
    elif choice == "3":
        print("退出设置")
        return
    
    else:
        print("❌ 无效选择")


def verify_api_key():
    """验证API密钥是否可用"""
    print("=== 验证API密钥 ===")
    
    api_key = os.environ.get("MIMO_API_KEY")
    if not api_key:
        print("❌ 未设置MIMO_API_KEY环境变量")
        print("请先设置环境变量：")
        print("$env:MIMO_API_KEY='your-api-key-here'")
        return False
    
    print(f"✅ 找到API密钥: {api_key[:8]}...{api_key[-4:]}")
    
    # 尝试导入openai库
    try:
        from openai import OpenAI
        print("✅ openai库已安装")
    except ImportError:
        print("❌ openai库未安装，请运行: pip install openai")
        return False
    
    # 尝试连接API
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.xiaomimimo.com/v1"
        )
        
        # 尝试一个简单的API调用
        print("正在测试API连接...")
        completion = client.chat.completions.create(
            model="mimo-v2.5",
            messages=[
                {
                    "role": "user",
                    "content": "Hello, just testing the API connection."
                }
            ],
            max_completion_tokens=10
        )
        
        print(f"✅ API连接成功！")
        print(f"模型: {completion.model}")
        print(f"响应: {completion.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_api_key()
    else:
        set_api_key()