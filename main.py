import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time

# ==========================================
# 1. 配置 400 檔標的與產業分類
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_stock_config():
    # 美股清單 (100科技, 50傳產, 50能源)
    us_tech = ['NVDA', 'AMD', 'INTC', 'TSM', 'AVGO', 'QCOM', 'MRVL', 'ARM', 'ASML', 'AMAT', 'LRCX', 'KLAC', 'MU', 'SMCI', 'DELL', 'HPE', 'VRT', 'ANET', 'MSFT', 'GOOGL', 'AMZN', 'META', 'PLTR', 'CDNS', 'SNPS', 'TXN', 'ADI', 'NXPI', 'MCHP', 'ON', 'MPWR', 'LSCC', 'POWI', 'RMBS', 'WOLF', 'CRUS', 'TER', 'ENTG', 'MKSI', 'CCCS', 'GFS', 'SWKS', 'QRVO', 'STM', 'LOGI', 'STX', 'WDC', 'NTAP', 'PSTG', 'NTNX', 'ESTC', 'SNOW', 'DDOG', 'MDB', 'CRWD', 'PANW', 'FTNT', 'ZS', 'OKTA', 'NET', 'CFLT', 'TEAM', 'ADSK', 'ORCL', 'IBM', 'AAPL', 'CSCO', 'ADBE', 'INTU', 'NOW', 'CRM', 'SAP', 'ACN', 'INFY', 'GDDY', 'WIX', 'SHOP', 'SQ', 'PYPL', 'AFRM', 'HOOD', 'COIN', 'MSTR', 'RIOT', 'MARA', 'CLSK', 'CAN', 'NCTY', 'BTBT', 'HIVE', 'BITF', 'HUT', 'CIFR', 'WULF', 'IREN', 'CORZ', 'TEL', 'APH']
    us_trad = ['CAT', 'DE', 'MMM', 'HON', 'GE', 'UPS', 'FDX', 'LMT', 'BA', 'NOC', 'GD', 'RTX', 'NSC', 'UNP', 'CSX', 'WM', 'RSG', 'ETN', 'ITW', 'PH', 'ROP', 'FAST', 'GWW', 'URI', 'PCAR', 'IR', 'DOV', 'XYL', 'CMI', 'TT', 'JCI', 'CARR', 'OTIS', 'HUBB', 'AOS', 'FNF', 'MAR', 'HLT', 'RCL', 'CCL', 'NCLH', 'EXPE', 'BKNG', 'DAL', 'UAL', 'AAL', 'LUV', 'JBLU', 'EMR']
    us_ener = ['XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BKR', 'OXY', 'MPC', 'PSX', 'VLO', 'EOG', 'DVN', 'FANG', 'MRO', 'APA', 'CTRA', 'EQT', 'AR', 'RRC', 'SWN', 'CHRD', 'CIVI', 'MTDR', 'PR', 'SM', 'HP', 'NOV', 'RIG', 'NE', 'DO', 'SDRL', 'PTEN', 'TDW', 'OII', 'FTI', 'TS', 'VAL', 'BORR', 'MUR', 'CRC', 'VTLE', 'SBOW', 'GPOR', 'NEE', 'DUK', 'SO', 'D', 'AEP']
    
    # 台股清單 (100科技, 50傳產, 50能源)
    tw_tech = ['2330.TW', '2454.TW', '2317.TW', '2382.TW', '3231.TW', '6669.TW', '2376.TW', '2357.TW', '3017.TW', '3324.TW', '3711.TW', '2308.TW', '2301.TW', '3661.TW', '3443.TW', '2303.TW', '5269.TW', '2379.TW', '3034.TW', '2449.TW', '8046.TW', '3037.TW', '3583.TW', '2356.TW', '3035.TW', '3227.TW', '6415.TW', '6138.TW', '2345.TW', '6239.TW', '6205.TW', '6182.TW', '6488.TW', '2351.TW', '2474.TW', '2324.TW', '2352.TW', '6515.TW', '6282.TW', '2458.TW', '2377.TW', '2353.TW', '2409.TW', '3481.TW', '6116.TW', '2408.TW', '2481.TW', '2441.TW', '3532.TW', '6271.TW', '3376.TW', '2421.TW', '3013.TW', '2412.TW', '4904.TW', '3045.TW', '2455.TW', '3189.TW', '4958.TW', '6414.TW', '2360.TW', '2439.TW', '6206.TW', '3005.TW', '2344.TW', '2337.TW', '3006.TW', '2368.TW', '2313.TW', '3044.TW', '2393.TW', '2486.TW', '2327.TW', '2492.TW', '6120.TW', '2451.TW', '3596.TW', '6213.TW', '3023.TW', '3042.TW', '2385.TW', '2383.TW', '6278.TW', '3030.TW', '6153.TW', '3533.TW', '3515.TW', '2347.TW', '2395.TW', '3293.TW']
    tw_trad = ['2105.TW', '1101.TW', '1102.TW', '1301.TW', '1303.TW', '1326.TW', '6505.TW', '2603.TW', '2609.TW', '2615.TW', '2002.TW', '2014.TW', '2006.TW', '2610.TW', '2618.TW', '9904.TW', '9910.TW', '9921.TW', '9914.TW', '1402.TW', '1434.TW', '1476.TW', '1477.TW', '1216.TW', '1227.TW', '1722.TW', '1710.TW', '1704.TW', '1504.TW', '1513.TW', '1519.TW', '1503.TW', '2312.TW', '2392.TW', '2912.TW', '2903.TW', '2707.TW', '2727.TW', '2633.TW', '2634.TW', '1802.TW', '2101.TW', '2106.TW', '2201.TW', '2204.TW', '2206.TW', '5522.TW', '2542.TW', '2548.TW']
    tw_ener = ['1514.TW', '1609.TW', '1608.TW', '1605.TW', '6806.TW', '6873.TW', '8926.TW', '6443.TW', '6477.TW', '3576.TW', '6409.TW', '3686.TW', '2406.TW', '9933.TW', '1723.TW', '1762.TW', '1314.TW', '1712.TW', '1714.TW', '1717.TW', '1720.TW', '1725.TW', '1727.TW', '1731.TW', '1733.TW', '1734.TW', '1736.TW', '4739.TW', '4755.TW', '4763.TW', '4766.TW', '4770.TW', '6504.TW', '6605.TW', '6670.TW', '6691.TW', '6781.TW', '6790.TW', '6854.TW', '6869.TW']
    
    return [
        (us_tech, '美股', '科技'), (us_trad, '美股', '傳產'), (us_ener, '美股', '能源'),
        (tw_tech, '台股', '科技'), (tw_trad, '台股', '傳產'), (tw_ener, '台股', '能源')
    ]

# ==========================================
# 2. 核心分析與市值過濾
# ==========================================
def get_fundamentals(ticker, market_type):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
        m_cap = info.get('marketCap', 0)
        
        # --- 市值與股價濾網 ---
        if market_type == '美股':
            if m_cap < 1000000000 or price < 5: return None # 10億美金 & 5元
        else:
            if m_cap < 5000000000 or price < 15: return None # 50億台幣 & 15元
            
        pe = info.get('trailingPE', np.nan)
        pb = info.get('priceToBook', np.nan)
        name = info.get('shortName', ticker)
        return {'Ticker': ticker, 'Name': name, 'Price': price, 'P/E': pe, 'P/B': pb, 'M_Cap': m_cap}
    except:
        return None

def analyze_technical(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty or len(df) < 25: return None
        df.index = df.index.tz_localize(None)
        
        # RSI, Bollinger, Volume
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['STD_20'] = df['Close'].rolling(window=20).std()
        df['Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))
        
        df['V_MA20'] = df['Volume'].rolling(window=20).mean()
        latest, prev = df.iloc[-1], df.iloc[-2]
        
        chg = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
        v_ratio = latest['Volume'] / latest['V_MA20'] if latest['V_MA20'] > 0 else 1
        
        status = "中性"
        if latest['RSI'] < 30: status = "RSI超賣"
        elif latest['Close'] <= latest['Lower'] * 1.02: status = "通道底部"
        elif latest['RSI'] > 30 and prev['RSI'] <= 30: status = "超賣反轉"
        if v_ratio > 1.5: status += "+量爆發"
            
        return {'Price': round(latest['Close'], 2), 'Chg%': round(chg, 2), 'RSI': round(latest['RSI'], 2), 'V_Ratio': round(v_ratio, 2), 'Status': status}
    except:
        return None

def scan_segment(stock_list, m_type, cat_type):
    results = []
    print(f"🔍 掃描 {m_type}-{cat_type} (共 {len(stock_list)} 檔)...")
    for ticker in stock_list:
        fund = get_fundamentals(ticker, m_type)
        if not fund: continue
        tech = analyze_technical(ticker)
        if not tech: continue
        
        data = {**fund, **tech, 'Market': m_type, 'Category': cat_type}
        score = 100
        if not np.isnan(data['P/E']) and data['P/E'] < 15: score += min((15 - data['P/E']) * 2, 40)
        if not np.isnan(data['P/B']) and data['P/B'] < 2: score += min((2 - data['P/B']) * 10, 40)
        score += (40 - data['RSI']) if data['RSI'] < 40 else 0
        if data['V_Ratio'] > 1.5: score += 30 
        if "底部" in data['Status'] or "反轉" in data['Status']: score += 20
        
        data['Score'] = score
        results.append(data)
        time.sleep(1.2)
    return results

# ==========================================
# 3. 執行執行與分組報告
# ==========================================
if __name__ == "__main__":
    configs = get_stock_config()
    all_results = []
    for s_list, m_type, c_type in configs:
        all_results.extend(scan_segment(s_list, m_type, c_type))
    
    df_all = pd.DataFrame(all_results)
    if df_all.empty:
        print("今日無資料")
        exit()

    report = f"📊 <b>【量化雷達 3.0：產業海選版】</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "-----------------------------------\n\n"

    for m in ['台股', '美股']:
        df_m = df_all[df_all['Market'] == m]
        report += f"👑 <b>{m} 總榜 Top 10</b>\n"
        top10 = df_m.sort_values('Score', ascending=False).head(10)
        for _, r in top10.iterrows():
            v_i = "🔥" if r['V_Ratio'] > 1.5 else ""
            w_i = "⚠️" if r['Chg%'] <= -10 else ""
            report += f"🔹 <code>{r['Ticker']}</code>: {r['Score']:.1f} {v_i}{w_i} ({r['Category']})\n"
        
        report += f"\n🏆 <b>{m} 分類精選 Top 5</b>\n"
        for cat in ['科技', '傳產', '能源']:
            df_cat = df_m[df_m['Category'] == cat]
            if not df_cat.empty:
                top5 = df_cat.sort_values('Score', ascending=False).head(5)
                report += f"📍 <i>{cat}:</i> " + ", ".join([f"<code>{r['Ticker']}</code>" for _, r in top5.iterrows()]) + "\n"
        report += "\n" + "="*20 + "\n\n"

    # Telegram 發送 (長訊息分割處理)
    if len(report) > 4000: report = report[:3900] + "\n...(訊息過長)"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": report, "parse_mode": "HTML"})
