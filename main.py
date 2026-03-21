import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time

# ==========================================
# 1. 從 GitHub Secrets 讀取金鑰 (免信用卡安全性設定)
# ==========================================
# 確保這兩行「完全大寫」，且與 GitHub Secrets 的名稱一字不差
# 括號裡面要填的是你在 GitHub Secrets 設定的「變數名稱」
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 定義股票池 (你可以自行增減)
# ==========================================
# 擴充版：台美股 50 檔 AI & 半導體供應鏈
# ==========================================

# 美股 25 檔：包含晶片設計、設備、軟體平台、AI散熱與資料中心
US_STOCKS = [
    'NVDA', 'AMD', 'INTC', 'TSM', 'AVGO',    # 五大晶片巨頭
    'QCOM', 'MRVL', 'ARM', 'ASML', 'AMAT',   # 網通、架構與設備商
    'LRCX', 'KLAC', 'MU', 'SMCI', 'DELL',    # 記憶體、檢測與伺服器組裝
    'HPE', 'VRT', 'ANET', 'MSFT', 'GOOGL',   # 散熱、交換器與雲端三巨頭
    'AMZN', 'META', 'PLTR', 'CDNS', 'SNPS'   # AI軟體、EDA工具與大數據
]

# 台股 25 檔：包含護國神山、ASIC設計、AI伺服器組裝、散熱與電源管理
TW_STOCKS = [
    '2330.TW', '2454.TW', '2317.TW', '2382.TW', '3231.TW', # 權值五虎
    '6669.TW', '2376.TW', '2357.TW', '3017.TW', '3324.TW', # 伺服器與散熱
    '3711.TW', '2308.TW', '2301.TW', '3661.TW', '3443.TW', # 封裝、電源與ASIC設計
    '2303.TW', '5269.TW', '2379.TW', '3034.TW', '2449.TW', # IC設計與測試
    '8046.TW', '3037.TW', '3583.TW', '6223.TW', '2049.TW'  # 載板、設備與機器人概念
]

# ==========================================
# 2. 防彈版量化核心 (已針對 yfinance 更新優化)
# ==========================================
def get_fundamentals(ticker):
    try:
        stock = yf.Ticker(ticker)
        # 優先抓取即時價格
        try:
            price = stock.fast_info['lastPrice']
        except:
            hist = stock.history(period="1d")
            price = hist['Close'].iloc[-1] if not hist.empty else 0
        
        info = stock.info
        eps = info.get('trailingEps', info.get('forwardEps', 1.0))
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
        if df.empty or len(df) < 20: return None
        
        # 移除時區限制，避免計算報錯
        df.index = df.index.tz_localize(None)

        # 手工計算指標：布林通道 (20, 2)
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['STD_20'] = df['Close'].rolling(window=20).std()
        df['Lower_Band'] = df['SMA_20'] - (df['STD_20'] * 2)
        
        # 手工計算指標：RSI (14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI_14'] = 100 - (100 / (1 + (gain / loss)))
        
        latest, prev = df.iloc[-1], df.iloc[-2]
        rsi_14, close_price, lower_band = latest['RSI_14'], latest['Close'], latest['Lower_Band']
        
        if pd.isna(rsi_14) or pd.isna(lower_band): return None
        
        tech_status = "中性"
        if rsi_14 < 30: tech_status = "RSI超賣"
        elif close_price <= lower_band * 1.02: tech_status = "通道底部支撐"
        elif rsi_14 > 30 and prev['RSI_14'] <= 30: tech_status = "超賣突破反轉"
            
        return {'RSI(14)': round(rsi_14, 2), 'Tech_Status': tech_status}
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
        score = 100
        if not np.isnan(data['P/E']) and data['P/E'] < 15: score += (15 - data['P/E']) * 2
        if not np.isnan(data['P/B']) and data['P/B'] < 2: score += (2 - data['P/B']) * 10
        if data['RSI(14)'] < 40: score += (40 - data['RSI(14)'])
        if data['Tech_Status'] in ["通道底部支撐", "超賣突破反轉"]: score += 20
        
        data['Total_Score'] = score
        results.append(data)
        time.sleep(2) # 稍微停頓，避免被 Yahoo 封鎖
    
    df = pd.DataFrame(results)
    return df.sort_values(by='Total_Score', ascending=False).head(10) if not df.empty else df

def send_telegram(message):
    """加強版：會回報失敗原因的發送函數"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ 錯誤：環境變數缺失，無法發送訊息。")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram 訊息發送成功！")
        else:
            print(f"❌ Telegram 發送失敗！錯誤碼: {response.status_code}")
            print(f"❌ 伺服器回傳訊息: {response.text}")
    except Exception as e:
        print(f"❌ 網路連線發生錯誤: {e}")

# ==========================================
# 4. 主程式執行
# ==========================================
if __name__ == "__main__":
    print(f"DEBUG: 嘗試讀取 Token 長度 = {len(str(TELEGRAM_TOKEN)) if TELEGRAM_TOKEN else '找不到'}")
    print(f"DEBUG: 嘗試讀取 Chat ID = {TELEGRAM_CHAT_ID if TELEGRAM_CHAT_ID else '找不到'}")
    
    print("🚀 啟動掃描...")
    # ... 原本的掃描程式碼 ...
    print("🚀 開始掃描美股...")
    us_df = run_quant_screener("美股", US_STOCKS)
    
    print("🚀 開始掃描台股...")
    tw_df = run_quant_screener("台股", TW_STOCKS)
    
    report = f"📊 <b>【量化雲端：正式啟動】</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "-----------------------------------\n"
    
    has_data = False
    if not tw_df.empty:
        has_data = True
        report += "🇹🇼 <b>台股 Top 10:</b>\n"
        for _, r in tw_df.iterrows(): report += f"🔹 <code>{r['Ticker']}</code>: {r['Total_Score']:.1f}\n"
            
    if not us_df.empty:
        has_data = True
        report += "\n🇺🇸 <b>美股 Top 10:</b>\n"
        for _, r in us_df.iterrows(): report += f"🔹 <code>{r['Ticker']}</code>: {r['Total_Score']:.1f}\n"

    if not has_data:
        report += "📢 今日兩大市場皆無符合標準的低估標的。\n"
    
    print("📤 正在嘗試發送 Telegram 報告...")
    send_telegram(report)
    print("🏁 程式執行完畢！")
