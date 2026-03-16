"""
风险控制模块测试
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.risk_manager import (
    RiskManager, Position, RiskLevel,
    calculate_kelly_criterion,
    calculate_volatility_adjusted_position
)


class TestPosition:
    """测试仓位类"""
    
    def test_position_properties(self):
        """测试仓位属性计算"""
        pos = Position(
            symbol="000001.SZ",
            quantity=1000,
            entry_price=10.0,
            current_price=12.0,
            stop_loss=9.0,
            take_profit=15.0
        )
        
        assert pos.market_value == 12000.0
        assert pos.unrealized_pnl == 2000.0
        assert pos.unrealized_pnl_pct == 0.2
        assert not pos.is_stop_loss_triggered
        assert not pos.is_take_profit_triggered
    
    def test_stop_loss_triggered(self):
        """测试止损触发"""
        pos = Position(
            symbol="000001.SZ",
            quantity=1000,
            entry_price=10.0,
            current_price=8.0,
            stop_loss=9.0
        )
        
        assert pos.is_stop_loss_triggered
        assert not pos.is_take_profit_triggered
    
    def test_take_profit_triggered(self):
        """测试止盈触发"""
        pos = Position(
            symbol="000001.SZ",
            quantity=1000,
            entry_price=10.0,
            current_price=16.0,
            take_profit=15.0
        )
        
        assert pos.is_take_profit_triggered
        assert not pos.is_stop_loss_triggered


class TestRiskManager:
    """测试风险管理器"""
    
    @pytest.fixture
    def risk_manager(self):
        """创建风控管理器实例"""
        return RiskManager(
            total_capital=1000000,
            max_position_pct=0.2,
            max_drawdown_pct=0.15,
            max_daily_loss_pct=0.05
        )
    
    def test_calculate_position_size(self, risk_manager):
        """测试仓位计算"""
        shares = risk_manager.calculate_position_size(
            symbol="000001.SZ",
            price=10.0,
            confidence=1.0
        )
        
        # 基础仓位 = 1000000 * 0.2 * 1.0 = 200000
        # 股数 = 200000 / 10 = 20000，向下取整到100的倍数 = 20000
        assert shares == 20000
    
    def test_can_open_position_success(self, risk_manager):
        """测试可以开仓的情况"""
        can_open, reason = risk_manager.can_open_position(
            symbol="000001.SZ",
            quantity=10000,
            price=10.0
        )
        
        assert can_open
        assert reason == "可以开仓"
    
    def test_can_open_position_exceed_limit(self, risk_manager):
        """测试超出仓位限制"""
        can_open, reason = risk_manager.can_open_position(
            symbol="000001.SZ",
            quantity=30000,
            price=10.0
        )
        
        assert not can_open
        assert "超出单票最大仓位限制" in reason
    
    def test_open_position(self, risk_manager):
        """测试开仓"""
        result = risk_manager.open_position(
            symbol="000001.SZ",
            quantity=10000,
            price=10.0
        )
        
        assert result["success"]
        assert "000001.SZ" in risk_manager.positions
        assert risk_manager.current_capital == 900000
    
    def test_close_position(self, risk_manager):
        """测试平仓"""
        # 先开仓
        risk_manager.open_position(
            symbol="000001.SZ",
            quantity=10000,
            price=10.0
        )
        
        # 再平仓（盈利）
        result = risk_manager.close_position(
            symbol="000001.SZ",
            price=12.0
        )
        
        assert result["success"]
        assert result["realized_pnl"] == 20000.0
        assert "000001.SZ" not in risk_manager.positions
    
    def test_check_stop_loss(self, risk_manager):
        """测试止损检查"""
        # 开仓并设置止损
        risk_manager.open_position(
            symbol="000001.SZ",
            quantity=10000,
            price=10.0,
            stop_loss=9.0
        )
        
        # 更新价格到止损线以下
        risk_manager.update_prices({"000001.SZ": 8.5})
        
        # 检查风控
        triggered = risk_manager.check_risk_limits()
        
        assert len(triggered) > 0
        assert triggered[0]["type"] == "stop_loss"
    
    def test_check_max_drawdown(self, risk_manager):
        """测试最大回撤检查"""
        # 模拟大幅回撤
        risk_manager.peak_capital = 1000000
        risk_manager.current_capital = 800000  # 20%回撤
        
        triggered = risk_manager.check_risk_limits()
        
        critical_events = [
            e for e in triggered
            if e.get("level") == RiskLevel.CRITICAL
        ]
        
        assert len(critical_events) > 0
        assert critical_events[0]["type"] == "max_drawdown"
    
    def test_portfolio_summary(self, risk_manager):
        """测试组合摘要"""
        # 开两个仓位
        risk_manager.open_position("000001.SZ", 5000, 10.0)
        risk_manager.open_position("000002.SZ", 5000, 20.0)
        
        summary = risk_manager.get_portfolio_summary()
        
        assert summary["total_capital"] == 1000000
        assert summary["position_count"] == 2
        assert summary["position_value"] == 150000
        assert "risk_level" in summary


class TestKellyCriterion:
    """测试凯利公式"""
    
    def test_kelly_basic(self):
        """测试基础凯利计算"""
        # 胜率60%，盈亏比2:1
        kelly = calculate_kelly_criterion(0.6, 2.0)
        
        # f* = (0.6*2 - 0.4) / 2 = 0.4
        # 半凯利 = 0.2
        assert 0.15 < kelly < 0.25
    
    def test_kelly_zero_win_rate(self):
        """测试胜率为0"""
        kelly = calculate_kelly_criterion(0.0, 2.0)
        assert kelly == 0.0
    
    def test_kelly_negative_expectation(self):
        """测试负期望值"""
        # 胜率40%，盈亏比1:1（负期望）
        kelly = calculate_kelly_criterion(0.4, 1.0)
        assert kelly == 0.0


class TestVolatilityAdjustment:
    """测试波动率调整"""
    
    def test_high_volatility(self):
        """测试高波动率情况"""
        # 当前波动率30%，目标15%，应该减半仓位
        adjusted = calculate_volatility_adjusted_position(
            base_position=100000,
            current_volatility=0.30,
            target_volatility=0.15
        )
        
        assert adjusted == 50000
    
    def test_low_volatility(self):
        """测试低波动率情况"""
        # 当前波动率10%，目标15%，应该增加仓位
        adjusted = calculate_volatility_adjusted_position(
            base_position=100000,
            current_volatility=0.10,
            target_volatility=0.15
        )
        
        assert adjusted == 150000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
