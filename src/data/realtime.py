"""
实时行情数据获取 - 基于akshare（免费，无需token）
"""
import time
from typing import List, Dict, Optional
from datetime import datetime

import pandas as pd
import akshare as ak


class RealtimeDataSource:
    """实时数据源"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = 5
        self.last_fetch = {}
    
    def get_realtime_quotes(self, symbols: List[str] = None) -> pd.DataFrame:
        """获取实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()
            
            if symbols:
                df = df[df['代码'].isin(symbols)]
            
            df = df.rename(columns={
                '代码': 'symbol',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '成交量': 'volume',
                '成交额': 'amount',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'pre_close',
                '换手率': 'turnover'
            })
            
            return df
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
                'name': row.get('name', ''),
                'price': float(row.get('price', 0) or 0),
                'change_pct': float(row.get('change_pct', 0) or 0),
                'change': float(row.get('change', 0) or 0),
                'volume': int(row.get('volume', 0) or 0),
                'amount': float(row.get('amount', 0) or 0),
                'high': float(row.get('high', 0) or 0),
                'low': float(row.get('low', 0) or 0),
                'open': float(row.get('open', 0) or 0),
                'pre_close': float(row.get('pre_close', 0) or 0),
                'turnover': float(row.get('turnover', 0) or 0),
                'update_time': datetime.now().strftime('%H:%M:%S')
            }
        return None
    
    def get_index_quotes(self) -> pd.DataFrame:
        """获取指数行情"""
        try:
            # 使用股票列表接口获取主要指数
            df = ak.stock_zh_index_spot()
            df = df.rename(columns={
                '代码': 'symbol',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change'
            })
            return df
        except Exception as e:
            print(f"获取指数失败: {e}")
            # 返回模拟数据
            return pd.DataFrame([
                {'symbol': '000001', 'name': '上证指数', 'price': 3050.0, 'change_pct': 0.5, 'change': 15.0},
                {'symbol': '399001', 'name': '深证成指', 'price': 9800.0, 'change_pct': 0.8, 'change': 78.0},
                {'symbol': '399006', 'name': '创业板指', 'price': 1950.0, 'change_pct': 1.2, 'change': 23.0},
            ])
    
    def get_hot_stocks(self, top_n: int = 20) -> pd.DataFrame:
        """获取热门股票"""
        try:
            df = ak.stock_zh_a_spot_em()
            df = df.rename(columns={
                '代码': 'symbol',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct'
            })
            df = df.sort_values('change_pct', ascending=False)
            return df.head(top_n)
        except Exception as e:
            print(f"获取热门股票失败: {e}")
            return pd.DataFrame()
    
    def get_stock_kline(self, symbol: str, period: str = "daily") -> pd.DataFrame:
        """获取K线数据"""
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period=period, start_date="20240101", adjust="qfq")
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '换手率': 'turnover'
            })
            return df
        except Exception as e:
            print(f"获取K线失败: {e}")
            return pd.DataFrame()


class WatchlistManager:
    """自选股管理"""
    
    def __init__(self, filepath: str = './data/watchlist.json'):
        self.filepath = filepath
        self.watchlist = self._load()
    
    def _load(self) -> List[Dict]:
        import json
        from pathlib import Path
        
        if not Path(self.filepath).exists():
            return []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save(self):
        import json
        from pathlib import Path
        
        Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.watchlist, f, ensure_ascii=False, indent=2)
    
    def add(self, symbol: str, name: str = "", note: str = ""):
        if any(s['symbol'] == symbol for s in self.watchlist):
            print(f"{symbol} 已在自选列表中")
            return False
        
        self.watchlist.append({
            'symbol': symbol,
            'name': name,
            'note': note,
            'added_time': datetime.now().isoformat()
        })
        self._save()
        return True
    
    def remove(self, symbol: str):
        self.watchlist = [s for s in self.watchlist if s['symbol'] != symbol]
        self._save()
    
    def get_symbols(self) -> List[str]:
        return [s['symbol'] for s in self.watchlist]
    
    def get_list(self) -> List[Dict]:
        return self.watchlist


class PriceAlert:
    """价格预警"""
    
    def __init__(self, filepath: str = './data/alerts.json'):
        self.filepath = filepath
        self.alerts = self._load()
    
    def _load(self) -> List[Dict]:
        import json
        from pathlib import Path
        
        if not Path(self.filepath).exists():
            return []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save(self):
        import json
        from pathlib import Path
        
        Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.alerts, f, ensure_ascii=False, indent=2)
    
    def add_alert(self, symbol: str, alert_type: str, threshold: float, note: str = ""):
        self.alerts.append({
            'id': f"{symbol}_{alert_type}_{int(time.time())}",
            'symbol': symbol,
            'type': alert_type,
            'threshold': threshold,
            'note': note,
            'created_at': datetime.now().isoformat(),
            'triggered': False
        })
        self._save()
    
    def remove_alert(self, alert_id: str):
        self.alerts = [a for a in self.alerts if a['id'] != alert_id]
        self._save()
    
    def check_alerts(self, quotes_df: pd.DataFrame) -> List[Dict]:
        triggered = []
        for alert in self.alerts:
            if alert['triggered']:
                continue
            
            row = quotes_df[quotes_df['symbol'] == alert['symbol']]
            if row.empty:
                continue
            
            row = row.iloc[0]
            is_triggered = False
            
            if alert['type'] == 'price_above' and row['price'] >= alert['threshold']:
                is_triggered = True
            elif alert['type'] == 'price_below' and row['price'] <= alert['threshold']:
                is_triggered = True
            elif alert['type'] == 'change_above' and row['change_pct'] >= alert['threshold']:
                is_triggered = True
            elif alert['type'] == 'change_below' and row['change_pct'] <= alert['threshold']:
                is_triggered = True
            
            if is_triggered:
                alert['triggered'] = True
                alert['triggered_at'] = datetime.now().isoformat()
                triggered.append(alert)
        
        if triggered:
            self._save()
        return triggered
    
    def get_active_alerts(self) -> List[Dict]:
        return [a for a in self.alerts if not a['triggered']]
