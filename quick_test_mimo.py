#!/usr/bin/env python3
"""快速测试小米MiMo API识别油价图片"""

import json
import time
from pathlib import Path

from openai import OpenAI

API_KEY = "tp-c7af33knz2kyu6dxw9y1wyci7iu3ldmac7691cncauts12z8"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://token-plan-cn.xiaomimimo.com/v1"
)

PROMPT = """请识别这张国内成品油价格表图片，提取以下信息：
1. 日期（从标题或内容中提取，格式：YYYY-MM-DD）
2. 标题
3. 地区数据（包括地区名称、汽油价格、柴油价格、所属区域）

请按以下JSON格式输出：
{
  "date": "YYYY-MM-DD",
  "title": "表格标题",
  "regions": [
    {
      "name": "地区名称",
      "gasoline_price": 数字（元/吨）,
      "diesel_price": 数字（元/吨）或null,
      "section": "一省一价 或 暂不实行一省一价"
    }
  ],
  "notes": ["注释内容"]
}

注意：
1. 价格单位是元/吨
2. 如果某个价格在图片中没有显示，设为null
3. 地区名称保持原样，不要修改
4. 日期从图片标题或内容中提取
5. 请只输出JSON，不要其他解释文字"""

def main():
    project_root = Path(__file__).parent
    base64_file = project_root / "temp" / "all_images_base64.json"
    data_dir = project_root / "api" / "v1" / "oil-price" / "data"
    data_dir.mkdir(exist_ok=True)

    with open(base64_file, 'r', encoding='utf-8') as f:
        all_images = json.load(f)
    image_map = {img['filename']: img for img in all_images}

    # 选择3张未处理的图片进行测试
    test_files = [
        "oil_price_2021-09-06.jpg",
        "oil_price_2022-01-17.jpg",
        "oil_price_2023-01-03.jpg"
    ]

    results = []
    for i, filename in enumerate(test_files):
        print(f"\n[{i+1}/{len(test_files)}] Processing {filename}...")
        
        image_info = image_map[filename]
        
        try:
            completion = client.chat.completions.create(
                model="mimo-v2.5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are MiMo, an AI assistant developed by Xiaomi."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_info['base64_with_prefix']
                                }
                            },
                            {
                                "type": "text",
                                "text": PROMPT
                            }
                        ]
                    }
                ],
                max_completion_tokens=4096
            )

            content = completion.choices[0].message.content
            print(f"  Response length: {len(content)} chars")

            # Parse JSON
            parsed = None
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                import re
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    try:
                        parsed = json.loads(match.group())
                    except:
                        pass

            if parsed:
                regions = parsed.get('regions', [])
                print(f"  SUCCESS: {len(regions)} regions, date={parsed.get('date', 'N/A')}")
                if regions:
                    for r in regions[:3]:
                        print(f"    {r.get('name', '?')}: gasoline={r.get('gasoline_price')}, diesel={r.get('diesel_price')}")
                
                # Save result
                date_str = filename.replace('oil_price_', '').split('.')[0]
                parsed['success'] = True
                parsed['model'] = 'mimo-v2.5'
                data_file = data_dir / f"oil_price_{date_str}.json"
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                print(f"  Saved to: {data_file.name}")
                
                results.append({"filename": filename, "success": True, "regions": len(regions)})
            else:
                print(f"  FAILED: JSON parse error")
                print(f"  Raw: {content[:200]}...")
                results.append({"filename": filename, "success": False, "raw": content[:200]})

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"filename": filename, "success": False, "error": str(e)})

        if i < len(test_files) - 1:
            time.sleep(2)

    # Summary
    success_count = sum(1 for r in results if r['success'])
    print(f"\n{'='*50}")
    print(f"Test complete: {success_count}/{len(test_files)} successful")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()