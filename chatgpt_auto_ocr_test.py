#!/usr/bin/env python3
"""
Gemini网页版自动OCR处理脚本（测试版）
自动处理前5张图片
"""

import os
import sys
import json
import time
import asyncio
import re
from pathlib import Path
from typing import List, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def get_pending_images() -> List[Dict[str, str]]:
    """获取待处理的图片列表"""
    image_dir = project_root / "api" / "v1" / "oil-price" / "images"
    data_dir = project_root / "api" / "v1" / "oil-price" / "data"
    
    all_images = sorted(image_dir.glob("oil_price_*"))
    
    processed = set()
    if data_dir.exists():
        for f in data_dir.glob("oil_price_*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                if data.get("success") and data.get("regions"):
                    date_str = f.stem.replace("oil_price_", "")
                    processed.add(date_str)
            except:
                pass
    
    pending = []
    for img in all_images:
        stem = img.stem
        date_str = stem.replace("oil_price_", "")
        if date_str not in processed:
            pending.append({
                "path": str(img.absolute()),
                "date": date_str,
                "filename": img.name
            })
    
    return pending


async def main():
    """主函数"""
    from playwright.async_api import async_playwright
    
    # 获取待处理图片
    pending = await get_pending_images()
    
    if not pending:
        print("[INFO] 没有待处理的图片！")
        return
    
    # 只处理前5张测试
    images = pending[:5]
    
    print("=" * 60)
    print("ChatGPT 自动OCR处理（测试版）")
    print("=" * 60)
    print(f"[INFO] 待处理图片: {len(images)} 张")
    print(f"[INFO] 图片列表: {', '.join(img['date'] for img in images)}")
    print()
    
    # 准备提示词 - 简短中文版本
    dates = ', '.join(img['date'] for img in images)
    prompt = f"""请识别这{len(images)}张成品油价格表，提取所有省市的汽油和柴油价格。

输出JSON数组，每个元素格式：
{{"date":"日期","title":"标题","regions":[{{"name":"地区","gasoline_price":数字,"diesel_price":数字或null,"section":"分类"}}]}}

价格单位：元/吨。只输出JSON，不要解释。

日期：{dates}"""
    
    async with async_playwright() as p:
        # 启动浏览器 - 使用Edge配置文件
        print("[INFO] 启动浏览器...")
        
        # Edge用户数据目录
        edge_user_data = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
        
        if not os.path.exists(edge_user_data):
            print(f"[FAIL] Edge配置文件不存在: {edge_user_data}")
            return
        
        print(f"[INFO] 使用Edge配置: {edge_user_data}")
        print("[INFO] 如果Edge正在运行，请先关闭它...")
        
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=edge_user_data,
                headless=False,
                channel="msedge",
                viewport={'width': 1920, 'height': 1080},
                args=['--start-maximized']
            )
            browser = None
        except Exception as e:
            print(f"[FAIL] Edge启动失败: {e}")
            print("[INFO] 请先关闭正在运行的Edge浏览器，然后重试")
            return
        
        page = await context.new_page()
        
        # 打开Gemini
        print("[INFO] 打开Gemini...")
        await page.goto('https://gemini.google.com/')
        
        # 等待页面加载完成
        print("[INFO] 等待Gemini加载（15秒）...")
        await page.wait_for_timeout(15000)
        
        # 检查是否已登录 - 查找输入框
        print("[INFO] 检查登录状态...")
        
        # 尝试多种输入框选择器（Gemini使用不同的DOM结构）
        input_found = False
        input_selectors = [
            'div[contenteditable="true"]',
            'textarea',
            'div[role="textbox"]',
            '.ql-editor',
            'rich-textarea div[contenteditable]',
            'input[type="text"]'
        ]
        
        # 多次尝试查找输入框
        for attempt in range(3):
            for selector in input_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        is_visible = await element.is_visible()
                        if is_visible:
                            print(f"[OK] 找到输入框: {selector} (可见)")
                            input_found = True
                            break
                        else:
                            print(f"[DEBUG] 找到输入框: {selector} (不可见)")
                except Exception as e:
                    print(f"[DEBUG] 尝试 {selector}: {e}")
                    continue
            
            if input_found:
                break
            
            if attempt < 2:
                print(f"[INFO] 第{attempt+1}次未找到输入框，等待10秒后重试...")
                await page.wait_for_timeout(10000)
        
        if not input_found:
            print("[WARN] 未找到可见的输入框，等待更长时间...")
            try:
                await page.wait_for_selector('div[contenteditable="true"], textarea, div[role="textbox"]', 
                                           state='visible', timeout=60000)
                print("[OK] 输入框已出现")
                input_found = True
            except Exception as e:
                print(f"[FAIL] 等待输入框超时: {e}")
                print("[INFO] 当前页面URL:", page.url)
                
                screenshot_path = project_root / "logs" / "gemini_debug.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                await page.screenshot(path=str(screenshot_path))
                print(f"[INFO] 已保存调试截图: {screenshot_path}")
                
                await browser.close()
                return
        
        # 上传图片 - 通过剪贴板粘贴
        print("\n[INFO] 通过剪贴板粘贴图片到Gemini...")
        
        import win32clipboard
        from PIL import Image
        import io
        
        def copy_image_to_clipboard(image_path):
            """将图片复制到Windows剪贴板"""
            image = Image.open(image_path)
            output = io.BytesIO()
            image.convert('RGB').save(output, 'BMP')
            data = output.getvalue()[14:]  # BMP文件头14字节
            output.close()
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
        
        # 先点击输入框确保焦点在输入框
        input_box = page.locator('div[contenteditable="true"]').first
        await input_box.click()
        await page.wait_for_timeout(500)
        
        # 逐张粘贴图片
        for img in images:
            try:
                copy_image_to_clipboard(img['path'])
                print(f"[OK] 已复制到剪贴板: {img['date']}")
                await page.wait_for_timeout(500)
                
                # 粘贴图片
                await page.keyboard.press('Control+v')
                await page.wait_for_timeout(3000)
                
                # 检查是否出现图片预览
                preview_count = await page.locator('img[src*="blob:"], img[src*="data:"], .image-preview, img[class*="upload"]').count()
                if preview_count > 0:
                    print(f"[OK] 已粘贴图片: {img['date']}")
                else:
                    print(f"[WARN] 粘贴后未检测到图片预览: {img['date']}")
                    
            except Exception as e:
                print(f"[FAIL] 粘贴图片失败 {img['date']}: {e}")
                continue
        
        print(f"[OK] 图片粘贴完成")
        await page.wait_for_timeout(2000)
        
        # ============ 第一步：只发送图片，不带提示词 ============
        print("\n[INFO] 第一步：发送图片（不带提示词）...")
        try:
            # 等待图片tooltip消失
            print("[INFO] 等待tooltip消失（5秒）...")
            await page.wait_for_timeout(5000)
            
            # 按Escape关闭可能的tooltip
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
            
            # 使用键盘快捷键跳到输入框末尾
            await page.keyboard.press('Control+End')
            await page.wait_for_timeout(500)
            
            # 只输入简短的触发词，让Gemini开始处理图片
            await page.keyboard.type("请识别这些图片中的表格数据", delay=5)
            await page.wait_for_timeout(1000)
            
            # 按Enter发送
            await page.keyboard.press('Enter')
            print("[OK] 已发送图片消息")
                
        except Exception as e:
            print(f"[FAIL] 发送图片消息失败: {e}")
        
        # ============ 等待Gemini确认收到图片 ============
        print("\n[INFO] 等待Gemini确认收到图片（等待回复稳定）...")
        
        try:
            # 等待Gemini开始回复
            await page.wait_for_timeout(10000)
            
            # 等待回复完成
            max_wait_confirm = 120  # 最多等待2分钟
            start_time = time.time()
            last_length = 0
            stable_count = 0
            
            while time.time() - start_time < max_wait_confirm:
                elapsed = int(time.time() - start_time)
                
                # 检查回复内容
                response_selectors_wait = [
                    '.response-content',
                    '.model-response',
                    'message-content',
                    '.markdown-main-panel',
                    'div[class*="response"]',
                    'div[class*="message"]'
                ]
                
                current_length = 0
                current_text = ""
                for sel in response_selectors_wait:
                    try:
                        elements = page.locator(sel)
                        if await elements.count() > 0:
                            last_elem = elements.last
                            current_text = await last_elem.inner_text()
                            current_length = len(current_text)
                            if current_length > 10:
                                break
                    except:
                        continue
                
                # 检查是否还在生成
                stop_button = page.locator('button[aria-label="Stop"], button:has(mat-icon:has-text("stop"))')
                is_generating = await stop_button.count() > 0
                
                if is_generating:
                    print(f"[DEBUG] {elapsed}s - Gemini仍在生成中...")
                    await page.wait_for_timeout(2000)
                    stable_count = 0
                    last_length = current_length
                elif current_length > 50:
                    if current_length == last_length:
                        stable_count += 1
                        if stable_count >= 3:
                            print(f"[OK] Gemini已确认收到图片，回复长度: {current_length} 字符")
                            break
                    else:
                        stable_count = 0
                        last_length = current_length
                    await page.wait_for_timeout(2000)
                else:
                    await page.wait_for_timeout(2000)
            
            print(f"[DEBUG] Gemini确认回复前200字符: {current_text[:200]}")
            
        except Exception as e:
            print(f"[WARN] 等待Gemini确认失败: {e}")
        
        # ============ 第二步：发送提取JSON的请求 ============
        print("\n[INFO] 第二步：发送JSON提取请求...")
        try:
            # 等待一下确保Gemini完成了图片识别的回复
            await page.wait_for_timeout(3000)
            
            # 保存截图以便调试
            screenshot_path = project_root / "logs" / "gemini_before_step2.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[DEBUG] 已保存第二步前截图: {screenshot_path}")
            
            # 找到新的输入框（Gemini会在回复后出现新的输入框）
            input_box = page.locator('div[contenteditable="true"]').last
            await input_box.click()
            await page.wait_for_timeout(500)
            
            # 输入提取JSON的提示词
            await page.keyboard.type(prompt, delay=3)
            await page.wait_for_timeout(1000)
            
            # 保存截图以便调试
            screenshot_path = project_root / "logs" / "gemini_after_prompt.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[DEBUG] 已保存输入提示词后截图: {screenshot_path}")
            
            # 按Enter发送
            await page.keyboard.press('Enter')
            print("[OK] 已发送JSON提取请求")
                
        except Exception as e:
            print(f"[FAIL] 发送JSON提取请求失败: {e}")
        
        # 等待Gemini回复
        print("\n[INFO] 等待Gemini回复（这可能需要2-5分钟，取决于图片数量）...")
        
        try:
            # 等待回复开始 - 增加等待时间
            print("[INFO] 等待Gemini开始处理...")
            await page.wait_for_timeout(15000)  # 等待15秒让Gemini开始处理
            
            # 等待回复完成 - 增加最大等待时间
            max_wait = 300  # 最多等待5分钟
            start_time = time.time()
            last_length = 0
            stable_count = 0
            min_content_length = 200  # 至少需要200字符才算有意义的回复
            screenshot_taken = False
            
            while time.time() - start_time < max_wait:
                elapsed = int(time.time() - start_time)
                
                # 检查是否还在生成 - Gemini的选择器
                stop_button = page.locator('button[aria-label="Stop"], button:has(mat-icon:has-text("stop"))')
                is_generating = await stop_button.count() > 0
                
                # 检查回复内容长度 - Gemini的选择器
                response_selectors_wait = [
                    '.response-content',
                    '.model-response',
                    'message-content',
                    '.markdown-main-panel',
                    'div[class*="response"]',
                    'div[class*="message"]'
                ]
                
                current_length = 0
                current_text = ""
                for sel in response_selectors_wait:
                    try:
                        elements = page.locator(sel)
                        if await elements.count() > 0:
                            last_elem = elements.last
                            current_text = await last_elem.inner_text()
                            current_length = len(current_text)
                            if current_length > 10:
                                break
                    except:
                        continue
                
                # 30秒时截图一次以便调试
                if not screenshot_taken and elapsed >= 30:
                    screenshot_taken = True
                    try:
                        screenshot_path = project_root / "logs" / "gemini_30s_state.png"
                        await page.screenshot(path=str(screenshot_path), full_page=True)
                        print(f"\n[DEBUG] 已保存30秒截图: {screenshot_path}")
                        
                        # 也获取页面所有文本
                        all_text = await page.inner_text('body')
                        debug_path = project_root / "logs" / "gemini_30s_text.txt"
                        with open(debug_path, 'w', encoding='utf-8') as f:
                            f.write(all_text)
                        print(f"[DEBUG] 已保存页面文本: {debug_path}")
                        print(f"[DEBUG] 当前回复长度: {current_length} 字符")
                        if current_text:
                            print(f"[DEBUG] 回复前200字符: {current_text[:200]}")
                    except Exception as e:
                        print(f"[DEBUG] 截图失败: {e}")
                
                if is_generating:
                    # 仍在生成中
                    if elapsed % 10 == 0:
                        print(f"\n[DEBUG] {elapsed}s - 生成中，当前长度: {current_length} 字符")
                    await page.wait_for_timeout(1000)
                    print(".", end="", flush=True)
                    stable_count = 0
                    last_length = current_length
                elif current_length < min_content_length:
                    if elapsed % 30 == 0:
                        print(f"\n[DEBUG] {elapsed}s - 内容太短({current_length} < {min_content_length})，继续等待...")
                    await page.wait_for_timeout(2000)
                    stable_count = 0
                    last_length = current_length
                else:
                    if current_length == last_length:
                        stable_count += 1
                        print(f"\n[DEBUG] {elapsed}s - 长度稳定({current_length}字符) 第{stable_count}次")
                        if stable_count >= 3:
                            print(f"\n[OK] 回复已稳定，长度: {current_length} 字符")
                            break
                    else:
                        stable_count = 0
                        last_length = current_length
                        print(f"\n[DEBUG] {elapsed}s - 长度变化: {current_length} 字符")
                    
                    await page.wait_for_timeout(2000)
            
            print("\n[OK] 回复完成")
            
            # 提取回复内容
            print("[INFO] 提取回复内容...")
            
            # 等待一下让内容完全加载
            await page.wait_for_timeout(5000)
            
            # Gemini回复选择器
            response_selectors = [
                '.response-content',
                '.model-response',
                'message-content',
                '.markdown-main-panel',
                'div[class*="response"]',
                'div[class*="message"]',
                '.conversation-container'
            ]
            
            response_text = None
            for selector in response_selectors:
                try:
                    messages = page.locator(selector)
                    message_count = await messages.count()
                    
                    print(f"[DEBUG] 选择器 {selector}: 找到 {message_count} 个元素")
                    
                    if message_count > 0:
                        # 获取最后一条回复的文本
                        last_message = messages.last
                        response_text = await last_message.inner_text()
                        print(f"[OK] 使用选择器 {selector} 找到回复，长度: {len(response_text)} 字符")
                        if len(response_text) > 100:
                            break
                except Exception as e:
                    print(f"[DEBUG] 尝试选择器 {selector}: {e}")
                    continue
            
            # 如果还是找不到，尝试获取整个页面的文本
            if not response_text or len(response_text) < 100:
                print("[WARN] 未找到回复内容，尝试获取页面文本...")
                try:
                    all_text = await page.inner_text('body')
                    # 保存完整页面文本用于调试
                    log_dir = project_root / "logs"
                    log_dir.mkdir(exist_ok=True)
                    with open(log_dir / "gemini_full_page.txt", 'w', encoding='utf-8') as f:
                        f.write(all_text)
                    print(f"[INFO] 已保存完整页面文本: {log_dir / 'gemini_full_page.txt'}")
                    
                    # 尝试从页面文本中提取JSON
                    json_match = re.search(r'\[[\s\S]*?\{[\s\S]*?\}[\s\S]*?\]', all_text)
                    if json_match:
                        response_text = json_match.group(0)
                        print(f"[OK] 从页面文本中提取到JSON，长度: {len(response_text)} 字符")
                except Exception as e:
                    print(f"[FAIL] 获取页面文本失败: {e}")
            
            if response_text:
                print(f"[INFO] 回复长度: {len(response_text)} 字符")
                
                # 保存原始回复
                log_dir = project_root / "logs"
                log_dir.mkdir(exist_ok=True)
                
                with open(log_dir / "gemini_response_test.txt", 'w', encoding='utf-8') as f:
                    f.write(response_text)
                
                # 解析JSON
                try:
                    # 提取JSON
                    json_str = response_text
                    
                    # 尝试从代码块中提取
                    if '```json' in response_text:
                        json_str = response_text.split('```json')[1].split('```')[0]
                    elif '```' in response_text:
                        json_str = response_text.split('```')[1].split('```')[0]
                    
                    # 找到JSON数组
                    array_match = re.search(r'\[[\s\S]*\]', json_str)
                    if array_match:
                        json_str = array_match.group(0)
                    
                    results = json.loads(json_str)
                    if not isinstance(results, list):
                        results = [results]
                    
                    print(f"[OK] 成功解析 {len(results)} 条数据")
                    
                    # 保存数据
                    data_dir = project_root / "api" / "v1" / "oil-price" / "data"
                    data_dir.mkdir(exist_ok=True)
                    
                    for result in results:
                        if result.get('date'):
                            json_file = data_dir / f"oil_price_{result['date']}.json"
                            result['success'] = True
                            
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(result, f, ensure_ascii=False, indent=2)
                            
                            print(f"[OK] 已保存: {result['date']} ({len(result.get('regions', []))} 个地区)")
                    
                except json.JSONDecodeError as e:
                    print(f"[FAIL] JSON解析失败: {e}")
                    print(f"[INFO] 原始回复前1000字符:")
                    print(response_text[:1000])
            else:
                print("[FAIL] 未找到回复内容")
                
        except Exception as e:
            print(f"[FAIL] 获取回复失败: {e}")
            
            # 保存调试截图
            try:
                screenshot_path = project_root / "logs" / "gemini_debug_final.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                await page.screenshot(path=str(screenshot_path))
                print(f"[INFO] 已保存调试截图: {screenshot_path}")
            except:
                pass
        
        # 保持浏览器打开一会儿
        print("\n[INFO] 处理完成，浏览器将在10秒后关闭...")
        await page.wait_for_timeout(10000)
        await context.close()
    
    # 导入到数据库
    print("\n[INFO] 导入数据到数据库...")
    try:
        from database.oil_price_db import OilPriceDatabase
        from processors.ocr_processor import OilPriceOCRProcessor
        
        db = OilPriceDatabase()
        processor = OilPriceOCRProcessor()
        
        data_dir = project_root / "api" / "v1" / "oil-price" / "data"
        for json_file in data_dir.glob("oil_price_*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get("success"):
                    # 重新验证
                    validation = processor.validate_data(data)
                    data['validation'] = validation
                    
                    # 导入数据库
                    db.insert_announcement(data)
            except Exception as e:
                print(f"[FAIL] 导入失败 {json_file.name}: {e}")
        
        stats = db.get_statistics()
        print(f"\n[INFO] 数据库统计:")
        print(f"  公告数量: {stats['announcements_count']}")
        print(f"  有效数据: {stats['valid_data_count']}")
        print(f"  地区数据: {stats['regions_count']}")
        
    except Exception as e:
        print(f"[FAIL] 数据库导入失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())