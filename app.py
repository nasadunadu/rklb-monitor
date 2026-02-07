import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import datetime
from deep_translator import GoogleTranslator

# --- 1. 页面设置 ---
st.set_page_config(page_title="RKLB 智能情报终端 - 翻译版", layout="wide")

# --- 2. 翻译引擎 (调用 Google 翻译) ---
def translate_text(text):
    try:
        # 自动识别源语言并翻译成中文
        return GoogleTranslator(source='auto', target='zh-CN').translate(text)
    except:
        return "翻译暂时离线 (请检查网络)"

# --- 3. 增强型数据抓取 ---
def get_intel_data():
    # 股价与基本面
    tk = yf.Ticker("RKLB")
    hist = tk.history(period="1mo")
    info = tk.info
    
    # 新闻抓取 (Finviz)
    headers = {'User-Agent': 'Mozilla/5.0'}
    news_list = []
    try:
        url = 'https://finviz.com/quote.ashx?t=RKLB'
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        news_table = soup.find(id='news-table')
        if news_table:
            # 抓取前 10 条，并逐一翻译
            for row in news_table.findAll('tr')[:10]:
                cols = row.findAll('td')
                link_tag = cols[1].find('a')
                raw_link = link_tag['href']
                actual_link = raw_link if raw_link.startswith('http') else f"https://finviz.com/{raw_link}"
                
                eng_title = link_tag.text
                news_list.append({
                    "eng": eng_title,
                    "link": actual_link,
                    "time": cols[0].text.strip()
                })
    except: pass
    return hist, info, news_list

hist, info, news_items = get_intel_data()

# --- 4. 界面布局 ---
st.title("🚀 RKLB 智能战略终端 (全自动翻译版)")

col_left, col_right = st.columns([1.3, 0.7])

with col_left:
    st.subheader("📈 1个月日K线与趋势分析")
    if not hist.empty:
        # 专业 K 线图
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'],
            low=hist['Low'], close=hist['Close'], name='K线'
        )])
        # 20日均线
        ma20 = hist['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=ma20, name='20日线', line=dict(color='#00FFCC', width=2)))
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=550)
        st.plotly_chart(fig, use_container_width=True)
        
        # 自动诊断
        c1, c2, c3 = st.columns(3)
        last_p = hist['Close'].iloc[-1]
        last_m = ma20.iloc[-1]
        with c1: st.metric("当前价", f"${last_p:.2f}")
        with c2: 
            if last_p > last_m: st.success("趋势: 多头阶段")
            else: st.warning("趋势: 压力阶段")
        with c3:
            st.info(f"市值: ${info.get('marketCap', 0)/1e9:.2f}B")
    else:
        st.error("数据源异常")

with col_right:
    st.subheader("📰 实时全球情报 (已翻译)")
    if news_items:
        for n in news_items:
            with st.container():
                # 顶部显示中文翻译 (醒目)
                translated_title = translate_text(n['eng'])
                st.markdown(f"🏮 **{translated_title}**")
                
                # 底部折叠/小字显示英文原意
                with st.expander("查看英文原标题"):
                    st.caption(n['eng'])
                
                st.caption(f"🕒 {n['time']} | [阅读原文]({n['link']})")
                st.divider()
    else:
        st.info("正在搜索全球卫星信号...")

st.caption(f"全自动翻译系统运行中 | {datetime.datetime.now().strftime('%H:%M:%S')}")