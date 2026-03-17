#!/usr/bin/env python3
"""
多因子选股策略
结合价值、动量、质量、成长四大类因子
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class MultiFactorStrategy:
    """
    多因子选股策略
    
    因子权重配置:
    - 价值因子: PE、PB、PCF (低估值)
    - 动量因子: 收益率、RSI (趋势延续)
    - 质量因子: ROE、ROA、毛利率 (高质量)
    - 成长因子: 营收增速、利润增速 (高成长)
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        初始化多因子策略
        
        Args:
            weights: 因子权重字典，如 {'value': 0.25, 'momentum': 0.25, ...}
        """
        self.weights = weights or {
            'value': 0.25,
            'momentum': 0.25,
            'quality': 0.25,
            'growth': 0.25
        }
        
        # 验证权重和为1
        assert abs(sum(self.weights.values()) - 1.0) < 1e-6, "权重和必须等于1"
        
    def calculate_value_factor(self, df: pd.DataFrame) -> pd.Series:
        """
        计算价值因子
        使用EP(PE倒数)和BP(PB倒数)，值越大越好
        """
        # EP = 1/PE，PE越低越好
        ep = 1 / df['pe_ratio'].replace(0, np.nan)
        # BP = 1/PB，PB越低越好
        bp = 1 / df['pb_ratio'].replace(0, np.nan)
        
        # 合并价值因子
        value_factor = (ep.fillna(ep.median()) + bp.fillna(bp.median())) / 2
        return value_factor
    
    def calculate_momentum_factor(self, df: pd.DataFrame) -> pd.Series:
        """
        计算动量因子
        使用60日收益率和RSI
        """
        # 60日收益率
        returns_60d = df['close'].pct_change(60)
        
        # RSI计算 (14日)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 合并动量因子 (RSI在50附近最好，避免超买超卖)
        rsi_score = 100 - abs(rsi - 50) * 2  # RSI越接近50分数越高
        momentum_factor = (returns_60d.fillna(0) * 0.7 + rsi_score.fillna(50) * 0.3)
        
        return momentum_factor
    
    def calculate_quality_factor(self, df: pd.DataFrame) -> pd.Series:
        """
        计算质量因子
        使用ROE、ROA、毛利率
        """
        # ROE 越高越好
        roe = df.get('roe', pd.Series(index=df.index)).fillna(0.1)
        # ROA 越高越好
        roa = df.get('roa', pd.Series(index=df.index)).fillna(0.05)
        # 毛利率 越高越好
        gross_margin = df.get('gross_margin', pd.Series(index=df.index)).fillna(0.2)
        
        # 标准化后合并
        quality_factor = (roe + roa + gross_margin) / 3
        return quality_factor
    
    def calculate_growth_factor(self, df: pd.DataFrame) -> pd.Series:
        """
        计算成长因子
        使用营收增速、利润增速
        """
        # 营收同比增速
        revenue_growth = df.get('revenue_growth', pd.Series(index=df.index)).fillna(0)
        # 利润同比增速
        profit_growth = df.get('profit_growth', pd.Series(index=df.index)).fillna(0)
        
        # 合并成长因子
        growth_factor = (revenue_growth.fillna(0) + profit_growth.fillna(0)) / 2
        return growth_factor
    
    def standardize(self, series: pd.Series) -> pd.Series:
        """
        Z-Score标准化
        """
        mean = series.mean()
        std = series.std()
        if std == 0:
            return pd.Series(0, index=series.index)
        return (series - mean) / std
    
    def select_stocks(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        多因子选股
        
        Args:
            df: 股票数据DataFrame
            top_n: 选出前N只股票
            
        Returns:
            选中的股票DataFrame，包含因子得分和排名
        """
        # 计算各因子
        df['value_factor'] = self.calculate_value_factor(df)
        df['momentum_factor'] = self.calculate_momentum_factor(df)
        df['quality_factor'] = self.calculate_quality_factor(df)
        df['growth_factor'] = self.calculate_growth_factor(df)
        
        # 标准化
        df['value_factor_std'] = self.standardize(df['value_factor'])
        df['momentum_factor_std'] = self.standardize(df['momentum_factor'])
        df['quality_factor_std'] = self.standardize(df['quality_factor'])
        df['growth_factor_std'] = self.standardize(df['growth_factor'])
        
        # 计算综合得分
        df['composite_score'] = (
            df['value_factor_std'] * self.weights['value'] +
            df['momentum_factor_std'] * self.weights['momentum'] +
            df['quality_factor_std'] * self.weights['quality'] +
            df['growth_factor_std'] * self.weights['growth']
        )
        
        # 排序并选择Top N
        df = df.sort_values('composite_score', ascending=False)
        df['rank'] = range(1, len(df) + 1)
        
        selected = df.head(top_n).copy()
        
        logger.info(f"多因子选股完成，选中 {len(selected)} 只股票")
        logger.info(f"Top 5: {selected['code'].head(5).tolist()}")
        
        return selected
    
    def get_factor_exposure(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        获取当前因子暴露
        """
        return {
            'value': df['value_factor_std'].mean(),
            'momentum': df['momentum_factor_std'].mean(),
            'quality': df['quality_factor_std'].mean(),
            'growth': df['growth_factor_std'].mean()
        }


class FactorTimingStrategy:
    """
    因子择时策略
    根据市场环境动态调整因子权重
    """
    
    def __init__(self):
        self.market_regimes = {
            'bull': {'value': 0.15, 'momentum': 0.40, 'quality': 0.20, 'growth': 0.25},
            'bear': {'value': 0.40, 'momentum': 0.15, 'quality': 0.30, 'growth': 0.15},
            'sideways': {'value': 0.30, 'momentum': 0.20, 'quality': 0.30, 'growth': 0.20},
        }
    
    def detect_market_regime(self, df: pd.DataFrame) -> str:
        """
        检测市场环境
        
        Returns:
            'bull' | 'bear' | 'sideways'
        """
        # 计算市场趋势
        returns_20d = df['close'].pct_change(20).mean()
        volatility = df['close'].pct_change().std() * np.sqrt(252)
        
        if returns_20d > 0.05 and volatility < 0.3:
            return 'bull'
        elif returns_20d < -0.05:
            return 'bear'
        else:
            return 'sideways'
    
    def get_dynamic_weights(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        获取动态因子权重
        """
        regime = self.detect_market_regime(df)
        return self.market_regimes.get(regime, self.market_regimes['sideways'])


# 预配置的策略模板
STRATEGY_TEMPLATES = {
    '均衡配置': {
        'value': 0.25, 'momentum': 0.25, 'quality': 0.25, 'growth': 0.25
    },
    '价值投资': {
        'value': 0.50, 'momentum': 0.10, 'quality': 0.30, 'growth': 0.10
    },
    '趋势跟踪': {
        'value': 0.15, 'momentum': 0.50, 'quality': 0.15, 'growth': 0.20
    },
    '质量成长': {
        'value': 0.20, 'momentum': 0.15, 'quality': 0.35, 'growth': 0.30
    },
}
