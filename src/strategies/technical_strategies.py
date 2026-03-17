#!/usr/bin/env python3
"""
技术指标策略集合
MACD、RSI、双均线、布林带等经典策略
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MACDStrategy:
    """
    MACD策略
    
    原理:
    - DIF = EMA(12) - EMA(26)
    - DEA = EMA(DIF, 9)
    - MACD = 2 * (DIF - DEA)
    
    信号:
    - DIF上穿DEA (金叉): 买入
    - DIF下穿DEA (死叉): 卖出
    - 顶背离: 价格新高但MACD未新高 → 卖出信号
    - 底背离: 价格新低但MACD未新低 → 买入信号
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        初始化MACD策略
        
        Args:
            fast: 快线周期，默认12
            slow: 慢线周期，默认26
            signal: 信号线周期，默认9
        """
        self.fast = fast
        self.slow = slow
        self.signal = signal
        
    def calculate_macd(self, close: pd.Series) -> pd.DataFrame:
        """计算MACD指标"""
        ema_fast = close.ewm(span=self.fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow, adjust=False).mean()
        
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=self.signal, adjust=False).mean()
        macd = 2 * (dif - dea)
        
        return pd.DataFrame({
            'DIF': dif,
            'DEA': dea,
            'MACD': macd
        })
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Returns:
            DataFrame with 'signal' column (1:买入, -1:卖出, 0:持有)
        """
        close = df['close']
        macd_df = self.calculate_macd(close)
        
        df['DIF'] = macd_df['DIF']
        df['DEA'] = macd_df['DEA']
        df['MACD'] = macd_df['MACD']
        
        # 金叉/死叉信号
        df['signal'] = 0
        # 金叉: DIF上穿DEA
        golden_cross = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
        # 死叉: DIF下穿DEA
        death_cross = (df['DIF'] < df['DEA']) & (df['DIF'].shift(1) >= df['DEA'].shift(1))
        
        df.loc[golden_cross, 'signal'] = 1
        df.loc[death_cross, 'signal'] = -1
        
        # 背离检测
        df['divergence'] = self.detect_divergence(df)
        
        return df
    
    def detect_divergence(self, df: pd.DataFrame, window: int = 20) -> pd.Series:
        """
        检测顶背离和底背离
        
        Returns:
            Series: 1(顶背离/卖出), -1(底背离/买入), 0(无背离)
        """
        divergence = pd.Series(0, index=df.index)
        
        for i in range(window, len(df)):
            price_window = df['close'].iloc[i-window:i]
            macd_window = df['MACD'].iloc[i-window:i]
            
            # 顶背离: 价格新高，MACD未新高
            if price_window.iloc[-1] > price_window.max() * 0.98:
                if macd_window.iloc[-1] < macd_window.max() * 0.95:
                    divergence.iloc[i] = 1
            
            # 底背离: 价格新低，MACD未新低
            if price_window.iloc[-1] < price_window.min() * 1.02:
                if macd_window.iloc[-1] > macd_window.min() * 1.05:
                    divergence.iloc[i] = -1
        
        return divergence


class RSIStrategy:
    """
    RSI相对强弱指数策略
    
    原理:
    - RSI = 100 - 100/(1 + RS)
    - RS = 平均上涨幅度 / 平均下跌幅度
    
    信号:
    - RSI < 30: 超卖，买入信号
    - RSI > 70: 超买，卖出信号
    - 30 < RSI < 70: 观望
    
    优化:
    - 结合趋势判断，牛市RSI>50，熊市RSI<50
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        """
        初始化RSI策略
        
        Args:
            period: RSI计算周期，默认14
            oversold: 超卖阈值，默认30
            overbought: 超买阈值，默认70
        """
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def calculate_rsi(self, close: pd.Series) -> pd.Series:
        """计算RSI指标"""
        delta = close.diff()
        
        gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df['RSI'] = self.calculate_rsi(df['close'])
        
        df['signal'] = 0
        
        # 超卖买入
        oversold_condition = (df['RSI'] < self.oversold) & (df['RSI'].shift(1) >= self.oversold)
        df.loc[oversold_condition, 'signal'] = 1
        
        # 超买卖出
        overbought_condition = (df['RSI'] > self.overbought) & (df['RSI'].shift(1) <= self.overbought)
        df.loc[overbought_condition, 'signal'] = -1
        
        # 添加趋势判断
        df['trend'] = self.detect_trend(df)
        
        return df
    
    def detect_trend(self, df: pd.DataFrame) -> pd.Series:
        """
        检测趋势方向
        使用60日均线判断
        """
        ma60 = df['close'].rolling(window=60).mean()
        trend = pd.Series(0, index=df.index)
        trend[df['close'] > ma60] = 1  # 牛市
        trend[df['close'] < ma60] = -1  # 熊市
        return trend


class DoubleMAStrategy:
    """
    双均线策略
    
    原理:
    - 短期均线上穿长期均线 (金叉): 买入
    - 短期均线下穿长期均线 (死叉): 卖出
    
    参数优化:
    - 短线: 5日、10日
    - 中长线: 20日、60日
    """
    
    def __init__(self, short: int = 5, long: int = 20):
        """
        初始化双均线策略
        
        Args:
            short: 短期均线周期，默认5
            long: 长期均线周期，默认20
        """
        self.short = short
        self.long = long
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df[f'MA{self.short}'] = df['close'].rolling(window=self.short).mean()
        df[f'MA{self.long}'] = df['close'].rolling(window=self.long).mean()
        
        df['signal'] = 0
        
        # 金叉: 短均线上穿长均线
        golden_cross = (df[f'MA{self.short}'] > df[f'MA{self.long}']) & \
                      (df[f'MA{self.short}'].shift(1) <= df[f'MA{self.long}'].shift(1))
        
        # 死叉: 短均线下穿长均线
        death_cross = (df[f'MA{self.short}'] < df[f'MA{self.long}']) & \
                     (df[f'MA{self.short}'].shift(1) >= df[f'MA{self.long}'].shift(1))
        
        df.loc[golden_cross, 'signal'] = 1
        df.loc[death_cross, 'signal'] = -1
        
        return df


class BollingerBandsStrategy:
    """
    布林带策略
    
    原理:
    - 中轨 = N日移动平均线
    - 上轨 = 中轨 + k * 标准差
    - 下轨 = 中轨 - k * 标准差
    
    信号:
    - 价格触及下轨: 买入 (超卖)
    - 价格触及上轨: 卖出 (超买)
    - 价格突破中轨: 趋势确认
    
    布林带 squeeze: 带宽收窄预示大行情
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        初始化布林带策略
        
        Args:
            period: 计算周期，默认20
            std_dev: 标准差倍数，默认2.0
        """
        self.period = period
        self.std_dev = std_dev
    
    def calculate_bands(self, close: pd.Series) -> pd.DataFrame:
        """计算布林带"""
        middle = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()
        
        upper = middle + self.std_dev * std
        lower = middle - self.std_dev * std
        
        # 带宽百分比 (%B)
        percent_b = (close - lower) / (upper - lower)
        
        # 带宽 (Bandwidth)
        bandwidth = (upper - lower) / middle
        
        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'percent_b': percent_b,
            'bandwidth': bandwidth
        })
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        bands = self.calculate_bands(df['close'])
        df = pd.concat([df, bands], axis=1)
        
        df['signal'] = 0
        
        # 触及下轨买入
        buy_condition = (df['close'] <= df['lower'] * 1.01) & \
                       (df['close'].shift(1) > df['lower'].shift(1) * 1.01)
        
        # 触及上轨卖出
        sell_condition = (df['close'] >= df['upper'] * 0.99) & \
                        (df['close'].shift(1) < df['upper'].shift(1) * 0.99)
        
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        # Squeeze检测 (带宽收窄)
        df['squeeze'] = df['bandwidth'] < df['bandwidth'].rolling(window=120).min() * 1.05
        
        return df


class GridTradingStrategy:
    """
    网格交易策略
    
    原理:
    - 在价格区间内设置多个网格
    - 价格下跌到网格线买入
    - 价格上涨到网格线卖出
    - 适合震荡行情
    
    参数:
    - 价格区间 [lower, upper]
    - 网格数量 n
    - 每格资金投入
    """
    
    def __init__(self, lower_price: float, upper_price: float, grid_num: int = 10):
        """
        初始化网格策略
        
        Args:
            lower_price: 价格区间下限
            upper_price: 价格区间上限
            grid_num: 网格数量，默认10
        """
        self.lower_price = lower_price
        self.upper_price = upper_price
        self.grid_num = grid_num
        self.grids = self._create_grids()
        
    def _create_grids(self) -> np.ndarray:
        """创建网格线"""
        return np.linspace(self.lower_price, self.upper_price, self.grid_num + 1)
    
    def get_grid_level(self, price: float) -> int:
        """
        获取当前价格所在网格层级
        
        Returns:
            网格层级 (0到grid_num)
        """
        for i in range(len(self.grids) - 1):
            if self.grids[i] <= price <= self.grids[i + 1]:
                return i
        return 0 if price < self.grids[0] else self.grid_num
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成网格交易信号
        
        需要记录上一个价格所在的网格，判断是否需要交易
        """
        df['grid_level'] = df['close'].apply(self.get_grid_level)
        df['grid_line'] = df['grid_level'].apply(lambda x: self.grids[x])
        
        df['signal'] = 0
        
        # 向下突破网格线买入
        for i in range(1, len(df)):
            if df['grid_level'].iloc[i] > df['grid_level'].iloc[i-1]:
                df.loc[df.index[i], 'signal'] = -1  # 卖出
            elif df['grid_level'].iloc[i] < df['grid_level'].iloc[i-1]:
                df.loc[df.index[i], 'signal'] = 1  # 买入
        
        return df
    
    def calculate_grid_profit(self, price_changes: int) -> float:
        """
        计算网格收益
        
        Args:
            price_changes: 价格穿越的网格数
            
        Returns:
            收益率
        """
        grid_size = (self.upper_price - self.lower_price) / self.grid_num
        profit_per_grid = grid_size / ((self.upper_price + self.lower_price) / 2)
        return profit_per_grid * abs(price_changes)


# 策略工厂
STRATEGY_MAP = {
    'macd': MACDStrategy,
    'rsi': RSIStrategy,
    'double_ma': DoubleMAStrategy,
    'bollinger': BollingerBandsStrategy,
    'grid': GridTradingStrategy,
}

def create_strategy(name: str, **kwargs):
    """
    创建策略实例
    
    Args:
        name: 策略名称
        **kwargs: 策略参数
        
    Returns:
        策略实例
    """
    if name not in STRATEGY_MAP:
        raise ValueError(f"未知策略: {name}，可用策略: {list(STRATEGY_MAP.keys())}")
    
    return STRATEGY_MAP[name](**kwargs)
