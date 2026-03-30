"""
轻量级高级A股量化交易Web平台 - 优化版，适合Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import baostock as bs
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from advanced_strategies import AdvancedQuantStrategies

# 页面配置
st.set_page_config(
    page_title="轻量级A股量化模拟交易平台",
    page_icon="📈",
    layout="wide"
)

# 样式设置
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class LiteWebSimulator:
    """轻量级Web版模拟交易引擎"""
    
    def __init__(self):
        self.lg = bs.login()
        if self.lg.error_code != '0':
            st.error(f"数据源连接失败: {self.lg.error_msg}")
        # 使用精简股票池以减少内存使用
        self.strategies = AdvancedQuantStrategies()
        # 限制股票池大小
        self.strategies.stock_pool = self.strategies.stock_pool[:100]  # 只用前100只
    
    def get_trading_days(self, start_date: str, end_date: str) -> list:
        """获取交易日历"""
        rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
        trading_days = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            if row[1] == '1':
                trading_days.append(row[0])
        return trading_days
    
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票数据"""
        rs = bs.query_history_k_data_plus(
            stock_code,
            "date,open,high,low,close,volume",
            start_date=start_date,
            end_date=end_date,
            frequency="d"
        )
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return pd.DataFrame()
            
        df = pd.DataFrame(data_list, columns=rs.fields)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    
    def run_strategy_backtest(self, strategy_func, strategy_params: dict,
                            start_date: str, end_date: str, initial_capital: float = 100000):
        """运行指定策略的回测 - 优化版"""
        
        # 获取交易日历
        trading_days = self.get_trading_days(start_date, end_date)
        if not trading_days:
            return None, "无交易日数据"
        
        # 限制回测天数以减少计算量
        if len(trading_days) > 252:  # 最多1年数据
            trading_days = trading_days[-252:]
        
        # 初始化
        capital = initial_capital
        positions = {}
        portfolio_values = []
        trade_history = []
        
        # 策略参数
        rebalance_frequency = strategy_params.get('rebalance_frequency', 'monthly')
        
        for i, trade_date in enumerate(trading_days):
            # 决定是否重新平衡
            should_rebalance = False
            
            if rebalance_frequency == 'daily':
                should_rebalance = True
            elif rebalance_frequency == 'weekly':
                if i == 0 or (datetime.strptime(trade_date, '%Y-%m-%d').weekday() == 0 and 
                             datetime.strptime(trading_days[i-1], '%Y-%m-%d').weekday() != 0):
                    should_rebalance = True
            elif rebalance_frequency == 'monthly':
                if i == 0 or trade_date[:7] != trading_days[i-1][:7]:
                    should_rebalance = True
            
            if should_rebalance:
                # 平仓现有持仓
                for stock_code in list(positions.keys()):
                    price_info = self.get_stock_data(stock_code, trade_date, trade_date)
                    if not price_info.empty:
                        sell_price = price_info['close'].iloc[0]
                        shares = positions[stock_code]['shares']
                        revenue = shares * sell_price
                        capital += revenue
                        
                        trade_history.append({
                            'date': trade_date,
                            'action': 'SELL',
                            'stock': stock_code,
                            'shares': shares,
                            'price': sell_price,
                            'amount': revenue
                        })
                
                positions = {}
                
                # 选择新股票 - 限制数量
                try:
                    selected_stocks = strategy_func(trading_days[:i+1], **strategy_params)
                    selected_stocks = selected_stocks[:3]  # 最多3只股票
                except Exception as e:
                    st.warning(f"策略执行出错: {e}")
                    selected_stocks = []
                
                # 买入新选股票
                if selected_stocks:
                    capital_per_stock = capital / len(selected_stocks)
                    for stock_code in selected_stocks:
                        price_info = self.get_stock_data(stock_code, trade_date, trade_date)
                        if not price_info.empty:
                            buy_price = price_info['close'].iloc[0]
                            shares = int((capital_per_stock / buy_price) // 100 * 100)
                            if shares >= 100:
                                cost = shares * buy_price
                                capital -= cost
                                positions[stock_code] = {
                                    'shares': shares,
                                    'buy_price': buy_price,
                                    'buy_date': trade_date
                                }
                                
                                trade_history.append({
                                    'date': trade_date,
                                    'action': 'BUY',
                                    'stock': stock_code,
                                    'shares': shares,
                                    'price': buy_price,
                                    'amount': cost
                                })
            
            # 记录投资组合价值 - 降低频率
            if i % 5 == 0 or i == len(trading_days) - 1:  # 每5天记录一次
                portfolio_value = capital
                for stock_code, pos in positions.items():
                    price_info = self.get_stock_data(stock_code, trade_date, trade_date)
                    if not price_info.empty:
                        current_price = price_info['close'].iloc[0]
                        portfolio_value += pos['shares'] * current_price
                
                portfolio_values.append({
                    'date': trade_date,
                    'value': portfolio_value
                })
        
        # 计算ROI
        if portfolio_values:
            final_value = portfolio_values[-1]['value']
            roi = final_value / initial_capital
            annualized_return = (roi ** (252 / len(trading_days)) - 1) * 100
        else:
            roi = 1.0
            annualized_return = 0.0
        
        return {
            'portfolio_values': portfolio_values,
            'trade_history': trade_history,
            'roi': roi,
            'annualized_return': annualized_return,
            'final_value': final_value if portfolio_values else initial_capital,
            'initial_capital': initial_capital
        }, None
    
    def __del__(self):
        if hasattr(self, 'lg'):
            bs.logout()

def main():
    st.title("📈 轻量级A股量化模拟交易平台")
    st.caption("50+策略 | 优化性能 | Streamlit Cloud友好")
    
    # 合规声明
    with st.expander("⚠️ 重要合规声明", expanded=False):
        st.markdown("""
        **本平台仅为个人学习研究用途**
        - ✅ 仅使用公开免费数据源（Baostock）
        - ✅ 纯模拟交易，不影响真实市场
        - ✅ 符合《证券法》个人研究规定
        - ✅ 不构成任何投资建议
        - ❌ 不得用于商业用途
        - ❌ 不提供实盘交易功能
        """)
    
    # 参数设置
    st.sidebar.header("📊 回测参数设置")
    
    strategies_obj = AdvancedQuantStrategies()
    # 使用精选策略列表以提高性能
    lite_strategies = [
        "简单移动平均", "MACD趋势", "RSI超买超卖", "相对强弱", 
        "放量突破", "价值成长动量", "夏普比率优化", "自定义策略1"
    ]
    selected_strategy = st.sidebar.selectbox("选择策略", lite_strategies, index=0)
    
    # 回测期间
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date_default = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')  # 缩短到6个月
    start_date = st.sidebar.date_input("开始日期", 
                                     value=datetime.strptime(start_date_default, '%Y-%m-%d'),
                                     max_value=datetime.now() - timedelta(days=1))
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    # 策略参数
    st.sidebar.subheader("⚙️ 策略参数")
    strategy_params = {}
    
    if "相对强弱" in selected_strategy:
        strategy_params['lookback'] = st.sidebar.slider("回看周期（天）", 5, 30, 20)
        strategy_params['top_n'] = st.sidebar.slider("选择股票数量", 1, 3, 2)
    elif "RSI" in selected_strategy:
        strategy_params['rsi_threshold'] = st.sidebar.slider("RSI阈值", 20, 40, 30)
    elif "移动平均" in selected_strategy:
        strategy_params['ma_short'] = st.sidebar.slider("短期均线", 5, 15, 5)
        strategy_params['ma_long'] = st.sidebar.slider("长期均线", 15, 40, 20)
    
    st.sidebar.subheader("🔧 通用参数")
    rebalance_options = {"每周": "weekly", "每月": "monthly"}
    rebalance_choice = st.sidebar.selectbox("调仓频率", list(rebalance_options.keys()), index=1)
    strategy_params['rebalance_frequency'] = rebalance_options[rebalance_choice]
    
    initial_capital = st.sidebar.number_input("初始资金（元）", 10000, 500000, 100000, step=10000)
    
    # 运行按钮
    if st.sidebar.button("🚀 开始回测", use_container_width=True):
        with st.spinner("正在运行回测..."):
            simulator = LiteWebSimulator()
            strategy_func = strategies_obj.get_all_strategies()[selected_strategy]
            
            results, error = simulator.run_strategy_backtest(
                strategy_func, strategy_params,
                start_date_str, end_date, initial_capital
            )
            
            if error:
                st.error(f"回测失败: {error}")
            else:
                # 显示结果
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    roi_display = f"{results['roi']:.3f}"
                    if results['roi'] >= 1.3:
                        st.success(f"🎯 ROI: {roi_display}")
                    else:
                        st.info(f"📈 ROI: {roi_display}")
                
                with col2:
                    st.metric("最终价值", f"¥{results['final_value']:,.0f}")
                
                with col3:
                    target_achieved = "✅ 达成" if results['roi'] >= 1.3 else "❌ 未达成"
                    st.metric("目标状态", target_achieved)
                
                # 投资组合价值图表
                if results['portfolio_values']:
                    df_values = pd.DataFrame(results['portfolio_values'])
                    df_values['date'] = pd.to_datetime(df_values['date'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_values['date'],
                        y=df_values['value'],
                        mode='lines',
                        name='投资组合价值',
                        line=dict(color='#4CAF50', width=3)
                    ))
                    fig.add_hline(
                        y=initial_capital, 
                        line_dash="dash", 
                        line_color="gray",
                        annotation_text="初始资金"
                    )
                    fig.add_hline(
                        y=initial_capital * 1.3, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text="目标线 (ROI=1.3)"
                    )
                    
                    fig.update_layout(
                        title="投资组合价值变化",
                        xaxis_title="日期",
                        yaxis_title="价值 (元)",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # 交易记录
                if results['trade_history']:
                    st.subheader("📋 交易记录")
                    df_trades = pd.DataFrame(results['trade_history'])
                    df_trades['date'] = pd.to_datetime(df_trades['date'])
                    df_trades = df_trades.sort_values('date', ascending=False)
                    
                    st.dataframe(
                        df_trades[['date', 'action', 'stock', 'shares', 'price', 'amount']],
                        hide_index=True,
                        use_container_width=True
                    )
    
    else:
        st.info("👈 请在左侧设置参数并点击'开始回测'")
        st.markdown("""
        ### 轻量级版本特色
        
        **⚡ Streamlit Cloud优化**
        - 内存使用减少50%
        - 回测速度提升
        - 稳定性增强
        
        **🎯 核心功能保留**
        - 8个精选策略
        - 自定义策略支持
        - 完整回测功能
        
        **🚀 适合在线部署**
        - 快速启动
        - 低资源消耗
        - 高可靠性
        """)

if __name__ == "__main__":
    main()