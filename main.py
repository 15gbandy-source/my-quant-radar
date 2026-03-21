import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time

# ==========================================
# 1. 環境變數與清單 (維持 50 檔)
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

US_STOCKS = [
    # --- 科技業 (100 檔) ---
    'NVDA', 'AMD', 'INTC', 'TSM', 'AVGO', 'QCOM', 'MRVL', 'ARM', 'ASML', 'AMAT',
    'LRCX', 'KLAC', 'MU', 'SMCI', 'DELL', 'HPE', 'VRT', 'ANET', 'MSFT', 'GOOGL',
    'AMZN', 'META', 'PLTR', 'CDNS', 'SNPS', 'TXN', 'ADI', 'NXPI', 'MCHP', 'ON',
    'MPWR', 'LSCC', 'POWI', 'RMBS', 'WOLF', 'CRUS', 'TER', 'ENTG', 'MKSI', 'CCCS',
    'GFS', 'SWKS', 'QRVO', 'STM', 'LOGI', 'STX', 'WDC', 'NTAP', 'PSTG', 'NTNX',
    'ESTC', 'SNOW', 'DDOG', 'MDB', 'CRWD', 'PANW', 'FTNT', 'ZS', 'OKTA', 'NET',
    'CFLT', 'TEAM', 'ADSK', 'ORCL', 'IBM', 'AAPL', 'CSCO', 'ADBE', 'INTU', 'NOW',
    'CRM', 'SAP', 'ACN', 'INFY', 'GDDY', 'WIX', 'SHOP', 'SQ', 'PYPL', 'AFRM',
    'HOOD', 'COIN', 'MSTR', 'RIOT', 'MARA', 'CLSK', 'CAN', 'NCTY', 'BTBT', 'HIVE',
    'BITF', 'HUT', 'CIFR', 'WULF', 'IREN', 'CORZ', 'TERW', 'WBT', 'TEL', 'APH',
    # --- 傳統工業 (50 檔) ---
    'CAT', 'DE', 'MMM', 'HON', 'GE', 'UPS', 'FDX', 'LMT', 'BA', 'NOC', 
    'GD', 'RTX', 'NSC', 'UNP', 'CSX', 'WM', 'RSG', 'ETN', 'ITW', 'PH', 
    'ROP', 'FAST', 'GWW', 'URI', 'PCAR', 'IR', 'DOV', 'XYL', 'CMI', 'TT', 
    'JCI', 'CARR', 'OTIS', 'HUBB', 'AOS', 'FNF', 'MAR', 'HLT', 'RCL', 'CCL', 
    'NCLH', 'EXPE', 'BKNG', 'DAL', 'UAL', 'AAL', 'LUV', 'JBLU', 'EMR', 'DOV',
    # --- 能源 (50 檔) ---
    'XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BKR', 'OXY', 'MPC', 'PSX', 'VLO', 
    'EOG', 'DVN', 'FANG', 'MRO', 'APA', 'CTRA', 'EQT', 'AR', 'RRC', 'SWN', 
    'CHRD', 'CIVI', 'MTDR', 'PR', 'SM', 'CPE', 'HP', 'NOV', 'RIG', 'NE', 
    'DO', 'SDRL', 'PTEN', 'TDW', 'OII', 'FTI', 'TS', 'VAL', 'BORR', 'MUR', 
    'CRC', 'CHK', 'VTLE', 'SBOW', 'GPOR', 'NEE', 'DUK', 'SO', 'D', 'AEP'
]
TW_STOCKS = [
    # --- 科技業 (100 檔) ---
    '2330.TW', '2454.TW', '2317.TW', '2382.TW', '3231.TW', '6669.TW', '2376.TW', '2357.TW',
    '3017.TW', '3324.TW', '3711.TW', '2308.TW', '2301.TW', '3661.TW', '3443.TW', '2303.TW',
    '5269.TW', '2379.TW', '3034.TW', '2449.TW', '8046.TW', '3037.TW', '3583.TW', '6223.TW',
    '2049.TW', '2356.TW', '4966.TW', '4961.TW', '3035.TW', '3529.TW', '3227.TW', '6415.TW',
    '6138.TW', '2345.TW', '6239.TW', '6205.TW', '6147.TW', '6182.TW', '5483.TW', '6488.TW',
    '3105.TW', '2351.TW', '2474.TW', '2324.TW', '2352.TW', '3264.TW', '6515.TW', '6282.TW',
    '2458.TW', '2377.TW', '2353.TW', '2409.TW', '3481.TW', '6116.TW', '2408.TW', '2481.TW',
    '2441.TW', '3532.TW', '6271.TW', '3376.TW', '2421.TW', '3013.TW', '2412.TW', '4904.TW',
    '3045.TW', '2455.TW', '3189.TW', '4958.TW', '6414.TW', '2360.TW', '2439.TW', '6206.TW',
    '3005.TW', '2344.TW', '2337.TW', '3006.TW', '2368.TW', '2313.TW', '3044.TW', '2393.TW',
    '2486.TW', '5347.TW', '2327.TW', '2492.TW', '6120.TW', '2451.TW', '3596.TW', '6213.TW',
    '3023.TW', '3042.TW', '2385.TW', '2383.TW', '6278.TW', '3030.TW', '6153.TW', '3533.TW',
    '3515.TW', '2347.TW', '2395.TW', '3293.TW',
    # --- 傳統工業 (50 檔) ---
    '2105.TW', '1101.TW', '1102.TW', '1301.TW', '1303.TW', '1326.TW', '6505.TW', '2603.TW',
    '2609.TW', '2615.TW', '2002.TW', '2014.TW', '2006.TW', '2610.TW', '2618.TW', '9904.TW',
    '9910.TW', '9921.TW', '9914.TW', '1402.TW', '1434.TW', '1476.TW', '1477.TW', '1216.TW',
    '1227.TW', '1722.TW', '1710.TW', '1704.TW', '1504.TW', '1513.TW', '1519.TW', '1503.TW',
    '2312.TW', '2392.TW', '2912.TW', '2903.TW', '5904.TW', '2707.TW', '2727.TW', '2633.TW',
    '2634.TW', '1802.TW', '2101.TW', '2106.TW', '2201.TW', '2204.TW', '2206.TW', '5522.TW',
    '2542.TW', '2548.TW',
    # --- 能源/重電/綠能 (50 檔) ---
    '1513.TW', '1519.TW', '1514.TW', '1609.TW', '1608.TW', '1605.TW', '6806.TW', '6873.TW',
    '8916.TW', '8926.TW', '6443.TW', '6477.TW', '3576.TW', '6409.TW', '6244.TW', '3686.TW',
    '3514.TW', '2406.TW', '9933.TW', '6508.TW', '1723.TW', '1762.TW', '1314.TW', '1712.TW',
    '1714.TW', '1717.TW', '1720.TW', '1725.TW', '1727.TW', '1731.TW', '1733.TW', '1734.TW',
    '1736.TW', '4725.TW', '4739.TW', '4755.TW', '4763.TW', '4766.TW', '4770.TW', '6504.TW',
    '6509.TW', '6605.TW', '6612.TW', '6670.TW', '6691.TW', '6781.TW', '6790.TW', '6803.TW',
    '6854.TW', '6869.TW'
]

# ==========================================
# 2. 核心分析引擎 (加入漲跌幅監控)
# ==========================================
def get_fundamentals(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        pe = info.get('trailingPE', np.nan)
        pb = info.get('priceToBook', np.nan)
        name = info.get('shortName', ticker)
        return {'Ticker': ticker, 'Name': name, 'P/E': pe, 'P/B': pb}
    except:
        return None

def analyze_technical(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty or len(df) < 25: return None
        df.index = df.index.tz_localize(None)

        # 指標計算
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['STD_20'] = df['Close'].rolling(window=20).std()
        df['Lower_Band'] = df['SMA_20'] - (df['STD_20'] * 2)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI_14'] = 100 - (100 / (1 + (gain / loss)))
        
        df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- 核心更新：計算今日漲跌幅 ---
        change_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
        vol_ratio = latest['Volume'] / latest['Vol_MA20'] if latest['Vol_MA20'] > 0 else 1
        
        tech_status = "中性"
        if latest['RSI_14'] < 30: tech_status = "RSI超賣"
        elif latest['Close'] <= latest['Lower_Band'] * 1.02: tech_status = "通道底部"
        elif latest['RSI_14'] > 30 and prev['RSI_14'] <= 30: tech_status = "超賣反轉"
        
        if vol_ratio > 1.5: tech_status += "+量爆發"
            
        return {
            'Price': round(latest['Close'], 2),
            'Change_Pct': round(change_pct, 2),
            'RSI(14)': round(latest['RSI_14'], 2), 
            'Vol_Ratio': round(vol_ratio, 2), 
            'Tech_Status': tech_status
        }
    except:
        return None

def run_quant_screener(market_name, stock_list):
    results = []
    print(f"🔍 開始掃描 {market_name}...")
    for ticker in stock_list:
        fund = get_fundamentals(ticker)
        if not fund: continue
        tech = analyze_technical(ticker)
        if not tech: continue
        
        data = {**fund, **tech, 'Market': market_name}
        score = 100
        
        # 評分與封頂 (維持之前的邏輯)
        if not np.isnan(data['P/E']) and data['P/E'] < 15: score += min((15 - data['P/E']) * 2, 40)
        if not np.isnan(data['P/B']) and data['P/B'] < 2: score += min((2 - data['P/B']) * 10, 40)
        if data['RSI(14)'] < 40: score += (40 - data['RSI(14)'])
        if data['Vol_Ratio'] > 1.5: score += 30 
        if "通道底部" in data['Tech_Status'] or "超賣反轉" in data['Tech_Status']: score += 20
        
        data['Total_Score'] = score
        results.append(data)
        time.sleep(1.2)
    
    df = pd.DataFrame(results)
    return df.sort_values(by='Total_Score', ascending=False).head(10) if not df.empty else df

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

# ==========================================
# 3. 報表生成 (加入警示標籤)
# ==========================================
if __name__ == "__main__":
    us_df = run_quant_screener("美股", US_STOCKS)
    tw_df = run_quant_screener("台股", TW_STOCKS)
    
    report = f"🚀 <b>【量化雷達 2.1：安全升級版】</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "-----------------------------------\n"
    report += "🔥:量爆發  ⚠️:暴跌警示(>-10%)\n\n"
    
    for market_name, df in [("🇹🇼 <b>台股 Top 10</b>", tw_df), ("🇺🇸 <b>美股 Top 10</b>", us_df)]:
        report += f"{market_name}:\n"
        if not df.empty:
            for _, r in df.iterrows():
                # 判定圖示
                vol_icon = "🔥" if r['Vol_Ratio'] > 1.5 else ""
                warn_icon = "⚠️" if r['Change_Pct'] <= -10 else ""
                
                # 漲跌幅格式化 (+5.2% 或 -12.3%)
                change_str = f"+{r['Change_Pct']}%" if r['Change_Pct'] > 0 else f"{r['Change_Pct']}%"
                
                report += f"🔹 <code>{r['Ticker']}</code>: {r['Total_Score']:.1f} {vol_icon}{warn_icon}\n"
                report += f"   <i>(價:{r['Price']}, 漲跌:{change_str})</i>\n"
                report += f"   <i>({r['Tech_Status']}, 量比:{r['Vol_Ratio']})</i>\n"
        else:
            report += "無符合標的\n"
        report += "\n"
    
    send_telegram(report)
