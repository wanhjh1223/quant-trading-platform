"""
数据下载脚本 - 一键下载A股历史数据
"""
import argparse
import os
from datetime import datetime, timedelta

from loguru import logger

# 添加src到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data.tushare_loader import DataDownloader


def main():
    parser = argparse.ArgumentParser(description='下载A股历史数据')
    parser.add_argument('--symbol', type=str, help='股票代码，如 000001.SZ')
    parser.add_argument('--start', type=str, help='开始日期 YYYYMMDD')
    parser.add_argument('--end', type=str, help='结束日期 YYYYMMDD')
    parser.add_argument('--exchange', type=str, default='SZSE', 
                       choices=['SSE', 'SZSE'], help='交易所')
    parser.add_argument('--all', action='store_true', help='下载全部股票')
    parser.add_argument('--max-stocks', type=int, help='最大下载数量（测试用）')
    parser.add_argument('--data-dir', type=str, default='./data', help='数据目录')
    parser.add_argument('--token', type=str, help='Tushare Token')
    
    args = parser.parse_args()
    
    # 设置日志
    logger.add(f"{args.data_dir}/download.log", rotation="10 MB")
    
    # 默认日期
    if args.end is None:
        args.end = datetime.now().strftime('%Y%m%d')
    if args.start is None:
        args.start = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    # 初始化下载器
    downloader = DataDownloader(args.data_dir, args.token)
    
    if args.all:
        # 批量下载
        logger.info(f"开始批量下载 {args.exchange} 交易所股票数据")
        downloader.download_all_stocks(
            exchange=args.exchange,
            start_date=args.start,
            end_date=args.end,
            max_stocks=args.max_stocks
        )
    elif args.symbol:
        # 单只股票
        logger.info(f"下载单只股票: {args.symbol}")
        path = downloader.download_stock_daily(
            ts_code=args.symbol,
            start_date=args.start,
            end_date=args.end
        )
        if path:
            logger.info(f"下载完成: {path}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
