#!/usr/bin/env python3
"""
AI机器学习策略
使用LSTM、XGBoost等模型预测价格走势
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureEngine:
    """
    特征工程
    构建机器学习所需的特征
    """
    
    def __init__(self):
        self.feature_names = []
    
    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        创建技术指标特征
        """
        features = pd.DataFrame(index=df.index)
        
        # 价格特征
        features['returns'] = df['close'].pct_change()
        features['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # 移动平均线
        for window in [5, 10, 20, 60]:
            features[f'ma_{window}'] = df['close'].rolling(window=window).mean()
            features[f'ma_ratio_{window}'] = df['close'] / features[f'ma_{window}']
        
        # 波动率特征
        for window in [5, 20]:
            features[f'volatility_{window}'] = features['returns'].rolling(window=window).std()
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        features['rsi'] = 100 - (100 / (1 + gain / loss))
        
        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        features['macd'] = ema12 - ema26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        
        # 成交量特征
        features['volume_ma'] = df['volume'].rolling(window=20).mean()
        features['volume_ratio'] = df['volume'] / features['volume_ma']
        
        # 价格位置
        features['high_low_ratio'] = (df['close'] - df['low']) / (df['high'] - df['low'] + 1e-10)
        
        self.feature_names = features.columns.tolist()
        return features
    
    def create_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 2, 3, 5]) -> pd.DataFrame:
        """
        创建滞后特征
        """
        features = pd.DataFrame(index=df.index)
        
        for lag in lags:
            features[f'returns_lag_{lag}'] = df['returns'].shift(lag)
            features[f'volume_lag_{lag}'] = df['volume_ratio'].shift(lag)
        
        return features
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        准备完整特征集
        """
        tech_features = self.create_technical_features(df)
        lag_features = self.create_lag_features(tech_features)
        
        all_features = pd.concat([tech_features, lag_features], axis=1)
        
        # 目标变量: 未来N日收益率
        all_features['target'] = df['close'].pct_change(5).shift(-5)
        
        # 移除NaN
        all_features = all_features.dropna()
        
        return all_features


class LSTMStrategy:
    """
    LSTM深度学习策略
    
    使用LSTM神经网络预测未来价格走势
    """
    
    def __init__(self, sequence_length: int = 60, n_features: int = 20):
        """
        初始化LSTM策略
        
        Args:
            sequence_length: 输入序列长度，默认60
            n_features: 特征数量
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = None
        self.scaler = None
        
    def prepare_sequences(self, data: np.ndarray) -> tuple:
        """
        准备LSTM所需的序列数据
        
        Returns:
            X: 输入序列 (samples, sequence_length, features)
            y: 目标值
        """
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:(i + self.sequence_length)])
            y.append(data[i + self.sequence_length, 0])  # 假设第一列是目标
        
        return np.array(X), np.array(y)
    
    def predict(self, recent_data: pd.DataFrame) -> Dict:
        """
        预测未来走势
        
        Returns:
            预测结果字典
        """
        # 这里简化处理，实际应加载训练好的模型
        # 返回基于近期趋势的信号
        
        returns = recent_data['close'].pct_change().dropna()
        
        # 简单动量预测
        momentum = returns.rolling(window=20).mean().iloc[-1]
        
        signal = 0
        if momentum > 0.02:
            signal = 1  # 买入
        elif momentum < -0.02:
            signal = -1  # 卖出
        
        return {
            'signal': signal,
            'momentum': momentum,
            'confidence': min(abs(momentum) * 10, 1.0)
        }


class XGBoostStrategy:
    """
    XGBoost机器学习策略
    
    使用XGBoost进行价格方向预测
    """
    
    def __init__(self):
        self.model = None
        self.feature_engine = FeatureEngine()
        
    def train(self, df: pd.DataFrame) -> 'XGBoostStrategy':
        """
        训练模型（简化版）
        """
        try:
            import xgboost as xgb
            
            # 准备特征
            features_df = self.feature_engine.prepare_features(df)
            
            X = features_df.drop('target', axis=1)
            y = (features_df['target'] > 0).astype(int)  # 分类：涨/跌
            
            # 训练XGBoost
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            self.model.fit(X, y)
            
            logger.info("XGBoost模型训练完成")
            
        except ImportError:
            logger.warning("XGBoost未安装，使用简化版本")
            self.model = None
        
        return self
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """
        预测未来涨跌
        """
        if self.model is None:
            # 简化版本：基于技术指标判断
            features = self.feature_engine.create_technical_features(df)
            
            # 综合多个指标
            rsi = features['rsi'].iloc[-1]
            macd = features['macd'].iloc[-1]
            macd_signal = features['macd_signal'].iloc[-1]
            
            score = 0
            if rsi < 40: score += 1
            if rsi > 60: score -= 1
            if macd > macd_signal: score += 1
            if macd < macd_signal: score -= 1
            
            if score >= 1:
                signal = 1
            elif score <= -1:
                signal = -1
            else:
                signal = 0
            
            return {
                'signal': signal,
                'score': score,
                'rsi': rsi,
                'macd_diff': macd - macd_signal
            }
        
        # 使用训练好的模型预测
        features = self.feature_engine.create_technical_features(df)
        X = features.iloc[-1:].values
        
        prediction = self.model.predict(X)[0]
        probability = self.model.predict_proba(X)[0]
        
        return {
            'signal': 1 if prediction == 1 else -1,
            'probability_up': probability[1],
            'confidence': max(probability)
        }


class EnsembleStrategy:
    """
    集成策略
    综合多个策略的信号进行决策
    """
    
    def __init__(self, strategies: List[Dict] = None):
        """
        初始化集成策略
        
        Args:
            strategies: 策略配置列表
        """
        self.strategies = strategies or [
            {'name': 'macd', 'weight': 0.3, 'params': {}},
            {'name': 'rsi', 'weight': 0.2, 'params': {}},
            {'name': 'double_ma', 'weight': 0.3, 'params': {'short': 5, 'long': 20}},
            {'name': 'bollinger', 'weight': 0.2, 'params': {}},
        ]
        
    def combine_signals(self, signals: Dict[str, int]) -> Dict:
        """
        综合多个策略信号
        
        Args:
            signals: 各策略的信号字典
            
        Returns:
            综合决策
        """
        weighted_score = 0
        
        for strategy_config in self.strategies:
            name = strategy_config['name']
            weight = strategy_config['weight']
            
            if name in signals:
                weighted_score += signals[name] * weight
        
        # 决策
        if weighted_score >= 0.3:
            final_signal = 1
        elif weighted_score <= -0.3:
            final_signal = -1
        else:
            final_signal = 0
        
        return {
            'signal': final_signal,
            'weighted_score': weighted_score,
            'individual_signals': signals
        }


# 策略配置模板
AI_STRATEGY_CONFIGS = {
    'lstm_trend': {
        'class': LSTMStrategy,
        'params': {'sequence_length': 60},
        'description': 'LSTM趋势预测策略'
    },
    'xgboost_direction': {
        'class': XGBoostStrategy,
        'params': {},
        'description': 'XGBoost方向预测策略'
    },
    'ensemble_vote': {
        'class': EnsembleStrategy,
        'params': {},
        'description': '多策略投票集成'
    },
}
