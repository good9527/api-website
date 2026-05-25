#!/usr/bin/env python3
"""
油价数据库模块
负责存储和管理油价数据
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class OilPriceDatabase:
    """
    油价数据库管理类
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径，默认为项目目录下的data/oil_price.db
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent
            db_path = project_root / "data" / "oil_price.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建公告表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    title TEXT,
                    subtitle TEXT,
                    image_path TEXT,
                    ocr_text_length INTEGER,
                    success BOOLEAN,
                    error_message TEXT,
                    is_stranded BOOLEAN DEFAULT FALSE,
                    stranded_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建地区油价表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS region_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    announcement_id INTEGER,
                    region_name TEXT NOT NULL,
                    gasoline_price REAL,
                    diesel_price REAL,
                    section TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (announcement_id) REFERENCES announcements (id)
                )
            ''')
            
            # 创建验证结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    announcement_id INTEGER,
                    is_valid BOOLEAN,
                    warnings TEXT,
                    errors TEXT,
                    total_regions INTEGER,
                    complete_regions INTEGER,
                    completeness_rate REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (announcement_id) REFERENCES announcements (id)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_announcements_date ON announcements(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_region_prices_announcement ON region_prices(announcement_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_region_prices_region ON region_prices(region_name)')
            
            # 迁移：为现有表添加is_stranded和stranded_reason字段
            self._migrate_add_stranded_fields(cursor)
            
            conn.commit()
    
    def _migrate_add_stranded_fields(self, cursor):
        """
        迁移：为announcements表添加is_stranded和stranded_reason字段
        
        Args:
            cursor: 数据库游标
        """
        try:
            # 检查is_stranded字段是否存在
            cursor.execute("PRAGMA table_info(announcements)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'is_stranded' not in columns:
                cursor.execute('ALTER TABLE announcements ADD COLUMN is_stranded BOOLEAN DEFAULT FALSE')
                print("添加字段: is_stranded")
            
            if 'stranded_reason' not in columns:
                cursor.execute('ALTER TABLE announcements ADD COLUMN stranded_reason TEXT')
                print("添加字段: stranded_reason")
                
        except Exception as e:
            print(f"迁移警告: {e}")
    
    def insert_announcement(self, data: Dict[str, Any]) -> int:
        """
        插入公告数据
        
        Args:
            data: 解析后的油价数据
            
        Returns:
            插入的公告ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在该日期的公告
            date = data.get('date', '')
            if date:
                cursor.execute('SELECT id FROM announcements WHERE date = ?', (date,))
                existing = cursor.fetchone()
                if existing:
                    # 更新现有记录
                    cursor.execute('''
                        UPDATE announcements 
                        SET title = ?, subtitle = ?, image_path = ?, ocr_text_length = ?, 
                            success = ?, error_message = ?, is_stranded = ?, stranded_reason = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE date = ?
                    ''', (
                        data.get('title', ''),
                        data.get('subtitle', ''),
                        data.get('image_path', ''),
                        data.get('ocr_text_length', 0),
                        data.get('success', False),
                        data.get('error', ''),
                        data.get('is_stranded', False),
                        data.get('stranded_reason', ''),
                        date
                    ))
                    announcement_id = existing[0]
                else:
                    # 插入新记录
                    cursor.execute('''
                        INSERT INTO announcements 
                        (date, title, subtitle, image_path, ocr_text_length, success, error_message, is_stranded, stranded_reason)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        date,
                        data.get('title', ''),
                        data.get('subtitle', ''),
                        data.get('image_path', ''),
                        data.get('ocr_text_length', 0),
                        data.get('success', False),
                        data.get('error', ''),
                        data.get('is_stranded', False),
                        data.get('stranded_reason', '')
                    ))
                    announcement_id = cursor.lastrowid
            else:
                # 没有日期，直接插入
                cursor.execute('''
                    INSERT INTO announcements 
                    (date, title, subtitle, image_path, ocr_text_length, success, error_message, is_stranded, stranded_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    '',
                    data.get('title', ''),
                    data.get('subtitle', ''),
                    data.get('image_path', ''),
                    data.get('ocr_text_length', 0),
                    data.get('success', False),
                    data.get('error', ''),
                    data.get('is_stranded', False),
                    data.get('stranded_reason', '')
                ))
                announcement_id = cursor.lastrowid
            
            # 插入地区数据
            regions = data.get('regions', [])
            for region in regions:
                cursor.execute('''
                    INSERT INTO region_prices 
                    (announcement_id, region_name, gasoline_price, diesel_price, section)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    announcement_id,
                    region.get('name', ''),
                    region.get('gasoline_price'),
                    region.get('diesel_price'),
                    region.get('section', '')
                ))
            
            # 插入验证结果
            validation = data.get('validation', {})
            if validation:
                cursor.execute('''
                    INSERT INTO validation_results 
                    (announcement_id, is_valid, warnings, errors, total_regions, complete_regions, completeness_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    announcement_id,
                    validation.get('is_valid', False),
                    json.dumps(validation.get('warnings', []), ensure_ascii=False),
                    json.dumps(validation.get('errors', []), ensure_ascii=False),
                    validation.get('statistics', {}).get('total_regions', 0),
                    validation.get('statistics', {}).get('complete_regions', 0),
                    validation.get('statistics', {}).get('completeness_rate', 0)
                ))
            
            conn.commit()
            return announcement_id
    
    def get_announcement_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """
        根据日期获取公告
        
        Args:
            date: 日期字符串
            
        Returns:
            公告数据
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取公告
            cursor.execute('SELECT * FROM announcements WHERE date = ?', (date,))
            announcement = cursor.fetchone()
            
            if not announcement:
                return None
            
            # 获取地区数据
            cursor.execute('SELECT * FROM region_prices WHERE announcement_id = ?', (announcement['id'],))
            regions = cursor.fetchall()
            
            # 获取验证结果
            cursor.execute('SELECT * FROM validation_results WHERE announcement_id = ?', (announcement['id'],))
            validation = cursor.fetchone()
            
            # 组装数据
            result = dict(announcement)
            result['regions'] = [dict(region) for region in regions]
            
            if validation:
                validation_dict = dict(validation)
                validation_dict['warnings'] = json.loads(validation_dict['warnings'])
                validation_dict['errors'] = json.loads(validation_dict['errors'])
                result['validation'] = validation_dict
            
            return result
    
    def get_all_announcements(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取所有公告
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            公告列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM announcements 
                ORDER BY date DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            announcements = cursor.fetchall()
            result = []
            
            for announcement in announcements:
                # 获取地区数据
                cursor.execute('SELECT * FROM region_prices WHERE announcement_id = ?', (announcement['id'],))
                regions = cursor.fetchall()
                
                # 获取验证结果
                cursor.execute('SELECT * FROM validation_results WHERE announcement_id = ?', (announcement['id'],))
                validation = cursor.fetchone()
                
                # 组装数据
                announcement_dict = dict(announcement)
                announcement_dict['regions'] = [dict(region) for region in regions]
                
                if validation:
                    validation_dict = dict(validation)
                    validation_dict['warnings'] = json.loads(validation_dict['warnings'])
                    validation_dict['errors'] = json.loads(validation_dict['errors'])
                    announcement_dict['validation'] = validation_dict
                
                result.append(announcement_dict)
            
            return result
    
    def get_region_price_history(self, region_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取地区油价历史
        
        Args:
            region_name: 地区名称
            limit: 限制数量
            
        Returns:
            油价历史列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rp.*, a.date 
                FROM region_prices rp
                JOIN announcements a ON rp.announcement_id = a.id
                WHERE rp.region_name = ?
                ORDER BY a.date DESC
                LIMIT ?
            ''', (region_name, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 公告数量
            cursor.execute('SELECT COUNT(*) FROM announcements')
            announcements_count = cursor.fetchone()[0]
            
            # 成功公告数量
            cursor.execute('SELECT COUNT(*) FROM announcements WHERE success = 1')
            successful_announcements = cursor.fetchone()[0]
            
            # 地区数据数量
            cursor.execute('SELECT COUNT(*) FROM region_prices')
            regions_count = cursor.fetchone()[0]
            
            # 有效数据数量
            cursor.execute('SELECT COUNT(*) FROM validation_results WHERE is_valid = 1')
            valid_data_count = cursor.fetchone()[0]
            
            # 最新公告日期
            cursor.execute('SELECT MAX(date) FROM announcements')
            latest_date = cursor.fetchone()[0]
            
            # 最旧公告日期
            cursor.execute('SELECT MIN(date) FROM announcements')
            oldest_date = cursor.fetchone()[0]
            
            return {
                'announcements_count': announcements_count,
                'successful_announcements': successful_announcements,
                'regions_count': regions_count,
                'valid_data_count': valid_data_count,
                'latest_date': latest_date,
                'oldest_date': oldest_date,
                'success_rate': successful_announcements / announcements_count if announcements_count > 0 else 0
            }
    
    def import_from_json_files(self, data_dir: str = None):
        """
        从JSON文件导入数据到数据库
        
        Args:
            data_dir: JSON文件目录
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent
            data_dir = project_root / "api" / "v1" / "oil-price" / "data"
        
        data_dir = Path(data_dir)
        
        # 查找所有JSON文件
        json_files = list(data_dir.glob("oil_price_*.json"))
        
        print(f"找到 {len(json_files)} 个JSON文件")
        
        imported_count = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 插入数据库
                self.insert_announcement(data)
                imported_count += 1
                
            except Exception as e:
                print(f"导入失败 {json_file.name}: {e}")
        
        print(f"成功导入 {imported_count} 个文件")
        return imported_count


def main():
    """测试函数"""
    # 初始化数据库
    db = OilPriceDatabase()
    
    # 导入JSON文件
    imported_count = db.import_from_json_files()
    
    # 获取统计信息
    stats = db.get_statistics()
    
    print("\n=== 数据库统计 ===")
    print(f"公告数量: {stats['announcements_count']}")
    print(f"成功公告: {stats['successful_announcements']}")
    print(f"地区数据: {stats['regions_count']}")
    print(f"有效数据: {stats['valid_data_count']}")
    print(f"最新日期: {stats['latest_date']}")
    print(f"最旧日期: {stats['oldest_date']}")
    print(f"成功率: {stats['success_rate']:.1%}")
    
    # 测试查询
    if stats['announcements_count'] > 0:
        # 获取最新公告
        latest_announcements = db.get_all_announcements(limit=3)
        print("\n最新3条公告:")
        for i, announcement in enumerate(latest_announcements, 1):
            print(f"{i}. {announcement['date']}: {announcement['title']}")
            print(f"   地区数: {len(announcement.get('regions', []))}")
            print(f"   有效: {announcement.get('validation', {}).get('is_valid', False)}")


if __name__ == "__main__":
    main()