"""
A股数据获取模块 - 基于Tushare Pro
"""
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

import tushare as ts
import pandas as pd
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class TushareDataSource:
    """Tushare数据源封装"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化Tushare数据源
        
        Args:
            token: Tushare Pro API Token，如未提供则从环境变量读取
        """
        self.token = token or os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("请提供Tushare Token或设置TUSHARE_TOKEN环境变量")
        
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        self._request_count = 0
        self._last_request_time = 0
        
    def _rate_limit(self):
        """简单的速率限制，避免触发API限制"""
        self._request_count += 1
        current_time = time.time()
        
        # 每60秒不超过200次请求
        if current_time - self._last_request_time < 60 and self._request_count >= 200:
            sleep_time = 60 - (current_time - self._last_request_time)
            logger.info(f"触发速率限制，等待 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)
            self._request_count = 0
            self._last_request_time = time.time()
        elif current_time - self._last_request_time >= 60:
            self._request_count = 0
            self._last_request_time = current_time
    
    def get_stock_list(self, exchange: str = 'SSE') -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            exchange: 交易所 SSE(上交所), SZSE(深交所), BSE(北交所)
            
        Returns:
            DataFrame包含股票代码、名称、行业等信息
        """
        self._rate_limit()
        
        try:
            df = self.pro.stock_basic(
                exchange=exchange,
                list_status='L',  # 上市
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            logger.info(f"获取 {exchange} 股票列表: {len(df)} 只")
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise
    
    def get_daily_data(
        self, 
        ts_code: str, 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """
        获取日线行情数据
        
        Args:
            ts_code: 股票代码，如 '000001.SZ'
            start_date: 开始日期，格式 'YYYYMMDD'
            end_date: 结束日期，格式 'YYYYMMDD'
            
        Returns:
            DataFrame包含OHLCV数据
        """
        self._rate_limit()
        
        try:
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.warning(f"{ts_code} 在 {start_date}~{end_date} 无数据")
                return df
            
            # 按日期排序
            df = df.sort_values('trade_date')
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            
            logger.debug(f"获取 {ts_code} 日线数据: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取日线数据失败 {ts_code}: {e}")
            raise
    
    def get_minute_data(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        freq: str = '1min'
    ) -> pd.DataFrame:
        """
        获取分钟线数据（需积分权限）
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            freq: 频率 '1min' 或 '5min'
        """
        self._rate_limit()
        
        try:
            df = ts.pro_bar(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                freq=freq
            )
            
            if df is None or df.empty:
                logger.warning(f"{ts_code} 分钟线数据为空")
                return pd.DataFrame()
            
            df = df.sort_values('trade_time')
            logger.debug(f"获取 {ts_code} {freq} 数据: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取分钟线数据失败 {ts_code}: {e}")
            return pd.DataFrame()
    
    def get_financial_data(
        self,
        ts_code: str,
        report_type: str = 'income'
    ) -> pd.DataFrame:
        """
        获取财务数据
        
        Args:
            ts_code: 股票代码
            report_type: 报表类型 income(利润表)/balance(资产负债表)/cashflow(现金流)
        """
        self._rate_limit()
        
        try:
            if report_type == 'income':
                df = self.pro.income(ts_code=ts_code)
            elif report_type == 'balance':
                df = self.pro.balancesheet(ts_code=ts_code)
            elif report_type == 'cashflow':
                df = self.pro.cashflow(ts_code=ts_code)
            else:
                raise ValueError(f"不支持的报表类型: {report_type}")
            
            logger.info(f"获取 {ts_code} {report_type} 报表: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取财务数据失败 {ts_code}: {e}")
            return pd.DataFrame()
    
    def get_index_list(self) -> pd.DataFrame:
        """获取指数列表"""
        self._rate_limit()
        
        try:
            df = self.pro.index_basic(
                market='SW',  # 申万指数
                fields='ts_code,name,market,publisher,category'
            )
            logger.info(f"获取指数列表: {len(df)} 个")
            return df
        except Exception as e:
            logger.error(f"获取指数列表失败: {e}")
            raise
    
    def get_index_daily(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取指数日线数据"""
        self._rate_limit()
        
        try:
            df = self.pro.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            df = df.sort_values('trade_date')
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            return df
        except Exception as e:
            logger.error(f"获取指数数据失败 {ts_code}: {e}")
            return pd.DataFrame()


class DataDownloader:
    """数据下载管理器"""
    
    def __init__(self, data_dir: str = './data', token: Optional[str] = None):
        """
        初始化下载器
        
        Args:
            data_dir: 数据存储目录
            token: Tushare Token
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (self.data_dir / 'raw' / 'daily').mkdir(parents=True, exist_ok=True)
        (self.data_dir / 'raw' / 'financial').mkdir(parents=True, exist_ok=True)
        (self.data_dir / 'raw' / 'index').mkdir(parents=True, exist_ok=True)
        
        self.source = TushareDataSource(token)
        logger.info(f"数据下载器初始化完成，存储目录: {self.data_dir}")
    
    def download_stock_daily(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
        force_update: bool = False
    ) -> Path:
        """
        下载单只股票日线数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            force_update: 强制更新
            
        Returns:
            存储文件路径
        """
        # 检查是否已存在
        output_file = self.data_dir / 'raw' / 'daily' / f"{ts_code.replace('.', '_')}.parquet"
        
        if output_file.exists() and not force_update:
            logger.info(f"{ts_code} 数据已存在，跳过下载")
            return output_file
        
        # 下载数据
        df = self.source.get_daily_data(ts_code, start_date, end_date)
        
        if df.empty:
            logger.warning(f"{ts_code} 无数据")
            return None
        
        # 保存为Parquet格式
        df.to_parquet(output_file, index=False)
        logger.info(f"{ts_code} 数据已保存: {output_file}")
        
        return output_file
    
    def download_all_stocks(
        self,
        exchange: str = 'SSE',
        start_date: str = None,
        end_date: str = None,
        max_stocks: Optional[int] = None
    ) -> List[Path]:
        """
        批量下载股票数据
        
        Args:
            exchange: 交易所
            start_date: 开始日期，默认一年前
            end_date: 结束日期，默认今天
            max_stocks: 最大下载数量，用于测试
        """
        # 默认日期范围
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        # 获取股票列表
        stock_list = self.source.get_stock_list(exchange)
        
        if max_stocks:
            stock_list = stock_list.head(max_stocks)
        
        logger.info(f"开始下载 {len(stock_list)} 只股票数据...")
        
        downloaded = []
        for idx, row in stock_list.iterrows():
            try:
                path = self.download_stock_daily(
                    row['ts_code'],
                    start_date,
                    end_date
                )
                if path:
                    downloaded.append(path)
                
                # 每10只报告一次进度
                if len(downloaded) % 10 == 0:
                    logger.info(f"进度: {len(downloaded)}/{len(stock_list)}")
                    
            except Exception as e:
                logger.error(f"下载失败 {row['ts_code']}: {e}")
                continue
        
        logger.info(f"批量下载完成: {len(downloaded)}/{len(stock_list)}")
        return downloaded


# 便捷函数
def get_data_source(token: Optional[str] = None) -> TushareDataSource:
    """获取数据源实例"""
    return TushareDataSource(token)


def download_single_stock(
    ts_code: str,
    start_date: str,
    end_date: str,
    data_dir: str = './data',
    token: Optional[str] = None
) -> Path:
    """下载单只股票数据（便捷函数）"""
    downloader = DataDownloader(data_dir, token)
    return downloader.download_stock_daily(ts_code, start_date, end_date)
