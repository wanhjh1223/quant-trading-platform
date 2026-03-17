"""
富途OpenAPI 交易接口封装
用于连接富途OpenAPI实现实盘/模拟交易
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

# 富途API导入（需先安装: pip install futu-api）
try:
    from futu import (
        OpenQuoteContext, OpenSecTradeContext,
        TrdEnv, TrdSide, OrderType, Market,
        RET_OK, RET_ERROR
    )
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False
    logging.warning("富途API未安装，请先执行: pip install futu-api")


class FutuTrader:
    """
    富途交易接口封装类
    
    功能：
    - 行情数据获取
    - 模拟/实盘交易下单
    - 订单查询与管理
    - 持仓查询
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 11111):
        """
        初始化交易接口
        
        Args:
            host: OpenD网关地址，默认本地
            port: OpenD网关端口，默认11111
        """
        if not FUTU_AVAILABLE:
            raise ImportError("富途API未安装，请先执行: pip install futu-api")
        
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """
        连接OpenD网关
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 连接行情接口
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            self.logger.info(f"行情接口连接成功: {self.host}:{self.port}")
            
            # 连接交易接口
            self.trade_ctx = OpenSecTradeContext(host=self.host, port=self.port)
            self.logger.info("交易接口连接成功")
            
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            self.quote_ctx = None
        if self.trade_ctx:
            self.trade_ctx.close()
            self.trade_ctx = None
        self.logger.info("连接已断开")
    
    def get_market_snapshot(self, codes: List[str]) -> Tuple[bool, pd.DataFrame]:
        """
        获取实时行情快照
        
        Args:
            codes: 股票代码列表，如 ['HK.00700', 'US.AAPL']
            
        Returns:
            (success, data): 是否成功，数据DataFrame
        """
        if not self.quote_ctx:
            return False, pd.DataFrame()
        
        ret, data = self.quote_ctx.get_market_snapshot(codes)
        if ret == RET_OK:
            return True, data
        else:
            self.logger.error(f"获取行情失败: {data}")
            return False, pd.DataFrame()
    
    def place_order(
        self,
        code: str,
        price: float,
        qty: int,
        side: str = 'buy',
        order_type: str = 'normal',
        trd_env: str = 'simulate'
    ) -> Tuple[bool, Dict]:
        """
        下单
        
        Args:
            code: 股票代码，如 'HK.00700'
            price: 委托价格
            qty: 委托数量
            side: 'buy'或'sell'
            order_type: 'normal'(限价)或'market'(市价)
            trd_env: 'simulate'(模拟)或'real'(实盘)
            
        Returns:
            (success, order_info): 是否成功，订单信息
        """
        if not self.trade_ctx:
            return False, {}
        
        # 转换参数
        trd_side = TrdSide.BUY if side == 'buy' else TrdSide.SELL
        order_type_enum = OrderType.NORMAL if order_type == 'normal' else OrderType.MARKET
        env = TrdEnv.SIMULATE if trd_env == 'simulate' else TrdEnv.REAL
        
        ret, data = self.trade_ctx.place_order(
            price=price,
            qty=qty,
            code=code,
            trd_side=trd_side,
            order_type=order_type_enum,
            trd_env=env
        )
        
        if ret == RET_OK:
            self.logger.info(f"下单成功: {code} {side} {qty}@{price}")
            return True, data.to_dict()
        else:
            self.logger.error(f"下单失败: {data}")
            return False, {}
    
    def cancel_order(self, order_id: str, trd_env: str = 'simulate') -> bool:
        """
        撤单
        
        Args:
            order_id: 订单ID
            trd_env: 'simulate'或'real'
            
        Returns:
            bool: 是否成功
        """
        if not self.trade_ctx:
            return False
        
        env = TrdEnv.SIMULATE if trd_env == 'simulate' else TrdEnv.REAL
        ret, data = self.trade_ctx.cancel_order(order_id=order_id, trd_env=env)
        
        if ret == RET_OK:
            self.logger.info(f"撤单成功: {order_id}")
            return True
        else:
            self.logger.error(f"撤单失败: {data}")
            return False
    
    def get_order_list(self, trd_env: str = 'simulate') -> Tuple[bool, pd.DataFrame]:
        """
        查询订单列表
        
        Args:
            trd_env: 'simulate'或'real'
            
        Returns:
            (success, orders): 是否成功，订单列表
        """
        if not self.trade_ctx:
            return False, pd.DataFrame()
        
        env = TrdEnv.SIMULATE if trd_env == 'simulate' else TrdEnv.REAL
        ret, data = self.trade_ctx.get_order_list(trd_env=env)
        
        if ret == RET_OK:
            return True, data
        else:
            self.logger.error(f"查询订单失败: {data}")
            return False, pd.DataFrame()
    
    def get_position_list(self, trd_env: str = 'simulate') -> Tuple[bool, pd.DataFrame]:
        """
        查询持仓列表
        
        Args:
            trd_env: 'simulate'或'real'
            
        Returns:
            (success, positions): 是否成功，持仓列表
        """
        if not self.trade_ctx:
            return False, pd.DataFrame()
        
        env = TrdEnv.SIMULATE if trd_env == 'simulate' else TrdEnv.REAL
        ret, data = self.trade_ctx.get_position_list(trd_env=env)
        
        if ret == RET_OK:
            return True, data
        else:
            self.logger.error(f"查询持仓失败: {data}")
            return False, pd.DataFrame()
    
    def subscribe(self, codes: List[str], sub_types: List[str]) -> bool:
        """
        订阅实时推送
        
        Args:
            codes: 股票代码列表
            sub_types: 订阅类型列表，如['QUOTE', 'ORDER_BOOK']
            
        Returns:
            bool: 是否成功
        """
        if not self.quote_ctx:
            return False
        
        # 订阅类型转换
        from futu import SubType
        type_map = {
            'QUOTE': SubType.QUOTE,
            'ORDER_BOOK': SubType.ORDER_BOOK,
            'TICKER': SubType.TICKER,
            'K_1M': SubType.K_1M,
            'K_5M': SubType.K_5M,
            'K_DAY': SubType.K_DAY
        }
        
        sub_type_enums = [type_map.get(t, SubType.QUOTE) for t in sub_types]
        ret, data = self.quote_ctx.subscribe(codes, sub_type_enums)
        
        if ret == RET_OK:
            self.logger.info(f"订阅成功: {codes}")
            return True
        else:
            self.logger.error(f"订阅失败: {data}")
            return False


class MockTrader:
    """
    模拟交易器（用于测试）
    不依赖富途API，本地模拟交易逻辑
    """
    
    def __init__(self, initial_cash: float = 1000000.0):
        self.cash = initial_cash
        self.positions = {}  # code -> {'qty': int, 'avg_price': float}
        self.orders = []
        self.order_id_counter = 0
        
    def place_order(
        self,
        code: str,
        price: float,
        qty: int,
        side: str = 'buy'
    ) -> Tuple[bool, Dict]:
        """模拟下单"""
        self.order_id_counter += 1
        order_id = f"MOCK_{self.order_id_counter}"
        
        amount = price * qty
        
        if side == 'buy':
            if amount > self.cash:
                return False, {'error': '资金不足'}
            self.cash -= amount
            
            if code in self.positions:
                pos = self.positions[code]
                total_cost = pos['qty'] * pos['avg_price'] + amount
                pos['qty'] += qty
                pos['avg_price'] = total_cost / pos['qty']
            else:
                self.positions[code] = {'qty': qty, 'avg_price': price}
        else:  # sell
            if code not in self.positions or self.positions[code]['qty'] < qty:
                return False, {'error': '持仓不足'}
            
            self.cash += amount
            self.positions[code]['qty'] -= qty
            if self.positions[code]['qty'] == 0:
                del self.positions[code]
        
        order = {
            'order_id': order_id,
            'code': code,
            'side': side,
            'price': price,
            'qty': qty,
            'status': 'FILLED',
            'create_time': datetime.now()
        }
        self.orders.append(order)
        
        return True, order
    
    def get_portfolio(self) -> Dict:
        """获取投资组合"""
        return {
            'cash': self.cash,
            'positions': self.positions,
            'total_orders': len(self.orders)
        }


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 使用模拟交易器测试
    trader = MockTrader(initial_cash=100000)
    
    # 模拟买入
    success, order = trader.place_order('HK.00700', 500.0, 100, 'buy')
    print(f"买入结果: {success}, 订单: {order}")
    
    # 查看持仓
    portfolio = trader.get_portfolio()
    print(f"当前持仓: {portfolio}")
