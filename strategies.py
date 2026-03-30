"""
A股量化交易策略模块 - 包含10个经典策略
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import baostock as bs


class QuantStrategies:
    """量化策略集合类"""
    
    def __init__(self):
        self.stock_pool = [
            "sh.600036", "sh.601318", "sz.000858", "sz.002415",  # 蓝筹股
            "sh.600519", "sz.000333", "sh.601166", "sz.002594",  # 消费/制造
            "sh.600030", "sz.000725", "sh.601628", "sz.002475"   # 金融/科技
        ]
        self.stock_names = {
            'sh.600036': '招商银行', 'sh.601318': '中国平安', 'sz.000858': '五粮液',
            'sz.002415': '海康威视', 'sh.600519': '贵州茅台', 'sz.000333': '美的集团',
            'sh.601166': '兴业银行', 'sz.002594': '比亚迪', 'sh.600030': '中信证券',
            'sz.000725': '京东方A', 'sh.601628': '中国人寿', 'sz.002475': '立讯精密'
        }
    
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票数据（复用WebSimulator的方法）"""
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
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        if df.empty:
            return df
            
        df = df.copy()
        
        # 移动平均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = df['close'].ewm(span=12).mean()
        exp26 = df['close'].ewm(span=26).mean()
        df['macd'] = exp12 - exp26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # BOLLINGER BANDS
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # 成交量变化率
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma5']
        
        return df
    
    def strategy_momentum(self, trading_days: list, lookback_days: int = 20, 
                         top_n: int = 3, **kwargs) -> list:
        """1. 动量策略 - 选择近期表现最好的股票"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        momentum_scores = []
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=lookback_days*2)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= lookback_days:
                    prices = hist_data['close'].values
                    momentum = (prices[-1] - prices[-lookback_days]) / prices[-lookback_days]
                    momentum_scores.append((stock, momentum))
            except:
                continue
        
        momentum_scores.sort(key=lambda x: x[1], reverse=True)
        selected_stocks = [score[0] for score in momentum_scores[:top_n]]
        return selected_stocks
    
    def strategy_mean_reversion(self, trading_days: list, window: int = 20, 
                               bottom_n: int = 3, **kwargs) -> list:
        """2. 均值回归策略 - 选择超卖的股票"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        reversion_scores = []
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=window*2)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= window:
                    df_with_indicators = self.calculate_indicators(hist_data)
                    if not df_with_indicators.empty:
                        latest = df_with_indicators.iloc[-1]
                        # 超卖条件：价格低于布林带下轨且RSI < 30
                        if (latest['close'] < latest['bb_lower']) and (latest['rsi'] < 30):
                            score = -(latest['close'] - latest['bb_lower'])  # 越低分越高
                            reversion_scores.append((stock, score))
            except:
                continue
        
        reversion_scores.sort(key=lambda x: x[1], reverse=True)
        selected_stocks = [score[0] for score in reversion_scores[:bottom_n]]
        return selected_stocks
    
    def strategy_macd_crossover(self, trading_days: list, **kwargs) -> list:
        """3. MACD金叉策略 - MACD线上穿信号线"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=60)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= 30:
                    df_with_indicators = self.calculate_indicators(hist_data)
                    if not df_with_indicators.empty:
                        latest = df_with_indicators.iloc[-1]
                        prev = df_with_indicators.iloc[-2] if len(df_with_indicators) >= 2 else None
                        
                        if prev is not None:
                            # MACD金叉：当前MACD > 信号线，前一天MACD <= 信号线
                            if (latest['macd'] > latest['macd_signal']) and (prev['macd'] <= prev['macd_signal']):
                                selected_stocks.append(stock)
            except:
                continue
        
        return selected_stocks[:3]  # 最多选3只
    
    def strategy_rsi_divergence(self, trading_days: list, **kwargs) -> list:
        """4. RSI背离策略 - 价格新低但RSI未新低"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=90)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= 60:
                    df_with_indicators = self.calculate_indicators(hist_data)
                    if not df_with_indicators.empty and len(df_with_indicators) >= 20:
                        # 找最近的低点
                        recent_low_idx = df_with_indicators['low'].tail(20).idxmin()
                        recent_low_price = df_with_indicators.loc[recent_low_idx, 'low']
                        recent_low_rsi = df_with_indicators.loc[recent_low_idx, 'rsi']
                        
                        # 找之前的低点（40-60天前）
                        prev_period = df_with_indicators.iloc[-60:-20]
                        if not prev_period.empty:
                            prev_low_idx = prev_period['low'].idxmin()
                            prev_low_price = df_with_indicators.loc[prev_low_idx, 'low']
                            prev_low_rsi = df_with_indicators.loc[prev_low_idx, 'rsi']
                            
                            # 底背离：价格新低但RSI未新低
                            if (recent_low_price < prev_low_price) and (recent_low_rsi > prev_low_rsi):
                                selected_stocks.append(stock)
            except:
                continue
        
        return selected_stocks[:2]
    
    def strategy_volume_breakout(self, trading_days: list, volume_multiplier: float = 2.0, 
                                **kwargs) -> list:
        """5. 放量突破策略 - 成交量放大且价格突破均线"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= 10:
                    df_with_indicators = self.calculate_indicators(hist_data)
                    if not df_with_indicators.empty:
                        latest = df_with_indicators.iloc[-1]
                        # 放量：成交量是5日均量的2倍以上
                        # 突破：收盘价高于20日均线
                        if (latest['volume_ratio'] > volume_multiplier) and (latest['close'] > latest['ma20']):
                            selected_stocks.append(stock)
            except:
                continue
        
        return selected_stocks[:3]
    
    def strategy_dual_thrust(self, trading_days: list, k1: float = 0.7, k2: float = 0.7, 
                           **kwargs) -> list:
        """6. 双重推力策略 - 基于前N日高低点的突破策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=10)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= 5:
                    # 计算前4日的最高最高、最低最低、收盘最高、收盘最低
                    lookback_data = hist_data.iloc[:-1]  # 排除当天
                    if len(lookback_data) >= 4:
                        hh = lookback_data['high'].max()
                        hc = lookback_data['close'].max()
                        lc = lookback_data['close'].min()
                        ll = lookback_data['low'].min()
                        
                        range1 = hh - lc
                        range2 = hc - ll
                        range_val = max(range1, range2)
                        
                        # 计算上下轨
                        buy_line = hist_data.iloc[-2]['open'] + k1 * range_val  # 前一天开盘价
                        sell_line = hist_data.iloc[-2]['open'] - k2 * range_val
                        
                        today_close = hist_data.iloc[-1]['close']
                        today_open = hist_data.iloc[-1]['open']
                        
                        # 买入信号：开盘后价格突破上轨
                        if today_open < buy_line and today_close > buy_line:
                            selected_stocks.append(stock)
            except:
                continue
        
        return selected_stocks[:2]
    
    def strategy_grid_trading(self, trading_days: list, grid_levels: int = 5, 
                             **kwargs) -> list:
        """7. 网格交易策略 - 在价格区间内高抛低吸"""
        # 网格交易通常针对单只股票，这里简化为选择波动性大的股票
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        volatility_scores = []
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=60)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= 30:
                    # 计算波动率（标准差/均值）
                    returns = hist_data['close'].pct_change().dropna()
                    if len(returns) > 0:
                        volatility = returns.std() * np.sqrt(252)  # 年化波动率
                        volatility_scores.append((stock, volatility))
            except:
                continue
        
        volatility_scores.sort(key=lambda x: x[1], reverse=True)
        selected_stocks = [score[0] for score in volatility_scores[:2]]  # 选波动最大的2只
        return selected_stocks
    
    def strategy_factor_combo(self, trading_days: list, **kwargs) -> list:
        """8. 多因子组合策略 - 结合价值、成长、动量因子"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        factor_scores = []
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=120)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= 60:
                    df_with_indicators = self.calculate_indicators(hist_data)
                    if not df_with_indicators.empty:
                        latest = df_with_indicators.iloc[-1]
                        
                        # 动量因子（20日收益率）
                        momentum_score = (latest['close'] - df_with_indicators.iloc[-21]['close']) / df_with_indicators.iloc[-21]['close'] if len(df_with_indicators) >= 21 else 0
                        
                        # 趋势因子（价格在均线之上）
                        trend_score = 1 if latest['close'] > latest['ma20'] else -1
                        
                        # 波动因子（适中波动最佳）
                        returns = df_with_indicators['close'].pct_change().tail(20).dropna()
                        volatility = returns.std() if len(returns) > 0 else 0
                        volatility_score = 1 - abs(volatility - 0.02) / 0.02 if volatility <= 0.04 else -1
                        
                        total_score = momentum_score + trend_score * 0.5 + volatility_score * 0.3
                        factor_scores.append((stock, total_score))
            except:
                continue
        
        factor_scores.sort(key=lambda x: x[1], reverse=True)
        selected_stocks = [score[0] for score in factor_scores[:3]]
        return selected_stocks
    
    def strategy_bollinger_squeeze(self, trading_days: list, **kwargs) -> list:
        """9. 布林带收口策略 - 布林带收窄后的突破"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=40)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data(stock, hist_start, current_date)
                if len(hist_data) >= 30:
                    df_with_indicators = self.calculate_indicators(hist_data)
                    if not df_with_indicators.empty and len(df_with_indicators) >= 10:
                        # 检查最近5天布林带宽度是否在收窄
                        recent_bandwidth = (df_with_indicators['bb_upper'] - df_with_indicators['bb_lower']).tail(5)
                        if recent_bandwidth.is_monotonic_decreasing or recent_bandwidth.iloc[-1] < recent_bandwidth.mean() * 0.8:
                            # 当前价格突破布林带上轨或下轨
                            latest = df_with_indicators.iloc[-1]
                            if latest['close'] > latest['bb_upper'] or latest['close'] < latest['bb_lower']:
                                selected_stocks.append(stock)
            except:
                continue
        
        return selected_stocks[:2]
    
    def strategy_market_timing(self, trading_days: list, **kwargs) -> list:
        """10. 市场择时策略 - 基于大盘指数的趋势判断"""
        # 简化版：使用沪深300作为市场指标
        try:
            current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
            hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                        timedelta(days=60)).strftime('%Y-%m-%d')
            
            # 获取沪深300数据
            hs300_data = self.get_stock_data("sh.000300", hist_start, current_date)
            if len(hs300_data) >= 20:
                df_with_indicators = self.calculate_indicators(hs300_data)
                if not df_with_indicators.empty:
                    latest = df_with_indicators.iloc[-1]
                    # 大盘在20日均线上方且MACD为正，才选股
                    if latest['close'] > latest['ma20'] and latest['macd'] > 0:
                        # 如果市场趋势好，选择动量最好的股票
                        return self.strategy_momentum(trading_days, lookback_days=10, top_n=4)
                    else:
                        return []  # 市场不好时不选股
        except:
            pass
        
        return []
    
    def get_all_strategies(self):
        """返回所有策略的字典"""
        return {
            "动量策略": self.strategy_momentum,
            "均值回归": self.strategy_mean_reversion,
            "MACD金叉": self.strategy_macd_crossover,
            "RSI背离": self.strategy_rsi_divergence,
            "放量突破": self.strategy_volume_breakout,
            "双重推力": self.strategy_dual_thrust,
            "网格交易": self.strategy_grid_trading,
            "多因子组合": self.strategy_factor_combo,
            "布林带收口": self.strategy_bollinger_squeeze,
            "市场择时": self.strategy_market_timing
        }
    
    def get_strategy_descriptions(self):
        """返回策略描述"""
        return {
            "动量策略": "选择近期涨幅最大的股票，追涨杀跌",
            "均值回归": "选择超卖的股票，期待价格回归均值",
            "MACD金叉": "MACD指标金叉时买入，死叉时卖出",
            "RSI背离": "价格创新低但RSI未创新低时买入",
            "放量突破": "成交量放大且价格突破关键均线时买入",
            "双重推力": "基于前N日价格区间的突破策略",
            "网格交易": "在设定价格区间内高抛低吸",
            "多因子组合": "结合动量、趋势、波动等多个因子",
            "布林带收口": "布林带收窄后突破时交易",
            "市场择时": "先判断大盘趋势，再决定是否交易"
        }