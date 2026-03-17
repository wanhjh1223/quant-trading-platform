# 量化交易平台 - 使用指南

## 目录
1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [策略使用](#策略使用)
4. [回测系统](#回测系统)
5. [实盘交易](#实盘交易)
6. [风险控制](#风险控制)
7. [API参考](#api参考)
8. [常见问题](#常见问题)

---

## 系统概述

### 功能特性
- **数据层**: 自动获取A股实时/历史数据
- **特征工程**: 技术指标、多因子模型
- **回测引擎**: 事件驱动回测，支持滑点、佣金
- **策略库**: 内置多种经典策略
- **AI预测**: LSTM、XGBoost机器学习
- **实盘交易**: 富途OpenAPI接口
- **风险控制**: 仓位管理、止损止盈
- **Web界面**: 实时监控与可视化

### 系统架构
```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (WebUI)                       │
├─────────────────────────────────────────────────────────────┤
│    策略层    │    回测引擎    │    风控模块    │   AI模型   │
├─────────────────────────────────────────────────────────────┤
│              数据层 (股票数据/财务数据/宏观数据)               │
├─────────────────────────────────────────────────────────────┤
│              交易接口 (富途/模拟/回测)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 环境安装

```bash
# 克隆仓库
git clone https://github.com/wanhjh1223/quant-trading-platform.git
cd quant-trading-platform

# 安装依赖
pip install -r requirements.txt

# 启动Web界面
python src/web/app.py
```

### 2. 快速回测示例

```python
from src.backtest.engine import BacktestEngine
from src.strategies.technical_strategies import MACDStrategy

# 创建策略
strategy = MACDStrategy(fast=12, slow=26, signal=9)

# 创建回测引擎
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,  # 佣金0.1%
    slippage=0.002     # 滑点0.2%
)

# 运行回测
result = engine.run(
    stock_code='000001.SZ',
    start_date='2023-01-01',
    end_date='2024-01-01',
    strategy=strategy
)

# 查看结果
print(f"总收益率: {result.total_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
print(f"最大回撤: {result.max_drawdown:.2%}")
```

---

## 策略使用

### 1. 技术指标策略

#### MACD策略
```python
from src.strategies.technical_strategies import MACDStrategy

strategy = MACDStrategy(
    fast=12,    # 快线周期
    slow=26,    # 慢线周期
    signal=9    # 信号线周期
)
```

**信号说明**:
- 金叉(DIF上穿DEA): 买入信号 (+1)
- 死叉(DIF下穿DEA): 卖出信号 (-1)
- 顶背离: 价格新高但MACD未新高 → 卖出
- 底背离: 价格新低但MACD未新低 → 买入

#### RSI策略
```python
from src.strategies.technical_strategies import RSIStrategy

strategy = RSIStrategy(
    period=14,       # RSI计算周期
    oversold=30,     # 超卖阈值
    overbought=70    # 超买阈值
)
```

#### 双均线策略
```python
from src.strategies.technical_strategies import DoubleMAStrategy

strategy = DoubleMAStrategy(
    short=5,   # 短期均线
    long=20    # 长期均线
)

# 其他常用组合
# 短线: short=5, long=10
# 中线: short=10, long=30
# 长线: short=20, long=60
```

#### 布林带策略
```python
from src.strategies.technical_strategies import BollingerBandsStrategy

strategy = BollingerBandsStrategy(
    period=20,     # 计算周期
    std_dev=2.0    # 标准差倍数
)
```

#### 网格交易策略
```python
from src.strategies.technical_strategies import GridTradingStrategy

strategy = GridTradingStrategy(
    lower_price=10.0,   # 价格下限
    upper_price=20.0,   # 价格上限
    grid_num=10         # 网格数量
)
```

### 2. 多因子选股策略

```python
from src.strategies.multi_factor_strategy import MultiFactorStrategy

# 创建多因子策略
strategy = MultiFactorStrategy(
    weights={
        'value': 0.25,      # 价值因子
        'momentum': 0.25,   # 动量因子
        'quality': 0.25,    # 质量因子
        'growth': 0.25      # 成长因子
    }
)

# 预配置模板
from src.strategies.multi_factor_strategy import STRATEGY_TEMPLATES

# 价值投资风格
value_strategy = MultiFactorStrategy(STRATEGY_TEMPLATES['价值投资'])

# 趋势跟踪风格
trend_strategy = MultiFactorStrategy(STRATEGY_TEMPLATES['趋势跟踪'])
```

**因子说明**:
- **价值因子**: PE、PB倒数，低估值得分高
- **动量因子**: 60日收益率 + RSI优化
- **质量因子**: ROE、ROA、毛利率
- **成长因子**: 营收增速、利润增速

### 3. AI机器学习策略

```python
from src.strategies.ai_strategies import XGBoostStrategy, LSTMStrategy

# XGBoost策略
xgb_strategy = XGBoostStrategy()
xgb_strategy.train(historical_data)
prediction = xgb_strategy.predict(recent_data)

# LSTM策略
lstm_strategy = LSTMStrategy(sequence_length=60)
result = lstm_strategy.predict(recent_data)
```

### 4. 集成策略

```python
from src.strategies.ai_strategies import EnsembleStrategy

# 综合多个策略
ensemble = EnsembleStrategy([
    {'name': 'macd', 'weight': 0.3},
    {'name': 'rsi', 'weight': 0.2},
    {'name': 'double_ma', 'weight': 0.3},
    {'name': 'bollinger', 'weight': 0.2},
])

# 综合决策
result = ensemble.combine_signals({
    'macd': 1,
    'rsi': 0,
    'double_ma': 1,
    'bollinger': -1
})
```

---

## 回测系统

### 1. 基础回测

```python
from src.backtest.engine import BacktestEngine
from src.strategies.technical_strategies import DoubleMAStrategy

engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,      # 手续费
    slippage=0.001,        # 滑点
    risk_free_rate=0.03    # 无风险利率
)

result = engine.run_backtest(
    strategy=DoubleMAStrategy(short=5, long=20),
    symbol='000001.SZ',
    start_date='2023-01-01',
    end_date='2024-01-01',
    timeframe='1d'
)

# 查看回测结果
result.print_report()
result.plot()
```

### 2. 回测指标

| 指标 | 说明 | 参考值 |
|------|------|--------|
| 总收益率 | 策略整体收益 | > 基准收益 |
| 年化收益率 | 收益年化后 | > 15% |
| 夏普比率 | 风险调整后收益 | > 1.5 |
| 最大回撤 | 最大资金回落 | < 20% |
| 胜率 | 盈利交易占比 | > 50% |
| 盈亏比 | 平均盈利/平均亏损 | > 2.0 |
| 信息比率 | 超额收益稳定性 | > 0.5 |
| Beta | 系统性风险 | < 1.2 |

### 3. 参数优化

```python
from src.backtest.optimizer import GridSearchOptimizer

# 网格搜索参数优化
optimizer = GridSearchOptimizer(
    strategy_class=DoubleMAStrategy,
    param_grid={
        'short': [5, 10, 20],
        'long': [20, 30, 60]
    },
    metric='sharpe_ratio'
)

best_params = optimizer.optimize(
    symbol='000001.SZ',
    start_date='2023-01-01',
    end_date='2024-01-01'
)

print(f"最优参数: {best_params}")
```

---

## 实盘交易

### 1. 富途OpenAPI配置

```python
from src.trading.futu_trader import FutuTrader

# 初始化交易接口
trader = FutuTrader(
    host='127.0.0.1',
    port=11111,
    unlock_password='your_password'
)

# 连接到OpenD
trader.connect()

# 订阅行情
trader.subscribe(['00700.HK', 'AAPL.US'])

# 查询账户信息
account_info = trader.get_account_info()
print(f"可用资金: {account_info.cash}")
print(f"总市值: {account_info.total_assets}")
```

### 2. 下单交易

```python
# 市价单
trader.place_order(
    code='00700.HK',
    side='buy',
    quantity=100,
    order_type='market'
)

# 限价单
trader.place_order(
    code='00700.HK',
    side='sell',
    quantity=100,
    order_type='limit',
    price=380.0
)

# 查询持仓
positions = trader.get_positions()
for pos in positions:
    print(f"{pos.code}: {pos.quantity}股, 盈亏{pos.pnl:.2f}")
```

### 3. 自动化交易

```python
from src.trading.auto_trader import AutoTrader
from src.strategies.technical_strategies import MACDStrategy

# 创建自动化交易系统
auto_trader = AutoTrader(
    strategy=MACDStrategy(),
    trader=trader,
    symbols=['00700.HK', 'AAPL.US'],
    risk_manager=risk_manager
)

# 启动自动交易
auto_trader.start()

# 停止交易
auto_trader.stop()
```

---

## 风险控制

### 1. 仓位管理

```python
from src.risk.position_sizer import PositionSizer

# 固定仓位
sizer = PositionSizer(method='fixed', fixed_amount=10000)

# 百分比仓位
sizer = PositionSizer(method='percent', percent=0.1)

# ATR仓位管理
sizer = PositionSizer(
    method='atr',
    risk_percent=0.02,    # 单笔风险2%
    atr_multiplier=2.0
)

# 计算仓位
position_size = sizer.calculate(
    price=100,
    stop_loss=95,
    account_value=100000
)
```

### 2. 止损止盈

```python
from src.risk.stop_loss import StopLossManager

# 固定止损
stop_loss = StopLossManager(
    method='fixed',
    stop_percent=0.05   # 5%止损
)

# ATR止损
stop_loss = StopLossManager(
    method='atr',
    atr_period=14,
    atr_multiplier=2.0
)

# 移动止损
stop_loss = StopLossManager(
    method='trailing',
    trail_percent=0.10  # 10%移动止损
)

# 检查是否触发止损
if stop_loss.should_stop(entry_price=100, current_price=94):
    print("触发止损，执行平仓")
```

### 3. 风险监控

```python
from src.risk.risk_manager import RiskManager

risk_manager = RiskManager(
    max_position_percent=0.2,    # 单票最大20%
    max_sector_percent=0.5,      # 单行业最大50%
    max_drawdown=0.15,           # 最大回撤15%
    daily_loss_limit=0.03        # 日亏损限制3%
)

# 检查风险
risk_check = risk_manager.check_risk(
    portfolio=current_portfolio,
    new_order=proposed_order
)

if not risk_check.passed:
    print(f"风险警告: {risk_check.warnings}")
```

---

## API参考

### 数据获取API

```python
from src.data.data_loader import DataLoader

loader = DataLoader()

# 获取历史K线
df = loader.get_kline(
    symbol='000001.SZ',
    start='2023-01-01',
    end='2024-01-01',
    frequency='day'    # day/minute/weekly/monthly
)

# 获取财务数据
financials = loader.get_financial_data(
    symbol='000001.SZ',
    report_type='income_statement'  # income/balance/cashflow
)

# 获取实时行情
quote = loader.get_realtime_quote('000001.SZ')
```

### 特征工程API

```python
from src.features.technical_indicators import TechnicalIndicators

tech = TechnicalIndicators()

# 计算MACD
df = tech.macd(df, fast=12, slow=26, signal=9)

# 计算RSI
df = tech.rsi(df, period=14)

# 计算布林带
df = tech.bollinger_bands(df, period=20, std_dev=2.0)

# 计算所有指标
df = tech.calculate_all(df)
```

---

## 常见问题

### Q1: 如何添加新的策略?
```python
# 继承基类，实现generate_signals方法
from src.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signals(self, df):
        df['signal'] = 0
        # 实现你的逻辑
        return df
```

### Q2: 回测和实盘的区别?
- 回测使用历史数据，实盘使用实时数据
- 回测假设成交价格，实盘受滑点影响
- 回测速度可调，实盘按实时节奏

### Q3: 如何优化策略参数?
- 使用GridSearchOptimizer进行网格搜索
- 使用Walk Forward Analysis避免过拟合
- 在样本外数据上验证

### Q4: 系统性能如何?
- 支持多线程回测
- 数据缓存机制
- 增量更新支持

### Q5: 数据源有哪些?
- Tushare (A股)
- YFinance (美股)
- Futu API (港股/美股)
- 本地CSV文件

---

## 更新日志

### v1.0.0 (2026-03-17)
- 初始版本发布
- 支持多种技术指标策略
- 多因子选股模型
- AI机器学习策略
- 富途OpenAPI实盘交易
- Web可视化界面

---

## 联系方式

- GitHub: https://github.com/wanhjh1223/quant-trading-platform
- 邮箱: your-email@example.com

---

**免责声明**: 本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
