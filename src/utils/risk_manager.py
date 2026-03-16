"""
风险控制模块 - 仓位管理、止损止盈、动态风控
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    CRITICAL = "极高风险"


@dataclass
class Position:
    """仓位信息"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def market_value(self) -> float:
        """市值"""
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        """浮动盈亏"""
        return self.quantity * (self.current_price - self.entry_price)
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """浮动盈亏百分比"""
        return (self.current_price - self.entry_price) / self.entry_price
    
    @property
    def is_stop_loss_triggered(self) -> bool:
        """是否触发止损"""
        if self.stop_loss is None:
            return False
        return self.current_price <= self.stop_loss
    
    @property
    def is_take_profit_triggered(self) -> bool:
        """是否触发止盈"""
        if self.take_profit is None:
            return False
        return self.current_price >= self.take_profit


class RiskManager:
    """风险管理器"""
    
    def __init__(
        self,
        total_capital: float,
        max_position_pct: float = 0.2,  # 单票最大仓位20%
        max_drawdown_pct: float = 0.15,  # 最大回撤15%
        max_daily_loss_pct: float = 0.05,  # 单日最大亏损5%
        default_stop_loss_pct: float = 0.08,  # 默认止损8%
        default_take_profit_pct: float = 0.15,  # 默认止盈15%
    ):
        self.total_capital = total_capital
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.default_stop_loss_pct = default_stop_loss_pct
        self.default_take_profit_pct = default_take_profit_pct
        
        # 持仓状态
        self.positions: Dict[str, Position] = {}
        self.daily_pnl = 0.0
        self.peak_capital = total_capital
        self.current_capital = total_capital
        
        # 风控触发记录
        self.risk_events: List[Dict] = []
    
    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        confidence: float = 1.0,
        volatility: Optional[float] = None
    ) -> int:
        """
        计算建议仓位大小（凯利公式改进版）
        
        Args:
            symbol: 股票代码
            price: 当前价格
            confidence: 信心指数 (0-1)
            volatility: 波动率 (可选)
        
        Returns:
            建议买入股数
        """
        # 基础仓位 = 总资金 * 最大仓位比例 * 信心指数
        base_position_value = self.total_capital * self.max_position_pct * confidence
        
        # 根据波动率调整（波动率越大，仓位越小）
        if volatility is not None and volatility > 0:
            vol_factor = min(1.0, 0.2 / volatility)  # 假设目标波动率20%
            base_position_value *= vol_factor
        
        # 计算股数（向下取整到100的倍数，A股整数手）
        shares = int(base_position_value / price / 100) * 100
        
        # 确保至少能买1手
        return max(100, shares)
    
    def can_open_position(self, symbol: str, quantity: int, price: float) -> Tuple[bool, str]:
        """
        检查是否可以开仓
        
        Returns:
            (是否可以开仓, 原因)
        """
        # 检查是否已触发风控
        if self.is_trading_halted():
            return False, "交易已暂停（风控触发）"
        
        # 检查单票仓位限制
        new_position_value = quantity * price
        new_position_pct = new_position_value / self.total_capital
        
        if new_position_pct > self.max_position_pct:
            return False, f"超出单票最大仓位限制 ({self.max_position_pct*100:.0f}%)"
        
        # 检查是否已持有该股票
        if symbol in self.positions:
            return False, f"已持有 {symbol}，不支持加仓"
        
        # 检查资金是否充足
        if new_position_value > self.current_capital:
            return False, "资金不足"
        
        return True, "可以开仓"
    
    def open_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict:
        """开仓"""
        can_open, reason = self.can_open_position(symbol, quantity, price)
        
        if not can_open:
            return {"success": False, "reason": reason}
        
        # 设置默认止损止盈
        if stop_loss is None:
            stop_loss = price * (1 - self.default_stop_loss_pct)
        if take_profit is None:
            take_profit = price * (1 + self.default_take_profit_pct)
        
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            current_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        self.current_capital -= quantity * price
        
        return {
            "success": True,
            "position": position,
            "remaining_capital": self.current_capital
        }
    
    def close_position(self, symbol: str, price: float) -> Dict:
        """平仓"""
        if symbol not in self.positions:
            return {"success": False, "reason": "未持有该股票"}
        
        position = self.positions[symbol]
        realized_pnl = position.quantity * (price - position.entry_price)
        
        self.current_capital += position.quantity * price
        self.daily_pnl += realized_pnl
        
        del self.positions[symbol]
        
        # 更新资金峰值
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        return {
            "success": True,
            "realized_pnl": realized_pnl,
            "realized_pnl_pct": realized_pnl / (position.quantity * position.entry_price),
            "current_capital": self.current_capital
        }
    
    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
    
    def check_risk_limits(self) -> List[Dict]:
        """
        检查风控限制
        
        Returns:
            触发的风控事件列表
        """
        triggered = []
        
        # 检查总回撤
        total_value = self.current_capital + sum(
            p.market_value for p in self.positions.values()
        )
        drawdown = (self.peak_capital - total_value) / self.peak_capital
        
        if drawdown > self.max_drawdown_pct:
            triggered.append({
                "type": "max_drawdown",
                "level": RiskLevel.CRITICAL,
                "message": f"触发最大回撤限制: {drawdown*100:.2f}% > {self.max_drawdown_pct*100:.0f}%",
                "action": "建议平仓所有头寸"
            })
        
        # 检查单日亏损
        daily_loss_pct = abs(min(0, self.daily_pnl)) / self.total_capital
        if daily_loss_pct > self.max_daily_loss_pct:
            triggered.append({
                "type": "daily_loss",
                "level": RiskLevel.HIGH,
                "message": f"触发单日亏损限制: {daily_loss_pct*100:.2f}% > {self.max_daily_loss_pct*100:.0f}%",
                "action": "建议暂停当日交易"
            })
        
        # 检查个股止损止盈
        for symbol, position in self.positions.items():
            if position.is_stop_loss_triggered:
                triggered.append({
                    "type": "stop_loss",
                    "level": RiskLevel.MEDIUM,
                    "symbol": symbol,
                    "message": f"{symbol} 触发止损: {position.unrealized_pnl_pct*100:.2f}%",
                    "action": "建议平仓"
                })
            elif position.is_take_profit_triggered:
                triggered.append({
                    "type": "take_profit",
                    "level": RiskLevel.LOW,
                    "symbol": symbol,
                    "message": f"{symbol} 触发止盈: +{position.unrealized_pnl_pct*100:.2f}%",
                    "action": "可考虑平仓"
                })
        
        self.risk_events.extend(triggered)
        return triggered
    
    def is_trading_halted(self) -> bool:
        """检查是否暂停交易"""
        # 检查是否有极高风险事件
        critical_events = [
            e for e in self.risk_events
            if e.get("level") == RiskLevel.CRITICAL
        ]
        return len(critical_events) > 0
    
    def get_portfolio_summary(self) -> Dict:
        """获取组合摘要"""
        total_position_value = sum(
            p.market_value for p in self.positions.values()
        )
        total_value = self.current_capital + total_position_value
        
        unrealized_pnl = sum(
            p.unrealized_pnl for p in self.positions.values()
        )
        
        return {
            "total_capital": self.total_capital,
            "current_capital": self.current_capital,
            "position_value": total_position_value,
            "total_value": total_value,
            "total_return": (total_value - self.total_capital) / self.total_capital,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl_today": self.daily_pnl,
            "drawdown": (self.peak_capital - total_value) / self.peak_capital,
            "position_count": len(self.positions),
            "risk_level": self._assess_risk_level()
        }
    
    def _assess_risk_level(self) -> RiskLevel:
        """评估当前风险等级"""
        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        
        if drawdown > self.max_drawdown_pct:
            return RiskLevel.CRITICAL
        elif drawdown > self.max_drawdown_pct * 0.7:
            return RiskLevel.HIGH
        elif drawdown > self.max_drawdown_pct * 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def reset_daily(self):
        """重置每日统计"""
        self.daily_pnl = 0.0
        self.risk_events = []


# 便捷函数
def calculate_kelly_criterion(win_rate: float, win_loss_ratio: float) -> float:
    """
    凯利公式计算最优仓位比例
    
    f* = (p*b - q) / b
    p = 胜率
    q = 败率 = 1-p
    b = 盈亏比
    """
    if win_loss_ratio <= 0:
        return 0.0
    
    q = 1 - win_rate
    kelly = (win_rate * win_loss_ratio - q) / win_loss_ratio
    
    # 限制在0-1之间，并取半凯利（更保守）
    return max(0, min(0.5, kelly / 2))


def calculate_volatility_adjusted_position(
    base_position: float,
    current_volatility: float,
    target_volatility: float = 0.15
) -> float:
    """
    根据波动率调整仓位
    
    波动率越大，仓位越小
    """
    if current_volatility <= 0:
        return base_position
    
    adjustment = target_volatility / current_volatility
    return base_position * adjustment
