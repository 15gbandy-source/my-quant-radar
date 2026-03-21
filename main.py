import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time

# ==========================================
# 1. 環境變數設定
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 擴充版：台美股 50 檔 AI & 半導體供應鏈
US_STOCKS = [
    'NVDA', 'AMD', 'INTC', 'TSM', 'AVGO', 'QCOM', 'MRVL', 'ARM', 'ASML', 'AMAT',
    'LRCX', 'KLAC', 'MU', 'SMCI', 'DELL', 'HPE', 'VRT', 'ANET', 'MSFT', 'GOOGL',
    'AMZN', 'META', 'PLTR', 'CDNS', 'SNPS'
]
TW_STOCKS = [
    '2330.TW', '2454.TW', '2317.TW', '2382.TW', '3231.TW', '6669.TW', '2376.TW', '2357.TW',
    '3017.TW', '3324.TW', '3711.TW', '2308.TW', '2301.TW', '3661.TW', '3443.TW', '2303.TW',
    '5269.TW', '2379.TW', '3034.TW', '2449.TW', '8046.TW', '3037.TW', '3583.TW', '6223.TW', '2049.TW'
]

# ==========================================
# 2. 核心分析引擎 (加入量能偵測)
# ==========================================
def get_fundamentals(ticker):
    try:
        stock = yf.Ticker(ticker)
        try:
            price = stock.fast_info['lastPrice']
        except:
            hist = stock.history(period="1d")
            price = hist['Close'].iloc[-1] if not hist.empty else 0
        
        info = stock.info
        eps = info.get('trailingEps', 1.0)
        pe = info.get('trailingPE', np.nan)
        pb = info.get('priceToBook', np.nan)
        name = info.get('shortName', ticker)

        if price == 0: return None
        return {'Ticker': ticker, 'Name': name, 'Price': price, 'P/E': pe, 'P/B': pb, 'EPS': eps}
    except:
        return None

def analyze_technical(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty or len(df) < 25: return None
        
        df.index = df.index.tz_localize(None)

        # 1. 計算布林與 RSI
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['STD_20'] = df['Close'].rolling(window=20).std()
        df['Lower_Band'] = df['SMA_20'] - (df['STD_20'] * 2)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI_14'] = 100 - (100 / (1 + (gain / loss)))
        
        # 2. 加入成交量濾網 (今日量 vs 20日均量)
        df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        vol_ratio = latest['Volume'] / latest['Vol_MA20'] if latest['Vol_MA20'] > 0 else 1
        
        tech_status = "中性"
        if latest['RSI_14'] < 30: tech_status = "RSI超賣"
        elif latest['Close'] <= latest['Lower_Band'] * 1.02: tech_status = "通道底部"
        elif latest['RSI_14'] > 30 and prev['RSI_14'] <= 30: tech_status = "超賣反轉"
        
        # 如果量能爆發，疊加狀態
        if vol_ratio > 1.5:
            tech_status += "+量能爆發"
            
        return {
            'RSI(14)': round(latest['RSI_14'], 2), 
            'Vol_Ratio': round(vol_ratio, 2),
            'Tech_Status': tech_status
        }
    except:
        return None

def run_quant_screener(market_name, stock_list):
    results = []
    for ticker in stock_list:
        fund = get_fundamentals(ticker)
        if not fund: continue
        tech = analyze_technical(ticker)
        if not tech: continue
        
        data = {**fund, **tech, 'Market': market_name}
        
        # --- 評分邏輯 2.0 (防暴走封頂版) ---
        score = 100
        
        # P/E 評分 (上限 40 分)
        if not np.isnan(data['P/E']) and data['P/E'] < 15:
            pe_bonus = (15 - data['P/E']) * 2
            score += min(pe_bonus, 40) # 封頂 40 分
            
        # P/B 評分 (上限 40 分)
        if not np.isnan(data['P/B']) and data['P/B'] < 2:
            pb_bonus = (2 - data['P/B']) * 10
            score += min(pb_bonus, 40) # 封頂 40 分
            
        # RSI 評分 (超跌補償)
        if data['RSI(14)'] < 40:
            score += (40 - data['RSI(14)'])
            
        # 量能爆發大加分
        if data['Vol_Ratio'] > 1.5:
            score += 30 
            
        # 技術面位置加分
        if "通道底部" in data['Tech_Status'] or "超賣反轉" in data['Tech_Status']:
            score += 20
        
        data['Total_Score'] = score
        results.append(data)
        time.sleep(1.2)
    
    df = pd.DataFrame(results)
    # 返回前 10 名
    return df.sort_values(by='Total_Score', ascending=False).head(10) if not df.empty else df

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

# ==========================================
# 3. 執行與報表
# ==========================================
if __name__ == "__main__":
    us_df = run_quant_screener("美股", US_STOCKS)
    tw_df = run_quant_screener("台股", TW_STOCKS)
    
    report = f"🚀 <b>【量化雷達 2.0：量能進化版】</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "-----------------------------------\n"
    report += "💡 評分包含：估值、RSI、量能爆發\n\n"
    
    for market_name, df in [("🇹🇼 台股 Top 10", tw_df), ("🇺🇸 美股 Top 10", us_df)]:
        report += f"<b>{market_name}:</b>\n"
        if not df.empty:
            for _, r in df.iterrows():
                # 標註量能爆發標的
                vol_tag = "🔥" if r['Vol_Ratio'] > 1.5 else ""
                report += f"🔹 <code>{r['Ticker']}</code>: {r['Total_Score']:.1f} {vol_tag}\n"
                report += f"   <small>({r['Tech_Status']}, 量比:{r['Vol_Ratio']})</small>\n"
        else:
            report += "無符合標的\n"
        report += "\n"
    
    send_telegram(report)
