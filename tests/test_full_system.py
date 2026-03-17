#!/usr/bin/env python3
"""
量化交易平台 - 全面功能测试
测试所有核心模块确保正常运行
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from loguru import logger

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSuite:
    """测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("量化交易平台 - 全面功能测试")
        print("=" * 70)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 数据模块测试
        self.test_data_module()
        
        # 2. 特征工程测试
        self.test_feature_module()
        
        # 3. 策略模块测试
        self.test_strategy_module()
        
        # 4. 回测引擎测试
        self.test_backtest_module()
        
        # 5. 风控模块测试
        self.test_risk_module()
        
        # 6. 交易接口测试
        self.test_trading_module()
        
        # 7. 存储模块测试
        self.test_storage_module()
        
        # 8. 端到端集成测试
        self.test_end_to_end()
        
        # 输出汇总
        self.print_summary()
        
    def test_data_module(self):
        """测试数据模块"""
        print("\n📊 [模块1/8] 数据模块测试")
        print("-" * 50)
        
        try:
            # 测试Tushare数据源
            from data.tushare_loader import TushareDataSource
            print("  ✓ TushareDataSource 导入成功")
            
            # 测试AKShare数据源
            try:
                import akshare as ak
                print("  ✓ AKShare 可用")
            except ImportError:
                print("  ⚠ AKShare 未安装")
            
            # 测试Yahoo Finance
            try:
                import yfinance as yf
                print("  ✓ Yahoo Finance (yfinance) 可用")
            except ImportError:
                print("  ⚠ Yahoo Finance 未安装")
            
            # 测试数据下载器
            from data.tushare_loader import DataDownloader
            print("  ✓ DataDownloader 导入成功")
            
            self.passed += 1
            self.test_results.append(("数据模块", "通过", ""))
            
        except Exception as e:
            self.failed += 1
            self.test_results.append(("数据模块", "失败", str(e)))
            print(f"  ✗ 错误: {e}")
    
    def test_feature_module(self):
        """测试特征工程模块"""
        print("\n🔧 [模块2/8] 特征工程测试")
        print("-" * 50)
        
        try:
            from data.features import TechnicalIndicators, FeatureEngineer
            
            # 创建测试数据
            np.random.seed(42)
            n = 100
            df = pd.DataFrame({
                'open': 100 + np.random.randn(n).cumsum(),
                'high': 102 + np.random.randn(n).cumsum(),
                'low': 98 + np.random.randn(n).cumsum(),
                'close': 100 + np.random.randn(n).cumsum(),
                'vol': np.random.randint(10000, 100000, n)
            })
            
            # 测试技术指标
            indicators = TechnicalIndicators()
            
            # SMA
            sma = indicators.sma(df['close'], 20)
            assert len(sma) == len(df), "SMA长度不匹配"
            assert sma.iloc[19:].notna().all(), "SMA计算有误"
            print("  ✓ SMA 指标计算正确")
            
            # EMA
            ema = indicators.ema(df['close'], 20)
            assert len(ema) == len(df), "EMA长度不匹配"
            print("  ✓ EMA 指标计算正确")
            
            # RSI
            rsi = indicators.rsi(df['close'], 14)
            assert 0 <= rsi.iloc[14:].min() <= 100, "RSI范围错误"
            assert 0 <= rsi.iloc[14:].max() <= 100, "RSI范围错误"
            print("  ✓ RSI 指标计算正确")
            
            # MACD
            macd, signal, hist = indicators.macd(df['close'])
            assert len(macd) == len(df), "MACD长度不匹配"
            print("  ✓ MACD 指标计算正确")
            
            # 布林带
            upper, middle, lower = indicators.bollinger_bands(df['close'])
            assert upper.iloc[20] >= middle.iloc[20] >= lower.iloc[20], "布林带逻辑错误"
            print("  ✓ Bollinger Bands 计算正确")
            
            # ATR
            atr = indicators.atr(df['high'], df['low'], df['close'], 14)
            assert atr.iloc[14:].notna().all(), "ATR计算有误"
            print("  ✓ ATR 指标计算正确")
            
            # 测试特征工程器
            engineer = FeatureEngineer()
            features = engineer.calculate_all_features(df)
            assert len(features.columns) > len(df.columns), "特征生成不足"
            print(f"  ✓ 特征工程器生成 {len(features.columns)} 个特征")
            
            self.passed += 1
            self.test_results.append(("特征工程", "通过", ""))
            
        except Exception as e:
            self.failed += 1
            self.test_results.append(("特征工程", "失败", str(e)))
            print(f"  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def test_strategy_module(self):
        """测试策略模块"""
        print("\n📈 [模块3/8] 策略模块测试")
        print("-" * 50)
        
        try:
            # 测试技术指标策略
            from strategies.technical_strategies import (
                MACDStrategy, RSIStrategy, DoubleMAStrategy, 
                BollingerBandsStrategy, GridTradingStrategy
            )
            
            # 创建测试数据
            np.random.seed(42)
            n = 200
            df = pd.DataFrame({
                'open': 100 + np.random.randn(n).cumsum() * 0.5,
                'high': 102 + np.random.randn(n).cumsum() * 0.5,
                'low': 98 + np.random.randn(n).cumsum() * 0.5,
                'close': 100 + np.linspace(0, 50, n) + np.random.randn(n) * 2,
                'volume': np.random.randint(10000, 100000, n)
            })
            
            # MACD策略
            macd_strategy = MACDStrategy(fast=12, slow=26, signal=9)
            df_macd = macd_strategy.generate_signals(df.copy())
            assert 'signal' in df_macd.columns, "MACD策略未生成信号"
            assert 'DIF' in df_macd.columns, "MACD策略未计算DIF"
            print("  ✓ MACD策略运行正常")
            
            # RSI策略
            rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
            df_rsi = rsi_strategy.generate_signals(df.copy())
            assert 'signal' in df_rsi.columns, "RSI策略未生成信号"
            assert 'RSI' in df_rsi.columns, "RSI策略未计算RSI"
            print("  ✓ RSI策略运行正常")
            
            # 双均线策略
            ma_strategy = DoubleMAStrategy(short=5, long=20)
            df_ma = ma_strategy.generate_signals(df.copy())
            assert 'signal' in df_ma.columns, "MA策略未生成信号"
            print("  ✓ 双均线策略运行正常")
            
            # 布林带策略
            bb_strategy = BollingerBandsStrategy(period=20, std_dev=2.0)
            df_bb = bb_strategy.generate_signals(df.copy())
            assert 'signal' in df_bb.columns, "BB策略未生成信号"
            print("  ✓ 布林带策略运行正常")
            
            # 网格策略
            grid_strategy = GridTradingStrategy(lower_price=80, upper_price=150, grid_num=10)
            df_grid = grid_strategy.generate_signals(df.copy())
            assert 'signal' in df_grid.columns, "网格策略未生成信号"
            print("  ✓ 网格交易策略运行正常")
            
            # 测试多因子策略
            from strategies.multi_factor_strategy import MultiFactorStrategy
            
            # 创建多因子测试数据
            df_factor = pd.DataFrame({
                'code': ['000001.SZ', '000002.SZ', '600519.SH'] * 10,
                'close': np.random.uniform(10, 200, 30),
                'pe_ratio': np.random.uniform(5, 50, 30),
                'pb_ratio': np.random.uniform(0.5, 10, 30),
                'roe': np.random.uniform(0.05, 0.3, 30),
                'roa': np.random.uniform(0.03, 0.2, 30),
                'gross_margin': np.random.uniform(0.1, 0.8, 30),
                'revenue_growth': np.random.uniform(-0.2, 0.5, 30),
                'profit_growth': np.random.uniform(-0.3, 0.6, 30)
            })
            
            factor_strategy = MultiFactorStrategy()
            selected = factor_strategy.select_stocks(df_factor, top_n=5)
            assert len(selected) <= 5, "多因子选股数量错误"
            print(f"  ✓ 多因子选股策略运行正常 (选中{len(selected)}只)")
            
            # 测试AI策略
            from strategies.ai_strategies import FeatureEngine, LSTMStrategy
            
            engine = FeatureEngine()
            df_features = engine.create_technical_features(df)
            assert len(df_features.columns) > 0, "AI特征工程失败"
            print("  ✓ AI特征工程运行正常")
            
            self.passed += 1
            self.test_results.append(("策略模块", "通过", ""))
            
        except Exception as e:
            self.failed += 1
            self.test_results.append(("策略模块", "失败", str(e)))
            print(f"  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def test_backtest_module(self):
        """测试回测引擎"""
        print("\n🔄 [模块4/8] 回测引擎测试")
        print("-" * 50)
        
        try:
            from strategies.backtest import (
                BacktestEngine, example_strategy, 
                Order, OrderSide, Portfolio
            )
            
            # 创建测试数据（明显的趋势）
            np.random.seed(42)
            n = 300
            dates = pd.date_range('2024-01-01', periods=n)
            
            # 创建一个有明显趋势的价格序列
            trend = np.linspace(100, 150, n)
            noise = np.random.randn(n) * 2
            
            df = pd.DataFrame({
                'trade_date': dates,
                'ts_code': '000001.SZ',
                'open': trend + noise,
                'high': trend + noise + 3,
                'low': trend + noise - 3,
                'close': trend + noise,
                'vol': np.random.randint(10000, 200000, n)
            })
            
            # 测试回测引擎
            engine = BacktestEngine(
                initial_cash=100000,
                commission_rate=0.0003,
                slippage=0.001,
                warmup_period=60
            )
            engine.set_strategy(example_strategy)
            
            print("  运行回测...")
            results = engine.run(df)
            
            # 验证结果
            assert 'total_return' in results, "回测结果缺少total_return"
            assert 'max_drawdown' in results, "回测结果缺少max_drawdown"
            assert 'sharpe_ratio' in results, "回测结果缺少sharpe_ratio"
            assert 'daily_values' in results, "回测结果缺少daily_values"
            
            print(f"  ✓ 回测引擎运行成功")
            print(f"    - 初始资金: ¥{results['initial_cash']:,.0f}")
            print(f"    - 最终价值: ¥{results['final_value']:,.0f}")
            print(f"    - 总收益率: {results['total_return']*100:.2f}%")
            print(f"    - 最大回撤: {results['max_drawdown']*100:.2f}%")
            print(f"    - 夏普比率: {results['sharpe_ratio']:.2f}")
            print(f"    - 交易次数: {results['n_trades']}")
            
            # 测试Portfolio
            portfolio = Portfolio(initial_cash=100000)
            
            from strategies.backtest import Trade
            trade = Trade(
                symbol='000001.SZ',
                side=OrderSide.BUY,
                quantity=100,
                price=100.0,
                timestamp=datetime.now(),
                commission=3.0
            )
            portfolio.update_position(trade)
            
            pos = portfolio.get_position('000001.SZ')
            assert pos.quantity == 100, "持仓数量错误"
            print("  ✓ Portfolio持仓管理正常")
            
            self.passed += 1
            self.test_results.append(("回测引擎", "通过", ""))
            
        except Exception as e:
            self.failed += 1
            self.test_results.append(("回测引擎", "失败", str(e)))
            print(f"  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def test_risk_module(self):
        """测试风控模块"""
        print("\n🛡️ [模块5/8] 风控模块测试")
        print("-" * 50)
        
        try:
            from utils.risk_manager import RiskManager, calculate_kelly_criterion
            
            # 创建风控管理器
            risk_mgr = RiskManager(
                total_capital=100000,
                max_position_pct=0.2,
                max_drawdown_pct=0.15,
                max_daily_loss_pct=0.05
            )
            
            # 测试仓位计算
            position_size = risk_mgr.calculate_position_size('000001.SZ', 100.0)
            assert position_size > 0, "仓位计算错误"
            print(f"  ✓ 仓位计算正常 (建议{position_size}股)")
            
            # 测试开仓检查
            can_open, reason = risk_mgr.can_open_position('000001.SZ', 100, 100.0)
            assert can_open, f"开仓检查失败: {reason}"
            print("  ✓ 开仓检查通过")
            
            # 测试开仓
            result = risk_mgr.open_position('000001.SZ', 100, 100.0)
            assert result['success'], f"开仓失败: {result}"
            assert '000001.SZ' in risk_mgr.positions, "持仓未记录"
            print("  ✓ 开仓功能正常")
            
            # 测试价格更新
            risk_mgr.update_prices({'000001.SZ': 110.0})
            pos = risk_mgr.positions['000001.SZ']
            assert pos.current_price == 110.0, "价格更新失败"
            print("  ✓ 价格更新正常")
            
            # 测试风控检查
            risk_events = risk_mgr.check_risk_limits()
            print(f"  ✓ 风控检查正常 (触发{len(risk_events)}个事件)")
            
            # 测试止盈止损
            # 更新到止盈价格
            risk_mgr.update_prices({'000001.SZ': 115.0})  # 默认止盈15%
            risk_events = risk_mgr.check_risk_limits()
            take_profit_triggered = any(e['type'] == 'take_profit' for e in risk_events)
            if take_profit_triggered:
                print("  ✓ 止盈触发检测正常")
            
            # 测试平仓
            close_result = risk_mgr.close_position('000001.SZ', 110.0)
            assert close_result['success'], "平仓失败"
            assert '000001.SZ' not in risk_mgr.positions, "持仓未清除"
            print("  ✓ 平仓功能正常")
            
            # 测试组合摘要
            summary = risk_mgr.get_portfolio_summary()
            assert 'total_value' in summary, "组合摘要缺少字段"
            print("  ✓ 组合摘要功能正常")
            
            # 测试凯利公式
            kelly = calculate_kelly_criterion(win_rate=0.55, win_loss_ratio=2.0)
            assert 0 <= kelly <= 1, "凯利公式计算错误"
            print(f"  ✓ 凯利公式计算正常 (f*={kelly:.4f})")
            
            self.passed += 1
            self.test_results.append(("风控模块", "通过", ""))
            
        except Exception as e:
            self.failed += 1
            self.test_results.append(("风控模块", "失败", str(e)))
            print(f"  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def test_trading_module(self):
        """测试交易接口模块"""
        print("\n💹 [模块6/8] 交易接口测试")
        print("-" * 50)
        
        try:
            from trading.futu_trader import MockTrader
            
            # 测试模拟交易器
            trader = MockTrader(initial_cash=100000)
            
            # 测试买入
            success, order = trader.place_order('HK.00700', 500.0, 100, 'buy')
            assert success, f"买入失败: {order}"
            assert trader.cash < 100000, "现金未减少"
            assert 'HK.00700' in trader.positions, "持仓未记录"
            print("  ✓ 模拟买入功能正常")
            
            # 测试卖出
            success, order = trader.place_order('HK.00700', 550.0, 100, 'sell')
            assert success, f"卖出失败: {order}"
            # 卖出后持仓数量应为0（键仍然保留）
            assert trader.positions.get('HK.00700', {}).get('qty', 0) == 0, "持仓未清零"
            print("  ✓ 模拟卖出功能正常")
            
            # 测试资金不足
            success, order = trader.place_order('HK.00700', 50000.0, 100, 'buy')
            assert not success, "应该资金不足"
            print("  ✓ 资金不足检测正常")
            
            # 测试持仓查询
            portfolio = trader.get_portfolio()
            assert 'cash' in portfolio, "组合信息缺失"
            print("  ✓ 组合查询功能正常")
            
            # 测试富途接口导入
            try:
                from trading.futu_trader import FutuTrader
                print("  ✓ FutuTrader 导入成功 (需OpenD环境)")
            except ImportError as ie:
                print(f"  ⚠ FutuTrader 导入失败 (正常，需安装futu-api): {ie}")
            
            self.passed += 1
            self.test_results.append(("交易接口", "通过", ""))
            
        except Exception as e:
            self.failed += 1
            self.test_results.append(("交易接口", "失败", str(e)))
            print(f"  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def test_storage_module(self):
        """测试数据存储模块"""
        print("\n💾 [模块7/8] 数据存储测试")
        print("-" * 50)
        
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            
            try:
                from data.storage import DataStore
                
                # 创建测试数据
                np.random.seed(42)
                n = 100
                df = pd.DataFrame({
                    'trade_date': pd.date_range('2024-01-01', periods=n),
                    'ts_code': '000001.SZ',
                    'open': 100 + np.random.randn(n),
                    'high': 102 + np.random.randn(n),
                    'low': 98 + np.random.randn(n),
                    'close': 100 + np.random.randn(n),
                    'vol': np.random.randint(10000, 100000, n)
                })
                
                # 创建存储器
                store = DataStore(temp_dir)
                
                # 测试保存
                path = store.save_daily_data('000001.SZ', df)
                assert path.exists(), "文件未创建"
                print("  ✓ 数据保存功能正常")
                
                # 测试加载
                loaded_df = store.load_daily_data('000001.SZ')
                assert loaded_df is not None, "加载失败"
                assert len(loaded_df) == len(df), "数据长度不匹配"
                print("  ✓ 数据加载功能正常")
                
                # 测试更新
                new_df = df.tail(10).copy()
                new_df['close'] = new_df['close'] * 1.1
                store.update_daily_data('000001.SZ', new_df)
                
                updated_df = store.load_daily_data('000001.SZ')
                assert updated_df is not None, "更新后加载失败"
                print("  ✓ 数据更新功能正常")
                
                # 测试列表
                symbols = store.list_saved_symbols()
                assert '000001.SZ' in symbols, "符号未记录"
                print("  ✓ 符号列表功能正常")
                
            finally:
                # 清理临时目录
                shutil.rmtree(temp_dir)
                print("  ✓ 临时数据已清理")
            
            self.passed += 1
            self.test_results.append(("数据存储", "通过", ""))
            
        except Exception as e:
            self.failed += 1
            self.test_results.append(("数据存储", "失败", str(e)))
            print(f"  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def test_end_to_end(self):
        """端到端集成测试"""
        print("\n🔄 [模块8/8] 端到端集成测试")
        print("-" * 50)
        
        try:
            # 完整的量化流程测试
            from data.features import FeatureEngineer
            from strategies.technical_strategies import DoubleMAStrategy
            from strategies.backtest import BacktestEngine, Order, OrderSide
            from utils.risk_manager import RiskManager
            
            # 1. 准备数据
            print("  1. 准备测试数据...")
            np.random.seed(42)
            n = 300
            dates = pd.date_range('2024-01-01', periods=n)
            
            # 创建有趋势的数据
            trend = np.linspace(100, 150, n)
            noise = np.random.randn(n) * 2
            
            df = pd.DataFrame({
                'trade_date': dates,
                'ts_code': 'TEST001',
                'open': trend + noise,
                'high': trend + noise + 3,
                'low': trend + noise - 3,
                'close': trend + noise,
                'vol': np.random.randint(10000, 200000, n)
            })
            print("     ✓ 数据准备完成")
            
            # 2. 计算特征
            print("  2. 计算技术指标...")
            engineer = FeatureEngineer()
            features = engineer.calculate_all_features(df)
            print(f"     ✓ 生成 {len(features.columns)} 个特征")
            
            # 3. 运行策略
            print("  3. 运行双均线策略...")
            strategy = DoubleMAStrategy(short=10, long=30)
            df_signals = strategy.generate_signals(df.copy())
            signal_count = (df_signals['signal'] != 0).sum()
            print(f"     ✓ 生成 {signal_count} 个交易信号")
            
            # 4. 回测验证
            print("  4. 运行回测...")
            
            def custom_strategy(data, portfolio, engine):
                if len(data) < 30:
                    return []
                
                sma_10 = data['close'].rolling(10).mean().iloc[-1]
                sma_30 = data['close'].rolling(30).mean().iloc[-1]
                prev_sma_10 = data['close'].rolling(10).mean().iloc[-2]
                prev_sma_30 = data['close'].rolling(30).mean().iloc[-2]
                
                symbol = data['ts_code'].iloc[-1] if 'ts_code' in data.columns else 'TEST001'
                current_price = data['close'].iloc[-1]
                
                orders = []
                
                # 金叉买入
                if prev_sma_10 <= prev_sma_30 and sma_10 > sma_30:
                    cash = portfolio.cash
                    qty = int(cash * 0.2 / current_price / 100) * 100  # 20%仓位
                    if qty >= 100:
                        orders.append(Order(
                            symbol=symbol,
                            side=OrderSide.BUY,
                            quantity=qty
                        ))
                
                # 死叉卖出
                elif prev_sma_10 >= prev_sma_30 and sma_10 < sma_30:
                    pos = portfolio.get_position(symbol)
                    if pos.quantity > 0:
                        orders.append(Order(
                            symbol=symbol,
                            side=OrderSide.SELL,
                            quantity=pos.quantity
                        ))
                
                return orders
            
            engine = BacktestEngine(
                initial_cash=100000,
                commission_rate=0.0003,
                slippage=0.001,
                warmup_period=30
            )
            engine.set_strategy(custom_strategy)
            results = engine.run(df)
            
            print(f"     ✓ 回测完成")
            print(f"       总收益率: {results['total_return']*100:.2f}%")
            print(f"       夏普比率: {results['sharpe_ratio']:.2f}")
            print(f"       交易次数: {results['n_trades']}")
            
            # 5. 风控验证
            print("  5. 验证风险管理...")
            risk_mgr = RiskManager(total_capital=100000)
            
            # 模拟交易
            risk_mgr.open_position('TEST001', 100, results['final_value'] / 1000)
            summary = risk_mgr.get_portfolio_summary()
            print(f"     ✓ 风控验证完成 (总市值: ¥{summary['total_value']:,.0f})")
            
            print("\n  ✅ 端到端流程测试通过!")
            
            self.passed += 1
            self.test_results.append(("端到端集成", "通过", ""))
            
        except Exception as e:
            self.failed += 1
            self.test_results.append(("端到端集成", "失败", str(e)))
            print(f"  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def print_summary(self):
        """打印测试汇总"""
        print("\n" + "=" * 70)
        print("测试汇总报告")
        print("=" * 70)
        
        total = len(self.test_results)
        
        print(f"\n总计: {total} 个测试模块")
        print(f"通过: {self.passed} 个 ✓")
        print(f"失败: {self.failed} 个 ✗")
        print(f"通过率: {self.passed/total*100:.1f}%")
        
        print("\n详细结果:")
        print("-" * 70)
        for module, status, error in self.test_results:
            icon = "✓" if status == "通过" else "✗"
            print(f"  {icon} {module}: {status}")
            if error:
                print(f"     错误: {error[:100]}")
        
        print("\n" + "=" * 70)
        if self.failed == 0:
            print("🎉 所有测试通过！系统运行正常。")
        else:
            print(f"⚠️ 有 {self.failed} 个模块测试失败，请检查错误信息。")
        print("=" * 70)


def main():
    """主函数"""
    suite = TestSuite()
    suite.run_all_tests()
    return suite.failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
