#!/usr/bin/env python3
"""
Flask API服务器
提供静态JSON文件服务和API端点
"""

import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request, send_file
from flask_cors import CORS

# 创建Flask应用
app = Flask(__name__, static_folder='api')
CORS(app)  # 启用CORS

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
API_DIR = PROJECT_ROOT / 'api'


@app.route('/')
def index():
    """首页 - 返回API信息"""
    return jsonify({
        'name': 'Static Data API Platform',
        'version': '1.0.0',
        'description': '通用静态数据API平台',
        'endpoints': {
            'health': '/api/health.json',
            'sources': '/api/metadata/sources.json',
            'data': '/api/v1/{source}/latest.json',
            'dashboard': '/dashboard/oil-price'
        }
    })


@app.route('/dashboard/oil-price')
def oil_price_dashboard():
    """油价数据可视化仪表盘"""
    dashboard_file = PROJECT_ROOT / 'web' / 'oil-price-dashboard.html'
    if dashboard_file.exists():
        return send_file(dashboard_file)
    else:
        return jsonify({
            'status': 'error',
            'error': '仪表盘文件不存在'
        }), 404


@app.route('/tools/chatgpt-ocr')
def chatgpt_ocr_helper():
    """ChatGPT批量OCR处理助手"""
    helper_file = PROJECT_ROOT / 'web' / 'chatgpt-batch-helper.html'
    if helper_file.exists():
        return send_file(helper_file)
    else:
        return jsonify({
            'status': 'error',
            'error': '助手页面不存在'
        }), 404


@app.route('/api/v1/oil-price/copy-image/<date>')
def copy_image_to_clipboard(date):
    """将指定日期的图片复制到剪贴板"""
    try:
        import subprocess
        
        # 查找图片文件
        image_dir = API_DIR / 'v1' / 'oil-price' / 'images'
        image_files = list(image_dir.glob(f'oil_price_{date}.*'))
        
        if not image_files:
            return jsonify({
                'status': 'error',
                'error': f'未找到日期 {date} 的图片'
            }), 404
        
        image_path = str(image_files[0])
        
        # 调用复制脚本
        result = subprocess.run(
            ['python', '-c', f'''
import win32clipboard
from PIL import Image
import io

img = Image.open(r"{image_path}")
output = io.BytesIO()
img.convert("RGB").save(output, "BMP")
data = output.getvalue()[14:]
output.close()

win32clipboard.OpenClipboard()
win32clipboard.EmptyClipboard()
win32clipboard.SetClipboardData(8, data)
win32clipboard.CloseClipboard()
print("OK")
'''],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        if "OK" in result.stdout:
            return jsonify({
                'status': 'success',
                'message': f'图片 {date} 已复制到剪贴板',
                'image': image_files[0].name
            })
        else:
            return jsonify({
                'status': 'error',
                'error': f'复制失败: {result.stderr}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'复制失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/data', methods=['POST'])
def save_oil_price_data():
    """保存油价数据（从ChatGPT解析的结果）"""
    try:
        from database.oil_price_db import OilPriceDatabase
        from processors.ocr_processor import OilPriceOCRProcessor
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'error': '没有接收到数据'
            }), 400
        
        # 确保有日期字段
        if not data.get('date'):
            return jsonify({
                'status': 'error',
                'error': '缺少date字段'
            }), 400
        
        # 添加成功标记
        data['success'] = True
        
        # 重新验证数据
        processor = OilPriceOCRProcessor()
        validation = processor.validate_data(data)
        data['validation'] = validation
        
        # 保存到JSON文件
        data_dir = API_DIR / 'v1' / 'oil-price' / 'data'
        data_dir.mkdir(exist_ok=True)
        
        json_file = data_dir / f"oil_price_{data['date']}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            import json as json_module
            json_module.dump(data, f, ensure_ascii=False, indent=2)
        
        # 保存到数据库
        db = OilPriceDatabase()
        db.insert_announcement(data)
        
        return jsonify({
            'status': 'success',
            'message': f'数据已保存: {data["date"]}',
            'regions_count': len(data.get('regions', [])),
            'is_valid': validation.get('is_valid', False)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'保存失败: {str(e)}'
        }), 500


@app.route('/api/health.json')
def health_check():
    """健康检查端点"""
    # 检查数据源状态
    sources_status = {}
    v1_dir = API_DIR / 'v1'
    
    if v1_dir.exists():
        for source_dir in v1_dir.iterdir():
            if source_dir.is_dir():
                latest_file = source_dir / 'latest.json'
                if latest_file.exists():
                    try:
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        sources_status[source_dir.name] = {
                            'status': 'success',
                            'last_updated': data.get('data', {}).get('update_time', 'unknown'),
                            'records_count': len(data.get('data', {}).get('restrictions', []))
                        }
                    except Exception as e:
                        sources_status[source_dir.name] = {
                            'status': 'error',
                            'error': str(e)
                        }
                else:
                    sources_status[source_dir.name] = {
                        'status': 'no_data',
                        'message': '数据文件不存在'
                    }
    
    return jsonify({
        'status': 'success',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'sources': sources_status
    })


@app.route('/api/metadata/sources.json')
def sources_metadata():
    """数据源元数据"""
    sources = []
    v1_dir = API_DIR / 'v1'
    
    if v1_dir.exists():
        for source_dir in v1_dir.iterdir():
            if source_dir.is_dir():
                latest_file = source_dir / 'latest.json'
                metadata_file = API_DIR / 'metadata' / f'{source_dir.name}.json'
                
                source_info = {
                    'name': source_dir.name,
                    'path': f'/api/v1/{source_dir.name}/latest.json',
                    'has_data': latest_file.exists()
                }
                
                # 读取元数据
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        source_info['metadata'] = metadata
                    except Exception:
                        pass
                
                sources.append(source_info)
    
    return jsonify({
        'status': 'success',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'sources': sources
    })


@app.route('/api/v1/<source>/latest.json')
def get_latest_data(source):
    """获取最新数据"""
    source_dir = API_DIR / 'v1' / source
    latest_file = source_dir / 'latest.json'
    
    if not latest_file.exists():
        return jsonify({
            'status': 'error',
            'error': f'数据源 {source} 不存在'
        }), 404
    
    try:
        return send_from_directory(source_dir, 'latest.json')
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/v1/<source>/<filename>')
def get_data_file(source, filename):
    """获取指定数据文件"""
    source_dir = API_DIR / 'v1' / source
    file_path = source_dir / filename
    
    if not file_path.exists():
        return jsonify({
            'status': 'error',
            'error': f'文件 {filename} 不存在'
        }), 404
    
    try:
        return send_from_directory(source_dir, filename)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/collect', methods=['POST'])
def trigger_collection():
    """触发数据采集（仅用于开发测试）"""
    # 这个端点在实际生产中应该由GitHub Actions触发
    # 这里仅用于本地开发测试
    return jsonify({
        'status': 'success',
        'message': '数据采集已触发',
        'note': '在生产环境中，请使用GitHub Actions触发采集'
    })


@app.route('/api/v1/oil-price/image')
def get_oil_price_image():
    """获取最新油价图片"""
    # 查找最新的油价图片
    image_dir = API_DIR / 'v1' / 'oil-price' / 'images'
    
    if not image_dir.exists():
        return jsonify({
            'status': 'error',
            'error': '油价图片目录不存在'
        }), 404
    
    # 查找最新的图片文件
    image_files = list(image_dir.glob('oil_price_*'))
    if not image_files:
        return jsonify({
            'status': 'error',
            'error': '未找到油价图片'
        }), 404
    
    # 按修改时间排序，获取最新的图片
    latest_image = max(image_files, key=lambda f: f.stat().st_mtime)
    
    try:
        return send_file(
            latest_image,
            mimetype='image/jpeg' if latest_image.suffix == '.jpg' else 'image/png'
        )
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'发送图片失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/collect', methods=['POST'])
def trigger_oil_price_collection():
    """触发油价数据采集（最新一条）"""
    try:
        # 动态导入采集器
        from collectors.oil_price import OilPriceCollector
        from collectors.registry import CollectorRegistry
        
        # 获取配置
        config_file = PROJECT_ROOT / 'config' / 'sources.yaml'
        if config_file.exists():
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            oil_config = config.get('sources', {}).get('oil-price', {})
        else:
            oil_config = {}
        
        # 创建采集器并执行
        collector = OilPriceCollector(oil_config)
        result = collector.run()
        
        return jsonify({
            'status': 'success' if result.status.value == 'success' else 'error',
            'message': '油价数据采集完成',
            'result': result.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'采集失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/collect-all', methods=['POST'])
def trigger_oil_price_collection_all():
    """触发所有油价数据采集"""
    try:
        # 动态导入采集器
        from collectors.oil_price import OilPriceCollector
        from collectors.registry import CollectorRegistry
        
        # 获取配置
        config_file = PROJECT_ROOT / 'config' / 'sources.yaml'
        if config_file.exists():
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            oil_config = config.get('sources', {}).get('oil-price', {})
        else:
            oil_config = {}
        
        # 创建采集器并执行
        collector = OilPriceCollector(oil_config)
        result = collector.collect_all()
        
        return jsonify({
            'status': 'success' if result.status.value == 'success' else 'error',
            'message': '所有油价数据采集完成',
            'result': result.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'采集失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/images')
def get_oil_price_images():
    """获取所有油价图片列表"""
    try:
        image_dir = API_DIR / 'v1' / 'oil-price' / 'images'
        
        if not image_dir.exists():
            return jsonify({
                'status': 'success',
                'images': [],
                'total': 0
            })
        
        # 获取所有图片文件
        image_files = list(image_dir.glob('oil_price_*'))
        
        # 构建图片信息列表
        images = []
        for image_file in image_files:
            # 从文件名提取日期
            filename = image_file.name
            date_match = re.search(r'oil_price_(\d{4}-\d{2}-\d{2})', filename)
            date_str = date_match.group(1) if date_match else 'unknown'
            
            images.append({
                'filename': filename,
                'date': date_str,
                'size': image_file.stat().st_size,
                'api_endpoint': f'/api/v1/oil-price/images/{filename}',
                'modified': datetime.fromtimestamp(image_file.stat().st_mtime).isoformat()
            })
        
        # 按日期排序
        images.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'images': images,
            'total': len(images)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'获取图片列表失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/image/<date>')
def get_oil_price_image_by_date(date):
    """根据日期获取油价图片"""
    try:
        image_dir = API_DIR / 'v1' / 'oil-price' / 'images'
        
        if not image_dir.exists():
            return jsonify({
                'status': 'error',
                'error': '油价图片目录不存在'
            }), 404
        
        # 查找指定日期的图片
        pattern = f'oil_price_{date}.*'
        image_files = list(image_dir.glob(pattern))
        
        if not image_files:
            return jsonify({
                'status': 'error',
                'error': f'未找到日期为{date}的油价图片'
            }), 404
        
        # 返回第一个匹配的图片
        image_file = image_files[0]
        
        return send_file(
            image_file,
            mimetype='image/jpeg' if image_file.suffix == '.jpg' else 'image/png'
        )
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'获取图片失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/data')
def get_oil_price_data_list():
    """获取所有结构化油价数据列表"""
    try:
        data_dir = API_DIR / 'v1' / 'oil-price' / 'data'
        
        if not data_dir.exists():
            return jsonify({
                'status': 'success',
                'data': [],
                'message': '数据目录不存在'
            })
        
        # 查找所有JSON文件
        data_files = list(data_dir.glob('oil_price_*.json'))
        
        # 提取数据列表
        data_list = []
        for data_file in data_files:
            # 从文件名提取日期
            filename = data_file.name
            date_str = filename.replace('oil_price_', '').replace('.json', '')
            
            # 读取数据
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data_list.append({
                    'date': date_str,
                    'filename': filename,
                    'success': data.get('success', False),
                    'regions_count': len(data.get('regions', [])),
                    'api_endpoint': f'/api/v1/oil-price/data/{date_str}',
                    'size': data_file.stat().st_size
                })
            except Exception as e:
                print(f"读取数据文件失败: {data_file}, 错误: {e}")
        
        # 按日期排序
        data_list.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'data': data_list,
            'total': len(data_list)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'获取数据列表失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/data/<date>')
def get_oil_price_data_by_date(date):
    """根据日期获取结构化油价数据"""
    try:
        data_dir = API_DIR / 'v1' / 'oil-price' / 'data'
        
        if not data_dir.exists():
            return jsonify({
                'status': 'error',
                'error': '数据目录不存在'
            }), 404
        
        # 查找匹配的数据文件
        data_file = data_dir / f'oil_price_{date}.json'
        
        if not data_file.exists():
            return jsonify({
                'status': 'error',
                'error': f'未找到日期 {date} 的数据'
            }), 404
        
        # 读取数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            'status': 'success',
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'获取数据失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/ocr', methods=['POST'])
def trigger_oil_price_ocr():
    """触发OCR识别处理"""
    try:
        # 获取请求参数
        request_data = request.get_json() if request.is_json else {}
        date = request_data.get('date')
        
        # 动态导入OCR处理器
        from processors.ocr_processor import OilPriceOCRProcessor
        
        # 创建处理器
        processor = OilPriceOCRProcessor()
        
        # 如果指定了日期，处理单张图片
        if date:
            image_path = API_DIR / 'v1' / 'oil-price' / 'images' / f'oil_price_{date}.png'
            if not image_path.exists():
                # 尝试.jpg格式
                image_path = API_DIR / 'v1' / 'oil-price' / 'images' / f'oil_price_{date}.jpg'
            
            if not image_path.exists():
                return jsonify({
                    'status': 'error',
                    'error': f'未找到日期 {date} 的图片'
                }), 404
            
            # 处理图片
            result = processor.process_image(str(image_path))
            
            # 保存结果
            if result.get('success'):
                data_dir = API_DIR / 'v1' / 'oil-price' / 'data'
                data_dir.mkdir(exist_ok=True)
                
                data_file = data_dir / f'oil_price_{date}.json'
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'status': 'success',
                'result': result
            })
        
        else:
            # 处理所有图片
            image_dir = API_DIR / 'v1' / 'oil-price' / 'images'
            if not image_dir.exists():
                return jsonify({
                    'status': 'error',
                    'error': '图片目录不存在'
                }), 404
            
            # 获取所有图片文件
            image_files = list(image_dir.glob('oil_price_*'))
            
            results = []
            for image_file in image_files:
                # 提取日期
                filename = image_file.name
                date_str = filename.replace('oil_price_', '').replace('.png', '').replace('.jpg', '')
                
                # 检查是否已经处理过
                data_file = API_DIR / 'v1' / 'oil-price' / 'data' / f'oil_price_{date_str}.json'
                if data_file.exists():
                    results.append({
                        'date': date_str,
                        'status': 'already_processed',
                        'message': '数据已存在'
                    })
                    continue
                
                # 处理图片
                result = processor.process_image(str(image_file))
                
                # 保存结果
                if result.get('success'):
                    data_dir = API_DIR / 'v1' / 'oil-price' / 'data'
                    data_dir.mkdir(exist_ok=True)
                    
                    data_file = data_dir / f'oil_price_{date_str}.json'
                    with open(data_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                
                results.append({
                    'date': date_str,
                    'status': 'success' if result.get('success') else 'failed',
                    'regions_count': len(result.get('regions', [])) if result.get('success') else 0,
                    'error': result.get('error') if not result.get('success') else None
                })
            
            return jsonify({
                'status': 'success',
                'results': results,
                'total': len(results)
            })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'OCR处理失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/db/stats')
def get_oil_price_db_stats():
    """获取油价数据库统计信息"""
    try:
        from database.oil_price_db import OilPriceDatabase
        db = OilPriceDatabase()
        stats = db.get_statistics()
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'获取统计信息失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/db/all')
def get_oil_price_db_all():
    """获取所有油价数据（从数据库）"""
    try:
        from database.oil_price_db import OilPriceDatabase
        
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        db = OilPriceDatabase()
        announcements = db.get_all_announcements(limit=limit, offset=offset)
        
        return jsonify({
            'status': 'success',
            'data': announcements,
            'total': len(announcements),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'获取数据失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/db/date/<date>')
def get_oil_price_db_by_date(date):
    """根据日期获取油价数据（从数据库）"""
    try:
        from database.oil_price_db import OilPriceDatabase
        db = OilPriceDatabase()
        
        announcement = db.get_announcement_by_date(date)
        
        if not announcement:
            return jsonify({
                'status': 'error',
                'error': f'未找到日期 {date} 的数据'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': announcement
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'获取数据失败: {str(e)}'
        }), 500


@app.route('/api/v1/oil-price/db/region/<region_name>')
def get_oil_price_region_history(region_name):
    """获取指定地区的油价历史"""
    try:
        from database.oil_price_db import OilPriceDatabase
        
        limit = request.args.get('limit', 50, type=int)
        
        db = OilPriceDatabase()
        history = db.get_region_price_history(region_name, limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': history,
            'region': region_name,
            'total': len(history)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'获取地区历史失败: {str(e)}'
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'status': 'error',
        'error': '资源不存在',
        'path': request.path
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'status': 'error',
        'error': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    print("启动Flask API服务器...")
    print("访问地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api/health.json")
    print("按Ctrl+C停止服务器")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )