"""
实时行情数据获取 - 基于新浪财经（无需token，网络友好）
"""
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd


class SinaRealtimeData:
    """新浪财经实时数据源"""
    
    BASE_URL = "https://hq.sinajs.cn"
    HEADERS = {
        "Referer": "https://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
    }
    
    # 指数代码映射
    INDEX_CODES = {
        'sh000001': '上证指数',
        'sz399001': '深证成指', 
        'sz399006': '创业板指',
        'sh000688': '科创50',
        'sh000016': '上证50',
        'sh000300': '沪深300',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def _format_symbol(self, symbol: str) -> str:
        """格式化股票代码为新浪格式"""
        symbol = symbol.lower().replace('.', '').replace('_', '')
        
        # 如果已经是sh/sz开头，直接使用
        if symbol.startswith('sh') or symbol.startswith('sz'):
            return symbol
        
        # 根据代码规则判断交易所
        # 600/601/603/688/689 - 上海
        # 000/001/002/003/300 - 深圳
        if symbol.startswith(('6', '688', '689')):
            return f"sh{symbol}"
        else:
            return f"sz{symbol}"
    
    def _parse_sina_data(self, data: str) -> Optional[Dict]:
        """解析新浪返回的数据"""
        try:
            # 数据格式: var hq_str_sh600000="股票名称,今日开盘,昨日收盘,当前价格,今日最高,今日最低,竞买价,竞卖价,成交股数,成交金额,买一量,买一价,买二量,买二价..."
            if not data or '="' not in data:
                return None
            
            # 提取引号内的内容
            content = data.split('="')[1].rstrip('";')
            if not content:
                return None
            
            # 新浪返回的是GBK编码，需要解码
            try:
                content = content.encode('latin1').decode('gbk')
            except:
                pass  # 如果解码失败，使用原始内容
            
            fields = content.split(',')
            if len(fields) < 30:
                return None
            
            return {
                'name': fields[0],
                'open': float(fields[1]),
                'pre_close': float(fields[2]),
                'price': float(fields[3]),
                'high': float(fields[4]),
                'low': float(fields[5]),
                'bid': float(fields[6]),
                'ask': float(fields[7]),
                'volume': int(fields[8]),
                'amount': float(fields[9]),
                'date': fields[30],
                'time': fields[31]
            }
        except Exception as e:
            print(f"解析数据失败: {e}, 原始数据: {data[:100]}")
            return None
    
    def get_realtime_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取多只股票实时行情
        
        Args:
            symbols: 股票代码列表，如 ['000001', '600000']
        """
        if not symbols:
            return pd.DataFrame()
        
        # 格式化代码
        sina_symbols = [self._format_symbol(s) for s in symbols]
        symbol_str = ','.join(sina_symbols)
        
        url = f"{self.BASE_URL}/list={symbol_str}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'gbk'
            
            results = []
            for line in response.text.strip().split('\n'):
                parsed = self._parse_sina_data(line)
                if parsed:
                    # 提取原始代码
                    code = line.split('hq_str_')[1].split('=')[0]
                    parsed['symbol'] = code.replace('sh', '').replace('sz', '')
                    parsed['change'] = parsed['price'] - parsed['pre_close']
                    parsed['change_pct'] = (parsed['change'] / parsed['pre_close']) * 100 if parsed['pre_close'] > 0 else 0
                    parsed['update_time'] = f"{parsed['date']} {parsed['time']}"
                    results.append(parsed)
            
            return pd.DataFrame(results)
            
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return pd.DataFrame()
    
    def get_single_stock(self, symbol: str) -> Optional[Dict]:
        """获取单只股票"""
        df = self.get_realtime_quotes([symbol])
        if not df.empty:
            row = df.iloc[0]
            return {
                'symbol': symbol,
                'name': row['name'],
                'price': float(row['price']),
                'change_pct': float(row['change_pct']),
                'change': float(row['change']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'pre_close': float(row['pre_close']),
                'volume': int(row['volume']),
                'amount': float(row['amount']),
                'update_time': row['update_time']
            }
        return None
    
    def get_index_quotes(self) -> pd.DataFrame:
        """获取大盘指数行情"""
        symbols = list(self.INDEX_CODES.keys())
        df = self.get_realtime_quotes(symbols)
        
        if not df.empty:
            # 添加指数名称
            df['index_name'] = df['symbol'].map({
                k.replace('sh', '').replace('sz', ''): v 
                for k, v in self.INDEX_CODES.items()
            })
        
        return df
    
    def get_hot_stocks(self, top_n: int = 20) -> pd.DataFrame:
        """
        获取热门股票（使用akshare获取全市场数据后排序）
        如果akshare不可用，返回空列表
        """
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            df = df.rename(columns={
                '代码': 'symbol',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '成交量': 'volume'
            })
            df = df.sort_values('change_pct', ascending=False)
            return df.head(top_n)
        except Exception as e:
            print(f"获取热门股票失败: {e}")
            return pd.DataFrame()
    
    def search_stock(self, keyword: str) -> List[Dict]:
        """搜索股票"""
        try:
            # 使用akshare搜索
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            
            # 按名称或代码搜索
            result = df[
                df['名称'].str.contains(keyword, na=False) | 
                df['代码'].str.contains(keyword, na=False)
            ]
            
            return result.head(10).to_dict('records')
        except:
            return []


# 兼容旧接口的别名
RealtimeDataSource = SinaRealtimeData


# 测试
if __name__ == '__main__':
    print("测试新浪财经数据源...")
    print("=" * 50)
    
    ds = SinaRealtimeData()
    
    print("\n[1/2] 获取单只股票 (000001 平安银行)...")
    info = ds.get_single_stock("000001")
    if info:
        print(f"✓ 成功: {info['name']}")
        print(f"  价格: {info['price']}, 涨跌: {info['change_pct']:.2f}%")
    else:
        print("✗ 失败")
    
    print("\n[2/2] 获取大盘指数...")
    df = ds.get_index_quotes()
    if not df.empty:
        print(f"✓ 成功: 获取到 {len(df)} 个指数")
        for _, row in df.iterrows():
            name = row.get('index_name', row['name'])
            print(f"  {name}: {row['price']} ({row['change_pct']:+.2f}%)")
    else:
        print("✗ 失败")
    
    print("\n" + "=" * 50)
    print("测试完成!")
