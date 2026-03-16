"""
简单测试盯盘功能
"""
import sys
sys.path.insert(0, './src')

print("测试实时数据源...")
from data.realtime import RealtimeDataSource

source = RealtimeDataSource()

print("\n[1/2] 获取单只股票 (000001 平安银行)...")
info = source.get_single_stock("000001")
if info:
    print(f"✓ 成功: {info['name']} 价格:{info['price']} 涨跌:{info['change_pct']}%")
else:
    print("✗ 失败")

print("\n[2/2] 获取大盘指数...")
df = source.get_index_quotes()
if not df.empty:
    print(f"✓ 成功: 获取到 {len(df)} 个指数")
    for _, row in df.head(3).iterrows():
        print(f"  {row['name']}: {row['price']} ({row['change_pct']}%)")
else:
    print("✗ 失败")

print("\n测试完成!")
