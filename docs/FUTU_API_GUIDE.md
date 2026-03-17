# 富途OpenAPI 接入指南

## 架构说明
```
Python程序 → FutuAPI(Python SDK) → OpenD网关 → 富途服务器 → 交易所
```

## 安装步骤

### 1. 安装OpenD网关
下载地址：https://www.futunn.com/OpenAPI
- 支持Windows/MacOS/Linux(CentOS/Ubuntu)
- 运行在本地或云端服务器
- 默认端口：11111

### 2. 安装Python SDK
```bash
pip install futu-api
```

### 3. 启动OpenD
```bash
# Linux/Mac
./OpenD

# 首次启动需配置牛牛号和密码
```

## 核心接口

### 行情接口 (OpenQuoteContext)
- `get_market_snapshot` - 获取实时行情
- `get_order_book` - 获取摆盘数据
- `subscribe` - 订阅实时推送
- `get_history_kline` - 获取历史K线

### 交易接口 (OpenSecTradeContext)
- `place_order` - 下单
- `cancel_order` - 撤单
- `modify_order` - 改单
- `get_order_list` - 查询订单
- `get_position_list` - 查询持仓

## 代码示例

### 获取行情
```python
from futu import OpenQuoteContext

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
ret, data = quote_ctx.get_market_snapshot(['HK.00700'])
if ret == 0:
    print(data)
quote_ctx.close()
```

### 模拟交易下单
```python
from futu import OpenSecTradeContext, TrdEnv, OrderType, TrdSide

trade_ctx = OpenSecTradeContext(host='127.0.0.1', port=11111)
# 模拟环境下单
ret, data = trade_ctx.place_order(
    price=500.0,
    qty=100,
    code="HK.00700",
    trd_side=TrdSide.BUY,
    order_type=OrderType.NORMAL,
    trd_env=TrdEnv.SIMULATE  # 模拟环境
)
trade_ctx.close()
```

## 权限说明

| 权限 | 说明 |
|------|------|
| BMP | 基础行情（延迟15分钟） |
| LV1 | 实时行情 |
| LV2 | 深度行情（摆盘、逐笔） |

## 限制
- 行情接口：30秒内最多请求30次
- 订阅额度：同时最多订阅1000只股票
- 历史K线：每30天最多拉取一定额度

## 参考文档
- 官方文档：https://openapi.futunn.com/
- Python SDK：https://github.com/FutunnOpen/py-futu-api
