import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time

# ==========================================
# 1. 配置與設定 (維持原樣)
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_stock_config():
    # ... (此處保留你原始的 400 檔標的清單，為節省篇幅以下略過) ...
    # 請將你原本的 get_stock_config 代碼貼回此處
    pass

# ==========================================
# 2. 進階分析邏輯 (新增精確公式與目標價)
# ==========================================
def analyze_stock_deep(ticker, market_type, cat_type):
    try:
        stock = yf.Ticker(ticker)
        # 抓取 6 個月資料以計算波動率與 MA
        df = stock.history(period="6mo")
        if df.empty or len(df) < 30: return None
        
        info = stock.info
        curr_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        chg_pct = ((curr_price - prev_price) / prev_price) * 100
        m_cap = info.get('marketCap', 0)

        # --- 濾網 (維持原樣) ---
        if market_type == '美股' and (m_cap < 1e9 or curr_price < 5): return None
        if market_type == '台股' and (m_cap < 5e9 or curr_price < 15): return None

        # --- 技術指標計算 ---
        # 1. RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain.iloc[-1] / loss.iloc[-1])))
        
        # 2. 趨勢 (MA20) 與 波動率 (Volatility)
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        v_ratio = df['Volume'].iloc[-1] / df['Volume'].rolling(window=20).mean().iloc[-1]
        daily_return = df['Close'].pct_change().dropna()
        volatility_7d = daily_return.std() * np.sqrt(5) # 一週(5交易日)的標準差幅度

        # --- 精確評分公式 (滿分 100) ---
        # A. 趨勢分 (30%): 股價高於 MA20 且 MA20 向上
        trend_score = 30 if curr_price > ma20 else 10
        # B. 價值分 (30%): P/E 與 P/B 低於產業平均 (簡化判定)
        pe = info.get('trailingPE', 30)
        value_score = max(0, 30 - (pe / 2)) 
        # C. 動能分 (40%): RSI 位於 40-60 強勢區 + 成交量爆發
        momentum_score = (40 if 40 < rsi < 70 else 10) + (10 if v_ratio > 1.5 else 0)
        
        total_score = trend_score + value_score + momentum_score

        # --- 一週目標價計算 (基於波動率與評分方向) ---
        # 如果分數高，看漲至 1-SD 上限；分數低，看跌至 1-SD 下限
        direction = 1 if total_score > 55 else -1
        target_price = curr_price * (1 + (volatility_7d * direction))

        # --- 判斷指標 ---
        status = "🔥強勢" if total_score > 75 else "轉強" if total_score > 60 else "觀望"
        if rsi > 75: status = "⚠️超買"
        elif rsi < 30: status = "❄️超跌"

        return {
            'Ticker': ticker,
            'Name': info.get('shortName', ticker),
            'Price': round(curr_price, 2),
            'Chg%': round(chg_pct, 2),
            'Target': round(target_price, 2),
            'Score': round(total_score, 1),
            'RSI': round(rsi, 1),
            'Status': status,
            'Market': market_type,
            'Category': cat_type
        }
    except Exception as e:
        return None

# ==========================================
# 3. 執行執行與報表生成
# ==========================================
if __name__ == "__main__":
    configs = get_stock_config()
    all_results = []
    
    # 這裡建議加上簡單的進度顯示，因為 400 檔會跑很久
    for s_list, m_type, c_type in configs:
        print(f"Scanning {m_type} {c_type}...")
        for t in s_list:
            res = analyze_stock_deep(t, m_type, c_type)
            if res: all_results.append(res)
            time.sleep(0.5) # 稍微加快一點速度

    df_all = pd.DataFrame(all_results)
    
    # 生成 Telegram 訊息
    report = f"🎯 <b>【量化雷達 4.0：高精確分析版】</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += "格式：代碼 | 現價(漲跌) | 🎯目標 | 分數\n"
    report += "-----------------------------------\n"

    for m in ['台股', '美股']:
        df_m = df_all[df_all['Market'] == m].sort_values('Score', ascending=False)
        report += f"\n👑 <b>{m} 強勢榜 Top 8</b>\n"
        for _, r in df_m.head(8).iterrows():
            report += f"🔹 <code>{r['Ticker']}</code>: {r['Price']}({r['Chg%']}%) 🎯{r['Target']} <b>[{r['Score']}]</b>\n"
            report += f"   ➔ 指標: {r['Status']} | RSI: {r['RSI']}\n"

    # Telegram 發送
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": report, "parse_mode": "HTML"})
