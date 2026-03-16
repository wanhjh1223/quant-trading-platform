"""
数据存储管理 - Parquet + SQLite混合存储
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

import polars as pl
import pandas as pd
from loguru import logger


class DataStore:
    """数据存储管理器"""
    
    def __init__(self, data_dir: str = './data'):
        """
        初始化数据存储
        
        Args:
            data_dir: 数据根目录
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / 'raw'
        self.processed_dir = self.data_dir / 'processed'
        self.features_dir = self.data_dir / 'features'
        
        # 确保目录存在
        for d in [self.raw_dir, self.processed_dir, self.features_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def save_daily_data(
        self,
        ts_code: str,
        df: pd.DataFrame,
        subdir: str = 'daily'
    ) -> Path:
        """
        保存日线数据
        
        Args:
            ts_code: 股票代码
            df: 数据DataFrame
            subdir: 子目录
        """
        output_dir = self.raw_dir / subdir
        output_dir.mkdir(exist_ok=True)
        
        # 文件名格式: 000001_SZ.parquet
        filename = f"{ts_code.replace('.', '_')}.parquet"
        output_path = output_dir / filename
        
        # 保存为Parquet（高效压缩）
        df.to_parquet(output_path, index=False, compression='zstd')
        logger.debug(f"数据已保存: {output_path}")
        
        return output_path
    
    def load_daily_data(
        self,
        ts_code: str,
        subdir: str = 'daily',
        use_polars: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        加载日线数据
        
        Args:
            ts_code: 股票代码
            subdir: 子目录
            use_polars: 是否使用Polars加载（更快）
        """
        filename = f"{ts_code.replace('.', '_')}.parquet"
        file_path = self.raw_dir / subdir / filename
        
        if not file_path.exists():
            logger.warning(f"数据文件不存在: {file_path}")
            return None
        
        try:
            if use_polars:
                # Polars加载更快
                df = pl.read_parquet(file_path).to_pandas()
            else:
                df = pd.read_parquet(file_path)
            
            return df
        except Exception as e:
            logger.error(f"加载数据失败 {ts_code}: {e}")
            return None
    
    def list_available_stocks(self, subdir: str = 'daily') -> List[str]:
        """获取已下载的股票列表"""
        data_dir = self.raw_dir / subdir
        if not data_dir.exists():
            return []
        
        stocks = []
        for f in data_dir.glob('*.parquet'):
            # 000001_SZ.parquet -> 000001.SZ
            code = f.stem.replace('_', '.')
            stocks.append(code)
        
        return sorted(stocks)
    
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据存储摘要"""
        summary = {
            'raw_daily': len(self.list_available_stocks('daily')),
            'raw_financial': len(self.list_available_stocks('financial')),
            'raw_index': len(self.list_available_stocks('index')),
        }
        
        # 计算总存储大小
        total_size = 0
        for ext in ['*.parquet', '*.csv', '*.json']:
            for f in self.data_dir.rglob(ext):
                total_size += f.stat().st_size
        
        summary['total_size_mb'] = round(total_size / 1024 / 1024, 2)
        
        return summary


class FeatureStore:
    """特征数据存储"""
    
    def __init__(self, data_dir: str = './data'):
        self.features_dir = Path(data_dir) / 'features'
        self.features_dir.mkdir(parents=True, exist_ok=True)
    
    def save_features(
        self,
        ts_code: str,
        features: pd.DataFrame,
        feature_name: str = 'technical'
    ) -> Path:
        """保存特征数据"""
        output_dir = self.features_dir / feature_name
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{ts_code.replace('.', '_')}.parquet"
        output_path = output_dir / filename
        
        features.to_parquet(output_path, index=False)
        logger.debug(f"特征已保存: {output_path}")
        
        return output_path
    
    def load_features(
        self,
        ts_code: str,
        feature_name: str = 'technical'
    ) -> Optional[pd.DataFrame]:
        """加载特征数据"""
        filename = f"{ts_code.replace('.', '_')}.parquet"
        file_path = self.features_dir / feature_name / filename
        
        if not file_path.exists():
            return None
        
        return pd.read_parquet(file_path)
