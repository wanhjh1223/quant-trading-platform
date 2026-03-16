"""
数据模块测试
"""
import os
import sys
import unittest
from pathlib import Path
import pandas as pd

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.storage import DataStore


class TestDataStore(unittest.TestCase):
    """测试数据存储"""
    
    def setUp(self):
        self.test_dir = './tests/test_data'
        self.store = DataStore(self.test_dir)
    
    def test_save_and_load(self):
        """测试保存和加载"""
        # 创建测试数据
        df = pd.DataFrame({
            'trade_date': pd.date_range('2024-01-01', periods=10),
            'open': [100.0] * 10,
            'close': [101.0] * 10,
            'high': [102.0] * 10,
            'low': [99.0] * 10,
            'vol': [10000] * 10
        })
        
        # 保存
        path = self.store.save_daily_data('000001.SZ', df)
        self.assertTrue(path.exists())
        
        # 加载
        loaded = self.store.load_daily_data('000001.SZ')
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 10)
    
    def test_list_stocks(self):
        """测试获取股票列表"""
        stocks = self.store.list_available_stocks()
        self.assertIsInstance(stocks, list)


class TestTushareLoader(unittest.TestCase):
    """测试Tushare数据加载（需要Token）"""
    
    @unittest.skipUnless(os.getenv('TUSHARE_TOKEN'), '需要Tushare Token')
    def test_get_stock_list(self):
        """测试获取股票列表"""
        from data.tushare_loader import get_data_source
        
        source = get_data_source()
        df = source.get_stock_list('SZSE')
        
        self.assertGreater(len(df), 0)
        self.assertIn('ts_code', df.columns)


if __name__ == '__main__':
    unittest.main()
