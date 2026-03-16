"""
技术指标计算模块
"""
from typing import Optional, List
import numpy as np
import pandas as pd
from loguru import logger


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def sma(close: pd.Series, window: int) -> pd.Series:
        """简单移动平均线"""
        return close.rolling(window=window).mean()
    
    @staticmethod
    def ema(close: pd.Series, window: int) -> pd.Series:
        """指数移动平均线"""
        return close.ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def rsi(close: pd.Series, window: int = 14) -> pd.Series:
        """
        RSI相对强弱指标
        
        Args:
            close: 收盘价序列
            window: 计算周期，默认14
        """
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD指标
        
        Returns:
            (macd_line, signal_line, histogram)
        """
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(
        close: pd.Series,
        window: int = 20,
        std_dev: float = 2.0
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        布林带
        
        Returns:
            (upper_band, middle_band, lower_band)
        """
        middle_band = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 14
    ) -> pd.Series:
        """
        ATR平均真实波幅
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        
        return atr
    
    @staticmethod
    def adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 14
    ) -> pd.Series:
        """
        ADX平均趋向指数
        """
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=window).mean()
        
        plus_di = 100 * plus_dm.rolling(window=window).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=window).mean() / atr
        
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=window).mean()
        
        return adx
    
    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """
        VWAP成交量加权平均价
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap
    
    @staticmethod
    def williams_r(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = 14
    ) -> pd.Series:
        """威廉指标"""
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        return williams_r
    
    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_window: int = 14,
        d_window: int = 3
    ) -> tuple[pd.Series, pd.Series]:
        """
        随机指标 (KDJ中的K和D)
        """
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_window).mean()
        
        return k, d


class FeatureEngineer:
    """特征工程器"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def calculate_all_features(
        self,
        df: pd.DataFrame,
        windows: List[int] = [5, 10, 20, 60]
    ) -> pd.DataFrame:
        """
        计算全部技术指标特征
        
        Args:
            df: 原始OHLCV数据
            windows: 移动平均窗口列表
        """
        features = df.copy()
        
        # 基础价格特征
        features['returns'] = df['close'].pct_change()
        features['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        features['volatility'] = features['returns'].rolling(window=20).std()
        
        # 移动平均线
        for window in windows:
            features[f'sma_{window}'] = self.indicators.sma(df['close'], window)
            features[f'ema_{window}'] = self.indicators.ema(df['close'], window)
            features[f'dist_sma_{window}'] = (df['close'] - features[f'sma_{window}']) / features[f'sma_{window}']
        
        # RSI
        features['rsi_14'] = self.indicators.rsi(df['close'], 14)
        features['rsi_6'] = self.indicators.rsi(df['close'], 6)
        
        # MACD
        macd_line, signal_line, histogram = self.indicators.macd(df['close'])
        features['macd'] = macd_line
        features['macd_signal'] = signal_line
        features['macd_histogram'] = histogram
        
        # 布林带
        upper, middle, lower = self.indicators.bollinger_bands(df['close'])
        features['bb_upper'] = upper
        features['bb_middle'] = middle
        features['bb_lower'] = lower
        features['bb_position'] = (df['close'] - lower) / (upper - lower)
        features['bb_width'] = (upper - lower) / middle
        
        # ATR
        features['atr_14'] = self.indicators.atr(df['high'], df['low'], df['close'], 14)
        features['atr_ratio'] = features['atr_14'] / df['close']
        
        # ADX
        features['adx'] = self.indicators.adx(df['high'], df['low'], df['close'], 14)
        
        # VWAP
        if 'vol' in df.columns or 'volume' in df.columns:
            vol_col = 'vol' if 'vol' in df.columns else 'volume'
            features['vwap'] = self.indicators.vwap(df['high'], df['low'], df['close'], df[vol_col])
            features['dist_vwap'] = (df['close'] - features['vwap']) / features['vwap']
        
        # 威廉指标
        features['williams_r'] = self.indicators.williams_r(df['high'], df['low'], df['close'])
        
        # 随机指标
        k, d = self.indicators.stochastic(df['high'], df['low'], df['close'])
        features['stoch_k'] = k
        features['stoch_d'] = d
        
        # 价格形态特征
        features['body'] = df['close'] - df['open']
        features['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        features['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        features['body_pct'] = abs(features['body']) / (df['high'] - df['low'])
        
        # 成交量特征
        if 'vol' in df.columns or 'volume' in df.columns:
            vol_col = 'vol' if 'vol' in df.columns else 'volume'
            features['vol_ma_20'] = df[vol_col].rolling(20).mean()
            features['vol_ratio'] = df[vol_col] / features['vol_ma_20']
        
        logger.info(f"特征计算完成: {len(features.columns)} 个特征")
        return features
    
    def select_features(
        self,
        df: pd.DataFrame,
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """选择特定特征子集"""
        if feature_names is None:
            # 默认排除原始OHLCV列
            exclude = ['open', 'high', 'low', 'close', 'vol', 'volume', 
                      'amount', 'trade_date', 'ts_code']
            feature_names = [c for c in df.columns if c not in exclude]
        
        return df[feature_names]
