"""
Streamlit盯盘WebUI - 实时行情监控
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime

from data.sina_realtime import SinaRealtimeData as RealtimeDataSource
from data.realtime import WatchlistManager, PriceAlert
from data.features import FeatureEngineer

# 页面配置
st.set_page_config(
    page_title="A股实时盯盘",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if 'data_source' not in st.session_state:
    st.session_state.data_source = RealtimeDataSource()
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = WatchlistManager()
if 'alert_manager' not in st.session_state:
    st.session_state.alert_manager = PriceAlert()
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# 样式定义
st.markdown("""
<style>
    .stock-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
    }
    .price-up {
        color: #ff4d4f;
        font-weight: bold;
    }
    .price-down {
        color: #52c41a;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def get_change_color(change_pct):
    """根据涨跌幅返回颜色"""
    if change_pct > 0:
        return "#ff4d4f"  # 红色（A股涨为红）
    elif change_pct < 0:
        return "#52c41a"  # 绿色
    return "#999999"


def get_change_class(change_pct):
    """获取涨跌样式类"""
    if change_pct > 0:
        return "price-up"
    elif change_pct < 0:
        return "price-down"
    return ""


# ============ 侧边栏 ============
st.sidebar.title("📊 导航")

page = st.sidebar.radio("选择页面", [
    "🏠 实时大盘",
    "⭐ 我的自选", 
    "📈 股票详情",
    "🔔 价格预警",
    "🔥 热门股票"
])

# 自动刷新设置
st.sidebar.divider()
auto_refresh = st.sidebar.checkbox("自动刷新", value=st.session_state.auto_refresh)
st.session_state.auto_refresh = auto_refresh

if auto_refresh:
    refresh_interval = st.sidebar.slider("刷新间隔(秒)", 5, 60, 10)
    time.sleep(0.1)  # 避免阻塞

# 手动刷新按钮
if st.sidebar.button("🔄 立即刷新"):
    st.session_state.last_refresh = datetime.now()
    st.rerun()

st.sidebar.caption(f"最后更新: {st.session_state.last_refresh.strftime('%H:%M:%S')}")


# ============ 页面内容 ============

if page == "🏠 实时大盘":
    st.title("🏠 A股实时大盘")
    
    # 获取指数数据
    with st.spinner("加载中..."):
        index_df = st.session_state.data_source.get_index_quotes()
    
    if not index_df.empty:
        # 主要指数
        main_indices = ['上证指数', '深证成指', '创业板指', '科创50']
        cols = st.columns(4)
        
        for idx, (col, index_name) in enumerate(zip(cols, main_indices)):
            row = index_df[index_df['name'] == index_name]
            if not row.empty:
                row = row.iloc[0]
                change_pct = float(row['change_pct'])
                color = get_change_color(change_pct)
                
                with col:
                    st.markdown(f"""
                    <div style='background-color: {"#fff2f0" if change_pct > 0 else "#f6ffed"}; 
                                padding: 15px; border-radius: 10px; text-align: center;'>
                        <h4>{index_name}</h4>
                        <h2 style='color: {color};'>{row['price']}</h2>
                        <p style='color: {color};'>{change_pct:+.2f}%  {row['change']:+.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        
        # 全部指数表格
        st.subheader("全部指数")
        display_df = index_df[['name', 'price', 'change_pct', 'change']].copy()
        display_df.columns = ['指数名称', '最新价', '涨跌幅(%)', '涨跌额']
        
        def highlight_change(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: #ff4d4f'
                elif val < 0:
                    return 'color: #52c41a'
            return ''
        
        styled_df = display_df.style.applymap(highlight_change, subset=['涨跌幅(%)', '涨跌额'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.error("无法获取指数数据，请检查网络连接")


elif page == "⭐ 我的自选":
    st.title("⭐ 我的自选股")
    
    # 添加自选股
    col1, col2 = st.columns([3, 1])
    with col1:
        new_symbol = st.text_input("添加股票代码", placeholder="输入股票代码，如：000001")
    with col2:
        if st.button("➕ 添加", use_container_width=True):
            if new_symbol:
                # 获取股票名称
                info = st.session_state.data_source.get_single_stock(new_symbol)
                if info:
                    st.session_state.watchlist.add(
                        new_symbol, 
                        info['name'],
                        note=f"添加于 {datetime.now().strftime('%m-%d')}"
                    )
                    st.success(f"已添加: {info['name']} ({new_symbol})")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("股票代码无效")
    
    # 获取自选股列表
    watchlist = st.session_state.watchlist.get_list()
    
    if watchlist:
        symbols = [s['symbol'] for s in watchlist]
        
        with st.spinner("加载实时行情..."):
            quotes_df = st.session_state.data_source.get_realtime_quotes(symbols)
        
        if not quotes_df.empty:
            # 合并自选股信息和行情
            merged_data = []
            for item in watchlist:
                symbol = item['symbol']
                quote = quotes_df[quotes_df['symbol'] == symbol]
                
                if not quote.empty:
                    q = quote.iloc[0]
                    merged_data.append({
                        'symbol': symbol,
                        'name': item['name'] or q.get('name', ''),
                        'price': float(q.get('price', 0)),
                        'change_pct': float(q.get('change_pct', 0)),
                        'change': float(q.get('change', 0)),
                        'volume': int(q.get('volume', 0)),
                        'turnover': float(q.get('turnover', 0)),
                        'note': item.get('note', '')
                    })
            
            # 显示自选股卡片
            for stock in merged_data:
                change_pct = stock['change_pct']
                color = get_change_color(change_pct)
                
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
                
                with col1:
                    st.markdown(f"**{stock['name']}**  
                                `{stock['symbol']}`")
                
                with col2:
                    st.markdown(f""<h3 style='color: {color};'>{stock['price']:.2f}</h3>""")
                
                with col3:
                    st.markdown(f""<p style='color: {color};'>{change_pct:+.2f}%  {stock['change']:+.2f}</p>""")
                
                with col4:
                    if stock['note']:
                        st.caption(f"备注: {stock['note']}")
                
                with col5:
                    if st.button("🗑️", key=f"del_{stock['symbol']}"):
                        st.session_state.watchlist.remove(stock['symbol'])
                        st.rerun()
                
                st.divider()
            
            # 检查预警
            alerts = st.session_state.alert_manager.check_alerts(quotes_df)
            if alerts:
                for alert in alerts:
                    st.toast(f"🚨 预警触发: {alert['symbol']} {alert['type']} {alert['threshold']}", icon="🔔")
        else:
            st.warning("无法获取实时行情")
    else:
        st.info("自选股列表为空，请添加股票")


elif page == "📈 股票详情":
    st.title("📈 股票详情")
    
    symbol = st.text_input("股票代码", placeholder="输入股票代码查看详情")
    
    if symbol:
        # 获取实时数据
        info = st.session_state.data_source.get_single_stock(symbol)
        
        if info:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                change_pct = info['change_pct']
                color = get_change_color(change_pct)
                st.metric("最新价", f"{info['price']:.2f}", f"{change_pct:+.2f}%")
            
            with col2:
                st.metric("涨跌额", f"{info['change']:+.2f}")
            
            with col3:
                st.metric("成交量", f"{info['volume']/10000:.0f}万")
            
            with col4:
                st.metric("换手率", f"{info['turnover']:.2f}%")
            
            st.divider()
            
            # K线图
            st.subheader("K线图")
            with st.spinner("加载K线数据..."):
                kline_df = st.session_state.data_source.get_stock_kline(symbol)
            
            if not kline_df.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=kline_df['date'],
                    open=kline_df['open'],
                    high=kline_df['high'],
                    low=kline_df['low'],
                    close=kline_df['close'],
                    name='K线'
                )])
                
                fig.update_layout(
                    title=f"{info['name']} ({symbol}) 日线",
                    xaxis_rangeslider_visible=False,
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 技术指标
                st.subheader("技术指标")
                engineer = FeatureEngineer()
                features = engineer.calculate_all_features(kline_df)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("RSI(14)", f"{features['rsi_14'].iloc[-1]:.2f}")
                with col2:
                    st.metric("MACD", f"{features['macd'].iloc[-1]:.4f}")
                with col3:
                    st.metric("ATR(14)", f"{features['atr_14'].iloc[-1]:.2f}")
            else:
                st.error("无法获取K线数据")
        else:
            st.error("股票代码无效")


elif page == "🔔 价格预警":
    st.title("🔔 价格预警")
    
    # 添加预警
    with st.expander("➕ 添加新预警"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            alert_symbol = st.text_input("股票代码", key="alert_symbol")
        
        with col2:
            alert_type = st.selectbox("预警类型", [
                ("price_above", "价格高于"),
                ("price_below", "价格低于"),
                ("change_above", "涨幅高于(%)"),
                ("change_below", "跌幅低于(%)")
            ], format_func=lambda x: x[1])[0]
        
        with col3:
            threshold = st.number_input("阈值", value=10.0)
        
        note = st.text_input("备注（可选）")
        
        if st.button("添加预警"):
            if alert_symbol:
                st.session_state.alert_manager.add_alert(
                    alert_symbol, alert_type, threshold, note
                )
                st.success("预警添加成功")
                time.sleep(0.5)
                st.rerun()
    
    # 显示预警列表
    st.subheader("当前预警")
    alerts = st.session_state.alert_manager.get_active_alerts()
    
    if alerts:
        for alert in alerts:
            type_names = {
                'price_above': '价格高于',
                'price_below': '价格低于',
                'change_above': '涨幅高于',
                'change_below': '跌幅低于'
            }
            
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{alert['symbol']}** - {type_names.get(alert['type'], alert['type'])} {alert['threshold']}")
            
            with col2:
                if alert['note']:
                    st.caption(alert['note'])
            
            with col3:
                if st.button("删除", key=f"del_alert_{alert['id']}"):
                    st.session_state.alert_manager.remove_alert(alert['id'])
                    st.rerun()
    else:
        st.info("暂无预警设置")


elif page == "🔥 热门股票":
    st.title("🔥 热门股票")
    
    tab1, tab2 = st.tabs(["📈 涨幅榜", "📉 跌幅榜"])
    
    with st.spinner("加载热门股票..."):
        hot_df = st.session_state.data_source.get_hot_stocks(50)
    
    if not hot_df.empty:
        with tab1:
            gainers = hot_df.head(20)
            display_cols = ['symbol', 'name', 'price', 'change_pct']
            st.dataframe(
                gainers[display_cols],
                column_config={
                    'symbol': '代码',
                    'name': '名称',
                    'price': '最新价',
                    'change_pct': st.column_config.NumberColumn('涨跌幅(%)', format='%.2f%%')
                },
                use_container_width=True
            )
        
        with tab2:
            losers = hot_df.tail(20).iloc[::-1]
            display_cols = ['symbol', 'name', 'price', 'change_pct']
            st.dataframe(
                losers[display_cols],
                column_config={
                    'symbol': '代码',
                    'name': '名称',
                    'price': '最新价',
                    'change_pct': st.column_config.NumberColumn('涨跌幅(%)', format='%.2f%%')
                },
                use_container_width=True
            )
    else:
        st.error("无法获取热门股票数据")


# 自动刷新
if st.session_state.auto_refresh:
    time.sleep(refresh_interval)
    st.session_state.last_refresh = datetime.now()
    st.rerun()
