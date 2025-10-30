import streamlit as st
import pandas as pd
import numpy as np
import io
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 设置页面配置
st.set_page_config(
    page_title="策略可视化应用",
    page_icon="📊",
    layout="wide"
)

# 页面标题
st.title("量化策略实盘监控")

# 数据URL
DATA_URL = "https://gist.githubusercontent.com/lawrencesun1011/a896403c442e4f8d13cb6ecb9e331b48/raw/data.csv"

# 加载数据的函数
@st.cache_data

def calculate_drawdown(equity_series):
    # 计算累计最大值
    running_max = equity_series.cummax()
    # 计算回撤
    drawdown = (equity_series - running_max) / running_max * 100
    return drawdown

def load_data():
    try:
        # 直接从URL读取数据到内存
        response = requests.get(DATA_URL)
        response.raise_for_status()  # 检查请求是否成功
        
        # 使用io.BytesIO处理响应内容
        data = pd.read_csv(
            io.BytesIO(response.content),
            # index_col=0,  # 第一列作为行索引
            parse_dates=['time']  # 解析time列为日期
        )
        
        # 检查必需的列是否存在
        if 'time' not in data.columns:
            st.error("数据中缺少 'time' 列")
            return None
        if '账户总净值' not in data.columns:
            st.error("数据中缺少 '账户总净值' 列")
            return None
        
        # 计算回撤
        data['drawdown'] = calculate_drawdown(data['账户总净值'])
        
        # 计算归一化净值（从1开始）
        data['归一化净值'] = data['账户总净值'] / data['账户总净值'].iloc[0]
        
        return data
    except Exception as e:
        st.error(f"加载数据时出错: {str(e)}")
        return None

# 加载数据
with st.spinner("正在加载数据..."):
    df = load_data()

if df is not None:
    # 显示数据统计信息
    st.subheader("数据统计信息")
    st.write("数据行数:", len(df))
    st.write("时间范围:", df['time'].min(), "至", df['time'].max())
    
    # 绘制图表
    st.subheader("净值曲线图")
    
    # 创建双Y轴图表
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 添加归一化净值曲线（左Y轴，从1开始）
    fig.add_trace(
        go.Scatter(
            x=df['time'], 
            y=df['归一化净值'], 
            name='归一化净值', 
            line=dict(color='#1f77b4'),
            hovertemplate='时间: %{x|%Y-%m-%d}<br>归一化净值: %{y:.4f}<extra></extra>'
        ),
        secondary_y=False,
    )
    
    # 添加回撤区域（右Y轴，灰色阴影，无边框）
    fig.add_trace(
        go.Scatter(
            x=df['time'], 
            y=df['drawdown'], 
            name='回撤(%)', 
            fill='tozeroy', 
            fillcolor='rgba(169, 169, 169, 0.3)', 
            line=dict(width=0),
            hovertemplate='时间: %{x|%Y-%m-%d}<br>回撤: %{y:.2f}%<extra></extra>'
        ),
        secondary_y=True,
    )
    
    # 更新布局
    fig.update_layout(
        title='净值曲线与回撤',
        height=600,  # 增加高度以提供更好的视觉效果
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified',  # 统一的悬停模式，显示同一时间点的所有数据
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        )
    )
    
    # 设置Y轴标签
    fig.update_xaxes(title_text='时间')
    fig.update_yaxes(title_text='归一化净值', secondary_y=False)
    fig.update_yaxes(title_text='回撤(%)', secondary_y=True)
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)
    
    # 计算并显示关键指标
    current_capital = df['账户总净值'].iloc[-1]  # 当前资金
    max_capital = df['账户总净值'].max()  # 最大资金
    min_capital = df['账户总净值'].min()  # 最小资金
    current_dd = df['drawdown'].iloc[-1]  # 当前回撤百分比
    max_dd = df['drawdown'].min()  # 最大回撤百分比
    st.info(f"当前资金: {current_capital:.2f} | 最大资金: {max_capital:.2f} | 最小资金: {min_capital:.2f}")
    st.info(f"当前回撤: {current_dd:.2f}% | 最大回撤: {max_dd:.2f}%")

# 侧边栏信息
with st.sidebar:
    st.header("关于")
    st.info(
        "这是用于量化策略实盘验证和监测的应用，展示净值曲线以及回撤。"
    )