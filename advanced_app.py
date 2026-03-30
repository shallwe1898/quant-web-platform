"""
高级A股量化交易Web平台 - 支持全部经典策略、自定义策略、组合优化
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
    page_title="高级A股量化模拟交易平台",
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
    .strategy-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .category-header {
        background-color: #e9ecef;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 1rem 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class AdvancedWebSimulator:
    """高级Web版模拟交易引擎"""
    
    def __init__(self):
        self.lg = bs.login()
        if self.lg.error_code != '0':
            st.error(f"数据源连接失败: {self.lg.error_msg}")
        self.strategies = AdvancedQuantStrategies()
    
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
        """运行指定策略的回测"""
        
        # 获取交易日历
        trading_days = self.get_trading_days(start_date, end_date)
        if not trading_days:
            return None, "无交易日数据"
        
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
                
                # 选择新股票
                try:
                    selected_stocks = strategy_func(trading_days[:i+1], **strategy_params)
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
            
            # 记录投资组合价值
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
    st.title("📈 高级A股量化模拟交易平台")
    st.caption("支持50+经典策略 | 自定义策略 | 组合优化 | 全市场股票")
    
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
    
    # 策略库介绍
    strategies_obj = AdvancedQuantStrategies()
    strategy_categories = strategies_obj.get_strategy_categories()
    
    with st.expander("🎯 策略库概览（50+种策略）", expanded=False):
        for category, strategies in strategy_categories.items():
            st.markdown(f'<div class="category-header">{category}</div>', unsafe_allow_html=True)
            cols = st.columns(2)
            for i, strategy in enumerate(strategies):
                with cols[i % 2]:
                    st.markdown(f"- {strategy}")
    
    # 参数设置侧边栏
    st.sidebar.header("📊 回测参数设置")
    
    # 模式选择
    mode = st.sidebar.radio("选择模式", ["单策略回测", "组合策略优化", "自定义策略"])
    
    if mode == "单策略回测":
        # 单策略模式
        all_strategies = list(strategies_obj.get_all_strategies().keys())
        selected_strategy = st.sidebar.selectbox("选择策略", all_strategies, index=0)
        
        # 策略特定参数
        st.sidebar.subheader("⚙️ 策略参数")
        strategy_params = {}
        
        # 这里可以为每个策略添加特定参数（简化处理）
        if "动量" in selected_strategy or "相对强弱" in selected_strategy:
            strategy_params['lookback'] = st.sidebar.slider("回看周期（天）", 5, 60, 20)
            strategy_params['top_n'] = st.sidebar.slider("选择股票数量", 1, 10, 5)
        elif "RSI" in selected_strategy:
            strategy_params['rsi_threshold'] = st.sidebar.slider("RSI阈值", 10, 50, 30)
        elif "移动平均" in selected_strategy:
            strategy_params['ma_short'] = st.sidebar.slider("短期均线", 5, 20, 5)
            strategy_params['ma_long'] = st.sidebar.slider("长期均线", 20, 60, 20)
        elif "波动率" in selected_strategy:
            strategy_params['atr_multiplier'] = st.sidebar.slider("ATR倍数", 1.0, 3.0, 2.0)
        
    elif mode == "组合策略优化":
        # 组合策略模式
        st.sidebar.subheader("选择策略组合")
        all_strategies = list(strategies_obj.get_all_strategies().keys())
        selected_strategies = st.sidebar.multiselect("选择多个策略", all_strategies, 
                                                   default=["相对强弱", "RSI超买超卖", "简单移动平均"])
        
        if selected_strategies:
            st.sidebar.subheader("策略权重")
            weights = []
            for strategy in selected_strategies:
                weight = st.sidebar.slider(f"{strategy}权重", 0.0, 1.0, 1.0/len(selected_strategies))
                weights.append(weight)
            
            # 归一化权重
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w/total_weight for w in weights]
            else:
                weights = [1.0/len(selected_strategies)] * len(selected_strategies)
            
            strategy_params = {'strategies_to_combine': selected_strategies, 'weights': weights}
            selected_strategy = "组合策略优化"
        
        else:
            selected_strategy = None
            
    else:
        # 自定义策略模式
        st.sidebar.subheader("自定义策略参数")
        custom_strategy = st.sidebar.selectbox("选择自定义策略", ["自定义策略1", "自定义策略2", "自定义策略3"])
        selected_strategy = custom_strategy
        
        # 自定义参数
        st.sidebar.text_area("策略逻辑说明", 
                           "修改 advanced_strategies.py 中的 custom_strategy_1/2/3 函数来实现你的策略",
                           height=100)
        
        strategy_params = {}
    
    # 通用参数
    if selected_strategy:
        st.sidebar.subheader("🔧 通用参数")
        
        # 回测期间
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date_default = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        start_date = st.sidebar.date_input("开始日期", 
                                         value=datetime.strptime(start_date_default, '%Y-%m-%d'),
                                         max_value=datetime.now() - timedelta(days=1))
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        rebalance_options = {"每日": "daily", "每周": "weekly", "每月": "monthly"}
        rebalance_choice = st.sidebar.selectbox("调仓频率", list(rebalance_options.keys()), index=2)
        strategy_params['rebalance_frequency'] = rebalance_options[rebalance_choice]
        
        initial_capital = st.sidebar.number_input("初始资金（元）", 10000, 1000000, 100000, step=10000)
        
        # 运行按钮
        if st.sidebar.button("🚀 开始回测", use_container_width=True):
            if mode == "组合策略优化" and not selected_strategies:
                st.error("请至少选择一个策略进行组合")
            else:
                with st.spinner("正在运行回测..."):
                    simulator = AdvancedWebSimulator()
                    
                    if mode == "组合策略优化":
                        results, error = simulator.run_strategy_backtest(
                            simulator.strategies.optimize_strategy_combination, 
                            strategy_params,
                            start_date_str, end_date, initial_capital
                        )
                    else:
                        strategy_func = strategies_obj.get_all_strategies()[selected_strategy]
                        results, error = simulator.run_strategy_backtest(
                            strategy_func, strategy_params,
                            start_date_str, end_date, initial_capital
                        )
                    
                    if error:
                        st.error(f"回测失败: {error}")
                    else:
                        # 显示结果
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            roi_display = f"{results['roi']:.3f}"
                            if results['roi'] >= 1.3:
                                st.success(f"🎯 ROI: {roi_display}")
                            else:
                                st.info(f"📈 ROI: {roi_display}")
                        
                        with col2:
                            st.metric("最终价值", f"¥{results['final_value']:,.0f}")
                        
                        with col3:
                            st.metric("年化收益", f"{results['annualized_return']:.1f}%")
                        
                        with col4:
                            target_achieved = "✅ 达成" if results['roi'] >= 1.3 else "❌ 未达成"
                            st.metric("目标状态", target_achieved)
                        
                        # 策略信息
                        st.subheader(f"📊 当前策略: {selected_strategy}")
                        if mode == "组合策略优化":
                            st.caption("多策略加权组合优化")
                            for strat, weight in zip(selected_strategies, weights):
                                st.write(f"- {strat}: {weight:.2%}")
                        else:
                            # 可以添加策略描述
                            pass
                        
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
        # 欢迎界面
        st.info("👈 请在左侧选择模式、策略并设置参数")
        
        st.markdown("""
        ### 平台特色
        
        **🎯 50+经典策略**
        - 趋势跟踪、均值回归、动量策略
        - 波动率策略、量价策略、多因子组合
        - 机器学习、高级策略、自定义策略
        
        **⚡ 组合优化**
        - 多策略加权组合
        - 实时权重调整
        - 最优组合搜索
        
        **🛠️ 自定义能力**
        - 修改策略逻辑
        - 添加新策略
        - 参数调优
        
        **📊 全市场覆盖**
        - 支持500+流动性好的A股
        - 扩展财务和技术指标
        - 高性能回测引擎
        
        **🚀 立即开始**
        选择模式，配置策略，测试你的量化想法！
        """)

if __name__ == "__main__":
    main()