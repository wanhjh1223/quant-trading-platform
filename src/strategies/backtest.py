"""
回测引擎 - 事件驱动回测
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import datetime
from enum import Enum

import pandas as pd
import numpy as np
from loguru import logger


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """订单"""
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None
    timestamp: Optional[datetime] = None
    order_id: Optional[str] = None


@dataclass
class Trade:
    """成交记录"""
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0
    order_id: Optional[str] = None


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: float = 0.0
    avg_cost: float = 0.0
    
    @property
    def market_value(self, current_price: float = None) -> float:
        if current_price is None:
            return 0.0
        return self.quantity * current_price
    
    @property
    def unrealized_pnl(self, current_price: float = None) -> float:
        if current_price is None or self.quantity == 0:
            return 0.0
        return self.quantity * (current_price - self.avg_cost)


@dataclass
class Portfolio:
    """投资组合"""
    initial_cash: float = 1000000.0
    cash: float = 1000000.0
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    
    def get_position(self, symbol: str) -> Position:
        """获取持仓"""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]
    
    def update_position(self, trade: Trade):
        """更新持仓"""
        pos = self.get_position(trade.symbol)
        
        if trade.side == OrderSide.BUY:
            # 买入 - 更新平均成本
            total_cost = pos.quantity * pos.avg_cost + trade.quantity * trade.price
            pos.quantity += trade.quantity
            if pos.quantity > 0:
                pos.avg_cost = total_cost / pos.quantity
            self.cash -= trade.quantity * trade.price + trade.commission
        else:
            # 卖出
            pos.quantity -= trade.quantity
            self.cash += trade.quantity * trade.price - trade.commission
        
        self.trades.append(trade)
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """获取总资产价值"""
        position_value = sum(
            pos.quantity * current_prices.get(symbol, 0)
            for symbol, pos in self.positions.items()
        )
        return self.cash + position_value


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        initial_cash: float = 1000000.0,
        commission_rate: float = 0.0003,  # 佣金率 0.03%
        slippage: float = 0.0,  # 滑点
        warmup_period: int = 60  # 预热期
    ):
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.warmup_period = warmup_period
        
        self.portfolio: Optional[Portfolio] = None
        self.current_data: Optional[pd.DataFrame] = None
        self.current_idx: int = 0
        self.orders: List[Order] = []
        
        # 记录每日净值
        self.daily_values: List[Dict] = []
        
        # 策略回调
        self.strategy: Optional[Callable] = None
    
    def set_strategy(self, strategy: Callable):
        """
        设置策略函数
        
        策略函数签名: strategy(data, portfolio, engine) -> List[Order]
        """
        self.strategy = strategy
    
    def run(self, data: pd.DataFrame) -> Dict:
        """
        运行回测
        
        Args:
            data: DataFrame包含OHLCV数据，按时间排序
        
        Returns:
            回测结果字典
        """
        self.portfolio = Portfolio(initial_cash=self.initial_cash, cash=self.initial_cash)
        self.current_data = data.reset_index(drop=True)
        self.daily_values = []
        self.orders = []
        
        logger.info(f"开始回测: {len(data)} 个时间步")
        
        # 遍历每个时间点
        for i in range(len(self.current_data)):
            self.current_idx = i
            
            # 跳过预热期
            if i < self.warmup_period:
                continue
            
            # 获取当前数据切片（包含历史）
            lookback_data = self.current_data.iloc[:i+1]
            current_bar = self.current_data.iloc[i]
            
            # 执行策略
            if self.strategy:
                try:
                    orders = self.strategy(
                        lookback_data,
                        self.portfolio,
                        self
                    )
                    if orders:
                        for order in orders:
                            self.submit_order(order, current_bar)
                except Exception as e:
                    logger.error(f"策略执行错误 at {i}: {e}")
            
            # 记录每日净值
            current_prices = {current_bar.get('ts_code', 'unknown'): current_bar['close']}
            total_value = self.portfolio.get_total_value(current_prices)
            
            self.daily_values.append({
                'timestamp': current_bar.get('trade_date', i),
                'cash': self.portfolio.cash,
                'total_value': total_value,
                'returns': (total_value - self.initial_cash) / self.initial_cash
            })
        
        logger.info("回测完成")
        return self.get_results()
    
    def submit_order(self, order: Order, current_bar: pd.Series):
        """提交订单并执行"""
        symbol = order.symbol
        price = current_bar['close']
        
        # 应用滑点
        if order.side == OrderSide.BUY:
            executed_price = price * (1 + self.slippage)
        else:
            executed_price = price * (1 - self.slippage)
        
        # 计算佣金
        commission = order.quantity * executed_price * self.commission_rate
        
        # 创建成交记录
        trade = Trade(
            symbol=symbol,
            side=order.side,
            quantity=order.quantity,
            price=executed_price,
            timestamp=current_bar.get('trade_date', datetime.now()),
            commission=commission,
            order_id=order.order_id
        )
        
        # 更新持仓
        self.portfolio.update_position(trade)
    
    def get_results(self) -> Dict:
        """获取回测结果"""
        if not self.daily_values:
            return {}
        
        values_df = pd.DataFrame(self.daily_values)
        
        # 计算绩效指标
        total_return = (values_df['total_value'].iloc[-1] - self.initial_cash) / self.initial_cash
        
        # 年化收益率
        n_days = len(values_df)
        annual_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
        
        # 最大回撤
        cummax = values_df['total_value'].cummax()
        drawdown = (values_df['total_value'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 夏普比率（简化版，假设无风险利率为0）
        daily_returns = values_df['total_value'].pct_change().dropna()
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if len(daily_returns) > 0 else 0
        
        # 交易统计
        n_trades = len(self.portfolio.trades)
        
        return {
            'initial_cash': self.initial_cash,
            'final_value': values_df['total_value'].iloc[-1],
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'n_trades': n_trades,
            'daily_values': values_df,
            'trades': self.portfolio.trades
        }


# 示例策略模板
def example_strategy(data: pd.DataFrame, portfolio: Portfolio, engine: BacktestEngine) -> List[Order]:
    """
    示例策略：双均线交叉
    
    当短期均线上穿长期均线时买入，下穿时卖出
    """
    if len(data) < 60:
        return []
    
    orders = []
    symbol = data['ts_code'].iloc[-1] if 'ts_code' in data.columns else 'UNKNOWN'
    current_price = data['close'].iloc[-1]
    
    # 计算均线
    sma_20 = data['close'].rolling(20).mean().iloc[-1]
    sma_60 = data['close'].rolling(60).mean().iloc[-1]
    
    prev_sma_20 = data['close'].rolling(20).mean().iloc[-2]
    prev_sma_60 = data['close'].rolling(60).mean().iloc[-2]
    
    position = portfolio.get_position(symbol)
    
    # 金叉买入
    if prev_sma_20 <= prev_sma_60 and sma_20 > sma_60 and position.quantity == 0:
        quantity = 100  # 买入100股
        orders.append(Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity
        ))
    
    # 死叉卖出
    elif prev_sma_20 >= prev_sma_60 and sma_20 < sma_60 and position.quantity > 0:
        orders.append(Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=position.quantity
        ))
    
    return orders
