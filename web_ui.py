"""
Streamlit可视化界面
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data.storage import DataStore
from data.features import FeatureEngineer
from strategies.backtest import BacktestEngine, example_strategy


st.set_page_config(
    page_title="AI量化交易平台",
    page_icon="📈",
    layout="wide"
)


def load_data(symbol: str, data_dir: str = './data'):
    """加载股票数据"""
    store = DataStore(data_dir)
    return store.load_daily_data(symbol)


def plot_candlestick(df: pd.DataFrame, title: str = "K线图"):
    """绘制K线图"""
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3]
    )
    
    # K线
    fig.add_trace(
        go.Candlestick(
            x=df['trade_date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线'
        ),
        row=1, col=1
    )
    
    # 成交量
    if 'vol' in df.columns or 'volume' in df.columns:
        vol_col = 'vol' if 'vol' in df.columns else 'volume'
        colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] else 'green' 
                 for i in range(len(df))]
        fig.add_trace(
            go.Bar(x=df['trade_date'], y=df[vol_col], marker_color=colors, name='成交量'),
            row=2, col=1
        )
    
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=600
    )
    
    return fig


def plot_technical_indicators(df: pd.DataFrame):
    """绘制技术指标"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('价格与均线', 'RSI', 'MACD')
    )
    
    # 价格与均线
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['close'], name='收盘价'), row=1, col=1)
    if 'sma_20' in df.columns:
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['sma_20'], name='SMA20'), row=1, col=1)
    if 'sma_60' in df.columns:
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['sma_60'], name='SMA60'), row=1, col=1)
    
    # RSI
    if 'rsi_14' in df.columns:
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['rsi_14'], name='RSI14'), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    if 'macd' in df.columns:
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['macd'], name='MACD'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['macd_signal'], name='Signal'), row=3, col=1)
    
    fig.update_layout(height=800)
    return fig


def plot_backtest_results(results: dict):
    """绘制回测结果"""
    if not results or 'daily_values' not in results:
        return None
    
    df = results['daily_values']
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('净值曲线', '回撤')
    )
    
    # 净值曲线
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['total_value'], name='总资产', line=dict(color='blue')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=[results['initial_cash']] * len(df), 
                  name='初始资金', line=dict(color='gray', dash='dash')),
        row=1, col=1
    )
    
    # 回撤
    cummax = df['total_value'].cummax()
    drawdown = (df['total_value'] - cummax) / cummax * 100
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=drawdown, name='回撤%', fill='tozeroy', 
                  fillcolor='rgba(255,0,0,0.3)', line=dict(color='red')),
        row=2, col=1
    )
    
    fig.update_layout(height=600, title="回测结果")
    return fig


# ====== Streamlit界面 ======

st.title("📈 AI量化交易平台")

# 侧边栏
st.sidebar.header("导航")
page = st.sidebar.radio("选择页面", [
    "🏠 首页",
    "📊 行情查看",
    "📈 技术指标",
    "🔄 回测",
    "🤖 AI预测"
])

if page == "🏠 首页":
    st.header("欢迎使用AI量化交易平台")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("股票数量", "待下载")
    with col2:
        st.metric("策略数量", "1")
    with col3:
        st.metric("AI模型", "LSTM/Transformer")
    
    st.markdown("""
    ### 功能模块
    1. **📊 行情查看** - K线图、成交量分析
    2. **📈 技术指标** - 自动计算RSI/MACD/布林带等
    3. **🔄 回测引擎** - 事件驱动回测，支持自定义策略
    4. **🤖 AI预测** - 深度学习价格预测
    
    ### 快速开始
    1. 在"行情查看"页面输入股票代码（如 000001.SZ）
    2. 使用"技术指标"页面分析走势
    3. 在"回测"页面测试策略
    """)

elif page == "📊 行情查看":
    st.header("📊 行情查看")
    
    symbol = st.text_input("股票代码", value="000001.SZ", help="格式: 000001.SZ 或 600000.SH")
    
    if st.button("加载数据"):
        df = load_data(symbol)
        
        if df is not None:
            st.success(f"成功加载 {len(df)} 条数据")
            
            # 基础统计
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("最新价", f"{df['close'].iloc[-1]:.2f}")
            with col2:
                change = (df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100
                st.metric("涨跌幅", f"{change:.2f}%", delta=f"{change:.2f}%")
            with col3:
                st.metric("成交量", f"{df['vol'].iloc[-1]/1e6:.2f}M")
            with col4:
                st.metric("区间最高", f"{df['high'].max():.2f}")
            
            # K线图
            fig = plot_candlestick(df, f"{symbol} K线图")
            st.plotly_chart(fig, use_container_width=True)
            
            # 原始数据
            with st.expander("查看原始数据"):
                st.dataframe(df.tail(20))
        else:
            st.error(f"未找到 {symbol} 数据，请先使用 download_data.py 下载")

elif page == "📈 技术指标":
    st.header("📈 技术指标分析")
    
    symbol = st.text_input("股票代码", value="000001.SZ")
    
    col1, col2 = st.columns(2)
    with col1:
        sma_short = st.slider("短期均线", 5, 30, 20)
    with col2:
        sma_long = st.slider("长期均线", 30, 120, 60)
    
    if st.button("计算指标"):
        df = load_data(symbol)
        
        if df is not None:
            # 计算特征
            engineer = FeatureEngineer()
            df_features = engineer.calculate_all_features(df)
            
            st.success("技术指标计算完成")
            
            # 指标概览
            st.subheader("指标概览")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("RSI(14)", f"{df_features['rsi_14'].iloc[-1]:.2f}")
            with col2:
                st.metric("MACD", f"{df_features['macd'].iloc[-1]:.4f}")
            with col3:
                st.metric("ATR", f"{df_features['atr_14'].iloc[-1]:.2f}")
            with col4:
                st.metric("波动率", f"{df_features['volatility'].iloc[-1]:.4f}")
            
            # 技术指标图
            fig = plot_technical_indicators(df_features)
            st.plotly_chart(fig, use_container_width=True)
            
            # 特征列表
            with st.expander("查看全部特征"):
                feature_cols = [c for c in df_features.columns if c not in ['open', 'high', 'low', 'close', 'vol']]
                st.dataframe(df_features[feature_cols].tail(20))
        else:
            st.error("数据不存在，请先下载")

elif page == "🔄 回测":
    st.header("🔄 策略回测")
    
    symbol = st.text_input("股票代码", value="000001.SZ")
    
    col1, col2 = st.columns(2)
    with col1:
        initial_cash = st.number_input("初始资金", value=100000, step=10000)
    with col2:
        commission = st.slider("佣金率", 0.0001, 0.001, 0.0003, format="%.4f")
    
    strategy_option = st.selectbox(
        "选择策略",
        ["双均线交叉", "RSI超买超卖"]
    )
    
    if st.button("运行回测"):
        df = load_data(symbol)
        
        if df is not None and len(df) > 60:
            with st.spinner("回测运行中..."):
                engine = BacktestEngine(
                    initial_cash=initial_cash,
                    commission_rate=commission
                )
                
                # 使用示例策略
                engine.set_strategy(example_strategy)
                results = engine.run(df)
            
            # 显示结果
            st.success("回测完成")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总收益率", f"{results['total_return']*100:.2f}%")
            with col2:
                st.metric("年化收益", f"{results['annual_return']*100:.2f}%")
            with col3:
                st.metric("最大回撤", f"{results['max_drawdown']*100:.2f}%")
            with col4:
                st.metric("夏普比率", f"{results['sharpe_ratio']:.2f}")
            
            # 净值曲线
            fig = plot_backtest_results(results)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # 交易记录
            with st.expander("查看交易记录"):
                trades_df = pd.DataFrame([
                    {
                        '时间': t.timestamp,
                        '方向': t.side.value,
                        '数量': t.quantity,
                        '价格': f"{t.price:.2f}",
                        '佣金': f"{t.commission:.2f}"
                    }
                    for t in results['trades']
                ])
                st.dataframe(trades_df)
        else:
            st.error("数据不足或不存在，需要至少60天的数据")

elif page == "🤖 AI预测":
    st.header("🤖 AI价格预测")
    
    st.info("AI预测功能需要预先训练模型")
    
    symbol = st.text_input("股票代码", value="000001.SZ")
    model_type = st.selectbox("模型类型", ["LSTM", "Transformer"])
    
    col1, col2 = st.columns(2)
    with col1:
        seq_len = st.slider("历史序列长度", 10, 60, 20)
    with col2:
        pred_horizon = st.slider("预测周期", 1, 10, 1)
    
    if st.button("训练模型"):
        st.warning("训练功能需要完整数据，当前为演示界面")
        st.info("实际使用步骤:\n1. 准备训练数据\n2. 训练LSTM/Transformer模型\n3. 进行价格预测")
