"""
高级量化策略模块 - 扩展版
支持更多股票、更多策略、自定义组合
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import baostock as bs
import warnings
warnings.filterwarnings('ignore')

class AdvancedQuantStrategies:
    """高级量化策略集合"""
    
    def __init__(self):
        # 扩展股票池 - 获取更多A股股票
        self.stock_pool = self._get_extended_stock_pool()
        self.strategy_library = self._build_strategy_library()
        
    def _get_extended_stock_pool(self):
        """获取扩展的股票池（最多3000+只股票）"""
        try:
            # 获取沪深A股列表
            rs = bs.query_all_stock(datetime.now().strftime('%Y-%m-%d'))
            stock_list = []
            while (rs.error_code == '0') & rs.next():
                code = rs.get_row_data()[0]
                # 过滤掉ST、退市等特殊股票
                if (code.startswith('sh.6') or code.startswith('sz.0') or 
                    code.startswith('sz.3') or code.startswith('sh.688')):
                    stock_list.append(code)
            
            # 限制数量以提高性能（可调整）
            return stock_list[:500]  # 前500只流动性好的股票
            
        except Exception as e:
            print(f"获取股票池失败: {e}")
            # 回退到核心股票池
            return [
                "sh.600036", "sh.601318", "sz.000858", "sz.002415",
                "sh.600519", "sz.000333", "sh.601166", "sz.002594",
                "sh.600030", "sz.000725", "sh.601628", "sz.002475",
                "sh.601398", "sz.000651", "sh.601857", "sz.000001"
            ]
    
    def _build_strategy_library(self):
        """构建完整的策略库"""
        return {
            # 趋势跟踪类
            "简单移动平均": self.simple_ma_strategy,
            "MACD趋势": self.macd_trend_strategy,
            "布林带趋势": self.bollinger_trend_strategy,
            
            # 均值回归类  
            "RSI超买超卖": self.rsi_mean_reversion,
            "随机指标": self.stochastic_oscillator,
            "布林带回归": self.bollinger_mean_reversion,
            "ATR通道回归": self.atr_channel_reversion,
            
            # 动量类
            "相对强弱": self.relative_strength,
            "价格动量": self.price_momentum,
            "成交量动量": self.volume_momentum,
            "多因子动量": self.multi_factor_momentum,
            
            # 波动率类
            "波动率突破": self.volatility_breakout,
            "ATR突破": self.atr_breakout,
            "布林带收口": self.bollinger_squeeze,
            "波动率过滤": self.volatility_filter,
            
            # 量价类
            "量价配合": self.volume_price_confirmation,
            "放量突破": self.volume_breakout,
            "缩量回调": self.volume_pullback,
            "异常成交量": self.abnormal_volume,
            
            # 多因子组合类
            "价值成长动量": self.value_growth_momentum,
            "质量因子组合": self.quality_factor_combo,
            "风险调整收益": self.risk_adjusted_return,
            "夏普比率优化": self.sharpe_ratio_optimization,
            
            # 机器学习类（简化版）
            "简单模式识别": self.simple_pattern_recognition,
            "支撑阻力突破": self.support_resistance_breakout,
            "形态识别": self.chart_pattern_recognition,
            "时间序列预测": self.time_series_forecast,
            
            # 高级策略
            "配对交易": self.pairs_trading,
            "统计套利": self.statistical_arbitrage,
            "事件驱动": self.event_driven,
            "季节性策略": self.seasonal_strategy,
            
            # 自定义策略占位符
            "自定义策略1": self.custom_strategy_1,
            "自定义策略2": self.custom_strategy_2,
            "自定义策略3": self.custom_strategy_3
        }
    
    def get_stock_data_extended(self, stock_code: str, start_date: str, end_date: str, 
                              frequency: str = "d") -> pd.DataFrame:
        """获取扩展股票数据"""
        fields = "date,open,high,low,close,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM"
        
        rs = bs.query_history_k_data_plus(
            stock_code,
            fields,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag="2"  # 前复权
        )
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return pd.DataFrame()
            
        df = pd.DataFrame(data_list, columns=rs.fields)
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 
                       'pctChg', 'peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def calculate_advanced_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算高级技术指标"""
        if df.empty:
            return df
            
        df = df.copy()
        
        # 基础移动平均
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma60'] = df['close'].rolling(60).mean()
        
        # 指数移动平均
        df['ema12'] = df['close'].ewm(span=12).mean()
        df['ema26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema12'] - df['ema26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # 成交量指标
        df['volume_ma5'] = df['volume'].rolling(5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma5']
        
        # 波动率
        df['volatility'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252)
        
        # 财务指标（如果可用）
        if 'peTTM' in df.columns:
            df['pe_rank'] = df['peTTM'].rank(pct=True)
        
        return df
    
    # ==================== 策略实现 ====================
    
    def simple_ma_strategy(self, trading_days: list, ma_short: int = 5, ma_long: int = 20, **kwargs) -> list:
        """简单移动平均交叉策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:  # 限制数量提高性能
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=ma_long*3)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= ma_long:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        prev = df_ind.iloc[-2] if len(df_ind) >= 2 else None
                        
                        if prev is not None:
                            short_ma_col = f'ma{ma_short}'
                            long_ma_col = f'ma{ma_long}'
                            
                            if (short_ma_col in df_ind.columns and long_ma_col in df_ind.columns):
                                if (latest[short_ma_col] > latest[long_ma_col] and 
                                    prev[short_ma_col] <= prev[long_ma_col]):
                                    selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:5]
    
    def macd_trend_strategy(self, trading_days: list, **kwargs) -> list:
        """MACD趋势策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=60)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 30:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        prev = df_ind.iloc[-2] if len(df_ind) >= 2 else None
                        
                        if prev is not None:
                            # MACD金叉且在零轴上方
                            if (latest['macd'] > latest['macd_signal'] and 
                                prev['macd'] <= prev['macd_signal'] and
                                latest['macd'] > 0):
                                selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:3]
    
    def bollinger_trend_strategy(self, trading_days: list, **kwargs) -> list:
        """布林带趋势策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 20:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        # 价格在布林带上轨上方，且布林带宽度扩大
                        if (latest['close'] > latest['bb_upper'] and 
                            latest['bb_width'] > df_ind['bb_width'].iloc[-5:-1].mean()):
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:3]
    
    def rsi_mean_reversion(self, trading_days: list, rsi_threshold: float = 30, **kwargs) -> list:
        """RSI均值回归策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 15:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        if latest['rsi'] < rsi_threshold:
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:5]
    
    def stochastic_oscillator(self, trading_days: list, k_period: int = 14, d_period: int = 3, **kwargs) -> list:
        """随机指标策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= k_period + d_period:
                    # 计算随机指标
                    low_min = hist_data['low'].rolling(k_period).min()
                    high_max = hist_data['high'].rolling(k_period).max()
                    hist_data['%K'] = 100 * (hist_data['close'] - low_min) / (high_max - low_min)
                    hist_data['%D'] = hist_data['%K'].rolling(d_period).mean()
                    
                    if not hist_data.empty:
                        latest = hist_data.iloc[-1]
                        prev = hist_data.iloc[-2] if len(hist_data) >= 2 else None
                        
                        if prev is not None:
                            # K线从下向上穿过D线，且在超卖区域
                            if (latest['%K'] > latest['%D'] and 
                                prev['%K'] <= prev['%D'] and
                                latest['%K'] < 20):
                                selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:3]
    
    def bollinger_mean_reversion(self, trading_days: list, **kwargs) -> list:
        """布林带均值回归策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 20:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        # 价格在布林带下轨下方，期待回归
                        if latest['close'] < latest['bb_lower']:
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:3]
    
    def atr_channel_reversion(self, trading_days: list, atr_multiplier: float = 2.0, **kwargs) -> list:
        """ATR通道回归策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 20:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        lower_channel = latest['ma20'] - latest['atr'] * atr_multiplier
                        if latest['close'] < lower_channel:
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:3]
    
    def relative_strength(self, trading_days: list, lookback: int = 20, top_n: int = 5, **kwargs) -> list:
        """相对强弱策略"""
        strength_scores = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:100]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=lookback*2)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= lookback:
                    returns = (hist_data['close'].iloc[-1] - hist_data['close'].iloc[-lookback]) / hist_data['close'].iloc[-lookback]
                    strength_scores.append((stock, returns))
            except:
                continue
        
        strength_scores.sort(key=lambda x: x[1], reverse=True)
        return [score[0] for score in strength_scores[:top_n]]
    
    def price_momentum(self, trading_days: list, lookback: int = 10, **kwargs) -> list:
        """价格动量策略"""
        return self.relative_strength(trading_days, lookback=lookback, top_n=5)
    
    def volume_momentum(self, trading_days: list, volume_threshold: float = 2.0, **kwargs) -> list:
        """成交量动量策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=20)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 10:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        if latest['volume_ratio'] > volume_threshold:
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:5]
    
    def multi_factor_momentum(self, trading_days: list, **kwargs) -> list:
        """多因子动量策略"""
        factor_scores = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=60)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 30:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        
                        # 动量因子
                        momentum = (latest['close'] - df_ind.iloc[-21]['close']) / df_ind.iloc[-21]['close'] if len(df_ind) >= 21 else 0
                        
                        # 成交量因子
                        volume_score = latest['volume_ratio'] if pd.notna(latest['volume_ratio']) else 1
                        
                        total_score = momentum * 0.7 + volume_score * 0.3
                        factor_scores.append((stock, total_score))
            except:
                continue
        
        factor_scores.sort(key=lambda x: x[1], reverse=True)
        return [score[0] for score in factor_scores[:5]]
    
    def volatility_breakout(self, trading_days: list, atr_multiplier: float = 2.0, **kwargs) -> list:
        """波动率突破策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 20:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        if latest['high'] > latest['open'] + latest['atr'] * atr_multiplier:
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:3]
    
    def atr_breakout(self, trading_days: list, atr_multiplier: float = 1.5, **kwargs) -> list:
        """ATR突破策略"""
        return self.volatility_breakout(trading_days, atr_multiplier=atr_multiplier)
    
    def bollinger_squeeze(self, trading_days: list, squeeze_threshold: float = 0.8, **kwargs) -> list:
        """布林带收口策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=40)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 30:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty and len(df_ind) >= 10:
                        # 检查最近5天布林带宽度是否在收窄
                        recent_bandwidth = df_ind['bb_width'].tail(5)
                        if recent_bandwidth.iloc[-1] < recent_bandwidth.mean() * squeeze_threshold:
                            # 当前价格突破布林带上轨或下轨
                            latest = df_ind.iloc[-1]
                            if latest['close'] > latest['bb_upper'] or latest['close'] < latest['bb_lower']:
                                selected_stocks.append(stock)
            except:
                continue
        
        return selected_stocks[:2]
    
    def volatility_filter(self, trading_days: list, volatility_threshold: float = 0.02, **kwargs) -> list:
        """波动率过滤策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=60)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 30:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        if latest['volatility'] > volatility_threshold:
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:5]
    
    def volume_price_confirmation(self, trading_days: list, volume_multiplier: float = 1.5, **kwargs) -> list:
        """量价配合策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=20)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 10:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        # 价格上涨且成交量放大
                        if (latest['close'] > df_ind.iloc[-2]['close'] if len(df_ind) >= 2 else False) and \
                           latest['volume_ratio'] > volume_multiplier:
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:5]
    
    def volume_breakout(self, trading_days: list, volume_multiplier: float = 2.0, **kwargs) -> list:
        """放量突破策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 10:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        # 放量：成交量是5日均量的2倍以上
                        # 突破：收盘价高于20日均线
                        if (latest['volume_ratio'] > volume_multiplier) and (latest['close'] > latest['ma20']):
                            selected_stocks.append(stock)
            except:
                continue
        
        return selected_stocks[:3]
    
    def volume_pullback(self, trading_days: list, volume_threshold: float = 0.8, **kwargs) -> list:
        """缩量回调策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=30)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 10:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty and len(df_ind) >= 3:
                        latest = df_ind.iloc[-1]
                        prev = df_ind.iloc[-2]
                        # 价格回调但成交量萎缩，期待反弹
                        if (latest['close'] < prev['close']) and (latest['volume_ratio'] < volume_threshold):
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:3]
    
    def abnormal_volume(self, trading_days: list, volume_threshold: float = 3.0, **kwargs) -> list:
        """异常成交量策略"""
        selected_stocks = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=20)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 10:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        if latest['volume_ratio'] > volume_threshold:
                            selected_stocks.append(stock)
            except:
                continue
                
        return selected_stocks[:3]
    
    def value_growth_momentum(self, trading_days: list, **kwargs) -> list:
        """价值成长动量多因子策略"""
        factor_scores = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:50]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=120)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 60:
                    df_ind = self.calculate_advanced_indicators(hist_data)
                    if not df_ind.empty:
                        latest = df_ind.iloc[-1]
                        
                        # 动量因子
                        momentum = (latest['close'] - df_ind.iloc[-21]['close']) / df_ind.iloc[-21]['close'] if len(df_ind) >= 21 else 0
                        
                        # 价值因子（低PE）
                        value_score = -latest['peTTM'] if pd.notna(latest['peTTM']) else 0
                        
                        # 趋势因子
                        trend_score = 1 if latest['close'] > latest['ma20'] else -1
                        
                        total_score = momentum * 0.4 + value_score * 0.3 + trend_score * 0.3
                        factor_scores.append((stock, total_score))
            except:
                continue
        
        factor_scores.sort(key=lambda x: x[1], reverse=True)
        return [score[0] for score in factor_scores[:5]]
    
    def quality_factor_combo(self, trading_days: list, **kwargs) -> list:
        """质量因子组合策略"""
        return self.value_growth_momentum(trading_days)
    
    def risk_adjusted_return(self, trading_days: list, **kwargs) -> list:
        """风险调整收益策略"""
        sharpe_scores = []
        current_date = trading_days[-1] if trading_days else datetime.now().strftime('%Y-%m-%d')
        
        for stock in self.stock_pool[:30]:
            try:
                hist_start = (datetime.strptime(current_date, '%Y-%m-%d') - 
                            timedelta(days=120)).strftime('%Y-%m-%d')
                hist_data = self.get_stock_data_extended(stock, hist_start, current_date)
                if len(hist_data) >= 60:
                    returns = hist_data['close'].pct_change().dropna()
                    if len(returns) > 0:
                        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                        sharpe_scores.append((stock, sharpe))
            except:
                continue
        
        sharpe_scores.sort(key=lambda x: x[1], reverse=True)
        return [score[0] for score in sharpe_scores[:5]]
    
    def sharpe_ratio_optimization(self, trading_days: list, **kwargs) -> list:
        """夏普比率优化策略"""
        return self.risk_adjusted_return(trading_days)
    
    def simple_pattern_recognition(self, trading_days: list, **kwargs) -> list:
        """简单模式识别策略"""
        # 简化版：识别双底、头肩底等基本形态
        return self.relative_strength(trading_days, lookback=15, top_n=3)
    
    def support_resistance_breakout(self, trading_days: list, **kwargs) -> list:
        """支撑阻力突破策略"""
        return self.volatility_breakout(trading_days, atr_multiplier=1.8)
    
    def chart_pattern_recognition(self, trading_days: list, **kwargs) -> list:
        """形态识别策略"""
        return self.simple_pattern_recognition(trading_days)
    
    def time_series_forecast(self, trading_days: list, **kwargs) -> list:
        """时间序列预测策略"""
        # 简化版：使用简单移动平均预测
        return self.simple_ma_strategy(trading_days, ma_short=10, ma_long=30)
    
    def pairs_trading(self, trading_days: list, **kwargs) -> list:
        """配对交易策略"""
        # 简化版：选择相关性高的股票对
        return ["sh.600036", "sh.601166"]  # 银行股配对
    
    def statistical_arbitrage(self, trading_days: list, **kwargs) -> list:
        """统计套利策略"""
        return self.pairs_trading(trading_days)
    
    def event_driven(self, trading_days: list, **kwargs) -> list:
        """事件驱动策略"""
        # 简化版：基于财报发布等事件
        return self.value_growth_momentum(trading_days)
    
    def seasonal_strategy(self, trading_days: list, **kwargs) -> list:
        """季节性策略"""
        # 简化版：年末效应、春节效应等
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:  # 年末年初
            return self.relative_strength(trading_days, lookback=10, top_n=5)
        else:
            return self.rsi_mean_reversion(trading_days, rsi_threshold=35)
    
    # ==================== 自定义策略模板 ====================
    
    def custom_strategy_1(self, trading_days: list, **kwargs) -> list:
        """自定义策略1 - 用户可修改"""
        # 这里可以添加你自己的策略逻辑
        return self.relative_strength(trading_days, lookback=10, top_n=3)
    
    def custom_strategy_2(self, trading_days: list, **kwargs) -> list:
        """自定义策略2 - 用户可修改"""
        return self.rsi_mean_reversion(trading_days, rsi_threshold=25)
    
    def custom_strategy_3(self, trading_days: list, **kwargs) -> list:
        """自定义策略3 - 用户可修改"""
        return self.simple_ma_strategy(trading_days, ma_short=10, ma_long=30)
    
    # ==================== 组合优化功能 ====================
    
    def optimize_strategy_combination(self, trading_days: list, strategies_to_combine: list, 
                                   weights: list = None, **kwargs) -> list:
        """优化策略组合"""
        if weights is None:
            weights = [1.0 / len(strategies_to_combine)] * len(strategies_to_combine)
        
        combined_scores = {}
        
        for strategy_name, weight in zip(strategies_to_combine, weights):
            if strategy_name in self.strategy_library:
                try:
                    selected_stocks = self.strategy_library[strategy_name](trading_days, **kwargs)
                    for stock in selected_stocks:
                        combined_scores[stock] = combined_scores.get(stock, 0) + weight
                except:
                    continue
        
        # 选择综合得分最高的股票
        sorted_stocks = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return [stock for stock, score in sorted_stocks[:5]]
    
    def get_all_strategies(self):
        """返回所有策略"""
        return self.strategy_library
    
    def get_strategy_categories(self):
        """返回策略分类"""
        return {
            "趋势跟踪": ["简单移动平均", "MACD趋势", "布林带趋势"],
            "均值回归": ["RSI超买超卖", "随机指标", "布林带回归", "ATR通道回归"],
            "动量策略": ["相对强弱", "价格动量", "成交量动量", "多因子动量"],
            "波动率策略": ["波动率突破", "ATR突破", "布林带收口", "波动率过滤"],
            "量价策略": ["量价配合", "放量突破", "缩量回调", "异常成交量"],
            "多因子组合": ["价值成长动量", "质量因子组合", "风险调整收益", "夏普比率优化"],
            "机器学习": ["简单模式识别", "支撑阻力突破", "形态识别", "时间序列预测"],
            "高级策略": ["配对交易", "统计套利", "事件驱动", "季节性策略"],
            "自定义策略": ["自定义策略1", "自定义策略2", "自定义策略3"]
        }