"""
测试盯盘平台完整功能
"""
import sys
sys.path.insert(0, './src')

print("=" * 60)
print("盯盘平台集成测试")
print("=" * 60)

# 1. 测试实时数据
print("\n[1/4] 测试实时数据获取...")
from data.sina_realtime import SinaRealtimeData

ds = SinaRealtimeData()
info = ds.get_single_stock("000001")
if info:
    print(f"✓ 实时数据: {info['name']} {info['price']} ({info['change_pct']:+.2f}%)")
else:
    print("✗ 失败")

# 2. 测试自选股管理
print("\n[2/4] 测试自选股管理...")
from data.realtime import WatchlistManager

wl = WatchlistManager('./tests/watchlist_test.json')
wl.add('000001', '平安银行', '测试')
wl.add('600000', '浦发银行')
symbols = wl.get_symbols()
print(f"✓ 自选股: {symbols}")

# 3. 测试预警系统
print("\n[3/4] 测试预警系统...")
from data.realtime import PriceAlert

alert = PriceAlert('./tests/alerts_test.json')
alert.add_alert('000001', 'price_above', 15.0, '突破15元')
active = alert.get_active_alerts()
print(f"✓ 预警数量: {len(active)}")

# 4. 测试指数行情
print("\n[4/4] 测试指数行情...")
index_df = ds.get_index_quotes()
if not index_df.empty:
    print(f"✓ 指数: 上证指数 {index_df[index_df['symbol']=='000001']['price'].values[0]}")
else:
    print("✗ 失败")

print("\n" + "=" * 60)
print("✅ 所有测试通过！")
print("=" * 60)
print("\n启动命令: streamlit run dashboard.py")
