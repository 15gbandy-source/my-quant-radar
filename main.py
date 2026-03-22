import os
import yfinance as yf
import pandas as pd
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
# 2. 核心量化引擎：長線多頭與乖離率策略
# ==========================================
def analyze_long_term_asset(ticker, market, category):
    try:
        asset = yf.Ticker(ticker)
        # 長線均線需要至少 1 年的歷史交易日
        df = asset.history(period="1y")
        if df.empty or len(df) < 200: 
            return None
        
        curr_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        chg_pct = ((curr_price - prev_price) / prev_price) * 100
        
        # --- 流動性防護網 ---
        avg_vol_20 = df['Volume'].rolling(window=20).mean().iloc[-1]
        daily_turnover = avg_vol_20 * curr_price
        # 台股均量單位為股，1億台幣為底線；美股/Crypto 1000萬美元為底線
        if market == '台股' and daily_turnover < 100_000_000: return None
        if market in ['美股', '加密貨幣'] and daily_turnover < 10_000_000: return None

        # --- 長線技術護城河 ---
        ma50 = df['Close'].rolling(window=50).mean().iloc[-1]
        ma200 = df['Close'].rolling(window=200).mean().iloc[-1]
        
        # [嚴格淘汰] 季線跌破年線，長線空頭確立，直接放棄
        if ma50 < ma200:
            return None

        score = 30 # 通過長線多頭考驗，給予基礎分
        reasons = []
        status = "觀察中"

        # --- 寬鬆的基本面加分項 (不強求，避免 API 報錯) ---
        pe_str, roe_str = "N/A", "N/A"
        if market != '加密貨幣':
            try:
                # 設定極短 timeout 或單純用 try-except 包覆，避免雲端執行卡死
                info = asset.info
                pe = info.get('trailingPE')
                roe = info.get('returnOnEquity')
                
                if pe and pe > 0:
                    pe_str = f"{float(pe):.1f}"
                    if (category == '科技' and pe < 35) or (category != '科技' and pe < 15):
                        score += 15
                        reasons.append("估值偏低")
                        
                if roe:
                    roe_val = float(roe) * 100
                    roe_str = f"{roe_val:.1f}%"
                    if roe_val > 15:
                        score += 15
                        reasons.append("高ROE")
            except Exception:
                pass # 忽略 yfinance info 錯誤，純走技術面

        # --- 價格乖離與買點判定 ---
        dist_to_ma50 = (curr_price - ma50) / ma50
        
        if -0.02 <= dist_to_ma50 <= 0.05:
            # 股價落在季線支撐帶附近 (+5% 到 -2%)，屬於波段最佳買點
            score += 40
            reasons.append("回測季線有撐")
            status = "⭐可建倉"
            
        elif dist_to_ma50 > 0.20:
            # 乖離過大，容易有短線回檔壓力
            score -= 10
            reasons.append("乖離過大")
            status = "🚨高風險"
            
        elif dist_to_ma50 > 0.05:
            # 已經發動，穩定爬升中
            score += 20
            reasons.append("多頭延續")
            status = "📈續抱區"
            
        else:
            # 跌破季線較深，有轉弱疑慮
            status = "⚠️跌破季線"

        # [嚴格淘汰] 總分不足 50 或跌破季線轉弱的標的，不顯示在報表上
        if score < 50 or status == "⚠️跌破季線": 
            return None

        reason_str = "、".join(reasons) if reasons else "長線多頭排列"

        return {
            'Ticker': ticker,
            'Market': market,
            'Category': category,
            'Price': curr_price,
            'ChgPct': chg_pct,
            'Score': score,
            'PE': pe_str,
            'ROE': roe_str,
            'DistMA50': dist_to_ma50 * 100, # 儲存數值方便後續排序
            'Status': status,
            'Reason': reason_str
        }
        
    except Exception as e:
        return None

# ==========================================
# 3. 報表生成與 Telegram 推播
# ==========================================
if __name__ == "__main__":
    print(f"啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    configs = get_market_config()
    all_results = []
    
    total_assets = sum(len(s[0]) for s in configs)
    print(f"🚀 長線價值雷達啟動，準備掃描 {total_assets} 檔標的...")

    for s_list, m_type, c_type in configs:
        for ticker in s_list:
            res = analyze_long_term_asset(ticker, m_type, c_type)
            if res:
                all_results.append(res)
            # 確保不會觸發 429 Too Many Requests
            time.sleep(0.3) 

    df_all = pd.DataFrame(all_results)
    if df_all.empty:
        print("❌ 今日全市場無符合【長線多頭】條件之標的，程式結束。")
        exit()

    # --- 建立報表 ---
    report = f"📊 <b>【長線投資雷達：優質標的觀察名單】</b>\n"
    report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "📝 邏輯：長線多頭 (50MA>200MA) + 季線乖離率判定\n"
    report += "-----------------------------------\n"

    markets_to_report = ['台股', '美股', '加密貨幣']

    for m in markets_to_report:
        df_m = df_all[df_all['Market'] == m]
        if df_m.empty: continue
        
        report += f"\n🏆 <b>{m} 市場掃描結果</b>\n"
        
        # 1. 優先顯示「⭐可建倉」(回測季線的標的)
        df_buy = df_m[df_m['Status'] == '⭐可建倉'].sort_values(by='DistMA50', ascending=True)
        if not df_buy.empty:
            report += "<b>【🎯 買點浮現區 (近季線)】</b>\n"
            for _, r in df_buy.head(10).iterrows():
                report += f"🌟 <code>{r['Ticker']}</code>: {r['Price']:.2f} ({r['ChgPct']:+.2f}%)\n"
                if m != '加密貨幣':
                    report += f"    ➔ 體質: PE {r['PE']} | ROE {r['ROE']}\n"
                report += f"    ➔ 距季線: {r['DistMA50']:.1f}% | 💡 {r['Reason']}\n"
            report += "\n"

        # 2. 顯示「📈續抱區」(強勢股)
        df_hold = df_m[df_m['Status'] == '📈續抱區'].sort_values(by='Score', ascending=False)
        if not df_hold.empty:
            report += "<b>【🚀 主升段強勢區 (宜續抱)】</b>\n"
            for _, r in df_hold.head(5).iterrows(): # 強勢股只看前 5 名避免版面太長
                report += f"🔹 <code>{r['Ticker']}</code>: {r['Price']:.2f} ({r['ChgPct']:+.2f}%)\n"
                report += f"    ➔ 距季線: {r['DistMA50']:.1f}%\n"
        
        report += "-----------------------------------\n"

    print("準備發送報表至 Telegram...")
    # 安全截斷，避免字串過長
    if len(report) > 3800:
        report = report[:3800] + "\n\n⚠️ <b>...(資料過多，已安全截斷)</b>"

    # 確保字串中沒有會破壞 HTML 解析的未閉合角括號 (將可能出錯的符號轉義)
    report = report.replace("<3", "&lt;3").replace(" > ", " &gt; ")

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
