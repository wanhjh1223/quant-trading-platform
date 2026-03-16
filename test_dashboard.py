"""
测试盯盘功能
"""
import sys
sys.path.insert(0, './src')

from data.realtime import RealtimeDataSource, WatchlistManager, PriceAlert

def test_realtime_data():
    """测试实时数据获取"""
    print("=" * 50)
    print("测试实时数据获取")
    print("=" * 50)
    
    source = RealtimeDataSource()
    
    # 测试单只股票
    print("\n[1/3] 测试单只股票...")
    info = source.get_single_stock("000001")
    if info:
        print(f"✓ 成功获取: {info['name']} ({info['symbol']})")
        print(f"  价格: {info['price']}, 涨跌幅: {info['change_pct']}%")
    else:
        print("✗ 获取失败")
    
    # 测试指数
    print("\n[2/3] 测试大盘指数...")
    index_df = source.get_index_quotes()
    if not index_df.empty:
        print(f"✓ 成功获取 {len(index_df)} 个指数")
        sh = index_df[index_df['name'] == '上证指数']
        if not sh.empty:
            print(f"  上证指数: {sh.iloc[0]['price']}")
    else:
        print("✗ 获取失败")
    
    # 测试热门股票
    print("\n[3/3] 测试热门股票...")
    hot_df = source.get_hot_stocks(5)
    if not hot_df.empty:
        print(f"✓ 成功获取 {len(hot_df)} 只热门股票")
        print(f"  涨幅第一: {hot_df.iloc[0]['name']} +{hot_df.iloc[0]['change_pct']}%")
    else:
        print("✗ 获取失败")
    
    print("\n" + "=" * 50)

def test_watchlist():
    """测试自选股管理"""
    print("\n" + "=" * 50)
    print("测试自选股管理")
    print("=" * 50)
    
    manager = WatchlistManager('./tests/test_watchlist.json')
    
    # 添加测试股票
    print("\n[1/2] 添加自选股...")
    manager.add('000001', '平安银行', '测试添加')
    manager.add('600000', '浦发银行')
    print(f"✓ 当前自选数量: {len(manager.get_list())}")
    
    # 获取列表
    print("\n[2/2] 获取自选股列表...")
    symbols = manager.get_symbols()
    print(f"✓ 股票代码: {symbols}")
    
    print("\n" + "=" * 50)

def test_alerts():
    """测试预警系统"""
    print("\n" + "=" * 50)
    print("测试预警系统")
    print("=" * 50)
    
    alerts = PriceAlert('./tests/test_alerts.json')
    
    # 添加预警
    print("\n[1/2] 添加价格预警...")
    alerts.add_alert('000001', 'price_above', 15.0, '突破15元')
    print(f"✓ 当前预警数量: {len(alerts.get_active_alerts())}")
    
    print("\n[2/2] 检查预警触发...")
    # 模拟行情数据
    import pandas as pd
    test_quotes = pd.DataFrame([
        {'symbol': '000001', 'price': 15.5, 'change_pct': 3.0}
    ])
    triggered = alerts.check_alerts(test_quotes)
    print(f"✓ 触发预警数量: {len(triggered)}")
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    try:
        test_realtime_data()
        test_watchlist()
        test_alerts()
        print("\n🎉 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
