import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time

# ==========================================
# 1. 系統設定與 Telegram 參數
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_market_config():
    # ---------------- 美股 (200 科技 + 50 能源) ----------------
    us_tech = [
        'NVDA', 'AMD', 'INTC', 'TSM', 'AVGO', 'QCOM', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'AAPL', 'CSCO', 'ADBE', 'ORCL', 'CRM', 'NOW', 'INTU', 'IBM', 'ACN', 'SAP',
        'TXN', 'ADI', 'NXPI', 'MCHP', 'ON', 'MPWR', 'CDNS', 'SNPS', 'KLAC', 'LRCX',
        'AMAT', 'ASML', 'MU', 'SMCI', 'DELL', 'HPE', 'VRT', 'ANET', 'PANW', 'CRWD',
        'FTNT', 'ZS', 'OKTA', 'NET', 'SNOW', 'DDOG', 'MDB', 'SHOP', 'SQ', 'PYPL',
        'PLTR', 'ARM', 'MRVL', 'STX', 'WDC', 'NTAP', 'PSTG', 'NTNX', 'ESTC', 'TEAM',
        'ADSK', 'INFY', 'GDDY', 'WIX', 'AFRM', 'HOOD', 'COIN', 'MSTR', 'RIOT', 'MARA',
        'CLSK', 'CAN', 'NCTY', 'BTBT', 'HIVE', 'BITF', 'HUT', 'CIFR', 'WULF', 'IREN',
        'CORZ', 'TEL', 'APH', 'KEYS', 'TER', 'ENTG', 'MKSI', 'CCCS', 'GFS', 'SWKS',
        'QRVO', 'STM', 'LOGI', 'RNG', 'AKAM', 'FSLY', 'U', 'RBLX', 'PATH', 'AI'
    ]
    us_ener = [
        'XOM', 'CVX', 'COP', 'SLB', 'HAL', 'CCJ', 'URA', 'SMR', 'OKLO', 'VST',
        'CEG', 'NLR', 'BW', 'FLR', 'UUUU', 'MPC', 'PSX', 'VLO', 'EOG', 'DVN',
        'FANG', 'NEE', 'DUK', 'SO', 'D'
    ]
    
    # ---------------- 台股 (200 科技 + 50 能源重電) ----------------
    tw_tech = [
        '2330.TW', '2454.TW', '2317.TW', '2382.TW', '3231.TW', '6669.TW', '2376.TW', '2357.TW', '3017.TW', '3324.TW',
        '3711.TW', '2308.TW', '2301.TW', '3661.TW', '3443.TW', '2303.TW', '5269.TW', '2379.TW', '3034.TW', '2449.TW',
        '8046.TW', '3037.TW', '3583.TW', '2356.TW', '3035.TW', '3227.TW', '6415.TW', '6138.TW', '2345.TW', '6239.TW',
        '6205.TW', '6182.TW', '6488.TW', '2351.TW', '2474.TW', '2324.TW', '2352.TW', '6515.TW', '6282.TW', '2458.TW',
        '2377.TW', '2353.TW', '2409.TW', '3481.TW', '6116.TW', '2408.TW', '2481.TW', '2441.TW', '3532.TW', '6271.TW',
        '3376.TW', '2421.TW', '3013.TW', '2412.TW', '4904.TW', '3045.TW', '2455.TW', '3189.TW', '4958.TW', '6414.TW',
        '2360.TW', '2439.TW', '6206.TW', '3005.TW', '2344.TW', '2337.TW', '3006.TW', '2368.TW', '2313.TW', '3044.TW',
        '2393.TW', '2486.TW', '2327.TW', '2492.TW', '6120.TW', '2451.TW', '3596.TW', '6213.TW', '3023.TW', '3042.TW',
        '2385.TW', '2383.TW', '6278.TW', '3030.TW', '6153.TW', '3533.TW', '3515.TW', '2347.TW', '2395.TW', '3293.TW',
        '6223.TW', '8021.TW', '3264.TW', '6147.TW', '5483.TW', '6411.TW', '3105.TW', '6188.TW', '5347.TW', '3680.TW'
    ]
    tw_ener = [
        '1513.TW', '1519.TW', '1503.TW', '1514.TW', '1609.TW', '1608.TW', '1605.TW', '6806.TW', '6873.TW', '8926.TW',
        '6443.TW', '6477.TW', '3576.TW', '6409.TW', '3686.TW', '2406.TW', '9933.TW', '1723.TW', '1762.TW', '1314.TW',
        '1712.TW', '1714.TW', '1717.TW', '1720.TW', '1725.TW'
    ]
    
    # ---------------- 加密貨幣 (10 檔知名) ----------------
    crypto = [
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD', 
        'ADA-USD', 'AVAX-USD', 'DOGE-USD', 'DOT-USD', 'LINK-USD'
    ]

    return [
        (us_tech, '美股', '科技'), (us_ener, '美股', '能源'),
        (tw_tech, '台股', '科技'), (tw_ener, '台股', '能源'),
        (crypto, '加密貨幣', 'Crypto')
    ]

# ==========================================
# 2. 核心量化分析與評分邏輯
# ==========================================
def analyze_asset(ticker, market, category):
    try:
        asset = yf.Ticker(ticker)
        # 抓取 6 個月歷史資料以計算波動率與均線
        df = asset.history(period="6mo")
        if df.empty or len(df) < 30: return None
        
        info = asset.info
        curr_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        chg_pct = ((curr_price - prev_price) / prev_price) * 100
        
        # --- 基本過濾 ---
        m_cap = info.get('marketCap', 0)
        if market == '美股' and (m_cap < 1e9 or curr_price < 5): return None
        if market == '台股' and (m_cap < 5e9 or curr_price < 15): return None

        # --- 技術指標計算 ---
        # 1. 均線與布林通道
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        std20 = df['Close'].rolling(window=20).std().iloc[-1]
        upper_band = ma20 + (2 * std20)
        
        # 2. RSI (相對強弱)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
        
        # 3. 波動率 (用於目標價)
        daily_return = df['Close'].pct_change().dropna()
        # 加密貨幣一週7天，股票一週5天
        days_in_week = 7 if market == '加密貨幣' else 5
        volatility_7d = daily_return.std() * np.sqrt(days_in_week)

        # --- 評分系統 (總分 100) 與 高分原因判定 ---
        score = 0
        reasons = []
        
        # A. 趨勢分 (最高 40)
        if curr_price > ma20:
            score += 30
            reasons.append("站上月線")
            if curr_price > upper_band:
                score += 10
                reasons.append("突破布林上軌")
        else:
            score += 10 # 跌破月線基礎分
            
        # B. 動能分 (最高 30)
        if 40 <= rsi <= 70:
            score += 30
            reasons.append("動能穩健")
        elif rsi < 30:
            score += 20
            reasons.append("RSI超賣反彈機率高")
        elif rsi > 70:
            score += 15 # 超買區風險較高，給分較低
            reasons.append("強勢但逼近超買")
            
        # C. 價值/題材分 (最高 30，加密貨幣以動能取代)
        if market != '加密貨幣':
            pe = info.get('trailingPE', 30)
            if pe < 15 and pe > 0:
                score += 30
                reasons.append("本益比偏低(<15)")
            elif pe < 25 and pe > 0:
                score += 15
                reasons.append("估值合理")
        else:
            # 加密貨幣若 24h 漲幅超過 5% 給予動能加分
            if chg_pct > 5:
                score += 30
                reasons.append("24H強勢爆發")
            elif chg_pct > 0:
                score += 15
                reasons.append("維持多頭格局")

        # 整理高分原因 (取前兩個最顯著的)
        reason_str = "、".join(reasons[:2]) if reasons else "盤整中"

        # --- 一週目標價推算 ---
        # 若分數 > 60，預測向上 1 個標準差；否則預測向下支撐
        direction = 1 if score > 60 else -1
        target_price = curr_price * (1 + (volatility_7d * direction))

        # --- 狀態標籤 ---
        status = "🔥強勢" if score >= 80 else "轉強" if score >= 60 else "⚠️轉弱"
        if rsi > 75: status = "🚨超買"
        if rsi < 25: status = "❄️超跌"

        return {
            'Ticker': ticker,
            'Market': market,
            'Category': category,
            'Price': curr_price,
            'ChgPct': chg_pct,
            'Target': target_price,
            'Score': score,
            'RSI': round(rsi, 1),
            'Status': status,
            'Reason': reason_str
        }
    except Exception as e:
        return None

# ==========================================
# 3. 執行分析與發送 Telegram 報表
# ==========================================
if __name__ == "__main__":
    print(f"啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    configs = get_market_config()
    all_results = []
    
    # 計算總標的數
    total_assets = sum(len(s[0]) for s in configs)
    print(f"🚀 量化雷達啟動，準備掃描 {total_assets} 檔標的...")

    for s_list, m_type, c_type in configs:
        for ticker in s_list:
            res = analyze_asset(ticker, m_type, c_type)
            if res:
                all_results.append(res)
            time.sleep(0.25) # 控制請求頻率，避免被 yfinance 擋

    df_all = pd.DataFrame(all_results)
    if df_all.empty:
        print("❌ 今日無掃描資料，程式結束。")
        exit()

    # --- 建立報表 ---
    report = f"📊 <b>【量化雷達 5.0：全市場掃描】</b>\n"
    report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "-----------------------------------\n"

    # 定義要發送的市場順序
    markets_to_report = ['加密貨幣', '台股', '美股']

    for m in markets_to_report:
        df_m = df_all[df_all['Market'] == m].sort_values(by='Score', ascending=False)
        if df_m.empty: continue
        
        report += f"\n🏆 <b>{m} 強勢榜 Top 10</b>\n"
        
        top_10 = df_m.head(10)
        for _, r in top_10.iterrows():
            # 數值格式化
            p_str = f"{r['Price']:.2f}"
            c_str = f"{r['ChgPct']:+.2f}%"
            t_str = f"{r['Target']:.2f}"
            
            icon = "⭐" if r['Score'] >= 80 else "🔹"
            
            # 第一行：代碼、現價、漲跌、目標價、分數
            report += f"{icon} <code>{r['Ticker']}</code>: {p_str} ({c_str}) 🎯{t_str} <b>[{r['Score']}]</b>\n"
            # 第二行：狀態、RSI、高分原因
            report += f"   ➔ {r['Status']} | RSI:{r['RSI']} | 💡{r['Reason']}\n"
            
        report += "-----------------------------------\n"

    # --- Telegram 發送邏輯 ---
    print("準備發送報表至 Telegram...")
    # 若訊息過長，Telegram API 限制為 4096 字元，進行安全截斷
    if len(report) > 4000:
        report = report[:3950] + "\n...(資料過多，僅顯示部分內容)"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": report, 
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ 報表已成功送達 Telegram！")
    else:
        print(f"❌ 發送失敗，錯誤代碼: {response.status_code}")
        print(response.text)
