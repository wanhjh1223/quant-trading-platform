"""
量化交易平台集成测试
"""
import os
import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.features import TechnicalIndicators, FeatureEngineer
from strategies.backtest import BacktestEngine, example_strategy, Order, OrderSide


class TestTechnicalIndicators(unittest.TestCase):
    """测试技术指标"""
    
    def setUp(self):
        """创建测试数据"""
        np.random.seed(42)
        n = 100
        self.df = pd.DataFrame({
            'open': 100 + np.random.randn(n).cumsum(),
            'high': 102 + np.random.randn(n).cumsum(),
            'low': 98 + np.random.randn(n).cumsum(),
            'close': 100 + np.random.randn(n).cumsum(),
            'vol': np.random.randint(10000, 100000, n)
        })
        self.indicators = TechnicalIndicators()
    
    def test_sma(self):
        """测试SMA"""
        sma = self.indicators.sma(self.df['close'], 20)
        self.assertEqual(len(sma), len(self.df))
        self.assertTrue(sma.iloc[19:].notna().all())
    
    def test_rsi(self):
        """测试RSI"""
        rsi = self.indicators.rsi(self.df['close'], 14)
        self.assertEqual(len(rsi), len(self.df))
        # RSI应该在0-100之间
        self.assertTrue(rsi.iloc[14:].min() >= 0)
        self.assertTrue(rsi.iloc[14:].max() <= 100)
    
    def test_macd(self):
        """测试MACD"""
        macd, signal, hist = self.indicators.macd(self.df['close'])
        self.assertEqual(len(macd), len(self.df))
        self.assertEqual(len(signal), len(self.df))
        self.assertEqual(len(hist), len(self.df))
    
    def test_bollinger_bands(self):
        """测试布林带"""
        upper, middle, lower = self.indicators.bollinger_bands(self.df['close'])
        self.assertEqual(len(upper), len(self.df))
        # 上轨应该大于中轨，中轨应该大于下轨
        valid_idx = 20
        self.assertTrue(upper.iloc[valid_idx] >= middle.iloc[valid_idx])
        self.assertTrue(middle.iloc[valid_idx] >= lower.iloc[valid_idx])


class TestFeatureEngineer(unittest.TestCase):
    """测试特征工程"""
    
    def setUp(self):
        np.random.seed(42)
        n = 100
        self.df = pd.DataFrame({
            'trade_date': pd.date_range('2024-01-01', periods=n),
            'ts_code': '000001.SZ',
            'open': 100 + np.random.randn(n).cumsum(),
            'high': 102 + np.random.randn(n).cumsum(),
            'low': 98 + np.random.randn(n).cumsum(),
            'close': 100 + np.random.randn(n).cumsum(),
            'vol': np.random.randint(10000, 100000, n)
        })
        self.engineer = FeatureEngineer()
    
    def test_calculate_all_features(self):
        """测试计算全部特征"""
        features = self.engineer.calculate_all_features(self.df)
        
        # 检查是否生成了特征
        self.assertGreater(len(features.columns), len(self.df.columns))
        
        # 检查关键特征是否存在
        key_features = ['returns', 'rsi_14', 'macd', 'bb_upper', 'atr_14']
        for f in key_features:
            self.assertIn(f, features.columns)


class TestBacktestEngine(unittest.TestCase):
    """测试回测引擎"""
    
    def setUp(self):
        """创建测试数据"""
        np.random.seed(42)
        n = 200
        dates = pd.date_range('2024-01-01', periods=n)
        
        # 创建一个趋势向上的价格序列
        trend = np.linspace(100, 150, n)
        noise = np.random.randn(n) * 2
        
        self.df = pd.DataFrame({
            'trade_date': dates,
            'ts_code': '000001.SZ',
            'open': trend + noise,
            'high': trend + noise + 2,
            'low': trend + noise - 2,
            'close': trend + noise,
            'vol': np.random.randint(10000, 100000, n)
        })
    
    def test_backtest_run(self):
        """测试回测运行"""
        engine = BacktestEngine(initial_cash=100000, warmup_period=60)
        engine.set_strategy(example_strategy)
        
        results = engine.run(self.df)
        
        # 检查结果
        self.assertIn('total_return', results)
        self.assertIn('max_drawdown', results)
        self.assertIn('sharpe_ratio', results)
        self.assertIn('daily_values', results)
        
        # 验证数值合理性
        self.assertGreater(len(results['daily_values']), 0)
        self.assertIsInstance(results['total_return'], float)
    
    def test_portfolio(self):
        """测试投资组合"""
        from strategies.backtest import Portfolio, Trade, OrderSide
        
        portfolio = Portfolio(initial_cash=100000)
        
        # 模拟买入
        trade = Trade(
            symbol='000001.SZ',
            side=OrderSide.BUY,
            quantity=100,
            price=100.0,
            timestamp=pd.Timestamp.now(),
            commission=3.0
        )
        portfolio.update_position(trade)
        
        # 验证持仓
        pos = portfolio.get_position('000001.SZ')
        self.assertEqual(pos.quantity, 100)
        self.assertEqual(pos.avg_cost, 100.0)
        self.assertLess(portfolio.cash, 100000)  # 现金应该减少


def run_integration_test():
    """运行集成测试"""
    print("=" * 60)
    print("量化交易平台集成测试")
    print("=" * 60)
    
    # 创建测试数据
    np.random.seed(42)
    n = 300
    dates = pd.date_range('2024-01-01', periods=n)
    
    # 价格序列
    trend = np.linspace(100, 150, n)
    noise = np.random.randn(n) * 3
    
    df = pd.DataFrame({
        'trade_date': dates,
        'ts_code': '000001.SZ',
        'open': trend + noise,
        'high': trend + noise + 3,
        'low': trend + noise - 3,
        'close': trend + noise,
        'vol': np.random.randint(10000, 200000, n)
    })
    
    print(f"\n[1/4] 测试数据创建完成: {len(df)} 条记录")
    
    # 1. 计算特征
    print("\n[2/4] 计算技术指标...")
    engineer = FeatureEngineer()
    features = engineer.calculate_all_features(df)
    print(f"✓ 生成 {len(features.columns)} 个特征")
    
    # 2. 运行回测
    print("\n[3/4] 运行策略回测...")
    engine = BacktestEngine(initial_cash=100000, warmup_period=60)
    engine.set_strategy(example_strategy)
    results = engine.run(df)
    
    print(f"✓ 回测完成")
    print(f"  总收益率: {results['total_return']*100:.2f}%")
    print(f"  最大回撤: {results['max_drawdown']*100:.2f}%")
    print(f"  夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"  交易次数: {results['n_trades']}")
    
    # 3. 数据存储测试
    print("\n[4/4] 测试数据存储...")
    from data.storage import DataStore
    
    store = DataStore('./tests/test_quant_data')
    path = store.save_daily_data('000001.SZ', df)
    loaded = store.load_daily_data('000001.SZ')
    
    if loaded is not None and len(loaded) == len(df):
        print("✓ 数据存储测试通过")
    else:
        print("✗ 数据存储测试失败")
    
    print("\n" + "=" * 60)
    print("集成测试完成!")
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    # 运行单元测试
    print("\n运行单元测试...\n")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # 运行集成测试
    print("\n")
    run_integration_test()
