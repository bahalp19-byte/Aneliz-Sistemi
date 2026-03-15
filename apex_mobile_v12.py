"""
╔══════════════════════════════════════════════════════════════════════╗
║  APEX PRO v12.0 — MOBILE-FIRST SUPREME ICT/SMC TRADING TERMINAL     ║
║  Kripto · Forex · US Hisse · BIST  ·  Telefon + Tablet + Masaüstü  ║
╠══════════════════════════════════════════════════════════════════════╣
║  ZAMAN DİLİMLERİ: 1m · 3m · 5m · 10m · 15m · 30m · 1s · 4s · 1g  ║
╠══════════════════════════════════════════════════════════════════════╣
║  v12.0 YENİLİKLER:                                                  ║
║  • Mobile-First CSS — 44px dokunma hedefi, swipe tab, alt nav bar   ║
║  • Responsive grid — 1-2-3-4 kolon otomatik adaptasyon             ║
║  • PWA benzeri alt navigasyon çubuğu (telefon için)                  ║
║  • Ticker şeridi, hızlı kart grid, yatay scroll container           ║
║  • Tüm v11.0 özellikleri korundu (hiçbir şey silinmedi)             ║
╠══════════════════════════════════════════════════════════════════════╣
║  KURULUM:                                                            ║
║  pip install streamlit pandas numpy requests plotly yfinance         ║
║  streamlit run apex_mobile_v12.py                                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import json
import threading
import hashlib
import base64
import io
import csv
import re
import warnings
import concurrent.futures
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any

# yfinance — birincil veri kaynağı (pip install yfinance)
try:
    import yfinance as yf
    _YF_OK = True
except ImportError:
    _YF_OK = False

warnings.filterwarnings("ignore")

from plotly.subplots import make_subplots
import plotly.graph_objects as go

st.set_page_config(
    page_title="APEX PRO v12.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",   # Telefonda sidebar kapalı başlar
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "APEX PRO v12.0 — ICT/SMC Trading Terminal"
    }
)

# ═══════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════
class CFG:
    FH_KEY = "d6lae89r01qr0gn6fqk0d6lae89r01qr0gn6fqkg"
    HF_KEY = "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"
    BIN    = "https://api.binance.com/api/v3"
    FH     = "https://finnhub.io/api/v1"
    HF_EP  = "https://router.huggingface.co/v1/chat/completions"
    TO     = 14
    SW     = 5  # swing window

    # Apısız Yahoo Finance endpoints
    YF1  = "https://query1.finance.yahoo.com/v8/finance/chart"
    YF2  = "https://query2.finance.yahoo.com/v8/finance/chart"
    YF_UA = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    ]
    # Yahoo Finance TF → (interval, range)
    TF_YF = {
        "1m":("1m","7d"),"5m":("5m","60d"),"15m":("15m","60d"),
        "30m":("30m","60d"),"1h":("60m","730d"),"4h":("60m","730d"),
        "1d":("1d","10y"),"1w":("1wk","max"),
    }
    # FOREX: isim → Yahoo Finance sembol (apısız)
    FOREX = {
        "EUR/USD":"EURUSD=X",  "GBP/USD":"GBPUSD=X",
        "USD/JPY":"JPY=X",     "USD/CHF":"CHF=X",
        "AUD/USD":"AUDUSD=X",  "NZD/USD":"NZDUSD=X",
        "USD/CAD":"CAD=X",     "EUR/JPY":"EURJPY=X",
        "GBP/JPY":"GBPJPY=X",  "XAU/USD":"GC=F",
        "XAG/USD":"SI=F",      "EUR/GBP":"EURGBP=X",
        "USD/TRY":"TRY=X",     "EUR/TRY":"EURTRY=X",
        "GBP/CHF":"GBPCHF=X",  "AUD/JPY":"AUDJPY=X",
        "WTI/USD":"CL=F",      "USD/MXN":"MXN=X",
        "USD/ZAR":"ZAR=X",     "USD/SEK":"SEK=X",
    }
    # Finnhub yedek (sadece bilinen çiftler)
    FOREX_FH = {
        "EUR/USD":"OANDA:EUR_USD","GBP/USD":"OANDA:GBP_USD",
        "USD/JPY":"OANDA:USD_JPY","USD/CHF":"OANDA:USD_CHF",
        "AUD/USD":"OANDA:AUD_USD","NZD/USD":"OANDA:NZD_USD",
        "USD/CAD":"OANDA:USD_CAD","EUR/JPY":"OANDA:EUR_JPY",
        "GBP/JPY":"OANDA:GBP_JPY","XAU/USD":"OANDA:XAU_USD",
    }
    PIP = {
        "EUR/USD":.0001,"GBP/USD":.0001,"AUD/USD":.0001,"NZD/USD":.0001,
        "USD/CAD":.0001,"USD/CHF":.0001,"EUR/JPY":.01,"GBP/JPY":.01,
        "USD/JPY":.01,"XAU/USD":.1,
    }
    US_STOCKS = [
        "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","JPM","V","UNH",
        "XOM","JNJ","WMT","MA","PG","AVGO","HD","CVX","MRK","LLY",
        "ABBV","PEP","KO","COST","ADBE","CRM","NFLX","AMD","INTC","CSCO",
        "SPY","QQQ","IWM","GLD","TLT","DIA","VZ","T","NEE","BA",
    ]
    BIST = [
        "THYAO","BIMAS","AKBNK","GARAN","ISCTR","KCHOL","EREGL","PETKM",
        "SISE","TUPRS","TCELL","ARCLK","PGSUS","SAHOL","KOZAL","FROTO",
        "TOASO","ASELS","HALKB","VAKBN","YKBNK","EKGYO","TTKOM","MGROS",
        "BRISA","ULKER","ENKAI","AGHOL","DOHOL","TAVHL","SODA","VESTL",
        "CCOLA","HEKTS","KARSN","KONYA","OTKAR","TKFEN","TSKB","NTHOL",
    ]
    # ── Zaman Dilimleri — Binance API karşılıkları ──────────
    TF_BIN = {
        "1m":"1m", "3m":"3m", "5m":"5m", "10m":"15m",  # 10m → 15m yaklaşım
        "15m":"15m", "30m":"30m",
        "1s":"1h", "4s":"4h", "1g":"1d",               # Türkçe kısaltmalar
        "1h":"1h", "4h":"4h", "1d":"1d",               # İngilizce standart
    }
    # ── Kullanıcı arayüzü zaman dilimi seçenekleri ──────────
    TF_LABELS = ["1m","3m","5m","10m","15m","30m","1s","4s","1g"]  # Türkçe görünüm
    TF_DISPLAY = {
        "1m":"1 Dakika","3m":"3 Dakika","5m":"5 Dakika",
        "10m":"10 Dakika","15m":"15 Dakika","30m":"30 Dakika",
        "1s":"1 Saat","4s":"4 Saat","1g":"1 Gün",
        # eski format uyumu
        "1h":"1 Saat","4h":"4 Saat","1d":"1 Gün",
    }
    # Türkçe label → Binance interval
    TF_TO_BIN = {
        "1m":"1m","3m":"3m","5m":"5m","10m":"15m",
        "15m":"15m","30m":"30m","1s":"1h","4s":"4h","1g":"1d",
    }
    # Türkçe label → yfinance interval
    TF_TO_YF = {
        "1m":"1m","3m":"5m","5m":"5m","10m":"15m",
        "15m":"15m","30m":"30m","1s":"60m","4s":"60m","1g":"1d",
    }
    # Türkçe label → 4h resample gerekli mi?
    TF_RESAMPLE_4H = {"4s"}
    # HTF zinciri
    TF_FH  = {"5m":"5","15m":"15","1h":"60","4h":"240","1d":"D"}
    TF_STK = {"5m":"5m","10m":"15m","15m":"15m","30m":"30m","1s":"1h","4s":"1h","1g":"1d"}
    TF_STK_FH = {"5m":"5","15m":"15","1s":"60","4s":"240","1g":"D"}
    HTF_MAP = {
        "1m":"15m","3m":"15m","5m":"1s","10m":"1s",
        "15m":"4s","30m":"4s","1s":"1g","4s":"1g","1g":"1g",
        # Binance intervallar
        "1h":"1d","4h":"1d","1d":"1d",
        "5":"60","15":"240","60":"D","240":"D","D":"D",
    }
    KZ = {
        "Asya":    ("00:00","03:00","rgba(80,100,220,0.09)"),
        "Londra":  ("07:00","10:00","rgba(255,165,0,0.10)"),
        "NY":      ("13:00","16:00","rgba(220,50,50,0.09)"),
        "NY Gece": ("22:00","23:59","rgba(168,85,247,0.07)"),
    }
    SESSIONS = {"Asya":(0,3),"Londra":(7,10),"NY":(13,17),"All":(0,24)}
    # Tarama kriterleri
    SCAN_MIN_SCORE = 50
    SCAN_MIN_RR    = 1.5
    SCAN_MAX_RSI_L = 68
    SCAN_MIN_RSI_S = 32
    SCAN_MIN_ADX   = 15
    AI_MODELS = [
        ("meta-llama/Llama-3.3-70B-Instruct","🔥 Llama 3.3 70B"),
        ("Qwen/Qwen2.5-72B-Instruct","🧠 Qwen 2.5 72B"),
        ("deepseek-ai/DeepSeek-V3","🔮 DeepSeek V3"),
        ("meta-llama/Meta-Llama-3.1-8B-Instruct","⚡ Llama 3.1 8B"),
    ]
    AI_PROV = ["sambanova","novita","together","fireworks-ai","nebius",""]

# ═══════════════════════════════════════════════════
#  CSS — DARK TERMINAL STYLE
# ═══════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Bebas+Neue&family=Rajdhani:wght@400;500;600;700&display=swap');

/* ════════════════════════════════════════════
   DESIGN TOKENS
════════════════════════════════════════════ */
:root{
  --bg:#020609;--bg2:#040b12;--card:#060d18;--card2:#081220;
  --b1:rgba(0,212,255,.10);--b2:rgba(0,212,255,.20);--b3:rgba(0,212,255,.35);
  --c1:#00d4ff;--c2:#00ff88;--c3:#ff3355;--c4:#a855f7;--c5:#ffd600;--c6:#ff6b35;
  --tx:#c8d8f0;--tx2:#8a9dc0;--tx3:#3d5a80;
  --glow1:rgba(0,212,255,.15);--glow2:rgba(0,255,136,.12);--glow3:rgba(255,51,85,.12);
  --radius:10px;--radius-sm:6px;
  --touch-min:44px;   /* iOS/Android minimum dokunma hedefi */
  --font-base:13px;   /* mobilde okunabilir temel font */
  --font-sm:11px;
  --font-xs:10px;
  --font-label:9px;
}

/* ════════════════════════════════════════════
   GLOBAL RESET & BASE
════════════════════════════════════════════ */
*{-webkit-tap-highlight-color:transparent;box-sizing:border-box;}
html,body,[class*="css"]{
  background-color:var(--bg)!important;
  color:var(--tx)!important;
  font-family:'JetBrains Mono',monospace!important;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}
.stApp{background:var(--bg)!important;}
.main .block-container{
  padding:0.4rem 0.6rem!important;
  max-width:100%!important;
  padding-bottom:80px!important;   /* alt nav için boşluk */
}

/* ════════════════════════════════════════════
   SCROLLBAR
════════════════════════════════════════════ */
::-webkit-scrollbar{width:2px;height:2px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:#1a2840;border-radius:2px;}

/* ════════════════════════════════════════════
   SIDEBAR — MOBİL UYUMLU
════════════════════════════════════════════ */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#010610 0%,#030a14 100%)!important;
  border-right:1px solid var(--b1)!important;
  box-shadow:6px 0 24px rgba(0,0,0,.6)!important;
}
section[data-testid="stSidebar"] *{color:var(--tx)!important;}
section[data-testid="stSidebar"] .stSelectbox>div>div,
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input{
  background:rgba(4,10,20,.9)!important;
  border:1px solid var(--b1)!important;
  color:var(--tx)!important;
  border-radius:var(--radius-sm)!important;
  font-size:var(--font-base)!important;
  min-height:var(--touch-min)!important;
}
/* Sidebar toggle button büyütme (mobilde kolay tıklanabilir) */
button[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"]{
  min-width:var(--touch-min)!important;
  min-height:var(--touch-min)!important;
}

/* ════════════════════════════════════════════
   METRİKLER
════════════════════════════════════════════ */
div[data-testid="metric-container"]{
  background:linear-gradient(135deg,var(--card),var(--card2))!important;
  border:1px solid var(--b1)!important;
  border-radius:var(--radius-sm)!important;
  padding:8px 10px!important;
  transition:.2s!important;
  box-shadow:0 2px 8px rgba(0,0,0,.3)!important;
  min-height:60px!important;
}
div[data-testid="metric-container"]:hover{
  border-color:var(--b2)!important;
  box-shadow:0 0 12px var(--glow1)!important;
}
div[data-testid="metric-container"] label{
  color:var(--tx3)!important;
  font-size:var(--font-label)!important;
  letter-spacing:1px!important;
  text-transform:uppercase!important;
}
div[data-testid="stMetricValue"]{
  color:var(--c1)!important;
  font-size:14px!important;
  font-weight:700!important;
}
div[data-testid="stMetricDelta"]{font-size:var(--font-xs)!important;}

/* ════════════════════════════════════════════
   TABS — YATAY KAYDIRMA (MOBİL)
════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"]{
  background:linear-gradient(90deg,#010610,#030a14)!important;
  border-bottom:1px solid var(--b1)!important;
  gap:0!important;
  padding:0 2px!important;
  overflow-x:auto!important;
  overflow-y:hidden!important;
  white-space:nowrap!important;
  scrollbar-width:none!important;
  -webkit-overflow-scrolling:touch!important;
  flex-wrap:nowrap!important;
}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar{display:none;}
.stTabs [data-baseweb="tab"]{
  color:var(--tx3)!important;
  font-size:var(--font-xs)!important;
  font-weight:700!important;
  letter-spacing:.5px!important;
  padding:10px 10px!important;
  background:transparent!important;
  border-radius:0!important;
  transition:.2s!important;
  border-bottom:2px solid transparent!important;
  white-space:nowrap!important;
  min-width:fit-content!important;
  min-height:var(--touch-min)!important;
  flex-shrink:0!important;
}
.stTabs [data-baseweb="tab"]:hover{color:var(--c1)!important;}
.stTabs [aria-selected="true"]{
  color:var(--c1)!important;
  border-bottom:2px solid var(--c1)!important;
  background:rgba(0,212,255,.05)!important;
}

/* ════════════════════════════════════════════
   BUTONLAR — DOKUNMA UYUMLU
════════════════════════════════════════════ */
.stButton>button{
  background:rgba(0,212,255,.06)!important;
  border:1px solid rgba(0,212,255,.28)!important;
  color:var(--c1)!important;
  font-family:'JetBrains Mono',monospace!important;
  font-weight:700!important;
  font-size:var(--font-sm)!important;
  border-radius:var(--radius-sm)!important;
  transition:.2s!important;
  letter-spacing:.3px!important;
  min-height:var(--touch-min)!important;
  padding:8px 12px!important;
  width:100%!important;
}
.stButton>button:hover{
  background:rgba(0,212,255,.14)!important;
  box-shadow:0 0 14px rgba(0,212,255,.18)!important;
  border-color:rgba(0,212,255,.55)!important;
}
.stButton>button:active{
  transform:scale(0.97)!important;
  background:rgba(0,212,255,.20)!important;
}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,rgba(0,212,255,.20),rgba(0,255,136,.12))!important;
  border-color:rgba(0,212,255,.50)!important;
  box-shadow:0 2px 12px rgba(0,212,255,.14)!important;
}

/* ════════════════════════════════════════════
   INPUT ALANLARI — DOKUNMA UYUMLU
════════════════════════════════════════════ */
.stTextInput input,.stNumberInput input,.stTextArea textarea{
  background:var(--card)!important;
  border:1.5px solid var(--b1)!important;
  color:var(--tx)!important;
  border-radius:var(--radius-sm)!important;
  font-size:var(--font-base)!important;
  min-height:var(--touch-min)!important;
  padding:10px 12px!important;
}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{
  border-color:var(--b3)!important;
  box-shadow:0 0 8px var(--glow1)!important;
  outline:none!important;
}
.stSelectbox>div>div{
  background:var(--card)!important;
  border:1px solid var(--b1)!important;
  color:var(--tx)!important;
  border-radius:var(--radius-sm)!important;
  min-height:var(--touch-min)!important;
}
.stMultiSelect>div>div{background:var(--card)!important;border:1px solid var(--b1)!important;}
.stSlider>div>div>div{background:var(--b1)!important;}
/* Slider thumb büyütme */
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"]{font-size:var(--font-xs)!important;}
.stCheckbox>label{min-height:var(--touch-min)!important;align-items:center!important;}
.stCheckbox>label>div{background:var(--card)!important;border:1px solid var(--b1)!important;}
.stRadio>div{gap:4px!important;}
.stRadio label{min-height:var(--touch-min)!important;align-items:center!important;}

/* ════════════════════════════════════════════
   KOMPONENTler
════════════════════════════════════════════ */
.card{
  background:linear-gradient(135deg,var(--card),var(--card2));
  border:1px solid var(--b1);border-radius:var(--radius);
  padding:10px 12px;margin-bottom:6px;transition:.2s;
}
.card:hover{border-color:var(--b2);box-shadow:0 4px 16px rgba(0,0,0,.3);}
.rw{
  display:flex;justify-content:space-between;align-items:center;
  background:var(--card);border:1px solid #0a1828;
  border-radius:var(--radius-sm);
  padding:8px 10px;margin-bottom:3px;transition:.15s;
  min-height:36px;
}
.rw:hover,.rw:active{background:var(--card2);border-color:var(--b1);}

/* PILLS */
.pill{
  display:inline-flex;align-items:center;
  border-radius:12px;padding:3px 9px;
  font-size:var(--font-xs);font-weight:700;letter-spacing:.4px;
}
.pg{background:rgba(0,255,136,.09);border:1px solid rgba(0,255,136,.28);color:#00ff88;}
.pb{background:rgba(0,212,255,.09);border:1px solid rgba(0,212,255,.28);color:#00d4ff;}
.pr{background:rgba(255,51,85,.09);border:1px solid rgba(255,51,85,.28);color:#ff3355;}
.pp{background:rgba(168,85,247,.09);border:1px solid rgba(168,85,247,.28);color:#a855f7;}
.py{background:rgba(255,214,0,.09);border:1px solid rgba(255,214,0,.28);color:#ffd600;}
.po{background:rgba(255,107,53,.09);border:1px solid rgba(255,107,53,.28);color:#ff6b35;}

/* LOGO */
.apex-logo{
  font-family:'Bebas Neue',cursive;
  letter-spacing:.16em;
  background:linear-gradient(90deg,#00d4ff,#00ff88,#a855f7);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;line-height:1;
}

/* SECTION HEADER */
.sec{
  font-size:var(--font-label);font-weight:700;letter-spacing:2px;
  color:var(--tx3);text-transform:uppercase;
  margin:10px 0 4px;border-bottom:1px solid #0a1828;padding-bottom:2px;
}

/* MEO PANEL */
.meo-panel{background:var(--card);border:1px solid var(--b1);border-radius:var(--radius);overflow:hidden;margin-bottom:6px;box-shadow:0 2px 12px rgba(0,0,0,.25);}
.meo-hdr{background:linear-gradient(90deg,rgba(0,212,255,.08),transparent);border-bottom:1px solid var(--b1);padding:8px 12px;display:flex;justify-content:space-between;align-items:center;}
.meo-lbl{font-family:'Rajdhani',sans-serif;font-weight:700;font-size:var(--font-sm);letter-spacing:1.2px;color:var(--tx3);text-transform:uppercase;}
.meo-body{padding:6px 10px;}
.meo-row{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(10,24,40,.9);padding:6px 0;transition:.1s;min-height:32px;}
.meo-row:hover,.meo-row:active{background:rgba(0,212,255,.03);}

/* TABLOLAR */
.ind-tbl{width:100%;border-collapse:collapse;}
.ind-tbl th{background:rgba(0,212,255,.06);color:var(--tx3);font-size:var(--font-xs);letter-spacing:.6px;padding:6px 8px;text-align:center;border-bottom:1px solid var(--b1);}
.ind-tbl td{padding:5px 8px;text-align:center;border-bottom:1px solid rgba(10,20,35,.8);font-size:var(--font-sm);}
.ind-buy{color:#00ff88;font-weight:700;}.ind-sell{color:#ff3355;font-weight:700;}.ind-neut{color:#ffd600;}

/* SİNYALLER */
.sig-long{background:linear-gradient(135deg,rgba(0,255,136,.07),rgba(0,255,136,.03));border:2px solid rgba(0,255,136,.35);border-radius:var(--radius);padding:16px;text-align:center;box-shadow:0 0 24px rgba(0,255,136,.12);}
.sig-short{background:linear-gradient(135deg,rgba(255,51,85,.07),rgba(255,51,85,.03));border:2px solid rgba(255,51,85,.35);border-radius:var(--radius);padding:16px;text-align:center;box-shadow:0 0 24px rgba(255,51,85,.12);}
.sig-wait{background:rgba(255,214,0,.04);border:2px solid rgba(255,214,0,.22);border-radius:var(--radius);padding:14px;text-align:center;}
.bp-badge{background:rgba(0,255,136,.12);border:1.5px solid #00ff88;border-radius:5px;padding:4px 12px;font-size:var(--font-sm);font-weight:700;color:#00ff88;}
.sp-badge{background:rgba(255,51,85,.12);border:1.5px solid #ff3355;border-radius:5px;padding:4px 12px;font-size:var(--font-sm);font-weight:700;color:#ff3355;}

/* UYARILAR */
.warn-g{background:rgba(0,255,136,.04);border-left:3px solid #00ff88;padding:4px 8px;margin-bottom:3px;font-size:var(--font-sm);color:#00ff88;border-radius:0 4px 4px 0;}
.warn-r{background:rgba(255,51,85,.04);border-left:3px solid #ff3355;padding:4px 8px;margin-bottom:3px;font-size:var(--font-sm);color:#ff3355;border-radius:0 4px 4px 0;}
.warn-y{background:rgba(255,214,0,.04);border-left:3px solid #ffd600;padding:4px 8px;margin-bottom:3px;font-size:var(--font-sm);color:#ffd600;border-radius:0 4px 4px 0;}

/* İŞLEM SATIRLARI */
.trow-w{background:rgba(0,255,136,.04);border-left:3px solid #00ff88;padding:5px 10px;margin-bottom:3px;font-size:var(--font-sm);color:var(--tx);border-radius:0 4px 4px 0;}
.trow-l{background:rgba(255,51,85,.04);border-left:3px solid #ff3355;padding:5px 10px;margin-bottom:3px;font-size:var(--font-sm);color:var(--tx);border-radius:0 4px 4px 0;}

/* SOHBET */
.ubub{background:linear-gradient(135deg,#140c38,#221550);border:1px solid rgba(168,85,247,.35);border-radius:14px 14px 4px 14px;padding:10px 14px;margin:4px 0;font-size:.88rem;color:#e2d5fd;line-height:1.65;}
.abub{background:var(--card);border:1px solid var(--b1);border-top:2px solid rgba(0,212,255,.28);border-radius:14px 14px 14px 4px;padding:10px 14px;margin:4px 0;font-size:.86rem;line-height:1.8;}

/* İSTATİSTİK TABLOSU */
.stat-tbl{width:100%;border-collapse:collapse;}
.stat-tbl th{background:rgba(0,212,255,.06);color:var(--tx3);font-size:var(--font-xs);letter-spacing:.6px;padding:5px 7px;text-align:center;border-bottom:1px solid var(--b1);}
.stat-tbl td{padding:4px 7px;text-align:center;border-bottom:1px solid rgba(10,20,35,.8);font-size:var(--font-sm);}
.shdr-l{background:rgba(0,255,136,.09);color:#00ff88;font-weight:700;font-size:var(--font-sm);padding:5px 8px;border-radius:4px 4px 0 0;}
.shdr-s{background:rgba(255,51,85,.09);color:#ff3355;font-weight:700;font-size:var(--font-sm);padding:5px 8px;border-radius:4px 4px 0 0;}
.wr100{color:#00ff88;font-weight:700;}.wr80{color:#68d48a;font-weight:700;}.wr60{color:#ffd600;font-weight:700;}.wrbad{color:#ff3355;font-weight:700;}

/* STRATEJİ KUTULARI */
.strat-box{border-radius:var(--radius);padding:14px;margin-bottom:6px;}
.strat-l{background:rgba(0,255,136,.06);border:1.5px solid rgba(0,255,136,.28);}
.strat-s{background:rgba(255,51,85,.06);border:1.5px solid rgba(255,51,85,.28);}
.strat-n{background:rgba(255,214,0,.04);border:1.5px solid rgba(255,214,0,.20);}

/* MISC */
hr{border:none;border-top:1px solid var(--b1)!important;margin:6px 0!important;}
#MainMenu,footer,header,.stDeployButton{visibility:hidden;display:none;}

/* ANİMASYONLAR */
@keyframes glow-pulse{0%,100%{box-shadow:0 0 15px rgba(0,212,255,.10);}50%{box-shadow:0 0 30px rgba(0,212,255,.22);}}
.apex-header{animation:glow-pulse 4s ease-in-out infinite;}
@keyframes ticker-flash{0%{opacity:1;}50%{opacity:.6;}100%{opacity:1;}}
.price-live{animation:ticker-flash 1.5s ease-in-out infinite;}
@keyframes slideInUp{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
.slide-in{animation:slideInUp .25s ease-out;}

/* SCAN SATIRI */
.scan-row{transition:.15s!important;}
.scan-row:hover,.scan-row:active{transform:translateX(2px)!important;border-left-width:4px!important;}

/* HABER KARTI */
.news-card{transition:.2s;cursor:pointer;}
.news-card:hover,.news-card:active{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.4)!important;}

/* ════════════════════════════════════════════
   MOBİL — ALT NAVİGASYON ÇUBUĞU
════════════════════════════════════════════ */
.mobile-nav{
  position:fixed;bottom:0;left:0;right:0;z-index:9999;
  background:linear-gradient(180deg,rgba(2,6,9,.0),rgba(2,6,9,.98) 20%);
  border-top:1px solid var(--b1);
  padding:8px 4px 12px;
  display:flex;justify-content:space-around;align-items:center;
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
}
.mobile-nav-btn{
  display:flex;flex-direction:column;align-items:center;gap:3px;
  color:var(--tx3);font-size:8px;font-weight:700;letter-spacing:.5px;
  padding:4px 8px;border-radius:8px;transition:.2s;cursor:pointer;
  min-width:52px;text-transform:uppercase;
  -webkit-tap-highlight-color:transparent;
}
.mobile-nav-btn.active{color:var(--c1);}
.mobile-nav-btn .nav-icon{font-size:18px;line-height:1;}

/* ════════════════════════════════════════════
   MOBİL — HIZLI ERİŞİM KARTLARI
════════════════════════════════════════════ */
.quick-card{
  background:linear-gradient(135deg,var(--card),var(--card2));
  border:1px solid var(--b1);border-radius:var(--radius);
  padding:12px;text-align:center;transition:.2s;cursor:pointer;
}
.quick-card:hover,.quick-card:active{
  border-color:var(--c1);
  box-shadow:0 0 16px var(--glow1);
  transform:scale(0.98);
}
.quick-card .qc-icon{font-size:22px;margin-bottom:4px;}
.quick-card .qc-label{font-size:var(--font-xs);color:var(--tx3);font-weight:700;letter-spacing:.5px;}
.quick-card .qc-value{font-size:var(--font-sm);color:var(--c1);font-weight:700;}

/* ════════════════════════════════════════════
   MOBİL — FİYAT TICKER ŞERİDİ
════════════════════════════════════════════ */
.ticker-strip{
  background:linear-gradient(90deg,var(--bg),#020812);
  border:1px solid var(--b1);border-radius:var(--radius-sm);
  padding:6px 10px;margin-bottom:6px;
  overflow:hidden;white-space:nowrap;
  font-size:var(--font-xs);
}
@keyframes ticker-scroll{
  0%{transform:translateX(0);}
  100%{transform:translateX(-50%);}
}
.ticker-inner{
  display:inline-block;
  animation:ticker-scroll 30s linear infinite;
}
.ticker-inner:hover{animation-play-state:paused;}

/* ════════════════════════════════════════════
   MOBİL — KART GRID SİSTEMİ
════════════════════════════════════════════ */
.mobile-grid-2{
  display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px;
}
.mobile-grid-3{
  display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:6px;
}
.mobile-grid-4{
  display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:4px;margin-bottom:6px;
}

/* ════════════════════════════════════════════
   MOBİL — SWIPE SCROLL YATAY CONTAINER
════════════════════════════════════════════ */
.h-scroll{
  display:flex;gap:8px;
  overflow-x:auto;padding-bottom:6px;
  -webkit-overflow-scrolling:touch;
  scrollbar-width:none;
}
.h-scroll::-webkit-scrollbar{display:none;}

/* ════════════════════════════════════════════
   EKRAN BOYUTU ADAPTASYONU
   (Streamlit içinde CSS @media tam çalışır)
════════════════════════════════════════════ */

/* ── Tablet ve üzeri ──────────────────────── */
@media (min-width:768px){
  :root{
    --font-base:12px;
    --font-sm:10px;
    --font-xs:9px;
    --font-label:7.5px;
  }
  .main .block-container{padding:0.5rem 1rem!important;padding-bottom:20px!important;}
  .mobile-nav{display:none!important;}  /* tablet+ sidebar var */
  .stButton>button{min-height:36px!important;}
  .stTextInput input,.stNumberInput input{min-height:36px!important;}
}

/* ── Geniş masaüstü ──────────────────────── */
@media (min-width:1200px){
  :root{
    --font-base:11px;
    --font-sm:9.5px;
    --font-xs:8.5px;
    --font-label:6.5px;
  }
  .main .block-container{padding:0.4rem 1.2rem!important;}
}

/* ── Çok küçük ekran (eski telefonlar) ────── */
@media (max-width:360px){
  :root{--font-base:14px;--font-sm:12px;--font-xs:11px;}
  .stTabs [data-baseweb="tab"]{padding:10px 8px!important;font-size:9px!important;}
}

/* ════════════════════════════════════════════
   STREAMLIT ÖZEL DÜZELTMELER
════════════════════════════════════════════ */
/* Columns arası boşluk azalt */
[data-testid="column"]{padding:0 3px!important;}
/* Expander header dokunma hedefi */
.streamlit-expanderHeader{min-height:var(--touch-min)!important;}
/* Number input artı/eksi butonları */
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"]{
  min-width:36px!important;min-height:36px!important;
}
/* Form submit button */
button[kind="formSubmit"]{
  min-height:var(--touch-min)!important;
  font-size:var(--font-base)!important;
}
/* Markdown içeriği */
.stMarkdown p,.stMarkdown li{font-size:var(--font-sm)!important;line-height:1.6!important;}
/* Spinner */
.stSpinner{color:var(--c1)!important;}
/* Toast / alert */
.stAlert{border-radius:var(--radius)!important;font-size:var(--font-sm)!important;}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
#  CACHE + STATE + UTILS
# ═══════════════════════════════════════════════════
_CACHE: Dict[str, Any] = {}
_LOCK = threading.Lock()

def _ck(*a) -> str:
    return hashlib.md5(json.dumps(a, default=str, sort_keys=True).encode()).hexdigest()

def cget(k, ttl=60):
    with _LOCK:
        e = _CACHE.get(k)
        if e and time.time() - e["t"] < ttl:
            e["h"] = e.get("h", 0) + 1
            return e["d"]
    return None

def cset(k, d, ttl=60):
    with _LOCK:
        if len(_CACHE) > 700:
            old = sorted(_CACHE.items(), key=lambda x: x[1]["t"])[:60]
            for ok, _ in old: _CACHE.pop(ok, None)
        _CACHE[k] = {"d": d, "t": time.time(), "ttl": ttl, "h": 0}
    return d

def cclear(): 
    with _LOCK: _CACHE.clear()

def cstat():
    with _LOCK:
        n = time.time()
        return {"total": len(_CACHE),
                "alive": sum(1 for v in _CACHE.values() if n - v["t"] < v.get("ttl", 60)),
                "hits":  sum(v.get("h", 0) for v in _CACHE.values())}

def elog(fn, msg):
    el = st.session_state.get("elog", [])
    el.append({"t": datetime.utcnow().strftime("%H:%M:%S"), "fn": fn, "msg": str(msg)[:200]})
    st.session_state["elog"] = el[-80:]

def safe(fn, *a, fb=None, **kw):
    try: return fn(*a, **kw)
    except Exception as e: elog(getattr(fn, "__name__", "?"), str(e)); return fb

def _init():
    for k, v in {
        "bt": None, "bt_done": False, "mc": None, "scan": [], "chat": [], "elog": [],
        "last_sym": None, "ai_model": CFG.AI_MODELS[0][0], "ai_mode": "📈 ICT Trader",
        "ai_key": CFG.HF_KEY, "ai_temp": 0.7, "ai_tokens": 1800, "ai_mem": 8,
        "ai_t": 0.0, "ai_n": 0, "live_ctx": {}, "gchat": [],
    }.items():
        if k not in st.session_state: st.session_state[k] = v

_init()

def reset_if(sym):
    if st.session_state.get("last_sym") != sym:
        st.session_state.update({"bt": None, "bt_done": False, "mc": None, "last_sym": sym})

# ── Render helpers ────────────────────────────────
def fmt(v, d=2):
    if v is None: return "—"
    try:
        f = float(v)
        if np.isnan(f) or np.isinf(f): return "—"
        if abs(f) >= 1e9: return f"{f/1e9:.2f}B"
        if abs(f) >= 1e6: return f"{f/1e6:.2f}M"
        return f"{f:,.{d}f}"
    except: return str(v)

def dec(sym):
    p = CFG.PIP.get(sym, 0.0001)
    return 5 if p <= .0001 else 4 if p <= .001 else 3 if p <= .01 else 2

def pbar(p, c="#00d4ff", h=4):
    p = min(max(float(p) if p else 0, 0), 100)
    return (f'<div style="background:#0d1c2e;border-radius:2px;height:{h}px;">'
            f'<div style="width:{p:.0f}%;background:{c};height:{h}px;border-radius:2px;'
            f'box-shadow:0 0 4px {c}44;"></div></div>')

def kv(l, v, c="#cdd6f4", bl=""):
    st.markdown(
        f'<div class="rw" style="border-left:3px solid {bl or c}44;">'
        f'<span style="color:#3d5a80;font-size:7.5px;">{l}</span>'
        f'<span style="color:{c};font-weight:700;font-size:8.5px;">{v}</span></div>',
        unsafe_allow_html=True)

def dlbtn(data, fn, lbl, mime="text/csv"):
    b64 = base64.b64encode(data.encode()).decode()
    return (f'<a href="data:{mime};base64,{b64}" download="{fn}" style="background:'
            f'rgba(0,212,255,.08);border:1px solid rgba(0,212,255,.35);color:#00d4ff;'
            f'padding:4px 12px;border-radius:4px;font-size:8px;text-decoration:none;'
            f'font-weight:700;">⬇ {lbl}</a>')

def cv(df, col, default=0.0):
    """Safe column value getter"""
    try:
        if col in df.columns and len(df) > 0:
            v = df[col].iloc[-1]
            if pd.notna(v): return float(v)
    except: pass
    return float(default)


# ═══════════════════════════════════════════════════
#  DATA LAYER
# ═══════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_top100():
    try:
        r = requests.get(f"{CFG.BIN}/ticker/24hr", timeout=10)
        if r.ok:
            tickers = sorted(
                [t for t in r.json() if t["symbol"].endswith("USDT")
                 and float(t.get("quoteVolume", 0)) > 5e5],
                key=lambda x: float(x.get("quoteVolume", 0)), reverse=True
            )[:120]
            return {t["symbol"].replace("USDT",""):{"sym":t["symbol"],
                "price":float(t.get("lastPrice",0)),"chg":float(t.get("priceChangePercent",0)),
                "vol":float(t.get("quoteVolume",0)),"hi":float(t.get("highPrice",0)),
                "lo":float(t.get("lowPrice",0))} for t in tickers}
    except Exception as e: elog("get_top100", e)
    return {"BTC":{"sym":"BTCUSDT","price":0,"chg":0,"vol":0,"hi":0,"lo":0}}

# ═══════════════════════════════════════════════════
#  OTOMATIK SEMBOL DÜZENLEYİCİ
# ═══════════════════════════════════════════════════
# ═══════════════════════════════════════════════════
#  OTOMATIK SEMBOL DÜZENLEYİCİ (get_data ön-işlemcisi)
#  Kullanıcı ham giriş yapar → sistem otomatik çevirir
# ═══════════════════════════════════════════════════

# Özel emtia/futures eşlemesi
_COMMODITY_MAP = {
    "GOLD": "GC=F", "SILVER": "SI=F", "OIL": "CL=F", "WTI": "CL=F",
    "BRENT": "BZ=F", "GAS": "NG=F", "WHEAT": "ZW=F", "CORN": "ZC=F",
    "COPPER": "HG=F", "PLATINUM": "PL=F", "PALLADIUM": "PA=F",
    "XAU": "GC=F", "XAG": "SI=F", "XPT": "PL=F",
    "BTC": "BTC-USD", "ETH": "ETH-USD",  # spot (yfinance)
}

def fix_symbol(raw: str, market: str) -> str:
    """
    ╔══════════════════════════════════════════════════════╗
    ║  APEX PRO — OTOMATİK SEMBOL DÜZELTİCİ               ║
    ║  Kullanıcı ne girerse girsin doğru YF sembolü üretir ║
    ╠══════════════════════════════════════════════════════╣
    ║  BIST:  THYAO  → THYAO.IS                           ║
    ║         THYAO.IS → THYAO.IS  (idempotent)           ║
    ║  FOREX: EUR/USD → EURUSD=X                          ║
    ║         EURUSD  → EURUSD=X   (6 char pair)          ║
    ║         XAUUSD  → GC=F       (emtia eşlemesi)       ║
    ║         USD/TRY → TRY=X      (CFG.FOREX lookup)     ║
    ║  CRYPTO: BTCUSDT → BTCUSDT   (değişmez, Binance)    ║
    ║  US:    AAPL    → AAPL       (değişmez)             ║
    ╚══════════════════════════════════════════════════════╝
    """
    s = raw.strip().upper()

    # ── BIST ────────────────────────────────────────────────
    if market == "stock_bist":
        # Nokta varsa koru, yoksa ekle
        if "." in s:
            parts = s.split(".")
            s = parts[0] + ".IS"   # .XU100 gibi yanlış suffix'i da düzelt
        else:
            s = s + ".IS"
        return s

    # ── FOREX ────────────────────────────────────────────────
    if market == "forex":
        # 1. Önce CFG.FOREX display-name lookup (EUR/USD, XAU/USD vb.)
        if s in CFG.FOREX:
            return CFG.FOREX[s]

        # 2. "/" içeren serbest giriş: EUR/USD → EURUSD=X
        if "/" in s:
            base, quote = s.replace(" ","").split("/", 1)
            # Emtia sembolü mü?
            combo = base + quote
            if combo in _COMMODITY_MAP: return _COMMODITY_MAP[combo]
            if base  in _COMMODITY_MAP: return _COMMODITY_MAP[base]
            # =F futures kodu mu?
            if quote in ("USD","EUR") and base in ("GC","SI","CL","BZ","NG","HG","PL","PA","ZW","ZC"):
                return base + "=F"
            # Normal forex çifti
            return combo + "=X"

        # 3. Uzantı zaten var mı?
        if s.endswith("=X") or s.endswith("=F") or s.endswith("-USD"): return s

        # 4. 6 karakter → standart forex çifti
        if len(s) == 6 and s.isalpha():
            # Özel eşleme kontrolü
            if s in _COMMODITY_MAP: return _COMMODITY_MAP[s]
            return s + "=X"

        # 5. 3 karakter → base currency (varsayılan USD karşı)
        if len(s) == 3 and s.isalpha():
            if s in _COMMODITY_MAP: return _COMMODITY_MAP[s]
            return s + "USD=X"

        # 6. Emtia adı (GOLD, SILVER vb.)
        if s in _COMMODITY_MAP: return _COMMODITY_MAP[s]

        return s  # değiştiremediysek olduğu gibi bırak

    # ── US HİSSE ─────────────────────────────────────────────
    if market == "stock_us":
        return s  # zaten doğru format

    # ── KRİPTO ──────────────────────────────────────────────
    if market == "crypto":
        # Zaten tam Binance sembolü: BTCUSDT, ETHBTC, SOLUSDT vb.
        if s.endswith("USDT") or s.endswith("BUSD") or s.endswith("BNB"):
            return s
        # BTC/ETH pairs: ETHBTC, BNBBTC vb.
        if len(s) > 3 and (s.endswith("BTC") or s.endswith("ETH")):
            return s
        # Kısa sembol: BTC → BTCUSDT, ETH → ETHUSDT, SOL → SOLUSDT
        return s + "USDT"

    return s


# ═══════════════════════════════════════════════════
#  YFINANCE TABANLÎ VERİ KATMANI
# ═══════════════════════════════════════════════════

# yfinance interval → period mapping
_YF_PERIOD = {
    "1m":"7d","2m":"60d","5m":"60d","15m":"60d","30m":"60d",
    "60m":"730d","1h":"730d","90m":"60d",
    "1d":"10y","5d":"10y","1wk":"max","1mo":"max","3mo":"max",
}
# Uygulama TF label → yfinance interval
_TF_TO_YFI = {
    "1m":"1m", "3m":"5m", "5m":"5m", "10m":"15m",
    "15m":"15m", "30m":"30m",
    "1s":"1h", "4s":"1h",   # 4s = 1h çekip resample
    "1g":"1d",
    # backward compat
    "1h":"1h","4h":"1h","1d":"1d","1w":"1wk","1wk":"1wk",
}


def _df_from_yf_ticker(ticker_obj, yf_interval: str, period: str, bars: int) -> pd.DataFrame:
    """yfinance Ticker nesnesinden standart OHLCV DataFrame üret."""
    try:
        raw = ticker_obj.history(interval=yf_interval, period=period, auto_adjust=True, prepost=False)
        if raw is None or raw.empty:
            return pd.DataFrame()
        raw = raw.reset_index()
        # Kolon adı normaliz
        raw.columns = [str(c).lower() for c in raw.columns]
        time_col = next((c for c in raw.columns if c in ("datetime","date","timestamp","index")), None)
        if time_col is None: return pd.DataFrame()
        df = pd.DataFrame({
            "time":  pd.to_datetime(raw[time_col]).dt.tz_localize(None),
            "open":  pd.to_numeric(raw.get("open",   raw.iloc[:,1]), errors="coerce"),
            "high":  pd.to_numeric(raw.get("high",   raw.iloc[:,2]), errors="coerce"),
            "low":   pd.to_numeric(raw.get("low",    raw.iloc[:,3]), errors="coerce"),
            "close": pd.to_numeric(raw.get("close",  raw.iloc[:,4]), errors="coerce"),
            "volume":pd.to_numeric(raw.get("volume", [0]*len(raw)),  errors="coerce").fillna(0),
        })
        df = df.dropna(subset=["open","high","low","close"])
        df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
        return df.tail(bars).reset_index(drop=True) if len(df) >= 10 else pd.DataFrame()
    except Exception as e:
        elog("_df_from_yf_ticker", e)
        return pd.DataFrame()


def _resample_4h(df: pd.DataFrame) -> pd.DataFrame:
    """1h → 4h yeniden örnekleme"""
    try:
        df2 = df.set_index("time")
        r = df2.resample("4h", closed="left", label="left").agg(
            {"open":"first","high":"max","low":"min","close":"last","volume":"sum"}
        ).dropna(subset=["open","close"])
        return r.reset_index()
    except:
        return df


def _yf_fetch_raw_http(yf_sym: str, interval: str, period: str) -> pd.DataFrame:
    """
    Saf HTTP fallback — yfinance paketi yüklü değilse devreye girer.
    query1/query2 rotasyonlu, User-Agent havuzlu.
    """
    import random
    bases = [CFG.YF1, CFG.YF2]; random.shuffle(bases)
    for base in bases:
        for ua in CFG.YF_UA:
            for att in range(2):
                try:
                    r = requests.get(f"{base}/{yf_sym}",
                        params={"interval":interval,"range":period,
                                "includePrePost":"false","events":"div,splits"},
                        headers={"User-Agent":ua,"Accept":"application/json",
                                 "Accept-Language":"en-US,en;q=0.9"},
                        timeout=CFG.TO)
                    if r.status_code == 429: time.sleep(1.5+att*2); continue
                    if r.status_code == 404: return pd.DataFrame()
                    if not r.ok: break
                    data = r.json()
                    res  = data.get("chart",{}).get("result",[])
                    if not res: break
                    res  = res[0]
                    ts   = res.get("timestamp",[])
                    q    = res.get("indicators",{}).get("quote",[{}])[0]
                    if not ts or not q.get("close"): break
                    df = pd.DataFrame({
                        "time":  pd.to_datetime(ts, unit="s", utc=True).tz_localize(None),
                        "open":  pd.to_numeric(q.get("open",  [None]*len(ts)), errors="coerce"),
                        "high":  pd.to_numeric(q.get("high",  [None]*len(ts)), errors="coerce"),
                        "low":   pd.to_numeric(q.get("low",   [None]*len(ts)), errors="coerce"),
                        "close": pd.to_numeric(q.get("close", [None]*len(ts)), errors="coerce"),
                        "volume":pd.to_numeric(q.get("volume",[0]*len(ts)),    errors="coerce").fillna(0),
                    })
                    df = df.dropna(subset=["close","open","high","low"])
                    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
                    if len(df) >= 10: return df
                    break
                except Exception as e:
                    elog("_yf_fetch_raw_http", f"{yf_sym}: {e}")
                    time.sleep(0.5+att)
    return pd.DataFrame()


@st.cache_data(ttl=45, show_spinner=False)
def fetch_data(symbol: str, interval: str, bars: int = 700, market: str = "") -> pd.DataFrame:
    """
    APEX PRO — BİRLEŞİK VERİ FONKSİYONU
    Desteklenen TF: 1m,3m,5m,10m,15m,30m,1s,4s,1g (ve eski 1h,4h,1d)
    1. yfinance paketi — birincil
    2. Ham HTTP Yahoo Finance — yedek
    """
    yf_sym = fix_symbol(symbol, market) if market else symbol
    # 4s (4 saat) resample gerekli mi?
    resample_4h = interval in ("4s", "4h")
    # TF label → yfinance interval
    yf_interval = _TF_TO_YFI.get(interval, "1d")
    if resample_4h:
        yf_interval = "1h"
    period = _YF_PERIOD.get(yf_interval, "2y")

    df = pd.DataFrame()
    if _YF_OK:
        try:
            ticker = yf.Ticker(yf_sym)
            df = _df_from_yf_ticker(ticker, yf_interval, period, bars * 2)
        except Exception as e:
            elog("fetch_data[yfinance]", f"{yf_sym}: {e}")

    if df.empty:
        df = _yf_fetch_raw_http(yf_sym, yf_interval, period)

    if df.empty:
        return pd.DataFrame()

    if resample_4h and len(df) > 10:
        df = _resample_4h(df)

    return df.tail(bars).reset_index(drop=True)


# Backward-compat aliases
def fetch_yf(yf_sym, interval, bars=700):
    return fetch_data(yf_sym, interval, bars, market="")

def fetch_yahoo(symbol_yf, interval, bars=500):
    return fetch_data(symbol_yf, interval, bars, market="")

# ═══════════════════════════════════════════════════
#  get_data() — Kullanıcı Dostu API
#  Sembol formatını otomatik düzeltir, tek fonksiyon
# ═══════════════════════════════════════════════════
def get_data(symbol: str, timeframe: str = "1h", market: str = "auto",
             bars: int = 500) -> pd.DataFrame:
    """
    APEX PRO veri çekme API'si — kullanıcı dostu.

    Parametreler
    ────────────
    symbol    : Ham sembol — format otomatik düzeltilir
                BIST   → "THYAO", "BIMAS", "EREGL"
                Forex  → "EURUSD", "EUR/USD", "GOLD", "XAU/USD"
                US     → "AAPL", "MSFT", "SPY"
                Kripto → "BTC", "BTCUSDT", "ETH"
    timeframe : "1m","5m","15m","1h","4h","1d","1w"
    market    : "auto" (otomatik tespit), "forex", "crypto",
                "stock_us", "stock_bist"
    bars      : Kaç mum? (varsayılan 500)

    Döndürür
    ────────
    pandas DataFrame: time, open, high, low, close, volume
    Başarısız olursa boş DataFrame döner.

    Örnekler
    ────────
    >>> get_data("THYAO", "1d")          # BIST → THYAO.IS
    >>> get_data("EURUSD", "1h")         # Forex → EURUSD=X
    >>> get_data("GOLD", "4h")           # Emtia → GC=F
    >>> get_data("BTC", "15m")           # Kripto → BTCUSDT
    >>> get_data("EUR/USD", "1h")        # Slash desteklenir
    """
    s = symbol.strip().upper()

    # ── Otomatik piyasa tespiti ─────────────────────────────
    if market == "auto":
        # Kripto tespiti
        if s.endswith("USDT") or s.endswith("BTC") or s in (
            "BTC","ETH","BNB","SOL","XRP","ADA","DOGE","DOT","AVAX","LINK",
            "MATIC","LTC","UNI","ATOM","NEAR","APT","ARB","OP","INJ","SUI"
        ):
            market = "crypto"
        # BIST tespiti
        elif s.endswith(".IS") or s in (k for k in CFG.BIST):
            market = "stock_bist"
        # Forex tespiti
        elif (s in CFG.FOREX or "/" in s or s.endswith("=X") or s.endswith("=F")
              or s in _COMMODITY_MAP or (len(s)==6 and s.isalpha() and not any(
                  s.startswith(us[:3]) for us in ["APP","MSF","NVD","GOO"]))):
            market = "forex"
        else:
            # Varsayılan: US hisse
            market = "stock_us"

    return fetch_data(symbol=symbol, interval=timeframe, bars=bars, market=market)



@st.cache_data(ttl=25, show_spinner=False)
def fetch_bin(symbol, interval, limit=700):
    """Binance — kripto birincil kaynak (apısız, güvenilir)
    TF dönüşümü: 1s→1h, 4s→4h, 1g→1d, 10m→15m otomatik
    """
    # TF label → Binance API interval
    _bin_map = {
        "1m":"1m","3m":"3m","5m":"5m","10m":"15m",
        "15m":"15m","30m":"30m","1s":"1h","4s":"4h","1g":"1d",
        # eski format uyumu
        "1h":"1h","4h":"4h","1d":"1d",
    }
    bin_interval = _bin_map.get(interval, interval)
    resample_4s  = (interval == "4s")   # 4s için resample gerek yok (4h direkt çekilir)

    for attempt in range(3):
        try:
            r = requests.get(f"{CFG.BIN}/klines",
                params={"symbol":symbol,"interval":bin_interval,"limit":limit}, timeout=CFG.TO)
            r.raise_for_status()
            df = pd.DataFrame(r.json(),
                columns=["time","open","high","low","close","volume","ct","qav","nt","tb","tbq","ig"])
            df["time"] = pd.to_datetime(df["time"], unit="ms")
            for c in ["open","high","low","close","volume"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            return df[["time","open","high","low","close","volume"]].dropna().reset_index(drop=True)
        except Exception as e:
            if attempt < 2: time.sleep(0.6 + attempt)
            else: elog("fetch_bin", e)
    return pd.DataFrame()


# ═══════════════════════════════════════════════════
#  MARKET DATA — APÍSIZ YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def fetch_fg():
    """Fear & Greed Index — alternative.me (apısız)"""
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=7)
        if r.ok:
            d = r.json()["data"][0]
            labels_tr = {
                "Extreme Fear": "Aşırı Korku", "Fear": "Korku",
                "Neutral": "Nötr", "Greed": "Açgözlülük",
                "Extreme Greed": "Aşırı Açgözlülük"
            }
            lbl = d.get("value_classification", "Neutral")
            return {"value": int(d["value"]),
                    "label": labels_tr.get(lbl, lbl)}
    except: pass
    return {"value": 50, "label": "Nötr"}


@st.cache_data(ttl=90, show_spinner=False)
def fetch_funding(symbol: str) -> float:
    """Binance perp funding rate — apısız"""
    try:
        r = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex",
                         params={"symbol": symbol}, timeout=6)
        if r.ok:
            return round(float(r.json().get("lastFundingRate", 0)) * 100, 4)
    except: pass
    return 0.0


@st.cache_data(ttl=90, show_spinner=False)
def fetch_ob(symbol: str) -> dict:
    """Binance order book bid/ask ratio — apısız"""
    try:
        r = requests.get(f"{CFG.BIN}/depth",
                         params={"symbol": symbol, "limit": 20}, timeout=6)
        if r.ok:
            d = r.json()
            bids = np.array([[float(p), float(q)] for p, q in d["bids"]])
            asks = np.array([[float(p), float(q)] for p, q in d["asks"]])
            bv = bids[:, 1].sum()
            av = asks[:, 1].sum()
            return {"bid": round(bv, 2), "ask": round(av, 2),
                    "ratio": round(bv / (av + 1e-9), 3)}
    except: pass
    return {}


@st.cache_data(ttl=180, show_spinner=False)
def fetch_news() -> list:
    """Kripto + finans haberleri — RSS (apısız)"""
    import xml.etree.ElementTree as ET
    feeds = [
        ("CoinDesk",  "https://www.coindesk.com/arc/outboundfeeds/rss/",       "🪙"),
        ("CoinTel",   "https://cointelegraph.com/rss",                          "📡"),
        ("Reuters",   "https://feeds.reuters.com/reuters/businessNews",          "📰"),
        ("BBC Biz",   "https://feeds.bbci.co.uk/news/business/rss.xml",         "🌍"),
    ]
    items = []
    for name, url, icon in feeds:
        try:
            r = requests.get(url, timeout=8,
                             headers={"User-Agent": "Mozilla/5.0"})
            if not r.ok:
                continue
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:5]:
                t_ = item.findtext("title", "").strip()
                l_ = item.findtext("link",  "").strip()
                d_ = re.sub(r"<[^>]+>", "",
                            item.findtext("description", ""))[:120].strip()
                pub = item.findtext("pubDate", "")[:22]
                if t_:
                    items.append({"title": t_, "link": l_, "desc": d_,
                                  "src": name, "icon": icon, "pub": pub})
        except:
            continue
    return items


@st.cache_data(ttl=20, show_spinner=False)
def live_price(sym_api, market):
    """Canlı fiyat — Kripto: WS stream (anlık), diğerleri: yfinance/HTTP."""
    yf_sym = fix_symbol(sym_api, market)
    try:
        if market == "crypto":
            # 1. WS stream (anlık — en hızlı)
            ws = get_ws_price(sym_api)
            if ws and ws.get("price", 0) > 0:
                return ws
            # 2. WS hazır değilse Binance REST
            r = requests.get(f"{CFG.BIN}/ticker/24hr", params={"symbol":sym_api}, timeout=5)
            if r.ok:
                d = r.json()
                return {"price":float(d.get("lastPrice",0)),"chg":float(d.get("priceChangePercent",0)),
                        "hi":float(d.get("highPrice",0)),"lo":float(d.get("lowPrice",0)),
                        "vol":float(d.get("quoteVolume",0))}

        # yfinance fast_info (birincil)
        if _YF_OK:
            try:
                t = yf.Ticker(yf_sym)
                fi = t.fast_info
                p = float(getattr(fi, "last_price", 0) or 0)
                prev = float(getattr(fi, "previous_close", p) or p)
                if p > 0:
                    return {"price":p,"chg":(p-prev)/max(prev,1e-9)*100,
                            "hi":float(getattr(fi,"day_high",p) or p),
                            "lo":float(getattr(fi,"day_low", p) or p),
                            "vol":float(getattr(fi,"three_month_average_volume",0) or 0)}
            except: pass

        # HTTP fallback
        import random
        ua = random.choice(CFG.YF_UA)
        headers = {"User-Agent":ua,"Accept":"application/json"}
        for base in [CFG.YF1, CFG.YF2]:
            try:
                r = requests.get(f"{base}/{yf_sym}",
                    params={"interval":"1m","range":"1d"}, headers=headers, timeout=6)
                if r.ok:
                    meta = r.json().get("chart",{}).get("result",[{}])[0].get("meta",{})
                    p    = float(meta.get("regularMarketPrice",0))
                    prev = float(meta.get("chartPreviousClose",p) or p)
                    if p > 0:
                        return {"price":p,"chg":(p-prev)/max(prev,1e-9)*100,
                                "hi":float(meta.get("regularMarketDayHigh",p)),
                                "lo":float(meta.get("regularMarketDayLow",p)),
                                "vol":float(meta.get("regularMarketVolume",0))}
            except: pass
    except Exception as e:
        elog("live_price", e)
    return {"price":0,"chg":0,"hi":0,"lo":0,"vol":0}


# ═══════════════════════════════════════════════════
#  BİNANCE WEBSOCKET CANLI FİYAT AKIŞI
#  Kripto için arka planda WS bağlantısı tutar,
#  diğer piyasalar için polling fallback devreye girer.
# ═══════════════════════════════════════════════════
_WS_PRICES: dict = {}   # {symbol: {"price":…,"chg":…,"hi":…,"lo":…,"vol":…}}
_WS_THREADS: dict = {}  # {symbol: thread}
_WS_STOP: dict   = {}   # {symbol: threading.Event}

def _binance_ws_worker(symbol: str, stop_event: threading.Event):
    """
    Binance miniTicker WebSocket stream — arka plan thread.
    Bağlantı koptuğunda otomatik yeniden bağlanır.
    """
    import socket
    import ssl
    WS_URL = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@miniTicker"

    def _parse(raw: bytes):
        try:
            d = json.loads(raw)
            p    = float(d.get("c", 0))
            prev = float(d.get("o", p) or p)
            _WS_PRICES[symbol] = {
                "price": p,
                "chg":   (p - prev) / max(prev, 1e-9) * 100,
                "hi":    float(d.get("h", p)),
                "lo":    float(d.get("l", p)),
                "vol":   float(d.get("q", 0)),   # quote volume
            }
        except: pass

    while not stop_event.is_set():
        try:
            ctx = ssl.create_default_context()
            host, port = "stream.binance.com", 9443
            sock = socket.create_connection((host, port), timeout=10)
            ssock = ctx.wrap_socket(sock, server_hostname=host)
            # HTTP Upgrade
            req = (f"GET /ws/{symbol.lower()}@miniTicker HTTP/1.1\r\n"
                   f"Host: {host}:{port}\r\n"
                   f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                   f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                   f"Sec-WebSocket-Version: 13\r\n\r\n")
            ssock.sendall(req.encode())
            # Skip HTTP headers
            buf = b""
            while b"\r\n\r\n" not in buf:
                buf += ssock.recv(512)
            # Read WebSocket frames
            while not stop_event.is_set():
                ssock.settimeout(30)
                hdr = ssock.recv(2)
                if len(hdr) < 2: break
                length = hdr[1] & 0x7F
                if length == 126:
                    length = int.from_bytes(ssock.recv(2), "big")
                elif length == 127:
                    length = int.from_bytes(ssock.recv(8), "big")
                payload = b""
                while len(payload) < length:
                    chunk = ssock.recv(length - len(payload))
                    if not chunk: break
                    payload += chunk
                _parse(payload)
        except Exception as e:
            elog("ws_worker", f"{symbol}: {e}")
            if not stop_event.is_set():
                time.sleep(3)   # reconnect bekle


def start_ws_price(symbol: str):
    """Verilen kripto sembolü için WS thread başlat (tek seferlik)."""
    if symbol in _WS_THREADS and _WS_THREADS[symbol].is_alive():
        return
    stop = threading.Event()
    _WS_STOP[symbol]   = stop
    t = threading.Thread(target=_binance_ws_worker, args=(symbol, stop),
                         daemon=True, name=f"ws_{symbol}")
    t.start()
    _WS_THREADS[symbol] = t


def get_ws_price(symbol: str):
    """WS önbelleğinden anlık fiyat. Yoksa None döner (polling'e düş)."""
    return _WS_PRICES.get(symbol)


@st.cache_data(ttl=30, show_spinner=False)
def load_mtf(sym_api: str, tf: str, market: str):
    """
    Ana + 2 HTF DataFrame — fetch_data üzerinden (apısız, yfinance birincil).
    Kripto için Binance REST (en güvenilir).
    Returns: (df, df_htf, df_htf2, htf_label, htf2_label)
    """
    htf  = CFG.HTF_MAP.get(tf, tf)
    htf2 = CFG.HTF_MAP.get(htf, htf)

    def _get(sym, interval):
        try:
            if market == "crypto":
                return fetch_bin(sym, interval, 700)
            else:
                return fetch_data(sym, interval, 700, market=market)
        except Exception as e:
            elog("load_mtf._get", e)
        return pd.DataFrame()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f0 = ex.submit(_get, sym_api, tf)
        f1 = ex.submit(_get, sym_api, htf)
        f2 = ex.submit(_get, sym_api, htf2)
        try:    d0 = f0.result(timeout=25)
        except: d0 = pd.DataFrame()
        try:    d1 = f1.result(timeout=25)
        except: d1 = pd.DataFrame()
        try:    d2 = f2.result(timeout=25)
        except: d2 = pd.DataFrame()
    return d0, d1, d2, htf, htf2


# ═══════════════════════════════════════════════════
#  INDICATORS — COMPLETE ENGINE
# ═══════════════════════════════════════════════════
# ── SMC Sonuç Önbelleği (hash bazlı, tekrar hesaplamayı önler) ─────────────
_SMC_CACHE: dict = {}
_IND_CACHE: dict = {}

def _df_hash(df: pd.DataFrame) -> str:
    """DataFrame'in hızlı parmak izi — sadece son 5 satır + uzunluk."""
    try:
        tail = df[["open","high","low","close"]].tail(5).values.tobytes()
        return hashlib.md5(tail + len(df).to_bytes(4,"little")).hexdigest()
    except:
        return ""

def _series_to_pts(df: pd.DataFrame, col: str) -> list:
    """
    Tek bir DataFrame kolonunu [{"time":ts,"value":v}, …] listesine çevirir.
    iterrows() YOK — tamamen vektörel numpy.  ~10x hızlı.
    """
    if col not in df.columns:
        return []
    ts_arr  = (pd.to_datetime(df["time"]).astype("int64") // 1_000_000_000).values
    val_arr = pd.to_numeric(df[col], errors="coerce").values
    mask    = np.isfinite(val_arr)
    if not mask.any():
        return []
    ts_f  = ts_arr[mask].tolist()
    val_f = val_arr[mask].tolist()
    return [{"time": int(t), "value": float(v)} for t, v in zip(ts_f, val_f)]


def add_ind(df):
    if df is None or df.empty or len(df) < 20: return df
    # ── Önbellekten dön ───────────────────────────────
    h_ = _df_hash(df)
    if h_ and h_ in _IND_CACHE:
        return _IND_CACHE[h_]
    df = df.copy()
    c = df["close"]; h = df["high"]; l = df["low"]; v = df["volume"]
    n = len(df)

    # EMAs
    for span, col in [(9,"ema9"),(21,"ema21"),(50,"ema50"),(200,"ema200")]:
        df[col] = c.ewm(span=span, adjust=False).mean()
    df["sma200"] = c.rolling(200, min_periods=1).mean()

    # RSI
    delta = c.diff()
    up = delta.clip(lower=0); dn = (-delta).clip(lower=0)
    rs = up.ewm(14, adjust=False).mean() / (dn.ewm(14, adjust=False).mean().replace(0, 1e-9))
    df["rsi"] = 100 - 100 / (1 + rs)

    # MACD
    ema12 = c.ewm(12, adjust=False).mean(); ema26 = c.ewm(26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_sig"] = df["macd"].ewm(9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

    # Bollinger
    sma20 = c.rolling(20, min_periods=1).mean()
    std20 = c.rolling(20, min_periods=1).std().fillna(0)
    df["bb_up"] = sma20 + 2 * std20; df["bb_mid"] = sma20; df["bb_lo"] = sma20 - 2 * std20
    df["bb_w"] = (df["bb_up"] - df["bb_lo"]) / (sma20.replace(0,1e-9)) * 100

    # ATR
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(14, adjust=False).mean()
    df["atr_pct"] = df["atr"] / c.replace(0,1e-9) * 100

    # ADX / DI
    dmp = (h.diff()).clip(lower=0); dmm = (l.shift()-l).clip(lower=0)
    dmp[dmp < dmm] = 0; dmm[dmm < dmp] = 0
    a14 = tr.ewm(14, adjust=False).mean().replace(0,1e-9)
    dip = 100 * dmp.ewm(14, adjust=False).mean() / a14
    dim = 100 * dmm.ewm(14, adjust=False).mean() / a14
    di_sum = (dip + dim).replace(0,1e-9)
    df["adx"] = ((dip-dim).abs() / di_sum).ewm(14, adjust=False).mean() * 100
    df["di_p"] = dip; df["di_m"] = dim

    # Stochastic
    lo14 = l.rolling(14, min_periods=1).min(); hi14 = h.rolling(14, min_periods=1).max()
    df["stoch_k"] = 100 * (c - lo14) / (hi14 - lo14).replace(0,1e-9)
    df["stoch_d"] = df["stoch_k"].rolling(3, min_periods=1).mean()

    # MFI
    tp = (h+l+c)/3; mf = tp*v
    pmf = mf.where(tp > tp.shift(), 0).rolling(14, min_periods=1).sum()
    nmf = mf.where(tp < tp.shift(), 0).rolling(14, min_periods=1).sum()
    df["mfi"] = 100 - 100/(1 + pmf/(nmf.replace(0,1e-9)))

    # CMF
    mfm = ((c-l)-(h-c)) / (h-l).replace(0,1e-9)
    vsum = v.rolling(20, min_periods=1).sum().replace(0,1e-9)
    df["cmf"] = (mfm * v).rolling(20, min_periods=1).sum() / vsum

    # CCI
    tp2 = (h+l+c)/3; stp = tp2.rolling(20, min_periods=1).mean()
    mad = tp2.rolling(20, min_periods=1).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True).replace(0,1e-9)
    df["cci"] = (tp2 - stp) / (0.015 * mad)

    # Momentum
    df["mom"] = c.diff(10)

    # Williams %R
    df["willr"] = -100 * (hi14 - c) / (hi14 - lo14).replace(0,1e-9)

    # VWAP
    df["vwap"] = (tp * v).cumsum() / v.cumsum().replace(0,1e-9)

    # Volume ratio
    vmean = v.rolling(20, min_periods=1).mean().replace(0,1e-9)
    df["vol_r"] = v / vmean
    df["is_whale"] = (df["vol_r"] > 3).astype(int)

    # HA
    ha_c = (df["open"]+h+l+c)/4; ha_o = ha_c.copy()
    for i in range(1, n): ha_o.iloc[i] = (ha_o.iloc[i-1] + ha_c.iloc[i-1]) / 2
    df["ha_bull"] = (ha_c > ha_o).astype(int)

    # Squeeze Momentum
    kc_up = sma20 + 1.5 * df["atr"]; kc_lo = sma20 - 1.5 * df["atr"]
    df["squeeze"] = ((df["bb_lo"] > kc_lo) & (df["bb_up"] < kc_up)).astype(int)
    hh20 = h.rolling(20, min_periods=1).max(); ll20 = l.rolling(20, min_periods=1).min()
    df["sq_mom"] = (c - ((hh20+ll20)/2 + sma20)/2).ewm(12, adjust=False).mean()

    # Alligator
    df["ali_jaw"]   = c.ewm(13, adjust=False).mean().shift(8)
    df["ali_teeth"] = c.ewm(8,  adjust=False).mean().shift(5)
    df["ali_lips"]  = c.ewm(5,  adjust=False).mean().shift(3)

    result = df.ffill().bfill().fillna(0)
    if h_:
        _IND_CACHE[h_] = result
        if len(_IND_CACHE) > 80:          # bellek sınırı
            oldest = next(iter(_IND_CACHE))
            del _IND_CACHE[oldest]
    return result


# ═══════════════════════════════════════════════════
#  SMC ENGINE — TAMAMEN DÜZELTİLMİŞ
# ═══════════════════════════════════════════════════
def find_swings(H, L, w=5):
    """Swing High/Low tespiti — pencere tabanlı, güvenli."""
    n = len(H); sh = []; sl = []
    if n < w * 2 + 1:
        return sh, sl
    for i in range(w, n - w):
        window_h = H[max(0, i-w): i+w+1]
        window_l = L[max(0, i-w): i+w+1]
        if len(window_h) == 0:
            continue
        if H[i] == np.max(window_h) and H[i] > H[i-1] and H[i] > H[i+1]:
            sh.append((i, float(H[i])))
        if L[i] == np.min(window_l) and L[i] < L[i-1] and L[i] < L[i+1]:
            sl.append((i, float(L[i])))
    return sh, sl

def market_struct(sh, sl):
    """
    Piyasa yapısı: BULLISH / BEARISH / RANGING
    ICT kuralı:
      BULLISH  → HH + HL dizisi
      BEARISH  → LH + LL dizisi
      RANGING  → karışık veya yetersiz swing

    Robust tespit: Son 2 swing + genel eğilim (son 4 swing slope) birlikte değerlendirilir.
    """
    r = {"str":"RANGING","bos_b":False,"bos_s":False,"choch_b":False,"choch_s":False}
    if len(sh) < 2 or len(sl) < 2:
        return r

    # ── Son 2 swing karşılaştırması ─────────────────────────
    hh_ok = sh[-1][1] > sh[-2][1]   # Higher High
    hl_ok = sl[-1][1] > sl[-2][1]   # Higher Low
    lh_ok = sh[-1][1] < sh[-2][1]   # Lower High
    ll_ok = sl[-1][1] < sl[-2][1]   # Lower Low

    # ── Son 4 swing eğilimi (slope) ─────────────────────────
    sh_slope_bull = False; sl_slope_bull = False
    sh_slope_bear = False; sl_slope_bear = False

    if len(sh) >= 4:
        # En az 3 ardışık HH veya LL var mı?
        sh_vals = [p for _, p in sh[-4:]]
        sh_slope_bull = sh_vals[-1] > sh_vals[0]   # Genel artış
        sh_slope_bear = sh_vals[-1] < sh_vals[0]   # Genel düşüş
    if len(sl) >= 4:
        sl_vals = [p for _, p in sl[-4:]]
        sl_slope_bull = sl_vals[-1] > sl_vals[0]
        sl_slope_bear = sl_vals[-1] < sl_vals[0]

    # ── Yapı kararı ─────────────────────────────────────────
    # Güçlü bullish: Son 2 swing HH+HL VEYA genel eğilim yükselen
    is_bullish = (hh_ok and hl_ok) or (hl_ok and sl_slope_bull and sh_slope_bull)
    # Güçlü bearish: Son 2 swing LH+LL VEYA genel eğilim düşen
    is_bearish = (lh_ok and ll_ok) or (ll_ok and sl_slope_bear and sh_slope_bear)

    if is_bullish and not is_bearish:
        r["str"]   = "BULLISH"
        r["bos_b"] = True
    elif is_bearish and not is_bullish:
        r["str"]   = "BEARISH"
        r["bos_s"] = True

    # ── CHoCH: yapı karakterinin değişimi ───────────────────
    # Bearish yapıda en son SH, önceki SH'dan yüksek → CHoCH bullish
    if len(sh) >= 3 and not hh_ok and sh[-1][1] > sh[-3][1]:
        r["choch_b"] = True
    # Bullish yapıda en son SL, önceki SL'dan düşük → CHoCH bearish
    if len(sl) >= 3 and not ll_ok and sl[-1][1] < sl[-3][1]:
        r["choch_s"] = True

    return r

def find_mss(H, L, C, O, n, atr, disp=0.50):
    """
    Market Structure Shift (MSS) — ICT tanımına uygun.
    Koşullar:
      1. Displacement mumu: body/range >= disp eşiği
      2. Bullish MSS: close > son LH seviyesi (bearish yapıyı kırar)
      3. Bearish MSS: close < son HL seviyesi (bullish yapıyı kırar)
    """
    if n < 15:
        return {"b": False, "s": False, "idx": None, "r": 0.0}

    sh, sl = find_swings(H[:n], L[:n])
    if len(sh) < 2 or len(sl) < 2:
        return {"b": False, "s": False, "idx": None, "r": 0.0}

    # Son LH ve HL seviyeleri (yapı pivotları)
    # LH: swing high serisi içinde düşen birini bul
    lh_price = None
    for i in range(len(sh)-1, 0, -1):
        if sh[i][1] < sh[i-1][1]:   # Lower High
            lh_price = sh[i][1]
            break
    if lh_price is None and sh:
        lh_price = sh[-2][1]        # fallback

    # HL: swing low serisi içinde yükselen birini bul
    hl_price = None
    for i in range(len(sl)-1, 0, -1):
        if sl[i][1] > sl[i-1][1]:   # Higher Low
            hl_price = sl[i][1]
            break
    if hl_price is None and sl:
        hl_price = sl[-2][1]        # fallback

    # Son 30 mumda displacement + kırılım ara
    lookback = min(30, n - 1)
    for k in range(n - lookback, n):
        body  = abs(C[k] - O[k])
        rng   = max(H[k] - L[k], 1e-9)
        ratio = body / rng
        if ratio < disp:
            continue
        # Bullish MSS: close > LH + ATR*0.1 (false break filtresi)
        if lh_price is not None and C[k] > lh_price + atr * 0.1:
            return {"b": True, "s": False, "idx": int(k), "r": round(ratio, 2)}
        # Bearish MSS: close < HL - ATR*0.1
        if hl_price is not None and C[k] < hl_price - atr * 0.1:
            return {"b": False, "s": True, "idx": int(k), "r": round(ratio, 2)}

    return {"b": False, "s": False, "idx": None, "r": 0.0}

def find_fvg(H, L, n, lookback=100):
    """
    Fair Value Gap (FVG) / Imbalance tespiti.
    ICT tanımı: 3 mumlu pattern
      Bullish FVG: mum[i+2].low > mum[i].high  → gap yukarı
      Bearish FVG: mum[i+2].high < mum[i].low  → gap aşağı
    Doldurulma: Sonraki herhangi bir mumun ortayı geçmesi
    """
    zones = []
    lb = min(lookback, n - 3)
    if lb < 1:
        return [], None, None

    for i in range(max(0, n - lb), n - 2):
        gap_lo = H[i]
        gap_hi = L[i + 2]
        if gap_hi > gap_lo:          # Bullish FVG
            mid = (gap_hi + gap_lo) / 2
            # Doldurulma: herhangi bir sonraki mumun low'u mid'e düştü mü?
            filled = any(L[j] <= mid for j in range(i + 2, n))
            size_pct = (gap_hi - gap_lo) / max(gap_lo, 1e-9) * 100
            zones.append({
                "type": "bull", "hi": float(gap_hi), "lo": float(gap_lo),
                "mid": float(mid), "idx": i, "filled": filled,
                "size_pct": round(size_pct, 3)
            })
        bear_lo = H[i + 2]
        bear_hi = L[i]
        if bear_hi > bear_lo:        # Bearish FVG
            mid = (bear_hi + bear_lo) / 2
            filled = any(H[j] >= mid for j in range(i + 2, n))
            size_pct = (bear_hi - bear_lo) / max(bear_lo, 1e-9) * 100
            zones.append({
                "type": "bear", "hi": float(bear_hi), "lo": float(bear_lo),
                "mid": float(mid), "idx": i, "filled": filled,
                "size_pct": round(size_pct, 3)
            })

    # En son, doldurulmamış FVG'leri seç
    fb = next((z for z in reversed(zones) if z["type"] == "bull" and not z["filled"]), None)
    fs = next((z for z in reversed(zones) if z["type"] == "bear" and not z["filled"]), None)
    return zones[-20:], fb, fs

def find_obs(H, L, C, O, times, sh, sl, n, imb, disp=0.50):
    """
    Order Block (OB) tespiti — ICT tanımı:
    Bull OB: Swing low'dan önceki son bearish (C<O) mum
    Bear OB: Swing high'dan önceki son bullish (C>O) mum
    Geçerlilik: Displacement + invalidasyon yok + skor
    """
    bull_obs = []; bear_obs = []

    # ── Bull OB'ler ─────────────────────────────────────────
    for si, _ in sl[-15:]:
        ok_ = None
        # Swing low'dan geriye giderek son bearish mumu bul
        for k in range(si - 1, max(0, si - 8), -1):
            if C[k] < O[k]:          # Bearish candle (OB adayı)
                ok_ = k
                break
        if ok_ is None:
            continue

        # Displacement sonrası en az bir güçlü bullish mum olmalı
        disp_ok = False
        dr = 0.0
        for dk in range(ok_ + 1, min(ok_ + 6, n)):
            body_r = abs(C[dk] - O[dk]) / max(H[dk] - L[dk], 1e-9)
            if body_r >= disp and C[dk] > O[dk]:   # Güçlü bullish displacement
                disp_ok = True
                dr = body_r
                break
        if not disp_ok:
            continue

        # İnvalidasyon: fiyat OB'nin low'unun altına kapandı mı? (tolerans %0.3)
        invalidated = any(C[j] < L[ok_] * 0.997 for j in range(ok_ + 1, min(ok_ + 80, n)))
        if invalidated:
            continue

        # Test edildi mi (fiyat OB'ye geri döndü mü)?
        tested = any(L[j] <= H[ok_] * 1.001 for j in range(ok_ + 2, n))

        # FVG confluence: OB bölgesinde aktif FVG var mı?
        fvg_c = any(
            z["type"] == "bull" and not z.get("filled") and
            z["lo"] <= H[ok_] and z["hi"] >= L[ok_]
            for z in imb
        )

        bp = abs(C[ok_] - O[ok_]) / max(H[ok_] - L[ok_], 1e-9)
        # Skor hesabı (max 100)
        sc = min(100, int(
            bp * 25           # Vücut oranı
            + dr * 35         # Displacement gücü
            + (20 if fvg_c else 0)    # FVG confluence bonus
            + (5 if not tested else 10)  # Test edilmemişse daha değerli
            + min(10, int(si / max(n, 1) * 20))  # Yakın swing bonus
        ))

        bull_obs.append({
            "idx": int(ok_), "hi": float(H[ok_]), "lo": float(L[ok_]),
            "mid": float((H[ok_] + L[ok_]) / 2), "time": times[ok_],
            "status": "tested" if tested else "valid",
            "score": sc, "fvg": fvg_c, "disp": round(dr, 2)
        })

    # ── Bear OB'ler ─────────────────────────────────────────
    for si, _ in sh[-15:]:
        ok_ = None
        for k in range(si - 1, max(0, si - 8), -1):
            if C[k] > O[k]:          # Bullish candle (OB adayı)
                ok_ = k
                break
        if ok_ is None:
            continue

        disp_ok = False
        dr = 0.0
        for dk in range(ok_ + 1, min(ok_ + 6, n)):
            body_r = abs(C[dk] - O[dk]) / max(H[dk] - L[dk], 1e-9)
            if body_r >= disp and C[dk] < O[dk]:   # Güçlü bearish displacement
                disp_ok = True
                dr = body_r
                break
        if not disp_ok:
            continue

        # İnvalidasyon: fiyat OB'nin high'ının üzerine kapandı mı?
        invalidated = any(C[j] > H[ok_] * 1.003 for j in range(ok_ + 1, min(ok_ + 80, n)))
        if invalidated:
            continue

        tested = any(H[j] >= L[ok_] * 0.999 for j in range(ok_ + 2, n))

        fvg_c = any(
            z["type"] == "bear" and not z.get("filled") and
            z["lo"] <= H[ok_] and z["hi"] >= L[ok_]
            for z in imb
        )

        bp = abs(C[ok_] - O[ok_]) / max(H[ok_] - L[ok_], 1e-9)
        sc = min(100, int(
            bp * 25
            + dr * 35
            + (20 if fvg_c else 0)
            + (5 if not tested else 10)
            + min(10, int(si / max(n, 1) * 20))
        ))

        bear_obs.append({
            "idx": int(ok_), "hi": float(H[ok_]), "lo": float(L[ok_]),
            "mid": float((H[ok_] + L[ok_]) / 2), "time": times[ok_],
            "status": "tested" if tested else "valid",
            "score": sc, "fvg": fvg_c, "disp": round(dr, 2)
        })

    bull_obs.sort(key=lambda x: x["score"], reverse=True)
    bear_obs.sort(key=lambda x: x["score"], reverse=True)
    return bull_obs[:6], bear_obs[:6]

def find_liq(H, L, C, n, atr):
    tol = max(0.0015, atr / max(H[-1], 1e-9) * 0.5)
    eq_h = []; eq_l = []; seen_h = set(); seen_l = set()
    for i in range(max(0,n-100), n-3):
        for j in range(i+2, min(i+40, n)):
            if abs(H[i]-H[j]) / max(H[i], 1e-9) < tol:
                lv = round((H[i]+H[j])/2, 8)
                if lv not in seen_h:
                    seen_h.add(lv)
                    sw = any(H[k] > lv*1.0005 and C[k] < lv for k in range(max(0,n-25), n))
                    eq_h.append({"level":lv,"swept":sw,"prox":round(abs(C[-1]-lv)/(atr+1e-9),1)})
            if abs(L[i]-L[j]) / max(L[i], 1e-9) < tol:
                lv = round((L[i]+L[j])/2, 8)
                if lv not in seen_l:
                    seen_l.add(lv)
                    sw = any(L[k] < lv*0.9995 and C[k] > lv for k in range(max(0,n-25), n))
                    eq_l.append({"level":lv,"swept":sw,"prox":round(abs(C[-1]-lv)/(atr+1e-9),1)})
    bsl = float(max(H[max(0,n-60):])); ssl = float(min(L[max(0,n-60):]))
    pwh = float(max(H[max(0,n-10):])); pwl = float(min(L[max(0,n-10):]))
    def _sw(lv, d):
        for i in range(max(0,n-40), n):
            if d == "a" and H[i] > lv and C[i] < lv: return True, ("strong" if H[i]-lv >= atr*.4 else "weak")
            if d == "b" and L[i] < lv and C[i] > lv: return True, ("strong" if lv-L[i] >= atr*.4 else "weak")
        return False, None
    bsw, bq = _sw(bsl, "a"); ssw, sq = _sw(ssl, "b")
    return {"eq_h":eq_h[-6:],"eq_l":eq_l[-6:],"bsl":bsl,"ssl":ssl,"pwh":pwh,"pwl":pwl,
            "bsl_sw":bsw,"ssl_sw":ssw,"bsl_q":bq,"ssl_q":sq}

def calc_smc(df, bias="NEUTRAL"):
    """
    Full SMC hesaplama. Hash cache'li, exception-safe.
    ICT konseptleri: OB, FVG, MSS, BOS, CHoCH, Likidite, Fibonacci, PDH/PDL
    """
    h_ = (_df_hash(df) + bias) if df is not None else ""
    if h_ and h_ in _SMC_CACHE:
        return _SMC_CACHE[h_]
    try:
        if df is None or len(df) < 50:
            return {}

        H = df["high"].values.astype(float)
        L = df["low"].values.astype(float)
        C = df["close"].values.astype(float)
        O = df["open"].values.astype(float)
        n = len(df)
        times = df["time"].values

        # ATR
        atr = float(df["atr"].iloc[-1]) if ("atr" in df.columns and pd.notna(df["atr"].iloc[-1])) \
              else float(np.mean(H[-20:] - L[-20:]))
        atr = max(atr, 1e-9)

        # Swing tespiti
        sh, sl = find_swings(H, L, CFG.SW)
        if len(sh) < 3 or len(sl) < 3:
            return {}

        # Piyasa yapısı
        ms = market_struct(sh, sl)
        is_bull = (ms["str"] == "BULLISH")

        # MSS
        mss_d = find_mss(H, L, C, O, n, atr)

        # Fibonacci — son önemli swing range üzerinden
        # Bullish: ll → hh / Bearish: hh → ll (son 8 swing)
        recent_sh = sh[-8:] if len(sh) >= 8 else sh
        recent_sl = sl[-8:] if len(sl) >= 8 else sl
        hh = float(max(p for _, p in recent_sh))
        ll = float(min(p for _, p in recent_sl))
        rng = max(hh - ll, atr)
        eq  = (hh + ll) / 2

        fibs = {}
        for r_val, lbl in [(0,"0%"),(0.236,"23.6%"),(0.382,"38.2%"),(0.5,"50%"),
                            (0.618,"61.8%"),(0.786,"78.6%"),(1,"100%")]:
            if is_bull:
                fibs[lbl] = round(ll + rng * r_val, 8)
            else:
                fibs[lbl] = round(hh - rng * r_val, 8)

        # OTE zone (0.618 - 0.786 arası giriş bölgesi)
        if is_bull:
            ote_lo = ll + rng * 0.618
            ote_hi = ll + rng * 0.786
        else:
            ote_lo = hh - rng * 0.786
            ote_hi = hh - rng * 0.618

        # FVG ve OB
        imb, fvg_b, fvg_s = find_fvg(H, L, n)
        bull_obs, bear_obs = find_obs(H, L, C, O, times, sh, sl, n, imb)

        # Aktif OB seç
        ob1 = None
        if is_bull and bull_obs:
            # Fiyata en yakın geçerli OB'yi seç
            price_now = float(C[-1])
            valid_obs = [ob for ob in bull_obs if ob["lo"] <= price_now * 1.05]
            ob1 = valid_obs[0] if valid_obs else bull_obs[0]
        elif not is_bull and bear_obs:
            price_now = float(C[-1])
            valid_obs = [ob for ob in bear_obs if ob["hi"] >= price_now * 0.95]
            ob1 = valid_obs[0] if valid_obs else bear_obs[0]

        price = float(C[-1])

        # TP/SL — OB'ye dayalı, ATR çarpanlı
        if ob1:
            if is_bull:
                sl_p = ob1["lo"] * 0.9975          # OB low'unun %0.25 altı
                risk = abs(price - sl_p)
                risk = max(risk, atr * 0.5)        # minimum ATR/2 risk
                tp1  = price + risk * 1.0
                tp2  = price + risk * 2.0
                tp3  = price + risk * 3.5
            else:
                sl_p = ob1["hi"] * 1.0025
                risk = abs(sl_p - price)
                risk = max(risk, atr * 0.5)
                tp1  = price - risk * 1.0
                tp2  = price - risk * 2.0
                tp3  = price - risk * 3.5
        else:
            # OB yoksa swing level'lara dayan
            if is_bull and sl:
                sl_p = float(min(p for _, p in sl[-3:])) * 0.997
            elif not is_bull and sh:
                sl_p = float(max(p for _, p in sh[-3:])) * 1.003
            else:
                sl_p = price * (0.99 if is_bull else 1.01)
            risk = abs(price - sl_p)
            risk = max(risk, atr * 0.5)
            tp1  = price + (risk     if is_bull else -risk)
            tp2  = price + (risk*2   if is_bull else -risk*2)
            tp3  = price + (risk*3.5 if is_bull else -risk*3.5)

        rr = round(abs(price - tp3) / max(abs(price - sl_p), 1e-9), 2)

        # PDH/PDL — günlük önceki yüksek/düşük
        # Yaklaşık: n/7 veya son 24 mum (1h TF için = 1 gün)
        pd_lookback = max(24, n // 7)
        pdh = float(np.max(H[max(0, n - pd_lookback):]))
        pdl = float(np.min(L[max(0, n - pd_lookback):]))

        # HTF uyumu
        htf_ok = ((is_bull and bias in ("BULL", "NEUTRAL")) or
                  (not is_bull and bias in ("BEAR", "NEUTRAL")))

        # Likidite haritası
        liq = find_liq(H, L, C, n, atr)

        result = dict(
            is_bull  = is_bull,
            struct   = ms["str"],
            bos_b    = ms["bos_b"],
            bos_s    = ms["bos_s"],
            choch_b  = ms["choch_b"],
            choch_s  = ms["choch_s"],
            mss_b    = mss_d["b"],
            mss_s    = mss_d["s"],
            mss_idx  = mss_d["idx"],
            mss_r    = mss_d["r"],
            bull_obs = bull_obs,
            bear_obs = bear_obs,
            fvg_b    = fvg_b,
            fvg_s    = fvg_s,
            imb      = imb,
            hh=hh, ll=ll, eq=eq,
            fibs     = fibs,
            ote_lo   = ote_lo,
            ote_hi   = ote_hi,
            is_prem  = (price > eq),
            atr      = atr,
            bias     = bias,
            htf_ok   = htf_ok,
            tp1=tp1, tp2=tp2, tp3=tp3,
            sl_p     = sl_p,
            rr       = rr,
            pdh=pdh, pdl=pdl,
            sh_pts   = [(int(i), float(p)) for i, p in sh[-12:]],
            sl_pts   = [(int(i), float(p)) for i, p in sl[-12:]],
            **liq,
        )

        if h_:
            _SMC_CACHE[h_] = result
            if len(_SMC_CACHE) > 100:
                try:
                    del _SMC_CACHE[next(iter(_SMC_CACHE))]
                except StopIteration:
                    pass

        return result

    except Exception as e:
        elog("calc_smc", e)
        return {}


# ═══════════════════════════════════════════════════
#  STRATEJİ PANELİ — MEO PRO STYLE
# ═══════════════════════════════════════════════════
def build_strategy(df, smc, df_htf, bias, sym, dp=2):
    """Returns full MEO PRO style strategy dict. Never throws."""
    try:
        if df is None or df.empty or not smc: return {}
        price = float(df["close"].iloc[-1])
        is_bull = smc.get("is_bull", True)
        atr   = cv(df,"atr",price*.01)
        rsi   = cv(df,"rsi",50)
        adx   = cv(df,"adx",20)
        mfi   = cv(df,"mfi",50)
        macd  = cv(df,"macd",0)
        mhist = cv(df,"macd_hist",0)
        bb_up = cv(df,"bb_up",price)
        bb_lo = cv(df,"bb_lo",price)
        bb_mid= cv(df,"bb_mid",price)
        ema9  = cv(df,"ema9",price)
        ema21 = cv(df,"ema21",price)
        ema50 = cv(df,"ema50",price)
        sma200= cv(df,"sma200",price)
        cci   = cv(df,"cci",0)
        mom   = cv(df,"mom",0)
        dmi   = cv(df,"di_p",25) - cv(df,"di_m",25)
        vr    = cv(df,"vol_r",1)
        cmf   = cv(df,"cmf",0)
        willr = cv(df,"willr",-50)
        atp   = cv(df,"atr_pct",1)
        bb_w  = cv(df,"bb_w",2)
        sq    = bool(df["squeeze"].iloc[-1]) if "squeeze" in df.columns else False

        cl_arr = df["close"].values
        pct20 = (price - cl_arr[-min(20,len(cl_arr))]) / max(cl_arr[-min(20,len(cl_arr))],1e-9) * 100

        # ── Trend Durumu
        if ema9>ema21>ema50 and price>ema50 and adx>25:
            trend_d="Güçlü Yükselen Boğa Trendi"; tc="#00ff88"
        elif ema9<ema21<ema50 and price<ema50 and adx>25:
            trend_d="Güçlü Düşen Ayı Trendi"; tc="#ff3355"
        elif ema9>ema21 and price>ema21:
            trend_d="Yükselen Trend"; tc="#00ff88"
        elif ema9<ema21 and price<ema21:
            trend_d="Düşen Trend"; tc="#ff3355"
        else:
            trend_d="Yatay / Belirsiz"; tc="#ffd600"

        # ── Trend Gücü
        if   adx>=40: tg_d=f"Çok Güçlü ({pct20:.1f}%)"; tg_c="#00ff88"; tg_lbl="ÇOK YÜKSEK"
        elif adx>=30: tg_d=f"Güçlü ({pct20:.1f}%)";     tg_c="#00ff88"; tg_lbl="YÜKSEK"
        elif adx>=20: tg_d=f"Orta ({pct20:.1f}%)";       tg_c="#ffd600"; tg_lbl="ORTA"
        else:         tg_d=f"Zayıf ({pct20:.1f}%)";      tg_c="#ff6b35"; tg_lbl="DÜŞÜK"

        # ── Volatilite
        if   atp>5 or bb_w>8: vol_d="Yüksek Volatilite ⚠";     vol_c="#ff3355"
        elif atp>2 or bb_w>4: vol_d="Orta Seviye Volatilite";   vol_c="#ffd600"
        else:                  vol_d="Düşük Volatilite / Sıkışma"; vol_c="#00d4ff"

        # ── Momentum
        if   rsi>65 and macd>0 and mom>0: mom_d="Güçlü Alış Momentumu 🚀"; mom_c="#00ff88"
        elif rsi<35 and macd<0 and mom<0: mom_d="Güçlü Satış Momentumu 📉"; mom_c="#ff3355"
        elif rsi>55 and mhist>0:          mom_d="Pozitif Momentum";         mom_c="#00ff88"
        elif rsi<45 and mhist<0:          mom_d="Negatif Momentum";         mom_c="#ff3355"
        else:                             mom_d="Nötr Momentum";            mom_c="#ffd600"

        # ── MFI
        if   mfi>80: mfi_d=f"Aşırı Alım (MFI:{mfi:.0f}) ⚠"; mfi_c="#ffd600"
        elif mfi<20: mfi_d=f"Aşırı Satım (MFI:{mfi:.0f}) ✓"; mfi_c="#00ff88"
        elif mfi>60: mfi_d=f"Alım Baskısı (MFI:{mfi:.0f})";  mfi_c="#00ff88"
        elif mfi<40: mfi_d=f"Satım Baskısı (MFI:{mfi:.0f})"; mfi_c="#ff3355"
        else:        mfi_d=f"Dengeli (MFI:{mfi:.0f})";        mfi_c="#3d5a80"

        # ── Hacim
        if   vr>3 and cmf>0: hacim_d="Kurumsal Alım Baskısı 🐋"; h_c="#00ff88"
        elif vr>3 and cmf<0: hacim_d="Kurumsal Satış Baskısı 🐋"; h_c="#ff3355"
        elif vr>1.5 and cmf>0: hacim_d="Güçlü Alım / Normal Hacim"; h_c="#00ff88"
        elif vr>1.5 and cmf<0: hacim_d="Güçlü Satış / Normal Hacim"; h_c="#ff3355"
        elif vr<0.6: hacim_d="Düşük Hacim — Dikkat!"; h_c="#ffd600"
        else: hacim_d="Normal Hacim Seviyeleri"; h_c="#3d5a80"

        # ── HTF Trend
        if df_htf is not None and not df_htf.empty and "ema9" in df_htf.columns:
            he9  = cv(df_htf,"ema9",price); he21 = cv(df_htf,"ema21",price)
            hcl  = cv(df_htf,"close",price); hrsi = cv(df_htf,"rsi",50)
            if he9>he21 and hcl>he21: htf_d="Güçlü Boğa";  htf_c2="#00ff88"
            elif he9<he21 and hcl<he21: htf_d="Güçlü Ayı"; htf_c2="#ff3355"
            else: htf_d="Nötr"; htf_c2="#ffd600"
            htf_rsi_d = (f"Aşırı Alım ({hrsi:.0f})" if hrsi>70 else
                         f"Aşırı Satım ({hrsi:.0f})" if hrsi<30 else f"Normal ({hrsi:.0f})")
        else:
            htf_d = bias; htf_c2 = "#ffd600"; htf_rsi_d = f"({bias})"

        # ── Uyarılar
        warns = []
        if rsi>70:   warns.append(("r",f"RSI Aşırı Alım: {rsi:.1f} — Dikkat"))
        elif rsi<30: warns.append(("g",f"RSI Aşırı Satım: {rsi:.1f} — Fırsat olabilir"))
        if price>bb_up: warns.append(("y","Fiyat BB Üst Bandın Üzerinde (Aşırı Uzama)"))
        elif price<bb_lo: warns.append(("g","Fiyat BB Alt Bandın Altında (Aşırı Satım)"))
        if mfi>80:   warns.append(("y",f"MFI Aşırı Alım: {mfi:.0f}"))
        if atp>5:    warns.append(("r","Yüksek Volatilite — Pozisyon boyutunu küçült"))
        if not smc.get("htf_ok",True): warns.append(("r","HTF-LTF Uyumsuz — İşlem riskli!"))
        if sq:       warns.append(("y","Squeeze Sıkışması — Büyük hamle bekleniyor"))
        if not warns: warns.append(("g","Kritik uyarı yok — Normal koşullar"))

        # ── Strateji Planı
        mss_ok = smc.get("mss_b") or smc.get("mss_s")
        bos_ok = smc.get("bos_b") or smc.get("bos_s")
        has_ob = bool(smc.get("bull_obs") if is_bull else smc.get("bear_obs"))
        tp3 = smc.get("tp3",price); sl_p = smc.get("sl_p",price)

        if is_bull and ema9>ema21 and (mss_ok or bos_ok) and has_ob:
            st_type="LONG"; st_cls="strat-l"; st_c="#00ff88"
            st_d="Trend Takibi / Uzun Vade LONG Strateji"
            st_sub=f"• Hedef: {fmt(tp3,dp)}\n• SL: {fmt(sl_p,dp)}\n• {('MSS+OB Confluence' if mss_ok else 'BOS+OB Giriş')}"
        elif not is_bull and ema9<ema21 and (mss_ok or bos_ok) and has_ob:
            st_type="SHORT"; st_cls="strat-s"; st_c="#ff3355"
            st_d="Trend Takibi / Uzun Vade SHORT Strateji"
            st_sub=f"• Hedef: {fmt(tp3,dp)}\n• SL: {fmt(sl_p,dp)}\n• {('MSS+OB Confluence' if mss_ok else 'BOS+OB Giriş')}"
        else:
            st_type="BEKLE"; st_cls="strat-n"; st_c="#ffd600"
            st_d="Konsolidasyon / Bekleme Modu"
            st_sub="• Net yön sinyali yok\n• Yeni yapı kırılması bekle\n• Pozisyon açma"

        risk_pts = sum([rsi>75, rsi<25, atp>4, not smc.get("htf_ok",True), not has_ob, vr<0.5])
        risk_rec = round(max(0.5, 3 - risk_pts*0.5), 1)

        # ── Indicator table
        ind = {
            "EMA9":    (fmt(ema9,dp),  "Alış" if price>ema9 else "Satış",   price>ema9),
            "SMA200":  (fmt(sma200,dp),"Alış" if price>sma200 else "Satış", price>sma200),
            "ADX":     (f"{adx:.1f}",  "Güçlü Trend" if adx>=25 else "Zayıf", adx>=25),
            "RSI":     (f"{rsi:.1f}",  "Aşırı Alım" if rsi>70 else "Aşırı Satım" if rsi<30 else "Nötr",
                        30<rsi<70),
            "MACD":    (f"{macd:.4f}", "Alış" if macd>0 else "Satış", macd>0),
            "Bollinger":(fmt(bb_up,dp),"Alış" if price>bb_mid else "Satış", price>bb_mid),
            "EMA50":   (fmt(ema50,dp), "Alış" if price>ema50 else "Satış", price>ema50),
            "CCI":     (f"{cci:.1f}",  "Alış" if cci>0 else "Satış", cci>0),
            "MFI":     (f"{mfi:.1f}",  "Nötr" if 40<mfi<60 else "Alış" if mfi<40 else "Satış",
                        40<mfi<60),
            "Momentum":(f"{mom:.2f}",  "Alış" if mom>0 else "Satış", mom>0),
            "DI+/DI-": (f"{cv(df,'di_p',25):.1f}/{cv(df,'di_m',25):.1f}",
                        "Alış" if dmi>0 else "Satış", dmi>0),
            "Will %R": (f"{willr:.1f}","Aşırı Satım" if willr<-80 else "Aşırı Alım" if willr>-20 else "Nötr",
                        -80<willr<-20),
        }

        return dict(
            trend_d=trend_d, tc=tc, tg_d=tg_d, tg_c=tg_c, tg_lbl=tg_lbl,
            vol_d=vol_d, vol_c=vol_c, mom_d=mom_d, mom_c=mom_c,
            mfi_d=mfi_d, mfi_c=mfi_c, hacim_d=hacim_d, h_c=h_c,
            htf_d=htf_d, htf_c2=htf_c2, htf_rsi_d=htf_rsi_d,
            warns=warns, st_type=st_type, st_cls=st_cls, st_c=st_c,
            st_d=st_d, st_sub=st_sub, risk_pts=risk_pts, risk_rec=risk_rec,
            ema9=ema9, ema21=ema21, ema50=ema50, sma200=sma200,
            adx=adx, rsi=rsi, macd=macd, bb_up=bb_up, mfi=mfi, ind=ind,
        )
    except Exception as e:
        elog("build_strategy", e)
        return {}


# ═══════════════════════════════════════════════════
#  CHART ENGINE — TAMAMEN DÜZELTİLMİŞ
#  (shapes listesi ile, row= parametresi YOK)
# ═══════════════════════════════════════════════════
# ── Shape helpers (Plotly fallback — backtest için) ─────────────────────
def _hline(y, color, w=1.0, dash="dash", row=1):
    """Yatay çizgi — Plotly shape dict"""
    yref = "y" if row == 1 else f"y{row}"
    return dict(type="line", xref="paper", yref=yref,
                x0=0, x1=1, y0=y, y1=y, line=dict(color=color, width=w, dash=dash))

def _hrect(y0, y1, color, row=1):
    """Yatay bant — Plotly shape dict"""
    yref = "y" if row == 1 else f"y{row}"
    return dict(type="rect", xref="paper", yref=yref, x0=0, x1=1, y0=y0, y1=y1,
                fillcolor=color, line=dict(width=0), layer="below")

def _xrect(x0, x1, color):
    """Dikey bant — Plotly shape dict"""
    return dict(type="rect", xref="x", yref="paper", x0=x0, x1=x1, y0=0, y1=1,
                fillcolor=color, line=dict(width=0), layer="below")


def build_chart(df, smc, sym,
                show_ema=True, show_bb=False, show_vwap=False, show_stoch=False,
                show_kz=True, show_fibs=True, show_ob=True, show_fvg=True,
                show_liq=True, show_mss=True, show_bp=True, dp=2,
                height=720, show_ha=False):
    """
    TradingView Lightweight Charts v4 — tam profesyonel ICT/SMC grafik.

    Yenilikler (v5.1):
    • iterrows() kaldırıldı — tüm seriler vektörel numpy ile ~10x hızlı
    • OB/FVG gerçek band dolgusu: addLineSeries upper+lower çifti +
      topColor/bottomColor gradient fill (priceline değil, alan serisi)
    • Heikin-Ashi modu: show_ha=True ile aktif
    • Kill Zone bantları JS tarafında çizilir (Python döngüsü yok)
    • Whale hacim rengi direkt VOLS dizisine numpy ile işlenir
    """
    if df is None or df.empty or len(df) < 5:
        return "<div style='color:#ff3355;padding:20px;font-size:11px;'>Veri yüklenemedi</div>"
    if not smc:
        smc = {}
    try:
        import json as _json
        is_bull = smc.get("is_bull", True)
        price   = float(df["close"].iloc[-1])

        # ── 1. CANDLE VERİSİ — vektörel ────────────────────────
        ts_arr = (pd.to_datetime(df["time"]).astype("int64") // 1_000_000_000).values
        o_arr  = pd.to_numeric(df["open"],   errors="coerce").values
        h_arr  = pd.to_numeric(df["high"],   errors="coerce").values
        l_arr  = pd.to_numeric(df["low"],    errors="coerce").values
        c_arr  = pd.to_numeric(df["close"],  errors="coerce").values
        v_arr  = pd.to_numeric(df.get("volume", pd.Series([0]*len(df))), errors="coerce").fillna(0).values

        # Heikin-Ashi dönüşümü
        if show_ha:
            ha_c = (o_arr + h_arr + l_arr + c_arr) / 4
            ha_o = ha_c.copy()
            for i in range(1, len(ha_o)):
                ha_o[i] = (ha_o[i-1] + ha_c[i-1]) / 2
            ha_h = np.maximum.reduce([h_arr, ha_o, ha_c])
            ha_l = np.minimum.reduce([l_arr, ha_o, ha_c])
            o_arr, h_arr, l_arr, c_arr = ha_o, ha_h, ha_l, ha_c

        mask = (np.isfinite(o_arr) & np.isfinite(h_arr) &
                np.isfinite(l_arr) & np.isfinite(c_arr))
        ts_f  = ts_arr[mask].tolist()
        bull_m = (c_arr[mask] >= o_arr[mask])

        candles = [
            {"time": int(t), "open": float(o), "high": float(h),
             "low": float(l), "close": float(c)}
            for t, o, h, l, c in zip(
                ts_f,
                o_arr[mask].tolist(), h_arr[mask].tolist(),
                l_arr[mask].tolist(), c_arr[mask].tolist())
        ]
        vols = [
            {"time": int(t),
             "value": float(v),
             "color": "rgba(0,255,136,0.45)" if b else "rgba(255,51,85,0.45)"}
            for t, v, b in zip(ts_f, v_arr[mask].tolist(), bull_m.tolist())
        ]

        # ── 2. EMA/BB/VWAP/STOCH — _series_to_pts ile ───────────
        ema_data = []
        if show_ema:
            for col, color, w, lbl in [
                ("ema9","#00d4ff",1.0,"EMA9"), ("ema21","#a855f7",0.9,"EMA21"),
                ("ema50","#ffd600",0.8,"EMA50"), ("sma200","#ff6b35",0.8,"SMA200"),
            ]:
                pts = _series_to_pts(df, col)
                if pts: ema_data.append({"data":pts,"color":color,"lineWidth":w,"label":lbl})

        bb_data = []
        if show_bb:
            for col, color in [("bb_up","rgba(0,180,210,0.55)"),
                                ("bb_mid","rgba(0,180,210,0.25)"),
                                ("bb_lo","rgba(0,180,210,0.55)")]:
                pts = _series_to_pts(df, col)
                if pts: bb_data.append({"data":pts,"color":color,"lineWidth":0.7})

        vwap_data = []
        if show_vwap:
            pts = _series_to_pts(df, "vwap")
            if pts: vwap_data = [{"data":pts,"color":"rgba(255,107,53,0.75)","lineWidth":1.2}]

        stoch_data = []
        if show_stoch:
            for col, color in [("stoch_k","#00d4ff"),("stoch_d","#a855f7")]:
                pts = _series_to_pts(df, col)
                if pts: stoch_data.append({"data":pts,"color":color,"lineWidth":0.9})

        # ── 3. PRICE LINES (TP, SL, Liq, PDH/PDL, EQ) ──────────
        plines = []
        def _pl(val, color, label, width=1.0, style="dashed"):
            try:
                v = float(val or 0)
                if v > 0 and abs(v - price) / max(price, 1e-9) < 0.6:
                    plines.append({"price":v,"color":color,"width":width,"label":label,"style":style})
            except: pass

        _pl(smc.get("tp3"), "#00ff88",            "TP3", 1.4)
        _pl(smc.get("tp2"), "rgba(0,255,136,0.7)", "TP2", 1.1)
        _pl(smc.get("tp1"), "rgba(0,255,136,0.5)", "TP1", 0.9)
        _pl(smc.get("sl_p"),"#ff3355",             "SL",  1.2)
        if show_liq:
            _pl(smc.get("bsl"), "#ff3355", "BSL ↑", 1.1, "dashed")
            _pl(smc.get("ssl"), "#00ff88", "SSL ↓", 1.1, "dashed")
            _pl(smc.get("pwh"), "#ffd600", "PWH",   0.8, "dotted")
            _pl(smc.get("pwl"), "#00d4ff", "PWL",   0.8, "dotted")
        _pl(smc.get("pdh"), "#00d4ff", "PDH", 0.7, "dotted")
        _pl(smc.get("pdl"), "#a855f7", "PDL", 0.7, "dotted")
        if smc.get("eq"):
            _pl(smc["eq"], "rgba(255,214,0,0.6)", "EQ", 0.8, "dotted")

        fib_plines = []
        if show_fibs and smc.get("fibs"):
            fc = {"61.8%":"#a855f7","78.6%":"#8b45cc","50%":"#ffd600",
                  "38.2%":"#00d4ff","23.6%":"#4a90a4"}
            for lbl_, val_ in smc["fibs"].items():
                if lbl_ in fc:
                    try:
                        fib_plines.append({"price":float(val_),"color":fc[lbl_],
                                           "label":f"Fib {lbl_}","width":0.5})
                    except: pass

        # ── 4. BAND OVERLAYS — OB, FVG, Premium/Discount ────────
        # Format: {label, upper:[{time,value}], lower:[{time,value}],
        #          fillTop, fillBot, lineColor, labelColor}
        # JS tarafında addAreaSeries(upper) + addLineSeries(lower) ile
        # topColor/bottomColor gradient band dolgusu sağlanır.
        band_zones = []
        tl_ts = int(ts_arr[-1]) if len(ts_arr) else 0
        t0_ts = int(ts_arr[0])  if len(ts_arr) else 0

        def _band(lo, hi, t_start, t_end, fill, border, label, lbl_color):
            """İki noktalı band: [t_start,lo/hi] → [t_end,lo/hi]"""
            if lo <= 0 or hi <= lo: return
            upper = [{"time": t_start, "value": float(hi)},
                     {"time": t_end,   "value": float(hi)}]
            lower = [{"time": t_start, "value": float(lo)},
                     {"time": t_end,   "value": float(lo)}]
            band_zones.append({
                "label": label, "labelColor": lbl_color,
                "upper": upper, "lower": lower,
                "fillTop": fill, "fillBot": fill.replace("0.13","0.0").replace("0.18","0.0").replace("0.07","0.0").replace("0.09","0.0").replace("0.04","0.0"),
                "lineColor": border,
            })

        # Premium / Discount
        hh_ = smc.get("hh", 0); ll_ = smc.get("ll", 0); eq_ = smc.get("eq", 0)
        if hh_ and ll_ and eq_ and float(hh_) > float(ll_):
            _band(float(eq_), float(hh_), t0_ts, tl_ts,
                  "rgba(255,51,85,0.04)", "rgba(255,51,85,0.0)", "PREMIUM", "rgba(255,51,85,0.45)")
            _band(float(ll_), float(eq_), t0_ts, tl_ts,
                  "rgba(0,255,136,0.04)", "rgba(0,255,136,0.0)", "DISCOUNT", "rgba(0,255,136,0.45)")

        # OTE
        if show_fibs:
            ote_lo = smc.get("ote_lo", 0); ote_hi = smc.get("ote_hi", 0)
            if ote_lo and ote_hi and float(ote_lo) < float(ote_hi):
                _band(float(ote_lo), float(ote_hi), t0_ts, tl_ts,
                      "rgba(168,85,247,0.10)", "rgba(168,85,247,0.55)", "OTE 61.8-78.6%", "#a855f7")

        # Order Blocks — gerçek kutu (başlangıç zamanından bugüne)
        if show_ob:
            for obs_list, fill, border, pfx in [
                (smc.get("bull_obs",[]), "rgba(0,255,136,0.13)", "rgba(0,255,136,0.9)", "Bull OB"),
                (smc.get("bear_obs",[]), "rgba(255,51,85,0.13)",  "rgba(255,51,85,0.9)",  "Bear OB"),
            ]:
                for ob in (obs_list or [])[:5]:
                    try:
                        ob_ts = int(pd.Timestamp(str(ob["time"])).timestamp())
                        _band(float(ob["lo"]), float(ob["hi"]), ob_ts, tl_ts,
                              fill, border,
                              f'{pfx} {fmt(float(ob["hi"]), dp)}',
                              border)
                    except: pass

        # FVG
        if show_fvg:
            for fvg_, fill, border, lbl in [
                (smc.get("fvg_b"), "rgba(0,255,136,0.10)", "rgba(0,255,136,0.7)", "Bull FVG"),
                (smc.get("fvg_s"), "rgba(255,51,85,0.10)",  "rgba(255,51,85,0.7)",  "Bear FVG"),
            ]:
                if fvg_:
                    try:
                        idx_ = int(fvg_.get("idx", 0))
                        fvg_ts = int(ts_arr[idx_]) if 0 <= idx_ < len(ts_arr) else t0_ts
                        _band(float(fvg_["lo"]), float(fvg_["hi"]), fvg_ts, tl_ts,
                              fill, border, f'{lbl} {fmt(float(fvg_["hi"]), dp)}', border)
                    except: pass

        # Buy-point / Sell-point ince band
        if show_bp:
            if is_bull and smc.get("bull_obs"):
                bp = float(smc["bull_obs"][0]["mid"])
                _band(bp*0.9975, bp*1.0025, t0_ts, tl_ts,
                      "rgba(0,255,136,0.20)", "rgba(0,255,136,0.95)", "Buy-point A", "#00ff88")
            elif not is_bull and smc.get("bear_obs"):
                sp = float(smc["bear_obs"][0]["mid"])
                _band(sp*0.9975, sp*1.0025, t0_ts, tl_ts,
                      "rgba(255,51,85,0.20)", "rgba(255,51,85,0.95)", "Sell-point A", "#ff3355")

        # ── 5. STRUCT MARKERS (vektörel) ────────────────────────
        struct_markers = []
        if show_mss:
            mss_idx = smc.get("mss_idx")
            if mss_idx is not None:
                yi = int(mss_idx)
                if 0 <= yi < len(ts_arr):
                    struct_markers.append({
                        "time": int(ts_arr[yi]),
                        "position": "belowBar" if is_bull else "aboveBar",
                        "color": "#a855f7",
                        "shape": "arrowUp" if is_bull else "arrowDown",
                        "text": "MSS"
                    })
            for si, _ in (smc.get("sh_pts") or [])[-8:]:
                if 0 <= si < len(ts_arr):
                    struct_markers.append({"time":int(ts_arr[si]),"position":"aboveBar",
                        "color":"rgba(255,51,85,0.7)","shape":"arrowDown","text":""})
            for si, _ in (smc.get("sl_pts") or [])[-8:]:
                if 0 <= si < len(ts_arr):
                    struct_markers.append({"time":int(ts_arr[si]),"position":"belowBar",
                        "color":"rgba(0,255,136,0.7)","shape":"arrowUp","text":""})
            struct_markers.sort(key=lambda x: x["time"])

        # ── 6. BOS / CHoCH çizgileri ────────────────────────────
        bos_lines = []
        for flag, pts_key, color, lbl in [
            ("bos_b",  "sl_pts", "rgba(0,255,136,0.75)", "BOS"),
            ("bos_s",  "sh_pts", "rgba(255,51,85,0.75)",  "BOS"),
            ("choch_b","sl_pts", "rgba(255,165,0,0.80)",  "CHoCH"),
            ("choch_s","sh_pts", "rgba(255,165,0,0.80)",  "CHoCH"),
        ]:
            if smc.get(flag):
                pts = smc.get(pts_key, [])
                idx_off = -2 if "choch" in flag else -1
                if len(pts) >= abs(idx_off):
                    si, sp = pts[idx_off]
                    if 0 <= si < len(ts_arr):
                        bos_lines.append({"t0":int(ts_arr[si]),"t1":tl_ts,
                                          "price":float(sp),"color":color,"label":lbl,"width":1.1})

        # ── 7. WHALE VOL markers ─────────────────────────────────
        whale_marks = []
        if "is_whale" in df.columns and "vol_r" in df.columns:
            wh_mask = (df["is_whale"].values == 1)
            if wh_mask.any():
                wh_ts  = ts_arr[wh_mask].tolist()
                wh_vol = v_arr[wh_mask].tolist()
                whale_marks = [{"time":int(t),"value":float(v),"color":"rgba(168,85,247,0.75)"}
                                for t,v in zip(wh_ts, wh_vol)]

        # ── 8a. TRENDLINES — swing'lerden otomatik ─────────────
        trendlines = []
        if show_mss:
            sh_pts = smc.get("sh_pts", []) or []
            sl_pts = smc.get("sl_pts", []) or []
            # Son 3 swing high → bear trendline
            if len(sh_pts) >= 2:
                pts_sorted = sorted(sh_pts[-4:], key=lambda x: x[0])
                for i in range(len(pts_sorted)-1):
                    i0, p0 = pts_sorted[i]
                    i1, p1 = pts_sorted[i+1]
                    if 0 <= i0 < len(ts_arr) and 0 <= i1 < len(ts_arr):
                        trendlines.append({
                            "t0": int(ts_arr[i0]), "p0": float(p0),
                            "t1": int(ts_arr[i1]), "p1": float(p1),
                            "color": "rgba(255,51,85,0.65)",
                            "width": 1.2, "dash": True,
                            "label": "LH" if p1 < p0 else "HH"
                        })
            # Son 3 swing low → bull trendline
            if len(sl_pts) >= 2:
                pts_sorted = sorted(sl_pts[-4:], key=lambda x: x[0])
                for i in range(len(pts_sorted)-1):
                    i0, p0 = pts_sorted[i]
                    i1, p1 = pts_sorted[i+1]
                    if 0 <= i0 < len(ts_arr) and 0 <= i1 < len(ts_arr):
                        trendlines.append({
                            "t0": int(ts_arr[i0]), "p0": float(p0),
                            "t1": int(ts_arr[i1]), "p1": float(p1),
                            "color": "rgba(0,255,136,0.65)",
                            "width": 1.2, "dash": True,
                            "label": "HL" if p1 > p0 else "LL"
                        })

        # ── 8b. SWING LABELS (HH/HL/LH/LL) ─────────────────────
        swing_labels = []
        if show_mss:
            sh_pts = smc.get("sh_pts", []) or []
            sl_pts = smc.get("sl_pts", []) or []
            sh_prices = [p for _, p in sh_pts]
            sl_prices = [p for _, p in sl_pts]
            for idx2, (si, sp) in enumerate(sh_pts[-6:]):
                if 0 <= si < len(ts_arr):
                    prev_sh = sh_prices[max(0, len(sh_pts)-6+idx2-1)] if idx2 > 0 else sp
                    lbl = "HH" if sp > prev_sh else "LH"
                    swing_labels.append({
                        "time": int(ts_arr[si]), "price": float(sp),
                        "label": lbl, "position": "above",
                        "color": "#ff3355" if lbl == "LH" else "#ffd600"
                    })
            for idx2, (si, sp) in enumerate(sl_pts[-6:]):
                if 0 <= si < len(ts_arr):
                    prev_sl = sl_prices[max(0, len(sl_pts)-6+idx2-1)] if idx2 > 0 else sp
                    lbl = "LL" if sp < prev_sl else "HL"
                    swing_labels.append({
                        "time": int(ts_arr[si]), "price": float(sp),
                        "label": lbl, "position": "below",
                        "color": "#00ff88" if lbl == "HL" else "#3d5a80"
                    })

        # ── 8c. KILLZONE BANTLARI ─────────────────────────────────
        kz_bands = []
        if show_kz and len(ts_arr) > 10:
            # UTC saat → killzone rengi
            kz_map = [
                (2, 5,   "rgba(0,212,255,0.06)", "Tokyo"),
                (8, 12,  "rgba(0,255,136,0.06)", "London"),
                (13,17,  "rgba(255,165,0,0.06)", "NY"),
            ]
            prev_kz = None
            kz_start = None
            kz_color = None
            kz_name = None
            for i, ts in enumerate(ts_arr.tolist()):
                import datetime as _dt
                hour = _dt.datetime.utcfromtimestamp(ts).hour
                matched = None
                for hs, he, color, name in kz_map:
                    if hs <= hour < he:
                        matched = (color, name)
                        break
                if matched and matched != (kz_color, kz_name):
                    if kz_start is not None and kz_color:
                        kz_bands.append({"t0": int(kz_start), "t1": int(ts),
                                         "color": kz_color, "label": kz_name})
                    kz_color, kz_name = matched
                    kz_start = ts
                elif not matched and kz_start is not None:
                    if kz_color:
                        kz_bands.append({"t0": int(kz_start), "t1": int(ts),
                                         "color": kz_color, "label": kz_name})
                    kz_start = None; kz_color = None; kz_name = None
            if kz_start and kz_color:
                kz_bands.append({"t0": int(kz_start), "t1": int(ts_arr[-1]),
                                 "color": kz_color, "label": kz_name})
            # Maksimum son 20 band
            kz_bands = kz_bands[-20:]

        
        # ── 8d. AI ASSİSTAN ÇİZİM VERİSİ ────────────────────────
        # Görüntüdeki gibi: I-BOS, BOS segmentleri, structure bölgeler,
        # premium/discount, OB+FVG label overlay, TP hedef okları
        ai_drawings = []

        def _ai_line(t0, p0, t1, p1, color, width, dash, label="", label_pos="end"):
            """Canvas üzerinde çizilecek bir çizgi segmenti"""
            ai_drawings.append({
                "type": "line",
                "t0": int(t0), "p0": float(p0),
                "t1": int(t1), "p1": float(p1),
                "color": color, "width": width, "dash": dash,
                "label": label, "label_pos": label_pos
            })

        def _ai_box(t0, p_lo, t1, p_hi, fill, border, label="", label_side="right"):
            """Canvas üzerinde çizilecek doldurulmuş kutu"""
            if p_lo >= p_hi: return
            ai_drawings.append({
                "type": "box",
                "t0": int(t0), "t1": int(t1),
                "lo": float(p_lo), "hi": float(p_hi),
                "fill": fill, "border": border,
                "label": label, "label_side": label_side
            })

        def _ai_arrow(t, price, direction, color, label=""):
            """Fiyat seviyesine ok işareti"""
            ai_drawings.append({
                "type": "arrow",
                "time": int(t), "price": float(price),
                "direction": direction,   # "up" | "down"
                "color": color, "label": label
            })

        def _ai_label(t, price, text, color, bg="rgba(4,8,16,0.85)", align="center"):
            """Grafik üzerinde etiket kutusu"""
            ai_drawings.append({
                "type": "label",
                "time": int(t), "price": float(price),
                "text": text, "color": color, "bg": bg, "align": align
            })

        sh_pts  = smc.get("sh_pts", []) or []
        sl_pts  = smc.get("sl_pts", []) or []
        is_bull = smc.get("is_bull", True)

        # ── I-BOS / BOS segmentleri (görüntüdeki gibi dashed) ──
        # Her iki ardışık swing high/low arasında I-BOS çizgisi
        for pts_list, col in [(sh_pts, "rgba(0,255,255,0.70)"),
                               (sl_pts, "rgba(0,255,136,0.70)")]:
            prev_pts = sorted(pts_list[-6:], key=lambda x: x[0])
            for k in range(len(prev_pts)-1):
                i0, p0_ = prev_pts[k]
                i1, p1_ = prev_pts[k+1]
                if 0 <= i0 < len(ts_arr) and 0 <= i1 < len(ts_arr):
                    mid_p = (p0_ + p1_) / 2
                    # I-BOS segmenti (yatay kesik çizgi)
                    _ai_line(ts_arr[i0], p0_, ts_arr[i1], p0_,
                             col, 1.2, True, "I-BoS", "mid")
                    # Trend çizgisi (eğimli)
                    _ai_line(ts_arr[i0], p0_, ts_arr[i1], p1_,
                             col.replace("0.70","0.35"), 0.8, True)

        # ── BOS kırılımı kutusu ─────────────────────────────────
        if smc.get("bos_b") and sl_pts:
            si, sp = sl_pts[-1]
            if 0 <= si < len(ts_arr):
                _ai_box(ts_arr[si], sp * 0.997, tl_ts, sp * 1.0005,
                        "rgba(0,255,136,0.08)", "rgba(0,255,136,0.60)", "BOS ↑")
                _ai_label(tl_ts, sp, "BOS", "#00ff88",
                          "rgba(0,255,136,0.15)", "right")

        if smc.get("bos_s") and sh_pts:
            si, sp = sh_pts[-1]
            if 0 <= si < len(ts_arr):
                _ai_box(ts_arr[si], sp * 0.9995, tl_ts, sp * 1.003,
                        "rgba(255,51,85,0.08)", "rgba(255,51,85,0.60)", "BOS ↓")
                _ai_label(tl_ts, sp, "BOS", "#ff3355",
                          "rgba(255,51,85,0.15)", "right")

        # ── CHoCH kutusu ────────────────────────────────────────
        if smc.get("choch_b") and sl_pts and len(sl_pts) >= 2:
            si, sp = sl_pts[-2]
            if 0 <= si < len(ts_arr):
                _ai_line(ts_arr[si], sp, tl_ts, sp,
                         "rgba(255,165,0,0.80)", 1.4, True, "CHoCH", "end")
        if smc.get("choch_s") and sh_pts and len(sh_pts) >= 2:
            si, sp = sh_pts[-2]
            if 0 <= si < len(ts_arr):
                _ai_line(ts_arr[si], sp, tl_ts, sp,
                         "rgba(255,165,0,0.80)", 1.4, True, "CHoCH", "end")

        # ── MSS ok işareti ──────────────────────────────────────
        mss_idx = smc.get("mss_idx")
        if mss_idx is not None:
            yi = int(mss_idx)
            if 0 <= yi < len(ts_arr):
                mss_p = float(l_arr[yi]) if is_bull else float(h_arr[yi])
                _ai_arrow(ts_arr[yi], mss_p,
                          "up" if is_bull else "down",
                          "#a855f7", "MSS")

        # ── TP hedef okları & çizgileri ─────────────────────────
        if smc.get("tp3"):
            _ai_line(tl_ts - (tl_ts - t0_ts) // 4, float(price),
                     tl_ts + 3600, float(smc["tp3"]),
                     "rgba(0,255,136,0.55)", 1.5, True, "TP3✓", "end")
        if smc.get("tp2"):
            _ai_line(tl_ts - (tl_ts - t0_ts) // 6, float(price),
                     tl_ts + 3600, float(smc["tp2"]),
                     "rgba(0,255,136,0.38)", 1.0, True, "TP2", "end")
        if smc.get("sl_p"):
            _ai_line(tl_ts - (tl_ts - t0_ts) // 6, float(price),
                     tl_ts + 3600, float(smc["sl_p"]),
                     "rgba(255,51,85,0.55)", 1.0, True, "SL", "end")

        # ── Premium / Discount zone etiketli ───────────────────
        hh_ = smc.get("hh", 0); ll_ = smc.get("ll", 0); eq_ = smc.get("eq", 0)
        if hh_ and ll_ and eq_:
            # Premium
            _ai_label(t0_ts + (tl_ts - t0_ts) // 2,
                      float(hh_) * 0.999,
                      "PREMIUM ZONE", "rgba(255,51,85,0.60)",
                      "rgba(255,51,85,0.08)")
            # Discount
            _ai_label(t0_ts + (tl_ts - t0_ts) // 2,
                      float(ll_) * 1.001,
                      "DISCOUNT ZONE", "rgba(0,255,136,0.60)",
                      "rgba(0,255,136,0.08)")
            # EQ seviyesi
            _ai_line(t0_ts, float(eq_), tl_ts, float(eq_),
                     "rgba(255,214,0,0.45)", 0.8, True, "EQ 50%", "end")

        # ── FVG çizimi (box + zaman etiketi) ───────────────────
        if show_fvg:
            if smc.get("fvg_b"):
                fvg = smc["fvg_b"]
                fidx = int(fvg.get("idx", 0))
                if 0 <= fidx < len(ts_arr):
                    _ai_label(ts_arr[fidx], float(fvg["hi"]),
                              f'FVG {fmt(float(fvg["hi"]), dp)}',
                              "#00ff88", "rgba(0,255,136,0.12)")
            if smc.get("fvg_s"):
                fvg = smc["fvg_s"]
                fidx = int(fvg.get("idx", 0))
                if 0 <= fidx < len(ts_arr):
                    _ai_label(ts_arr[fidx], float(fvg["lo"]),
                              f'FVG {fmt(float(fvg["lo"]), dp)}',
                              "#ff3355", "rgba(255,51,85,0.12)")

        # ── OB kutu etiketi (görüntüdeki OB 122.1 gibi) ────────
        if show_ob:
            for obs_list, col in [
                (smc.get("bull_obs", []), "#00ff88"),
                (smc.get("bear_obs", []), "#ff3355"),
            ]:
                for ob in (obs_list or [])[:3]:
                    try:
                        ob_ts = int(pd.Timestamp(str(ob["time"])).timestamp())
                        hi_   = float(ob["hi"])
                        _ai_label(ob_ts, hi_,
                                  f'OB {fmt(hi_, dp)}',
                                  col,
                                  f"rgba({'0,255,136' if col=='#00ff88' else '255,51,85'},0.12)")
                    except: pass

        # ── Fibonacci seviyeleri (yatay çizgi + etiket) ────────
        if show_fibs and smc.get("fibs"):
            fib_colors = {
                "23.6%": "rgba(0,212,255,0.60)",
                "38.2%": "rgba(0,212,255,0.70)",
                "50%":   "rgba(255,214,0,0.70)",
                "61.8%": "rgba(168,85,247,0.80)",
                "78.6%": "rgba(168,85,247,0.90)",
            }
            for lbl_, val_ in smc["fibs"].items():
                try:
                    v_ = float(val_)
                    col_ = fib_colors.get(lbl_, "rgba(255,255,255,0.40)")
                    _ai_line(t0_ts, v_, tl_ts, v_,
                             col_.replace("0.60","0.35").replace("0.70","0.35")
                             .replace("0.80","0.35").replace("0.90","0.35"),
                             0.7, True, lbl_, "end")
                except: pass

        # ── 8. JSON ──────────────────────────────────────────────
        j = _json.dumps
        vol_h   = 115
        stoch_h = 100 if show_stoch else 0
        main_h  = height - vol_h - stoch_h - 6

        badge_col  = "#00ff88" if is_bull else "#ff3355"
        badge_bg   = "rgba(0,255,136,0.12)" if is_bull else "rgba(255,51,85,0.12)"
        badge_text = "LONG — BULLISH" if is_bull else "SHORT — BEARISH"

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#040810;overflow:hidden;font-family:'JetBrains Mono',monospace;}}
#wrap{{display:flex;flex-direction:column;width:100%;height:{height}px;background:#040810;position:relative;}}
#main{{width:100%;height:{main_h}px;}}
#vol{{width:100%;height:{vol_h}px;border-top:1px solid #091525;}}
#stoch{{width:100%;height:{stoch_h}px;border-top:1px solid #091525;display:{('block' if show_stoch else 'none')};}}
#xhair{{position:absolute;top:6px;right:5px;z-index:20;background:rgba(4,8,16,0.93);
  border:1px solid #0d1e30;border-radius:5px;padding:5px 10px;font-size:9px;
  color:#cdd6f4;pointer-events:none;min-width:215px;line-height:1.9;}}
#badge{{position:absolute;top:6px;left:50%;transform:translateX(-50%);z-index:20;
  background:{badge_bg};border:1.5px solid {badge_col};border-radius:20px;padding:3px 16px;
  font-size:9.5px;font-weight:700;letter-spacing:1.5px;color:{badge_col};pointer-events:none;}}
#legend{{position:absolute;top:6px;left:8px;z-index:20;background:rgba(4,8,16,0.85);
  border:1px solid #0d1e30;border-radius:5px;padding:4px 8px;font-size:8.5px;
  color:#3d5a80;pointer-events:none;line-height:1.9;}}
#hamode{{position:absolute;bottom:130px;right:5px;z-index:20;font-size:7.5px;
  color:{"#ffd600" if show_ha else "#1a2a3a"};}}
#ai-badge{{position:absolute;bottom:6px;left:8px;z-index:20;
  background:rgba(168,85,247,0.10);border:1px solid rgba(168,85,247,0.30);
  border-radius:12px;padding:3px 10px;font-size:7px;font-weight:700;
  color:rgba(168,85,247,0.80);pointer-events:none;letter-spacing:.8px;}}
</style></head><body>
<div id="wrap">
  <div id="legend"></div>
  <div id="badge">{badge_text}</div>
  <div id="hamode">{"HA" if show_ha else ""}</div>
  <div id="ai-badge">🤖 AI ÇİZİMLER AKTİF</div>
  <div id="xhair">
    <div id="ch-sym" style="color:#00d4ff;font-weight:700;font-size:10px;">{sym}</div>
    <div id="ch-ohlc"></div><div id="ch-chg"></div><div id="ch-vol"></div>
  </div>
  <div id="main"></div><div id="vol"></div><div id="stoch"></div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
<script>
const CANDLES={j(candles)};
const VOLS={j(vols)};
const EMAS={j(ema_data)};
const BBS={j(bb_data)};
const VWAPS={j(vwap_data)};
const STOCHS={j(stoch_data)};
const PLINES={j(plines)};
const FIBLINES={j(fib_plines)};
const BAND_ZONES={j(band_zones)};
const MARKERS={j(struct_markers)};
const BOS_LINES={j(bos_lines)};
const WHALE_MARKS={j(whale_marks)};
const TRENDLINES={j(trendlines)};
const SWING_LABELS={j(swing_labels)};
const KZ_BANDS={j(kz_bands)};
const AI_DRAWINGS={j(ai_drawings)};
const IS_BULL={j(is_bull)};
const DP={dp};
const SHOW_STOCH={j(show_stoch)};
const SYM={j(str(sym))};

const BASE={{
  layout:{{background:{{type:"Solid",color:"#040810"}},textColor:"#3d5a80",fontSize:9}},
  grid:{{vertLines:{{color:"#091525"}},horzLines:{{color:"#091525"}}}},
  crosshair:{{mode:LightweightCharts.CrosshairMode.Normal,
    vertLine:{{color:"rgba(0,212,255,0.4)",width:0.8,style:1,labelBackgroundColor:"#0a1628"}},
    horzLine:{{color:"rgba(0,212,255,0.4)",width:0.8,style:1,labelBackgroundColor:"#0a1628"}}}},
  timeScale:{{timeVisible:true,secondsVisible:false,borderColor:"#091525",
    tickMarkFormatter:t=>{{const d=new Date(t*1000);
      return (d.getUTCMonth()+1)+"/"+d.getUTCDate()+" "+
             String(d.getUTCHours()).padStart(2,"0")+":"+String(d.getUTCMinutes()).padStart(2,"0");}}}},
  rightPriceScale:{{borderColor:"#091525",textColor:"#3d5a80"}},
  handleScroll:{{mouseWheel:true,pressedMouseMove:true}},
  handleScale:{{mouseWheel:true,pinch:true}},
}};

// ── Ana grafik
const MC=LightweightCharts.createChart(document.getElementById("main"),
  Object.assign({{}},BASE,{{
    width:document.getElementById("main").clientWidth,height:{main_h},
    rightPriceScale:{{...BASE.rightPriceScale,scaleMargins:{{top:0.04,bottom:0.04}}}},
    watermark:{{visible:true,fontSize:10,horzAlign:"left",vertAlign:"top",
                color:"rgba(0,212,255,0.07)",text:SYM+"  APEX PRO v10.0  ICT/SMC"}},
  }}));

// ── Mum serisi
const CS=MC.addCandlestickSeries({{
  upColor:"#00ff88",downColor:"#ff3355",
  borderUpColor:"#00ff88",borderDownColor:"#ff3355",
  wickUpColor:"rgba(0,255,136,0.6)",wickDownColor:"rgba(255,51,85,0.6)",
}});
CS.setData(CANDLES);
CS.setMarkers(MARKERS);

// ── Price lines: TP/SL/Liq/PDH/PDL
const SM={{dashed:1,dotted:2,solid:0}};
PLINES.forEach(pl=>CS.createPriceLine({{price:pl.price,color:pl.color,
  lineWidth:pl.width||1,lineStyle:SM[pl.style]||1,axisLabelVisible:true,title:pl.label||""}}));
FIBLINES.forEach(fl=>CS.createPriceLine({{price:fl.price,color:fl.color,
  lineWidth:fl.width||0.5,lineStyle:2,axisLabelVisible:true,title:fl.label}}));
BOS_LINES.forEach(bl=>CS.createPriceLine({{price:bl.price,color:bl.color,
  lineWidth:bl.width||1,lineStyle:1,axisLabelVisible:true,title:bl.label||""}}));

// ── BAND ZONES — OB/FVG/OTE gerçek kutu dolgusu
// Her zone için: üst + alt priceline (sınır) + araya canvas fillRect (dolgu)
// Bu LWC v4'te zone dolgusu için en kararlı yöntem
const _bzCanvas = document.createElement("canvas");
_bzCanvas.style.cssText = "position:absolute;top:0;left:0;pointer-events:none;z-index:5;";
document.getElementById("main").style.position = "relative";
document.getElementById("main").appendChild(_bzCanvas);

function _drawBandZones() {{
  const mainEl = document.getElementById("main");
  _bzCanvas.width  = mainEl.clientWidth;
  _bzCanvas.height = mainEl.clientHeight;
  const ctx = _bzCanvas.getContext("2d");
  ctx.clearRect(0, 0, _bzCanvas.width, _bzCanvas.height);

  BAND_ZONES.forEach(bz => {{
    try {{
      const yTop = MC.priceToCoordinate(bz.upper[0].value);
      const yBot = MC.priceToCoordinate(bz.lower[0].value);
      const xL   = MC.timeScale().timeToCoordinate(bz.upper[0].time);
      const xR   = MC.timeScale().timeToCoordinate(bz.upper[bz.upper.length-1].time);
      if (yTop == null || yBot == null || xL == null || xR == null) return;
      const x0 = Math.max(0, Math.min(xL, xR));
      const x1 = Math.max(xL, xR, _bzCanvas.width);
      const y0 = Math.min(yTop, yBot);
      const y1 = Math.max(yTop, yBot);

      // Dolgu
      ctx.fillStyle = bz.fillTop;
      ctx.fillRect(x0, y0, x1 - x0, y1 - y0);

      // Üst sınır
      ctx.strokeStyle = bz.lineColor;
      ctx.lineWidth = 1.5;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(x0, yTop); ctx.lineTo(x1, yTop);
      ctx.stroke();

      // Alt sınır
      ctx.beginPath();
      ctx.moveTo(x0, yBot); ctx.lineTo(x1, yBot);
      ctx.stroke();

      // Etiket (sağ tarafa)
      if (bz.label) {{
        ctx.font = "bold 8px 'JetBrains Mono',monospace";
        ctx.fillStyle = bz.labelColor || bz.lineColor;
        ctx.textAlign = "right";
        ctx.fillText(bz.label, x1 - 4, yTop - 3);
      }}
    }} catch(e) {{}}
  }});
}}

// İlk çizim + her scroll/scale/resize'da yeniden çiz
MC.timeScale().subscribeVisibleTimeRangeChange(_drawBandZones);
MC.subscribeCrosshairMove(_drawBandZones);
setTimeout(_drawBandZones, 200);

// ══════════════════════════════════════════════════
//  TRENDLINES + SWING LABELS + KILLZONE BANTLARI
//  Canvas overlay — gerçek TradingView görünümü
// ══════════════════════════════════════════════════

// Trendline + Swing canvas (band canvas'ının üstünde)
// ── roundRect polyfill (eski tarayıcı/Electron desteği) ────────
if(!CanvasRenderingContext2D.prototype.roundRect){{
  CanvasRenderingContext2D.prototype.roundRect=function(x,y,w,h,r){{
    r=Math.min(r||0,Math.abs(w)/2,Math.abs(h)/2);
    this.beginPath();
    this.moveTo(x+r,y);
    this.arcTo(x+w,y,x+w,y+h,r);this.arcTo(x+w,y+h,x,y+h,r);
    this.arcTo(x,y+h,x,y,r);this.arcTo(x,y,x+w,y,r);
    this.closePath();return this;
  }};
}}
const _tlCanvas = document.createElement("canvas");
_tlCanvas.style.cssText = "position:absolute;top:0;left:0;pointer-events:none;z-index:6;";
document.getElementById("main").appendChild(_tlCanvas);

function _drawTrendlines() {{
  const mainEl = document.getElementById("main");
  _tlCanvas.width  = mainEl.clientWidth;
  _tlCanvas.height = mainEl.clientHeight;
  const ctx = _tlCanvas.getContext("2d");
  ctx.clearRect(0, 0, _tlCanvas.width, _tlCanvas.height);

  // ── KillZone arka plan bantları ──────────────────
  KZ_BANDS.forEach(kz => {{
    try {{
      const x0 = MC.timeScale().timeToCoordinate(kz.t0);
      const x1 = MC.timeScale().timeToCoordinate(kz.t1);
      if (x0 == null || x1 == null) return;
      ctx.fillStyle = kz.color;
      ctx.fillRect(Math.min(x0,x1), 0, Math.abs(x1-x0), _tlCanvas.height);
      // KZ etiketi
      ctx.font = "bold 7px 'JetBrains Mono',monospace";
      ctx.fillStyle = kz.color.replace("0.06","0.55");
      ctx.textAlign = "left";
      ctx.fillText(kz.label, Math.min(x0,x1)+2, 10);
    }} catch(e) {{}}
  }});

  // ── Trendlines (dashed) ──────────────────────────
  TRENDLINES.forEach(tl => {{
    try {{
      const x0 = MC.timeScale().timeToCoordinate(tl.t0);
      const x1 = MC.timeScale().timeToCoordinate(tl.t1);
      const y0 = MC.priceToCoordinate(tl.p0);
      const y1 = MC.priceToCoordinate(tl.p1);
      if (x0==null||x1==null||y0==null||y1==null) return;

      // Trendi ekran dışına uzat (ince projeksiyon)
      const dx = x1 - x0;
      const dy = y1 - y0;
      const ext = _tlCanvas.width;  // uzatma miktarı (piksel)
      const ratio = dx !== 0 ? ext/Math.abs(dx) : 0;
      const xExt = x1 + dx * ratio;
      const yExt = y1 + dy * ratio;

      ctx.strokeStyle = tl.color;
      ctx.lineWidth = tl.width || 1.2;
      ctx.setLineDash(tl.dash ? [6, 3] : []);
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(xExt, yExt);
      ctx.stroke();
      ctx.setLineDash([]);

      // Trendline etiketi — uç noktada
      if (tl.label) {{
        ctx.font = "bold 8px 'JetBrains Mono',monospace";
        ctx.fillStyle = tl.color;
        ctx.textAlign = "right";
        ctx.fillText(tl.label, x1 - 3, y1 - 4);
      }}
    }} catch(e) {{}}
  }});

  // ── Swing Labels (HH / HL / LH / LL) ────────────
  SWING_LABELS.forEach(sl => {{
    try {{
      const x = MC.timeScale().timeToCoordinate(sl.time);
      const y = MC.priceToCoordinate(sl.price);
      if (x==null || y==null) return;

      const above = sl.position === "above";
      const py = above ? y - 14 : y + 10;

      // Pill background
      const lw = ctx.measureText(sl.label).width + 8;
      ctx.fillStyle = sl.color + "22";
      ctx.strokeStyle = sl.color;
      ctx.lineWidth = 0.8;
      ctx.beginPath();
      ctx.roundRect(x - lw/2, py - 9, lw, 12, 3);
      ctx.fill();
      ctx.stroke();

      // Label text
      ctx.font = "bold 7.5px 'JetBrains Mono',monospace";
      ctx.fillStyle = sl.color;
      ctx.textAlign = "center";
      ctx.fillText(sl.label, x, py);

      // Vertical tick to candle
      ctx.strokeStyle = sl.color + "66";
      ctx.lineWidth = 0.6;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      ctx.moveTo(x, above ? py + 4 : py - 14);
      ctx.lineTo(x, y);
      ctx.stroke();
      ctx.setLineDash([]);
    }} catch(e) {{}}
  }});
}}

// Subscribe to redraw on all chart changes
MC.timeScale().subscribeVisibleTimeRangeChange(_drawTrendlines);
MC.subscribeCrosshairMove(_drawTrendlines);
setTimeout(_drawTrendlines, 250);

// ══════════════════════════════════════════════════════
//  🤖 AI ASSİSTAN ÇİZİM MOTORU
//  I-BOS, BOS, CHoCH, MSS, TP/SL okları, OB/FVG etiketleri
//  Görüntüdeki profesyonel ICT chart overlay
// ══════════════════════════════════════════════════════

const _aiCanvas = document.createElement("canvas");
_aiCanvas.style.cssText = "position:absolute;top:0;left:0;pointer-events:none;z-index:8;";
document.getElementById("main").appendChild(_aiCanvas);

// ── Yardımcı: fiyat+zaman → koordinat ─────────────────
function _pc(p)  {{ return MC.priceToCoordinate(p); }}
function _tc(t)  {{ return MC.timeScale().timeToCoordinate(t); }}

function _drawAI() {{
  const el = document.getElementById("main");
  _aiCanvas.width  = el.clientWidth;
  _aiCanvas.height = el.clientHeight;
  const ctx = _aiCanvas.getContext("2d");
  ctx.clearRect(0,0,_aiCanvas.width,_aiCanvas.height);

  // ── roundRect polyfill ─────────────────────────────
  if(!ctx.roundRect){{
    ctx.roundRect=function(x,y,w,h,r){{
      r=Math.min(r||3,Math.abs(w)/2,Math.abs(h)/2);
      this.beginPath();
      this.moveTo(x+r,y);
      this.arcTo(x+w,y,x+w,y+h,r);this.arcTo(x+w,y+h,x,y+h,r);
      this.arcTo(x,y+h,x,y,r);this.arcTo(x,y,x+w,y,r);
      this.closePath();return this;
    }};
  }}

  AI_DRAWINGS.forEach(d => {{
    try {{
      if (d.type === "line") {{
        // ── Çizgi segmenti ─────────────────────────
        const x0 = _tc(d.t0), y0 = _pc(d.p0);
        const x1 = _tc(d.t1), y1 = _pc(d.p1);
        if (x0==null||y0==null||x1==null||y1==null) return;

        ctx.save();
        ctx.strokeStyle = d.color;
        ctx.lineWidth   = d.width || 1;
        ctx.setLineDash(d.dash ? [8,4] : []);
        ctx.shadowColor = d.color;
        ctx.shadowBlur  = d.width > 1.3 ? 4 : 0;
        ctx.beginPath();
        ctx.moveTo(x0,y0);
        ctx.lineTo(x1,y1);
        ctx.stroke();
        ctx.restore();

        // Etiket
        if (d.label) {{
          const lx = d.label_pos === "mid" ? (x0+x1)/2 : x1;
          const ly = d.label_pos === "mid" ? (y0+y1)/2 : y1;
          ctx.save();
          ctx.font = "bold 8px 'JetBrains Mono',monospace";
          const tw = ctx.measureText(d.label).width;
          ctx.fillStyle = d.color.replace(/[\\d.]+\\)$/,"0.18)");
          ctx.beginPath();
          ctx.roundRect(lx-tw/2-4, ly-10, tw+8, 13, 3);
          ctx.fill();
          ctx.fillStyle = d.color;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(d.label, lx, ly-3);
          ctx.restore();
        }}

      }} else if (d.type === "box") {{
        // ── Doldurulmuş kutu ───────────────────────
        const x0 = _tc(d.t0), x1 = _tc(d.t1);
        const y0 = _pc(d.hi), y1 = _pc(d.lo);
        if (x0==null||x1==null||y0==null||y1==null) return;
        const bx = Math.min(x0,x1), bw = Math.abs(x1-x0);
        const by = Math.min(y0,y1), bh = Math.abs(y1-y0);

        // Gradient fill
        const grad = ctx.createLinearGradient(bx,by,bx,by+bh);
        grad.addColorStop(0, d.fill.replace(/[\\d.]+\\)$/,"0.20)"));
        grad.addColorStop(1, d.fill.replace(/[\\d.]+\\)$/,"0.04)"));
        ctx.fillStyle = grad;
        ctx.fillRect(bx,by,bw,bh);

        // Border (top+bottom)
        ctx.strokeStyle = d.border;
        ctx.lineWidth   = 1.5;
        ctx.setLineDash([]);
        ctx.beginPath(); ctx.moveTo(bx,by);   ctx.lineTo(bx+bw,by);   ctx.stroke();
        ctx.beginPath(); ctx.moveTo(bx,by+bh); ctx.lineTo(bx+bw,by+bh); ctx.stroke();
        // Sol kenar ince
        ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.moveTo(bx,by); ctx.lineTo(bx,by+bh); ctx.stroke();

        // Etiket (sağ taraf)
        if (d.label) {{
          ctx.save();
          ctx.font = "bold 8px 'JetBrains Mono',monospace";
          const tw = ctx.measureText(d.label).width;
          ctx.fillStyle = d.border.replace(/[\\d.]+\\)$/,"0.15)");
          ctx.beginPath();
          ctx.roundRect(bx+bw-tw-12, by+2, tw+8, 12, 2);
          ctx.fill();
          ctx.fillStyle = d.border;
          ctx.textAlign = "right";
          ctx.textBaseline = "top";
          ctx.fillText(d.label, bx+bw-5, by+4);
          ctx.restore();
        }}

      }} else if (d.type === "arrow") {{
        // ── Ok işareti (MSS, entry noktaları) ─────
        const x = _tc(d.time), y = _pc(d.price);
        if (x==null||y==null) return;
        const up = d.direction === "up";
        const ay = up ? y + 22 : y - 22;

        ctx.save();
        ctx.fillStyle   = d.color;
        ctx.strokeStyle = d.color;
        ctx.shadowColor = d.color;
        ctx.shadowBlur  = 6;

        // Ok gövdesi
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(x, ay);
        ctx.lineTo(x, y + (up ? -4 : 4));
        ctx.stroke();

        // Ok ucu (üçgen)
        ctx.beginPath();
        ctx.moveTo(x,       up ? y-2 : y+2);
        ctx.lineTo(x-5,     up ? y+7 : y-7);
        ctx.lineTo(x+5,     up ? y+7 : y-7);
        ctx.closePath();
        ctx.fill();

        // Etiket
        if (d.label) {{
          ctx.font = "bold 8.5px 'JetBrains Mono',monospace";
          const tw = ctx.measureText(d.label).width;
          ctx.shadowBlur = 0;
          ctx.fillStyle  = d.color.replace(/[\\d.]+\\)$/,"0.15)") || "rgba(0,0,0,0.5)";
          ctx.beginPath();
          ctx.roundRect(x-tw/2-4, ay-12, tw+8, 12, 3);
          ctx.fill();
          ctx.fillStyle = d.color;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(d.label, x, ay-6);
        }}
        ctx.restore();

      }} else if (d.type === "label") {{
        // ── Etiket kutusu (OB 122.1, FVG 116.5 gibi) ──
        const x = _tc(d.time), y = _pc(d.price);
        if (x==null||y==null) return;

        ctx.save();
        ctx.font = "bold 8px 'JetBrains Mono',monospace";
        const tw = ctx.measureText(d.text).width;
        const bw2 = tw + 10, bh2 = 14;
        const bx2 = d.align === "right" ? _aiCanvas.width - bw2 - 4
                  : d.align === "left"  ? 4
                  : x - bw2/2;
        const by2 = y - bh2/2;

        // Pill background
        ctx.fillStyle = d.bg || "rgba(4,8,16,0.85)";
        ctx.strokeStyle = d.color;
        ctx.lineWidth = 0.8;
        ctx.beginPath();
        ctx.roundRect(bx2, by2, bw2, bh2, 3);
        ctx.fill();
        ctx.stroke();

        // Text
        ctx.fillStyle = d.color;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(d.text, bx2 + bw2/2, by2 + bh2/2);
        ctx.restore();
      }}
    }} catch(e) {{}}
  }});
}}

// Subscribe AI drawing to all chart events
MC.timeScale().subscribeVisibleTimeRangeChange(_drawAI);
MC.subscribeCrosshairMove(_drawAI);
setTimeout(_drawAI, 300);
setTimeout(_drawAI, 800);

// ── EMA serileri
const EMA_COLORS=["#00d4ff","#a855f7","#ffd600","#ff6b35"];
let lgHtml="";
EMAS.forEach((e,i)=>{{
  const s=MC.addLineSeries({{color:e.color,lineWidth:e.lineWidth,
    priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false}});
  s.setData(e.data);
  lgHtml+=`<span style="color:${{EMA_COLORS[i]}};margin-right:8px;">&#9632; ${{e.label}}</span>`;
}});
BBS.forEach(b=>{{
  const s=MC.addLineSeries({{color:b.color,lineWidth:b.lineWidth,
    priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false}});
  s.setData(b.data);
}});
VWAPS.forEach(v=>{{
  const s=MC.addLineSeries({{color:v.color,lineWidth:v.lineWidth,lineStyle:2,
    priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false}});
  s.setData(v.data);
}});
if(lgHtml) document.getElementById("legend").innerHTML=lgHtml;

// ── Hacim
const VC=LightweightCharts.createChart(document.getElementById("vol"),
  Object.assign({{}},BASE,{{width:document.getElementById("vol").clientWidth,height:{vol_h},
    timeScale:{{...BASE.timeScale,visible:false}},
    rightPriceScale:{{...BASE.rightPriceScale,scaleMargins:{{top:0.1,bottom:0.0}}}},
  }}));
const VS=VC.addHistogramSeries({{priceFormat:{{type:"volume"}},scaleMargins:{{top:0.05,bottom:0}}}});
// Whale rengi entegre
const volData=[...VOLS];
WHALE_MARKS.forEach(wm=>{{
  const i=volData.findIndex(v=>v.time===wm.time);
  if(i>=0) volData[i]={{...volData[i],color:"rgba(168,85,247,0.75)"}};
}});
VS.setData(volData);
// Vol MA20
const vma=[];
for(let i=19;i<volData.length;i++){{
  const avg=volData.slice(i-19,i+1).reduce((s,v)=>s+v.value,0)/20;
  vma.push({{time:volData[i].time,value:avg}});
}}
if(vma.length){{
  const vmaS=VC.addLineSeries({{color:"rgba(0,212,255,0.35)",lineWidth:0.8,
    priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false}});
  vmaS.setData(vma);
}}

// ── Stochastic
let SC=null;
if(SHOW_STOCH&&STOCHS.length>0){{
  SC=LightweightCharts.createChart(document.getElementById("stoch"),
    Object.assign({{}},BASE,{{width:document.getElementById("stoch").clientWidth,height:{stoch_h},
      timeScale:{{...BASE.timeScale,visible:false}},
      rightPriceScale:{{...BASE.rightPriceScale,scaleMargins:{{top:0.1,bottom:0.1}}}},
    }}));
  STOCHS.forEach(s=>{{
    const ss=SC.addLineSeries({{color:s.color,lineWidth:s.lineWidth,
      priceLineVisible:false,lastValueVisible:false}});
    ss.setData(s.data);
  }});
  const stBase=SC.addLineSeries({{color:"transparent",priceLineVisible:false,lastValueVisible:false}});
  [80,20].forEach(lv=>stBase.createPriceLine({{price:lv,
    color:lv===80?"rgba(255,51,85,0.35)":"rgba(0,255,136,0.35)",
    lineWidth:0.6,lineStyle:2,axisLabelVisible:true,title:lv===80?"OB":"OS"}}));
}}

// ── Crosshair bilgi
MC.subscribeCrosshairMove(p=>{{
  if(!p.time){{
    document.getElementById("ch-ohlc").innerHTML="";
    document.getElementById("ch-chg").innerHTML="";
    document.getElementById("ch-vol").innerHTML="";
    [VC,SC].forEach(c=>{{if(c)c.clearCrosshairPosition();}});
    return;
  }}
  const bar=p.seriesData.get(CS);
  if(bar){{
    const bull=bar.close>=bar.open;
    const col=bull?"#00ff88":"#ff3355";
    const chg=((bar.close-bar.open)/Math.max(bar.open,1e-9)*100).toFixed(2);
    document.getElementById("ch-ohlc").innerHTML=
      `<span style="color:#3d5a80">O:<b style="color:#cdd6f4">${{bar.open.toFixed(DP)}}</b> `+
      `H:<b style="color:#00ff88">${{bar.high.toFixed(DP)}}</b> `+
      `L:<b style="color:#ff3355">${{bar.low.toFixed(DP)}}</b> `+
      `C:<b style="color:${{col}}">${{bar.close.toFixed(DP)}}</b></span>`;
    document.getElementById("ch-chg").innerHTML=`<b style="color:${{col}}">${{bull?"+":""}}${{chg}}%</b>`;
  }}
  const vb=p.seriesData.get(VS);
  if(vb){{
    const vc=vb.color&&vb.color.includes("168,85,247")?"#a855f7":
             vb.color&&vb.color.includes("0,255,136")?"#00ff88":"#ff3355";
    const fv=vb.value>1e9?(vb.value/1e9).toFixed(2)+"B":
             vb.value>1e6?(vb.value/1e6).toFixed(2)+"M":
             vb.value>1e3?(vb.value/1e3).toFixed(1)+"K":vb.value.toFixed(0);
    document.getElementById("ch-vol").innerHTML=
      `<span style="color:#3d5a80">Vol: <b style="color:${{vc}}">${{fv}}</b></span>`;
  }}
  [VC,SC].forEach(c=>{{if(c)c.setCrosshairPosition(0,p.time,VS);}});
}});

// ── Zaman senkronizasyonu
MC.timeScale().subscribeVisibleLogicalRangeChange(r=>{{
  if(!r) return; [VC,SC].forEach(c=>{{if(c)c.timeScale().setVisibleLogicalRange(r);}});
}});
VC.timeScale().subscribeVisibleLogicalRangeChange(r=>{{
  if(!r) return; MC.timeScale().setVisibleLogicalRange(r);
  if(SC) SC.timeScale().setVisibleLogicalRange(r);
}});

// ── Responsive
const RO=new ResizeObserver(e=>{{
  const w=e[0].contentRect.width;
  MC.applyOptions({{width:w}}); VC.applyOptions({{width:w}});
  if(SC) SC.applyOptions({{width:w}});
}});
RO.observe(document.getElementById("wrap"));

MC.timeScale().fitContent();
VC.timeScale().fitContent();
if(SC) SC.timeScale().fitContent();
</script></body></html>"""
        return html

    except Exception as e:
        elog("build_chart", e)
        return f"<div style='color:#ff3355;padding:20px;'>Grafik hatası: {e}</div>"


def build_chart_plotly(df, smc, sym,
                show_ema=True, show_bb=False, show_vwap=False, show_stoch=False,
                show_kz=True, show_fibs=True, show_ob=True, show_fvg=True,
                show_liq=True, show_mss=True, show_bp=True, dp=2):
    """Plotly fallback — yalnızca backtest equity grafiği için"""
    try:
        if df is None or df.empty: return go.Figure()
        fig = make_subplots(rows=2,cols=1,shared_xaxes=True,
                            vertical_spacing=0.007,row_heights=[0.72,0.28])
        fig.add_trace(go.Candlestick(
            x=df["time"],open=df["open"],high=df["high"],low=df["low"],close=df["close"],
            increasing=dict(fillcolor="#111d11",line=dict(color="#00ff88",width=0.9)),
            decreasing=dict(fillcolor="#1d1111",line=dict(color="#ff3355",width=0.9)),
        ),row=1,col=1)
        vc=["rgba(0,255,136,0.5)" if c>=o else "rgba(255,51,85,0.5)"
            for c,o in zip(df["close"],df["open"])]
        fig.add_bar(x=df["time"],y=df["volume"],marker_color=vc,showlegend=False,row=2,col=1)
        fig.update_layout(height=500,margin=dict(l=0,r=75,t=10,b=0),
            paper_bgcolor="#040810",plot_bgcolor="#040810",
            font=dict(family="JetBrains Mono",size=8,color="#3d5a80"),
            showlegend=False,xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=True,gridcolor="#091525"),
            yaxis=dict(showgrid=True,gridcolor="#091525",side="right"),
            xaxis2=dict(showgrid=True,gridcolor="#091525"),
            yaxis2=dict(showgrid=False,side="right"))
        return fig
    except: return go.Figure()


# ═══════════════════════════════════════════════════
#  BACKTEST ENGINE
# ═══════════════════════════════════════════════════
def run_backtest(df, capital, risk_pct, daily_lim, commission,
                 mss_req, fvg_req, news_filter, sessions, max_tpd, spread, slip, bias):
    try:
        if df is None or len(df) < 60:
            return {"trades":[],"metrics":{},"eq":[capital],"long_stats":{},"short_stats":{},"error":"Yetersiz veri"}
        H = df["high"].values; L = df["low"].values
        C = df["close"].values; O = df["open"].values
        n = len(df); times = df["time"].values
        ATR = df["atr"].values if "atr" in df.columns else np.full(n, np.mean(H-L))
        cost = (spread + slip + commission) / 100

        trades = []; equity = capital
        day_trades: Dict[date, int] = {}; day_pnl: Dict[date, float] = {}
        eq_curve = [capital]

        for i in range(CFG.SW + 25, n - 5):
            ts = pd.Timestamp(times[i]); dk = ts.date()
            if day_trades.get(dk, 0) >= max_tpd: continue
            if news_filter:
                if ts.weekday() in (0,1,2) and 13 <= ts.hour <= 14: continue
            if "All" not in sessions:
                sess_ok = any(
                    CFG.SESSIONS.get(s,(0,24))[0] <= ts.hour <= CFG.SESSIONS.get(s,(0,24))[1]
                    for s in sessions
                )
                if not sess_ok: continue
            if day_pnl.get(dk, 0) <= -(equity * daily_lim / 100): continue

            atr_i = float(ATR[i])
            if atr_i < 1e-9: continue

            sh, sl = find_swings(H[:i], L[:i], CFG.SW)
            if len(sh) < 3 or len(sl) < 3: continue

            ms = market_struct(sh, sl); is_bull = ms["str"] == "BULLISH"
            mss_d = find_mss(H[:i], L[:i], C[:i], O[:i], i, atr_i)
            if mss_req and not ((is_bull and mss_d["b"]) or (not is_bull and mss_d["s"])): continue

            imb, fb, fs = find_fvg(H[:i], L[:i], i)
            if fvg_req and is_bull and not fb: continue
            if fvg_req and not is_bull and not fs: continue

            bull_obs, bear_obs = find_obs(H[:i], L[:i], C[:i], O[:i], times[:i], sh, sl, i, imb)
            ob1 = (bull_obs[0] if is_bull and bull_obs else
                   bear_obs[0] if not is_bull and bear_obs else None)
            if ob1 is None: continue

            if not (ob1["lo"] - atr_i*0.6 <= C[i] <= ob1["hi"] + atr_i*0.6): continue
            htf_ok = (bias in ("BULL","NEUTRAL") and is_bull) or (bias in ("BEAR","NEUTRAL") and not is_bull)
            if not htf_ok: continue

            entry  = C[i] * (1 + cost if is_bull else 1 - cost)
            sl_p   = ob1["lo"] * 0.997 if is_bull else ob1["hi"] * 1.003
            sl_d   = abs(entry - sl_p)
            if sl_d < atr_i * 0.1: continue

            tp1 = entry + (sl_d   if is_bull else -sl_d)
            tp2 = entry + (sl_d*2 if is_bull else -sl_d*2)
            tp3 = entry + (sl_d*3 if is_bull else -sl_d*3)
            risk_usd = equity * risk_pct / 100
            pos = risk_usd / (sl_d + 1e-9)

            outcome = "open"; exit_p = entry; hit_tp1 = False
            for j in range(i+1, min(i+120, n)):
                if is_bull:
                    if not hit_tp1 and H[j] >= tp1: hit_tp1 = True
                    if H[j] >= tp3: outcome = "tp3"; exit_p = tp3; break
                    elif H[j] >= tp2 and hit_tp1: outcome = "tp2"; exit_p = tp2; break
                    if L[j] <= sl_p: outcome = "sl"; exit_p = sl_p; break
                else:
                    if not hit_tp1 and L[j] <= tp1: hit_tp1 = True
                    if L[j] <= tp3: outcome = "tp3"; exit_p = tp3; break
                    elif L[j] <= tp2 and hit_tp1: outcome = "tp2"; exit_p = tp2; break
                    if H[j] >= sl_p: outcome = "sl"; exit_p = sl_p; break

            if outcome == "open":
                exit_p = C[min(i+120, n-1)]

            raw_pnl = (exit_p - entry)*pos if is_bull else (entry - exit_p)*pos
            raw_pnl -= pos * entry * (commission/100) * 2
            win = raw_pnl > 0; equity += raw_pnl
            eq_curve.append(equity)
            day_trades[dk] = day_trades.get(dk, 0) + 1
            day_pnl[dk]    = day_pnl.get(dk, 0) + raw_pnl

            best_h = max(H[i+1:min(i+120,n)]) if i+1 < n else entry
            best_l = min(L[i+1:min(i+120,n)]) if i+1 < n else entry
            best_pct = (max(best_h-entry,0)/entry*100) if is_bull else (max(entry-best_l,0)/entry*100)

            trades.append({
                "idx":i,"time":str(times[i])[:16],"dir":"LONG" if is_bull else "SHORT",
                "entry":round(entry,8),"sl":round(sl_p,8),
                "tp1":round(tp1,8),"tp2":round(tp2,8),"tp3":round(tp3,8),
                "exit":round(exit_p,8),"outcome":outcome,"pnl":round(raw_pnl,4),
                "win":win,"rr":round(abs(exit_p-entry)/(sl_d+1e-9),2),
                "eq":round(equity,2),"ob_sc":ob1.get("score",0),
                "best_pct":round(best_pct,2),
            })

        if not trades:
            return {"trades":[],"metrics":{},"eq":[capital],"long_stats":{},"short_stats":{},
                    "error":"İşlem üretilmedi — parametreleri gevşetin"}

        wins = [t for t in trades if t["win"]]
        losses = [t for t in trades if not t["win"]]
        tot = len(trades); wr = len(wins)/tot*100 if tot else 0
        gp = sum(t["pnl"] for t in wins); gl = sum(t["pnl"] for t in losses)
        pf = abs(gp/gl) if gl else 999

        pk = capital; mdd = 0.0
        for eq_ in eq_curve:
            if eq_ > pk: pk = eq_
            dd = (pk - eq_) / pk * 100 if pk > 0 else 0
            if dd > mdd: mdd = dd

        rets = np.diff(eq_curve) / (np.array(eq_curve[:-1]) + 1e-9)
        sharpe  = round(np.mean(rets)/(np.std(rets)+1e-9)*np.sqrt(252),2) if len(rets)>1 else 0
        down_r  = rets[rets < 0]
        sortino = round(np.mean(rets)/(np.std(down_r)+1e-9)*np.sqrt(252),2) if len(down_r)>0 else 0

        # Long/Short stats per TP
        def _tp_stat(tlist, tp_key):
            if not tlist: return {"times":0,"best":0.0,"now":0.0,"wr":0}
            hits = [t for t in tlist if t["outcome"]==tp_key]
            best = max((t["best_pct"] for t in tlist), default=0)
            now  = max((abs(t["exit"]-t["entry"])/t["entry"]*100 for t in tlist), default=0)
            return {"times":len(tlist),"best":round(best,1),
                    "now":round(now,2),"wr":round(len(hits)/len(tlist)*100)}

        longs  = [t for t in trades if t["dir"]=="LONG"]
        shorts = [t for t in trades if t["dir"]=="SHORT"]
        ls = {"total":len(longs),  "tp1":_tp_stat(longs,"tp1"),  "tp2":_tp_stat(longs,"tp2"),  "tp3":_tp_stat(longs,"tp3")}
        ss = {"total":len(shorts), "tp1":_tp_stat(shorts,"tp1"), "tp2":_tp_stat(shorts,"tp2"), "tp3":_tp_stat(shorts,"tp3")}

        metrics = {
            "total":tot,"wins":len(wins),"losses":len(losses),"win_rate":round(wr,1),
            "net_pnl":round(gp+gl,2),"profit_factor":round(pf,2),"max_dd":round(mdd,1),
            "sharpe":sharpe,"sortino":sortino,"final_eq":round(equity,2),
            "roi":round((equity-capital)/capital*100,2),
            "avg_win":round(gp/max(len(wins),1),4),"avg_loss":round(gl/max(len(losses),1),4),
        }
        return {"trades":trades,"metrics":metrics,"eq":eq_curve,"long_stats":ls,"short_stats":ss}
    except Exception as e:
        elog("run_backtest", e)
        return {"trades":[],"metrics":{},"eq":[capital],"long_stats":{},"short_stats":{},"error":str(e)}

def run_mc(trades, capital, n_sim=1000, horizon=60):
    if not trades: return {}
    try:
        pcts = [t["pnl"]/(max(t["eq"]-t["pnl"],1e-9)) for t in trades]
        sims = np.zeros((n_sim, horizon+1)); sims[:,0] = capital
        np.random.seed(42)
        for s in range(n_sim):
            eq = capital
            for j in range(horizon):
                eq = max(0, eq*(1 + float(np.random.choice(pcts)) + np.random.normal(0,.002)))
                sims[s,j+1] = eq
        ruin = int((sims[:,-1] < capital*0.5).sum())
        return {"p50":np.percentile(sims,50,axis=0).tolist(),
                "p10":np.percentile(sims,10,axis=0).tolist(),
                "p90":np.percentile(sims,90,axis=0).tolist(),
                "ruin":round(ruin/n_sim*100,1),"med":round(float(np.median(sims[:,-1])),2)}
    except Exception as e:
        elog("run_mc", e)
        return {}


# ═══════════════════════════════════════════════════
#  AI + SCANNER
# ═══════════════════════════════════════════════════
AI_MODES = {
    "📈 ICT Trader": "Sen APEX PRO — ICT/SMC uzmanı analistsin. BOS, CHoCH, MSS, OB, FVG, sweep, killzone biliyorsun. Net karar ver. Türkçe yaz.",
    "🔬 Araştır":    "Sen APEX PRO Araştırma Motoru. Özetle → Analiz et → Karar ver formatında Türkçe yaz.",
    "💻 Kod":        "Sen APEX PRO Mühendis. Python, trading, Streamlit uzmanı. Türkçe açıkla.",
    "📊 Makro":      "Sen APEX PRO Makroekonomist. DXY, Fed, tahvil, likidite analizi. Türkçe yaz.",
    "🧠 Genel":      "Türkçe yanıtla.",
}

def nexus_ai(msg):
    mode  = AI_MODES.get(st.session_state.get("ai_mode","📈 ICT Trader"),"")
    key   = st.session_state.get("ai_key", CFG.HF_KEY)
    model = st.session_state.get("ai_model", CFG.AI_MODELS[0][0])
    temp  = float(st.session_state.get("ai_temp", 0.7))
    max_t = int(st.session_state.get("ai_tokens", 1800))
    mem   = int(st.session_state.get("ai_mem", 8)) * 2
    hist  = st.session_state.get("chat", [])[-mem:]
    ctx   = st.session_state.get("live_ctx", {})
    sys_p = mode
    if ctx:
        sys_p += "\n\n[CANLI PİYASA — " + datetime.utcnow().strftime("%H:%M UTC") + "]\n"
        sys_p += "\n".join(f"{k}: {v}" for k,v in ctx.items())
    msgs = ([{"role":"system","content":sys_p}]
            + [{"role":m["role"],"content":m["content"]} for m in hist]
            + [{"role":"user","content":msg}])
    t0 = time.time()
    for prov in CFG.AI_PROV:
        try:
            m_ = f"{model}:{prov}" if prov else model
            r = requests.post(CFG.HF_EP,
                headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                json={"model":m_,"messages":msgs,"max_tokens":max_t,"temperature":temp},
                timeout=120)
            el = time.time() - t0
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip(), el
            if r.status_code in (401,403):
                return "🔑 API anahtarı geçersiz.", el
            if r.status_code == 429:
                return "🚦 Rate limit — bir süre bekle.", el
        except requests.Timeout:
            return "⏱ Timeout.", time.time()-t0
        except: continue
    return "❌ Tüm providerlar başarısız.", time.time()-t0

def scan_one(sym_api, tf, market):
    """
    Ultra gelişmiş tek sembol taraması.
    ICT/SMC skoru + ADX + RSI + R:R + Hacim konfluence.
    Returns dict veya None.
    """
    try:
        # Veri çek — fetch_data otomatik sembol düzeltme yapar
        if market == "crypto":
            df_ = fetch_bin(sym_api, tf, 400)
        else:
            df_ = fetch_data(sym_api, tf, 400, market=market)

        if df_ is None or df_.empty or len(df_) < 50: return None
        df_ = add_ind(df_)
        smc_ = calc_smc(df_)
        if not smc_: return None

        is_bull = smc_.get("is_bull", True)
        rsi_    = cv(df_, "rsi", 50)
        adx_    = cv(df_, "adx", 15)
        atr_    = cv(df_, "atr", 0)
        vol_r   = cv(df_, "vol_r", 1)
        cmf_    = cv(df_, "cmf", 0)
        ema9_   = cv(df_, "ema9",  float(df_["close"].iloc[-1]))
        ema21_  = cv(df_, "ema21", float(df_["close"].iloc[-1]))
        price_  = float(df_["close"].iloc[-1])

        ob1 = (smc_.get("bull_obs",[{}])[0] if is_bull and smc_.get("bull_obs")
               else smc_.get("bear_obs",[{}])[0] if not is_bull and smc_.get("bear_obs") else {})

        # ── Ultra skor hesaplama (0-100) ─────────────────
        sc = 0
        reasons = []

        # Yapısal sinyaller (40 puan)
        if smc_.get("mss_b") or smc_.get("mss_s"):
            sc += 15; reasons.append("MSS✓")
        if smc_.get("bos_b") or smc_.get("bos_s"):
            sc += 10; reasons.append("BOS✓")
        if smc_.get("choch_b") or smc_.get("choch_s"):
            sc += 8;  reasons.append("CHoCH✓")
        if ob1 and ob1.get("score",0) > 0:
            sc += min(12, ob1.get("score",0)//3); reasons.append("OB✓")

        # FVG + Imbalance (15 puan)
        if smc_.get("fvg_b") or smc_.get("fvg_s"):
            sc += 10; reasons.append("FVG✓")
        if smc_.get("imb") and len(smc_["imb"]) > 0:
            sc += 5; reasons.append("IMB✓")

        # Zone doğrulaması (10 puan)
        if is_bull and not smc_.get("is_prem"):
            sc += 10; reasons.append("Discount✓")
        elif not is_bull and smc_.get("is_prem"):
            sc += 10; reasons.append("Premium✓")

        # R:R (10 puan)
        rr_ = smc_.get("rr", 0)
        if rr_ >= 3:   sc += 10; reasons.append(f"R:R{rr_:.1f}✓")
        elif rr_ >= 2: sc += 7;  reasons.append(f"R:R{rr_:.1f}")
        elif rr_ >= 1.5: sc += 4

        # ADX trend gücü (10 puan)
        if adx_ >= 30:   sc += 10; reasons.append(f"ADX{adx_:.0f}✓")
        elif adx_ >= 20: sc += 7;  reasons.append(f"ADX{adx_:.0f}")
        elif adx_ >= 15: sc += 4

        # RSI konfirmasyonu (10 puan)
        if is_bull and 35 <= rsi_ <= 60:
            sc += 10; reasons.append(f"RSI{rsi_:.0f}✓")
        elif not is_bull and 40 <= rsi_ <= 65:
            sc += 10; reasons.append(f"RSI{rsi_:.0f}✓")
        elif 30 <= rsi_ <= 70:
            sc += 5

        # Hacim konfluence (5 puan)
        if vol_r >= 1.5 and ((is_bull and cmf_ > 0) or (not is_bull and cmf_ < 0)):
            sc += 5; reasons.append("VOL✓")

        # EMA pozisyon (5 puan)
        if is_bull and ema9_ > ema21_ and price_ > ema21_:
            sc += 5; reasons.append("EMA✓")
        elif not is_bull and ema9_ < ema21_ and price_ < ema21_:
            sc += 5; reasons.append("EMA✓")

        sc = min(100, sc)
        if sc < CFG.SCAN_MIN_SCORE: return None

        # RSI aşırı alım/satım filtresi
        if is_bull and rsi_ > CFG.SCAN_MAX_RSI_L: return None
        if not is_bull and rsi_ < CFG.SCAN_MIN_RSI_S: return None

        return {
            "sym":     sym_api,
            "dir":     "LONG" if is_bull else "SHORT",
            "score":   sc,
            "rr":      round(rr_, 2),
            "adx":     round(adx_, 1),
            "rsi":     round(rsi_, 1),
            "vol_r":   round(vol_r, 2),
            "mss":     bool(smc_.get("mss_b") or smc_.get("mss_s")),
            "bos":     bool(smc_.get("bos_b") or smc_.get("bos_s")),
            "choch":   bool(smc_.get("choch_b") or smc_.get("choch_s")),
            "fvg":     bool(smc_.get("fvg_b") or smc_.get("fvg_s")),
            "ob_sc":   ob1.get("score",0) if ob1 else 0,
            "tp3":     smc_.get("tp3", 0),
            "sl_p":    smc_.get("sl_p", 0),
            "price":   round(price_, 6),
            "reasons": " · ".join(reasons[:6]),
            "market":  market,
        }
    except Exception as e:
        elog("scan_one", f"{sym_api}: {e}")
        return None



# ═══════════════════════════════════════════════════
#  TAHMİN SKORU — Yükseliş/Düşüş Beklentisi
#  scan_one sonucuna ek olarak "bull_pct" + "bear_pct" hesaplar
# ═══════════════════════════════════════════════════
def predict_direction(sym_api, tf, market, bars=300):
    """
    Teknik analiz bazlı yönsel tahmin.
    Returns dict: {sym, market, tf, bull_pct, bear_pct,
                   expected_move, tp_target, sl_risk,
                   signals_bull, signals_bear, confidence}
    """
    try:
        df = fetch_data(sym_api, tf, bars, market)
        if df is None or df.empty or len(df) < 50:
            return None
        df = add_ind(df)
        smc = calc_smc(df)
        if not smc:
            return None

        bull_pts = 0; bear_pts = 0
        sig_bull = []; sig_bear = []

        c  = float(df["close"].iloc[-1])
        o  = float(df["open"].iloc[-1])
        c5 = float(df["close"].iloc[-5]) if len(df) >= 5 else c
        ema9  = float(df["ema9"].iloc[-1])  if "ema9"  in df.columns else c
        ema21 = float(df["ema21"].iloc[-1]) if "ema21" in df.columns else c
        ema50 = float(df["ema50"].iloc[-1]) if "ema50" in df.columns else c
        rsi   = float(df["rsi"].iloc[-1])   if "rsi"   in df.columns else 50
        adx   = float(df["adx"].iloc[-1])   if "adx"   in df.columns else 20
        macd  = float(df["macd"].iloc[-1])  if "macd"  in df.columns else 0
        macds = float(df["macd_s"].iloc[-1])if "macd_s" in df.columns else 0
        atr   = float(df["atr"].iloc[-1])   if "atr"   in df.columns else c * 0.01

        # ── EMA stack ──────────────────────────────────
        if c > ema9 > ema21 > ema50:
            bull_pts += 20; sig_bull.append("EMA Stack ↑")
        elif c < ema9 < ema21 < ema50:
            bear_pts += 20; sig_bear.append("EMA Stack ↓")
        elif c > ema50:
            bull_pts += 8; sig_bull.append("Fiyat > EMA50")
        elif c < ema50:
            bear_pts += 8; sig_bear.append("Fiyat < EMA50")

        # ── RSI momentum ───────────────────────────────
        if 50 < rsi < 70:
            bull_pts += 12; sig_bull.append(f"RSI {rsi:.0f} >50")
        elif rsi >= 70:
            bear_pts += 8; sig_bear.append(f"RSI {rsi:.0f} Aşırı Alım")
        elif 30 < rsi <= 50:
            bear_pts += 10; sig_bear.append(f"RSI {rsi:.0f} <50")
        elif rsi <= 30:
            bull_pts += 10; sig_bull.append(f"RSI {rsi:.0f} Aşırı Satım")

        # ── MACD ───────────────────────────────────────
        if macd > 0 and macd > macds:
            bull_pts += 10; sig_bull.append("MACD Pozitif")
        elif macd < 0 and macd < macds:
            bear_pts += 10; sig_bear.append("MACD Negatif")
        if macd > macds and float(df["macd"].iloc[-2]) if "macd" in df.columns and len(df) > 2 else 0 < macds:
            bull_pts += 6; sig_bull.append("MACD Kesişim ↑")

        # ── ADX trend gücü ─────────────────────────────
        if adx >= 30:
            if bull_pts >= bear_pts:
                bull_pts += 8; sig_bull.append(f"ADX {adx:.0f} Güçlü Trend")
            else:
                bear_pts += 8; sig_bear.append(f"ADX {adx:.0f} Güçlü Trend")

        # ── SMC structure ──────────────────────────────
        if smc.get("is_bull"):
            bull_pts += 15; sig_bull.append("Bullish Yapı")
        else:
            bear_pts += 15; sig_bear.append("Bearish Yapı")

        if smc.get("mss_b"):
            bull_pts += 12; sig_bull.append("MSS Bullish")
        if smc.get("mss_s"):
            bear_pts += 12; sig_bear.append("MSS Bearish")
        if smc.get("bos_b"):
            bull_pts += 8;  sig_bull.append("BOS ↑")
        if smc.get("bos_s"):
            bear_pts += 8;  sig_bear.append("BOS ↓")
        if smc.get("choch_b"):
            bull_pts += 10; sig_bull.append("CHoCH Bullish")
        if smc.get("choch_s"):
            bear_pts += 10; sig_bear.append("CHoCH Bearish")

        # ── OB / FVG ───────────────────────────────────
        if smc.get("bull_obs") and c >= float(smc["bull_obs"][0]["lo"]):
            bull_pts += 10; sig_bull.append("Bull OB'de")
        if smc.get("bear_obs") and c <= float(smc["bear_obs"][0]["hi"]):
            bear_pts += 10; sig_bear.append("Bear OB'de")
        if smc.get("fvg_b"):
            bull_pts += 7; sig_bull.append("Bull FVG Açık")
        if smc.get("fvg_s"):
            bear_pts += 7; sig_bear.append("Bear FVG Açık")

        # ── Momentum: son 5 mum ────────────────────────
        if c > c5:
            bull_pts += 8; sig_bull.append("5 Mum ↑ Momentum")
        elif c < c5:
            bear_pts += 8; sig_bear.append("5 Mum ↓ Momentum")

        # ── HTF bias ───────────────────────────────────
        bias = smc.get("htf_bias", "")
        if bias == "BULL":
            bull_pts += 10; sig_bull.append("HTF BULL Bias")
        elif bias == "BEAR":
            bear_pts += 10; sig_bear.append("HTF BEAR Bias")

        total = max(bull_pts + bear_pts, 1)
        bull_pct = round(bull_pts / total * 100, 1)
        bear_pct = round(bear_pts / total * 100, 1)

        # Hedef fiyat (ATR bazlı)
        rr    = smc.get("rr", 1.5)
        sl    = atr * 1.2
        tp    = atr * rr * 1.5
        direction = "BULL" if bull_pts >= bear_pts else "BEAR"
        tp_target = c + tp   if direction == "BULL" else c - tp
        sl_risk   = c - sl   if direction == "BULL" else c + sl

        confidence = min(100, int(abs(bull_pts - bear_pts) / max(total * 0.3, 1) * 100))

        return {
            "sym": sym_api, "market": market, "tf": tf,
            "price": c,
            "direction": direction,
            "bull_pct": bull_pct, "bear_pct": bear_pct,
            "tp_target": tp_target, "sl_risk": sl_risk,
            "expected_move_pct": round(tp / max(c, 1e-9) * 100, 2),
            "signals_bull": sig_bull[:4],
            "signals_bear": sig_bear[:4],
            "confidence": confidence,
            "rsi": rsi, "adx": adx, "atr": atr,
        }
    except Exception as e:
        elog("predict_direction", e)
        return None


def run_prediction_scan(syms_markets, tf="1h", min_confidence=30):
    """
    Birden fazla sembolü paralel tarar, yükseliş/düşüş beklentisine göre sıralar.
    Returns (bull_list, bear_list)
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = {
            ex.submit(predict_direction, sym, tf, mkt): (sym, mkt)
            for sym, mkt in syms_markets
        }
        for f in concurrent.futures.as_completed(futs, timeout=120):
            try:
                r = f.result()
                if r and r.get("confidence", 0) >= min_confidence:
                    results.append(r)
            except: pass

    bull_list = sorted(
        [r for r in results if r["direction"] == "BULL"],
        key=lambda x: x["bull_pct"], reverse=True
    )
    bear_list = sorted(
        [r for r in results if r["direction"] == "BEAR"],
        key=lambda x: x["bear_pct"], reverse=True
    )
    return bull_list, bear_list


def run_scanner(syms, tf, market, min_score=50):
    """Paralel ultra tarama — max 8 thread"""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(scan_one, s, tf, market): s for s in syms}
        for f in concurrent.futures.as_completed(futs, timeout=60):
            try:
                r = f.result()
                if r and r.get("score",0) >= min_score:
                    results.append(r)
            except: pass
    return sorted(results, key=lambda x: x["score"], reverse=True)


# ═══════════════════════════════════════════════════
#  ARKA PLAN FIRSATLAR TARAYICISI  (Async Threading)
# ═══════════════════════════════════════════════════

# 20 popüler Forex çifti + 20 popüler Kripto
_BG_FOREX = [
    "EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CHF",
    "NZD/USD","USD/CAD","EUR/JPY","GBP/JPY","XAU/USD",
    "XAG/USD","EUR/GBP","GBP/CHF","AUD/JPY","EUR/AUD",
    "WTI/USD","USD/TRY","USD/MXN","USD/ZAR","USD/SEK",
]
_BG_CRYPTO = [
    "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
    "ADAUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT",
    "MATICUSDT","LTCUSDT","UNIUSDT","ATOMUSDT","NEARUSDT",
    "APTUSDT","ARBUSDT","OPUSDT","INJUSDT","SUIUSDT",
]


# Top BIST stocks for background scan
_BG_BIST = ["THYAO","BIMAS","AKBNK","GARAN","ISCTR","KCHOL","EREGL","PETKM","SISE","TUPRS"]

def _bg_scan_worker():
    """
    Arka plan thread'i — 5 dakikada bir tam tarama yapar:
    • 20 popüler Forex çifti (1s = 1 saat)
    • 20 popüler Kripto (1s = 1 saat)
    • Top 10 BIST hissesi (1g = 1 gün)
    Skor > 80 olanları st.session_state["firsatlar"]'a yazar.
    """
    while True:
        try:
            syms_market = (
                [(s, "forex")       for s in _BG_FOREX] +
                [(s, "crypto")      for s in _BG_CRYPTO] +
                [(s, "stock_bist")  for s in _BG_BIST]
            )
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
                tf_map = {"forex":"1s","crypto":"1s","stock_bist":"1g","stock_us":"1s"}
                futs = {
                    ex.submit(scan_one, sym, tf_map.get(mkt,"1s"), mkt): (sym, mkt)
                    for sym, mkt in syms_market
                }
                for f in concurrent.futures.as_completed(futs, timeout=150):
                    try:
                        r = f.result()
                        if r and r.get("score", 0) > 80:
                            results.append(r)
                    except: pass

            results.sort(key=lambda x: x["score"], reverse=True)
            st.session_state["firsatlar"]    = results
            st.session_state["firsatlar_ts"] = datetime.now().strftime("%H:%M:%S")
            st.session_state["firsatlar_cnt"] = len(results)
            elog("bg_scanner", f"{len(results)} firsat bulundu — {datetime.now().strftime('%H:%M')}")

            _pr_pairs = (
                [(s, "forex")  for s in _BG_FOREX[:10]] +
                [(s, "crypto") for s in _BG_CRYPTO[:10]]
            )
            _p_bull, _p_bear = run_prediction_scan(_pr_pairs, "1s", min_confidence=25)
            st.session_state["bg_bull"] = _p_bull[:10]
            st.session_state["bg_bear"] = _p_bear[:10]
        except Exception as e:
            elog("_bg_scan_worker", e)
        time.sleep(300)


def _ensure_bg_scanner():
    """
    Arka plan tarayıcısını sadece bir kez başlatır.
    st.session_state['_bg_started'] ile takip edilir.
    """
    if not st.session_state.get("_bg_started"):
        t = threading.Thread(target=_bg_scan_worker, daemon=True, name="apex_bg_scan")
        t.start()
        st.session_state["_bg_started"] = True
        st.session_state["firsatlar"] = []
        st.session_state["firsatlar_ts"] = "—"


# ═══════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════
TOP100 = get_top100()

# Arka plan tarayıcısını başlat (tek seferlik daemon thread)
# ── Session state güvenli başlatma ───────────────────────────
for _ssk, _ssv in [
    ("firsatlar", []), ("firsatlar_ts", "—"), ("firsatlar_cnt", 0),
    ("bg_bull", []), ("bg_bear", []),
    ("scan", []), ("scan_params", {}),
    ("pr_bull", []), ("pr_bear", []), ("pr_done", False),
    ("bt", None), ("bt_done", False), ("mc", None),
    ("ai_history", []), ("ai_mode", "📈 ICT Trader"),
    ("ai_key", ""), ("ai_temp", 0.7), ("ai_tokens", 1800), ("ai_mem", 8),
    ("last_sym", ""), ("live_ctx", {}),
]:
    if _ssk not in st.session_state:
        st.session_state[_ssk] = _ssv

_ensure_bg_scanner()

with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:12px 0 6px;">'
        '<div class="apex-logo" style="font-size:2.1rem;">APEX PRO</div>'
        '<div style="font-size:5.5px;color:#3d5a80;letter-spacing:.14em;margin-top:2px;">'
        'v10.0 · SUPREME · TV CHARTS · SMC · AI · SCANNER</div>'
        '</div>'
        '<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,212,255,.3),transparent);margin:6px 0 10px;"></div>',
        unsafe_allow_html=True)

    # ── Market Type ───────────────────────────────
    market_type = st.radio("📊 Piyasa", ["🪙 Kripto","💱 Forex","🏛 US Hisse","🇹🇷 BIST"],
                           horizontal=True)
    market = ("crypto" if "Kripto" in market_type else
              "forex"  if "Forex"  in market_type else
              "stock_us" if "US" in market_type else "stock_bist")

    # ── Symbol + TF ───────────────────────────────
    # Tüm piyasalar için ortak TF seçenekleri
    _ALL_TF_OPTS = ["1m","3m","5m","10m","15m","30m","1s","4s","1g"]
    _TF_DISPLAY_MAP = {
        "1m":"1 Dk","3m":"3 Dk","5m":"5 Dk","10m":"10 Dk","15m":"15 Dk",
        "30m":"30 Dk","1s":"1 Saat","4s":"4 Saat","1g":"1 Gün",
    }

    if market == "crypto":
        sym_lbl = st.selectbox("Sembol", list(TOP100.keys()), index=0)
        sym_api = TOP100[sym_lbl]["sym"]
        start_ws_price(sym_api)
        tf_opts = _ALL_TF_OPTS
        tf_lbl  = st.selectbox("⏱ Zaman Dilimi",
                                tf_opts,
                                index=4,  # 15m default
                                format_func=lambda x: f"{x}  ·  {_TF_DISPLAY_MAP.get(x,'')}")
        tf_val  = tf_lbl; dp_ = 2

    elif market == "forex":
        sym_lbl = st.selectbox("Sembol", list(CFG.FOREX.keys()))
        sym_api = sym_lbl
        tf_opts = ["5m","10m","15m","30m","1s","4s","1g"]
        tf_lbl  = st.selectbox("⏱ Zaman Dilimi",
                                tf_opts,
                                index=2,  # 15m default
                                format_func=lambda x: f"{x}  ·  {_TF_DISPLAY_MAP.get(x,'')}")
        tf_val  = tf_lbl
        dp_ = 5 if CFG.PIP.get(sym_lbl,1e-4) <= 1e-4 else 3

    elif market == "stock_us":
        sym_lbl = st.selectbox("US Hisse", CFG.US_STOCKS, index=0)
        sym_api = sym_lbl
        tf_opts = ["5m","10m","15m","30m","1s","4s","1g"]
        tf_lbl  = st.selectbox("⏱ Zaman Dilimi",
                                tf_opts,
                                index=2,
                                format_func=lambda x: f"{x}  ·  {_TF_DISPLAY_MAP.get(x,'')}")
        tf_val  = tf_lbl; dp_ = 2

    else:  # BIST
        sym_lbl = st.selectbox("BIST Hisse", CFG.BIST, index=0)
        sym_api = sym_lbl + ".IS"
        tf_opts = ["15m","30m","1s","4s","1g"]
        tf_lbl  = st.selectbox("⏱ Zaman Dilimi",
                                tf_opts,
                                index=2,  # 1s default
                                format_func=lambda x: f"{x}  ·  {_TF_DISPLAY_MAP.get(x,'')}")
        tf_val  = tf_lbl; dp_ = 2

    # TF bilgi kartı
    _tf_full = _TF_DISPLAY_MAP.get(tf_val, tf_val)
    st.markdown(
        f'<div style="background:rgba(0,212,255,.06);border:1px solid rgba(0,212,255,.15);'
        f'border-radius:6px;padding:5px 10px;margin-top:3px;display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-size:7px;color:#3d5a80;letter-spacing:1px;">AKTİF TF</span>'
        f'<span style="font-size:10px;font-weight:800;color:#00d4ff;">{tf_val}</span>'
        f'<span style="font-size:7.5px;color:#3d5a80;">{_tf_full}</span>'
        f'</div>', unsafe_allow_html=True)

    reset_if(f"{sym_lbl}_{tf_val}_{market}")

    # ── Chart Layers ──────────────────────────────
    st.markdown('<div class="sec">📊 Grafik Katmanları</div>', unsafe_allow_html=True)
    c1_, c2_ = st.columns(2)
    with c1_:
        show_ema   = st.checkbox("EMA/SMA", True)
        show_bb    = st.checkbox("Bollinger", False)
        show_vwap  = st.checkbox("VWAP", False)
        show_kz    = st.checkbox("Kill Zones", True)
        show_ob    = st.checkbox("Order Block", True)
    with c2_:
        show_stoch = st.checkbox("Stoch", False)
        show_fibs  = st.checkbox("Fibonacci", True)
        show_fvg   = st.checkbox("FVG", True)
        show_liq   = st.checkbox("Likidite", True)
        show_bp    = st.checkbox("Buy/Sell Pt", True)
    show_mss = st.checkbox("MSS/BOS/CHoCH", True)
    show_ha  = st.checkbox("Heikin-Ashi Modu", False, help="Mumları Heikin-Ashi olarak göster")

    # WS bağlantı durumu göstergesi
    if market == "crypto" and sym_api:
        ws_live = bool(get_ws_price(sym_api) and get_ws_price(sym_api).get("price",0) > 0)
        ws_dot  = "🟢" if ws_live else "🟡"
        st.markdown(
            f'<div style="font-size:7.5px;color:#3d5a80;margin-top:3px;">'
            f'{ws_dot} WS Stream: <b style="color:{"#00ff88" if ws_live else "#ffd600"};">'
            f'{"Canlı" if ws_live else "Bağlanıyor…"}</b></div>',
            unsafe_allow_html=True)

    # ── Risk ──────────────────────────────────────
    st.markdown('<div class="sec">⚙️ Risk & Sermaye</div>', unsafe_allow_html=True)
    capital    = st.number_input("Sermaye ($)", value=10000, step=1000, min_value=100)
    risk_pct   = st.slider("Risk/İşlem (%)", 0.25, 5.0, 1.0, 0.25)
    daily_lim  = st.slider("Günlük Max Kayıp (%)", 1, 20, 4)
    commission = st.number_input("Komisyon (%)", value=0.05, step=0.01, format="%.3f", min_value=0.0)

    # ── Backtest ──────────────────────────────────
    st.markdown('<div class="sec">🔬 Backtest</div>', unsafe_allow_html=True)
    mss_req  = st.checkbox("MSS Zorunlu", False)
    fvg_req  = st.checkbox("FVG Zorunlu", False)
    news_flt = st.checkbox("News Blackout", True)
    max_tpd  = st.slider("Max İşlem/Gün", 1, 5, 2)
    sessions = st.multiselect("Seans", ["All","Asya","Londra","NY"], default=["All"])
    spread_  = st.number_input("Spread (%)", value=0.02, step=0.005, format="%.4f", min_value=0.0)
    slip_    = st.number_input("Slippage (%)", value=0.01, step=0.005, format="%.4f", min_value=0.0)
    run_bt   = st.button("▶ BACKTEST", use_container_width=True, type="primary")

    # ── AI ────────────────────────────────────────
    st.markdown('<div class="sec">🤖 NEXUS AI</div>', unsafe_allow_html=True)
    m_labels = [m[1] for m in CFG.AI_MODELS]
    m_ids    = [m[0] for m in CFG.AI_MODELS]
    cur_idx  = m_ids.index(st.session_state["ai_model"]) if st.session_state["ai_model"] in m_ids else 0
    sel_m    = st.selectbox("LLM", m_labels, index=cur_idx)
    st.session_state["ai_model"] = m_ids[m_labels.index(sel_m)]
    st.session_state["ai_mode"]  = st.selectbox("Mod", list(AI_MODES.keys()))
    st.session_state["ai_key"]   = st.text_input("HF API Key", value=st.session_state["ai_key"], type="password")
    st.session_state["ai_temp"]  = st.slider("Temp", 0.0, 1.0, 0.7, 0.05)
    st.session_state["ai_tokens"]= st.slider("Tokens", 256, 3000, 1800, 128)
    st.session_state["ai_mem"]   = st.slider("Hafıza (tur)", 2, 20, 8)

    auto_rf = st.checkbox("🔄 30s Oto-Yenile", False)
    st.markdown("<hr>", unsafe_allow_html=True)
    cs_ = cstat()
    st.markdown(f'<div style="font-size:7.5px;color:#3d5a80;">Cache: {cs_["alive"]}/{cs_["total"]} | Hits:{cs_["hits"]}</div>',
                unsafe_allow_html=True)
    if st.button("🗑 Cache Temizle", use_container_width=True):
        cclear(); st.cache_data.clear(); st.success("✓")

# ═══════════════════════════════════════════════════
#  PIYASA DURUMU — HAFTA SONU & KAPALI SEANS KORUMASI
# ═══════════════════════════════════════════════════
def _market_status(market: str) -> dict:
    """
    Piyasa açık/kapalı/hafta sonu durumunu tespit eder.
    Returns: {open: bool, reason: str, warn: bool, color: str}
    """
    now_utc = datetime.utcnow()
    wd = now_utc.weekday()   # 0=Pazartesi ... 6=Pazar
    hh = now_utc.hour
    mm = now_utc.minute

    if market == "crypto":
        return {"open": True, "reason": "🟢 Kripto 7/24 açık", "warn": False, "color": "#00ff88"}

    if market == "forex":
        # Forex: Cuma 22:00 UTC'den Pazar 22:00 UTC'ye kadar kapalı
        if wd == 6:   # Pazar
            return {"open": False, "reason": "⚠️ Forex Pazar günü kapalı (22:00 UTC'de açılır)", "warn": True, "color": "#ffd600"}
        if wd == 5 and hh >= 22:   # Cuma gece
            return {"open": False, "reason": "⚠️ Forex hafta sonu kapanışı (Cuma 22:00 UTC)", "warn": True, "color": "#ffd600"}
        # Londra + NY seansları aktif mi?
        london_open = (7 <= hh < 16)
        ny_open     = (13 <= hh < 22)
        if london_open or ny_open:
            session = "Londra" if london_open and not ny_open else "NY" if ny_open and not london_open else "Londra+NY"
            return {"open": True, "reason": f"🟢 Forex açık — {session} Seansı", "warn": False, "color": "#00ff88"}
        return {"open": True, "reason": "🟡 Forex açık — Asya Seansı (düşük likidite)", "warn": False, "color": "#ffd600"}

    if market in ("stock_us", "stock_bist"):
        # Hafta sonu tamamen kapalı
        if wd >= 5:
            day_name = "Cumartesi" if wd == 5 else "Pazar"
            mkt_name = "BIST" if market == "stock_bist" else "US Hisse"
            return {"open": False, "reason": f"⚠️ {mkt_name} hafta sonu kapalı ({day_name})", "warn": True, "color": "#ff6b35"}
        # US Hisse saatleri: 14:30 - 21:00 UTC (09:30 - 16:00 ET)
        if market == "stock_us":
            if 14 <= hh < 21 or (hh == 14 and mm >= 30):
                return {"open": True, "reason": "🟢 NYSE/NASDAQ açık", "warn": False, "color": "#00ff88"}
            return {"open": False, "reason": "🟡 NYSE/NASDAQ kapalı — piyasa dışı saat", "warn": False, "color": "#ffd600"}
        # BIST saatleri: 07:00 - 15:00 UTC (10:00 - 18:00 TRT)
        if market == "stock_bist":
            if 7 <= hh < 15:
                return {"open": True, "reason": "🟢 BIST açık", "warn": False, "color": "#00ff88"}
            return {"open": False, "reason": "🟡 BIST kapalı — işlem saatleri dışı", "warn": False, "color": "#ffd600"}

    return {"open": True, "reason": "Bilinmiyor", "warn": False, "color": "#3d5a80"}

def _data_is_stale(df: pd.DataFrame, market: str, tf_label: str) -> tuple:
    """
    Verinin eski (stale) olup olmadığını kontrol eder.
    Returns: (is_stale: bool, msg: str)
    TF bazlı beklenen yenilenme süresi ile son mum zamanını karşılaştırır.
    """
    if df is None or df.empty:
        return True, "Veri yok"
    try:
        last_time = pd.to_datetime(df["time"].iloc[-1])
        age_min = (datetime.utcnow() - last_time).total_seconds() / 60
        # TF bazlı max kabul edilebilir gecikme
        max_age = {
            "1m": 5, "3m": 10, "5m": 15, "10m": 25, "15m": 30,
            "30m": 60, "1s": 120, "4s": 480, "1g": 1440 * 3,
            # eski format
            "1h": 120, "4h": 480, "1d": 1440 * 3,
        }.get(tf_label, 120)

        if market in ("forex", "stock_us", "stock_bist"):
            mst = _market_status(market)
            if not mst["open"]:
                max_age *= 10   # Kapalıyken daha hoşgörülü ol

        if age_min > max_age:
            h = int(age_min // 60); m = int(age_min % 60)
            return True, f"Son mum {h}s {m}dk önce"
        return False, ""
    except Exception:
        return False, ""


# ═══════════════════════════════════════════════════
#  DATA LOAD
# ═══════════════════════════════════════════════════
with st.spinner(f"📡 {sym_lbl} {tf_lbl} yükleniyor…"):
    t_load = time.perf_counter()
    df_raw, df_htf_raw, df_htf2_raw, htf_str, htf2_str = load_mtf(sym_api, tf_val, market)
    load_ms = round((time.perf_counter()-t_load)*1000)

# ── Piyasa Durumu Kontrol ────────────────────────────────────────────
_mst = _market_status(market)
if _mst["warn"]:
    st.markdown(
        f'<div style="background:rgba(255,107,53,.07);border:1.5px solid rgba(255,107,53,.35);'
        f'border-radius:8px;padding:8px 16px;margin-bottom:6px;display:flex;align-items:center;gap:10px;">'
        f'<span style="font-size:16px;">⚠️</span>'
        f'<div>'
        f'<div style="color:#ff6b35;font-weight:700;font-size:9px;">{_mst["reason"]}</div>'
        f'<div style="color:#3d5a80;font-size:7.5px;">Gösterilen veriler son kapanış fiyatlarıdır. Canlı işlem yapılamaz.</div>'
        f'</div></div>',
        unsafe_allow_html=True)

# ── Veri Boş mu? ─────────────────────────────────────────────────────
if df_raw is None or df_raw.empty or len(df_raw) < 40:
    _reason = _mst["reason"] if _mst["warn"] else (
        "Hafta sonu forex/borsa kapalı olabilir" if market != "crypto" else "API bağlantı hatası"
    )
    st.markdown(
        f'<div style="background:rgba(255,51,85,.06);border:1.5px solid rgba(255,51,85,.3);'
        f'border-radius:10px;padding:32px;text-align:center;">'
        f'<div style="font-size:2rem;margin-bottom:8px;">📡</div>'
        f'<div style="color:#ff3355;font-weight:700;font-size:14px;margin-bottom:6px;">'
        f'Veri alınamadı: <span style="color:#00d4ff">{sym_lbl}</span></div>'
        f'<div style="color:#3d5a80;font-size:9px;margin-bottom:12px;">{_reason}</div>'
        f'<div style="display:flex;gap:8px;justify-content:center;">'
        f'</div></div>',
        unsafe_allow_html=True)
    col_r1, col_r2, col_r3 = st.columns([1,1,1])
    with col_r1:
        if st.button("🔄 Tekrar Dene", type="primary", use_container_width=True):
            st.cache_data.clear(); cclear(); st.rerun()
    with col_r2:
        if st.button("📊 Demo Modu", use_container_width=True, key="demo_btn"):
            st.session_state["demo_mode"] = True; st.rerun()
    with col_r3:
        if market != "crypto" and st.button("🪙 Kripto'ya Geç", use_container_width=True):
            st.session_state["market_override"] = "crypto"; st.rerun()
    st.stop()

# ── Stale Veri Uyarısı ───────────────────────────────────────────────
_stale, _stale_msg = _data_is_stale(df_raw, market, tf_val)
if _stale and not _mst["warn"]:
    st.markdown(
        f'<div style="background:rgba(255,214,0,.05);border:1px solid rgba(255,214,0,.25);'
        f'border-radius:6px;padding:5px 14px;margin-bottom:5px;font-size:8px;color:#ffd600;">'
        f'⏰ Veri gecikmeli — {_stale_msg} | Yenilemek için ▶ Tekrar Dene veya TF değiştirin'
        f'</div>', unsafe_allow_html=True)

# Add indicators
df = add_ind(df_raw)
df_htf  = add_ind(df_htf_raw)  if (df_htf_raw  is not None and not df_htf_raw.empty  and len(df_htf_raw)  > 20) else pd.DataFrame()
df_htf2 = add_ind(df_htf2_raw) if (df_htf2_raw is not None and not df_htf2_raw.empty and len(df_htf2_raw) > 20) else pd.DataFrame()

# HTF Bias
if not df_htf.empty and "ema9" in df_htf.columns:
    e9h = cv(df_htf,"ema9",0); e21h = cv(df_htf,"ema21",0); clh = cv(df_htf,"close",0)
    bias_ = ("BULL" if e9h > e21h and clh > e21h else
             "BEAR" if e9h < e21h and clh < e21h else "NEUTRAL")
else:
    bias_ = "NEUTRAL"

# SMC
smc_ = safe(calc_smc, df, bias_, fb={})
if not smc_:
    smc_ = {}
    st.warning("⚠ SMC analizi: yetersiz veri — daha fazla mum için TF değiştirin.")

# Strategy
strat_ = safe(build_strategy, df, smc_, df_htf if not df_htf.empty else None, bias_, sym_lbl, dp_, fb={})
if not strat_: strat_ = {}

# Live price
lv_ = safe(live_price, sym_api, market, fb={})
price_ = lv_.get("price", cv(df, "close", 0))
if price_ == 0: price_ = cv(df, "close", 0)
chg_   = lv_.get("chg", 0.0)
is_bull = smc_.get("is_bull", True)
rsi_    = cv(df, "rsi", 50)
atr_    = cv(df, "atr", price_*0.01)

# F&G
fg_ = safe(fetch_fg, fb={"value":50,"label":"Nötr"})

# Live context for AI
st.session_state["live_ctx"] = {
    f"{sym_lbl} Fiyat": f"{fmt(price_,dp_)} ({chg_:+.2f}%)",
    "Piyasa": market_type, "TF": tf_lbl,
    "Yapı": smc_.get("struct","?"), "HTF": bias_,
    "Trend": strat_.get("trend_d","?"), "Strateji": strat_.get("st_type","?"),
    "F&G": f"{fg_.get('value',50)} {fg_.get('label','')}",
    "RSI": f"{rsi_:.1f}", "ATR": fmt(atr_, dp_),
}

# Run backtest if requested
if run_bt:
    with st.spinner("⚙️ Backtest çalışıyor…"):
        bt_r = safe(run_backtest, df, capital, risk_pct, daily_lim, commission,
                    mss_req, fvg_req, news_flt, sessions, max_tpd, spread_, slip_, bias_, fb=None)
    if bt_r:
        st.session_state["bt"] = bt_r
        st.session_state["bt_done"] = True
        st.session_state["mc"] = None

if auto_rf:
    time.sleep(30); st.rerun()


# ═══════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════
pc_ = "#00ff88" if chg_ >= 0 else "#ff3355"
st_type = strat_.get("st_type","?")
st_c_   = "#00ff88" if st_type=="LONG" else "#ff3355" if st_type=="SHORT" else "#ffd600"
bias_c_ = "#00ff88" if bias_=="BULL" else "#ff3355" if bias_=="BEAR" else "#3d5a80"

market_icon = {"crypto":"🪙","forex":"💱","stock_us":"🏛","stock_bist":"🇹🇷"}.get(market,"📊")
_now_str = datetime.utcnow().strftime("%H:%M UTC")
_mst_h   = _market_status(market)
_mst_pill_col = _mst_h["color"]
_mst_pill_lbl = "AÇIK" if _mst_h["open"] else "KAPALI"

# ── Viewport meta + PWA meta tags ────────────────────────────────────
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#020609">
""", unsafe_allow_html=True)

# ── Ana Header (Responsive) ──────────────────────────────────────────
st.markdown(f"""
<div class="apex-header" style="
  background:linear-gradient(135deg,#010610,#040f1c,#020c16);
  border:1px solid rgba(0,212,255,.16);
  border-bottom:2px solid rgba(0,212,255,.25);
  border-radius:12px;padding:10px 14px;
  margin-bottom:8px;position:relative;overflow:hidden;">

  <div style="position:absolute;top:0;left:0;right:0;height:1px;
    background:linear-gradient(90deg,transparent,rgba(0,212,255,.5),rgba(0,255,136,.3),transparent);"></div>

  <!-- MASAÜSTÜ SATIRI -->
  <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
    <div>
      <div class="apex-logo" style="font-size:1.9rem;">APEX PRO</div>
      <div style="font-size:5px;color:#3d5a80;letter-spacing:.14em;margin-top:-2px;">v12.0 · MOBILE SUPREME</div>
    </div>
    <div style="border-left:1px solid #0d1e30;padding-left:14px;">
      <div class="price-live" style="font-family:'Bebas Neue',cursive;font-size:1.95rem;color:{pc_};letter-spacing:.04em;">{fmt(price_,dp_)}</div>
      <div style="font-size:8px;color:{pc_};">{"▲" if chg_>=0 else "▼"} {abs(chg_):.2f}%</div>
    </div>
    <div style="border-left:1px solid #0d1e30;padding-left:12px;display:none;" class="desktop-only">
      <div style="font-size:7px;color:#3d5a80;letter-spacing:1px;margin-bottom:2px;">YAPI</div>
      <div style="font-size:11px;font-weight:700;color:{'#00ff88' if is_bull else '#ff3355'};">
        {"▲ BULLISH" if is_bull else "▼ BEARISH"}</div>
    </div>
    <div style="margin-left:auto;display:flex;gap:4px;align-items:center;flex-wrap:wrap;">
      <span class="pill pb">{market_icon} {sym_lbl}</span>
      <span class="pill pb">{tf_lbl}</span>
      <span class="pill {'pg' if bias_=='BULL' else 'pr' if bias_=='BEAR' else 'pb'}">HTF {bias_}</span>
      <span class="pill {'pg' if st_type=='LONG' else 'pr' if st_type=='SHORT' else 'py'}" style="font-weight:800;">{st_type}</span>
      <span class="pill {'pg' if fg_.get('value',50)>55 else 'pr' if fg_.get('value',50)<45 else 'pb'}">F&G {fg_.get('value',50)}</span>
      <span class="pill" style="background:{_mst_pill_col}18;border:1px solid {_mst_pill_col}44;color:{_mst_pill_col};">{_mst_pill_lbl}</span>
      <span class="pill" style="background:rgba(0,0,0,.3);border:1px solid #0d1e30;color:#3d5a80;font-size:8px;">{_now_str}</span>
      <span class="pill" style="background:rgba(0,0,0,.3);border:1px solid #0d1e30;color:#3d5a80;">⚡{load_ms}ms</span>
    </div>
  </div>

  <div style="position:absolute;bottom:0;left:0;right:0;height:1px;
    background:linear-gradient(90deg,transparent,rgba(0,212,255,.15),transparent);"></div>
</div>
""", unsafe_allow_html=True)

# ── Mobil Alt Navigasyon Çubuğu ──────────────────────────────────────
# JavaScript ile tab değiştirme (Streamlit tab'larını tetikler)
st.markdown("""
<div class="mobile-nav" id="mobileNav">
  <div class="mobile-nav-btn active" onclick="switchTab(0)" id="mnav-0">
    <span class="nav-icon">📈</span>
    <span>Grafik</span>
  </div>
  <div class="mobile-nav-btn" onclick="switchTab(1)" id="mnav-1">
    <span class="nav-icon">⚡</span>
    <span>Strateji</span>
  </div>
  <div class="mobile-nav-btn" onclick="switchTab(2)" id="mnav-2">
    <span class="nav-icon">🔬</span>
    <span>SMC</span>
  </div>
  <div class="mobile-nav-btn" onclick="switchTab(8)" id="mnav-8">
    <span class="nav-icon">🤖</span>
    <span>AI</span>
  </div>
  <div class="mobile-nav-btn" onclick="switchTab(9)" id="mnav-9">
    <span class="nav-icon">📰</span>
    <span>Haberler</span>
  </div>
  <div class="mobile-nav-btn" onclick="switchTab(5)" id="mnav-5">
    <span class="nav-icon">🔭</span>
    <span>Scanner</span>
  </div>
</div>
<script>
(function(){
  function switchTab(idx){
    // Streamlit tab list'ini bul ve tıkla
    var tabs = document.querySelectorAll('[data-baseweb="tab"]');
    if(tabs && tabs[idx]){
      tabs[idx].click();
      // Aktif nav butonu güncelle
      document.querySelectorAll('.mobile-nav-btn').forEach(function(b){b.classList.remove('active');});
      var nb = document.querySelector('[onclick="switchTab('+idx+')"]');
      if(nb) nb.classList.add('active');
      // Sayfanın başına scroll
      window.scrollTo({top:0,behavior:'smooth'});
    }
  }
  window.switchTab = switchTab;
  // Tablet/masaüstü tespiti — nav'ı gizle
  function checkSize(){
    var nav = document.getElementById('mobileNav');
    if(nav) nav.style.display = window.innerWidth >= 768 ? 'none' : 'flex';
  }
  checkSize();
  window.addEventListener('resize', checkSize);
})();
</script>
""", unsafe_allow_html=True)

# ── Hızlı TF Değiştirici (Quick TF Switcher) ────────────────────────
_TF_ALL = ["1m","3m","5m","10m","15m","30m","1s","4s","1g"]
_TF_NAMES = {"1m":"1 Dk","3m":"3 Dk","5m":"5 Dk","10m":"10 Dk","15m":"15 Dk",
             "30m":"30 Dk","1s":"1 Saat","4s":"4 Saat","1g":"1 Gün"}
_tf_pills = ""
for _t in _TF_ALL:
    _active = (_t == tf_val)
    _bg = "rgba(0,212,255,.18)" if _active else "rgba(0,212,255,.04)"
    _border = "rgba(0,212,255,.60)" if _active else "rgba(0,212,255,.15)"
    _col = "#00d4ff" if _active else "#3d5a80"
    _fw = "800" if _active else "500"
    _shadow = "0 0 10px rgba(0,212,255,.25);" if _active else ""
    _tf_pills += (
        f'<span style="background:{_bg};border:1px solid {_border};color:{_col};'
        f'border-radius:6px;padding:4px 10px;font-size:8.5px;font-weight:{_fw};'
        f'cursor:pointer;transition:.15s;box-shadow:{_shadow}letter-spacing:.3px;"'
        f' title="{_TF_NAMES.get(_t,"")}">{_t}</span>'
    )
st.markdown(
    f'<div style="display:flex;align-items:center;gap:5px;padding:6px 4px;'
    f'background:linear-gradient(90deg,rgba(0,212,255,.03),transparent);'
    f'border:1px solid rgba(0,212,255,.08);border-radius:8px;margin-bottom:8px;flex-wrap:wrap;">'
    f'<span style="font-size:6.5px;color:#3d5a80;letter-spacing:1.5px;'
    f'font-weight:700;padding:0 6px;white-space:nowrap;">⏱ TF</span>'
    f'{_tf_pills}'
    f'<span style="margin-left:auto;font-size:7px;color:#3d5a80;padding-right:6px;">'
    f'Sidebar\'dan değiştirin</span>'
    f'</div>',
    unsafe_allow_html=True
)

# ── Metrikler — Mobil responsive (4+4 kolon) ────────────────────────
_mss_ok = (is_bull and smc_.get("mss_b")) or (not is_bull and smc_.get("mss_s"))
_bos_ok = smc_.get("bos_b") or smc_.get("bos_s")

m1,m2,m3,m4 = st.columns(4)
with m1: st.metric("💰 Fiyat", fmt(price_,dp_), f"{chg_:+.2f}%")
with m2: st.metric("⚡ Sinyal", st_type, smc_.get("struct","?"))
with m3: st.metric("📊 RSI", f"{rsi_:.1f}",
                   "Aşırı Alım" if rsi_>70 else "Aşırı Satım" if rsi_<30 else "Normal")
with m4: st.metric("🔄 R:R", f"1:{smc_.get('rr',0):.1f}",
                   "✓ İyi" if smc_.get("rr",0)>=2 else "✗ Düşük")

# İkinci satır — varsayılan kapalı, expander ile
with st.expander("📊 Tüm Metrikler", expanded=False):
    m5,m6,m7,m8 = st.columns(4)
    with m5: st.metric("📈 Trend", strat_.get("tg_lbl","?"), strat_.get("trend_d","?")[:16] if strat_ else "?")
    with m6: st.metric("🎯 MSS/BOS", "✓ MSS" if _mss_ok else "~ BOS" if _bos_ok else "✗ Yok",
                      f"r:{smc_.get('mss_r',0):.2f}")
    with m7: st.metric("🌊 MFI", f"{cv(df,'mfi',50):.1f}",
                       strat_.get("mfi_d","?")[:14] if strat_ else "?")
    with m8: st.metric("⚠ Risk", f"{strat_.get('risk_pts',0)}/6",
                       f"Rec%:{strat_.get('risk_rec',1):.1f}" if strat_ else "?")

st.markdown("<hr>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
#  CANLI SCANNER WIDGET — Ana Sayfa (skor > 80)
# ═══════════════════════════════════════════════════

# ═══════════════════════════════════════════════════
#  CANLI SCANNER BANERİ — Ana Sayfa (skor > 80)
# ═══════════════════════════════════════════════════
def _render_scanner_banner():
    """Arka plan scanner sonuçlarını ana sayfada banner olarak gösterir."""
    results = st.session_state.get("firsatlar", [])
    ts      = st.session_state.get("firsatlar_ts", "—")
    is_live = st.session_state.get("_bg_started", False)

    if not results:
        if is_live:
            st.markdown(
                '<div style="display:flex;align-items:center;gap:8px;padding:6px 14px;'
                'background:rgba(0,212,255,0.03);border:1px solid rgba(0,212,255,0.1);'
                'border-radius:6px;margin-bottom:6px;font-size:8px;color:#3d5a80;">'
                '<span>🔍</span>'
                ' Scanner arka planda çalışıyor (20 Forex · 20 Kripto · 10 BIST)'
                ' — skor &gt; 80 fırsatlar burada görünür'
                '</div>',
                unsafe_allow_html=True)
        return

    top6    = results[:6]
    long_n  = sum(1 for r in results if r.get("dir") == "LONG")
    short_n = sum(1 for r in results if r.get("dir") == "SHORT")

    MKT_ICON = {"forex": "💱", "crypto": "₿", "stock_bist": "🇹🇷", "stock_us": "🏛"}

    # ── Kart HTML'leri ──────────────────────────────────────────────────────
    def _card(r):
        is_long = r.get("dir") == "LONG"
        dc   = "#00ff88"  if is_long else "#ff3355"
        bk   = "rgba(0,255,136,0.06)" if is_long else "rgba(255,51,85,0.06)"
        lbl  = "LONG"     if is_long else "SHORT"
        mkt  = MKT_ICON.get(r.get("market", ""), "📊")
        sym  = r.get("sym", "?")
        sc   = r.get("score", 0)
        rr   = r.get("rr", 0.0)
        bw   = min(int(sc * 0.6), 60)
        bc   = "#00ff88" if sc >= 75 else "#ffd600" if sc >= 60 else "#ff6b35"

        sigs = ""
        if r.get("mss"):   sigs += '<span style="font-size:6px;padding:1px 4px;border-radius:2px;background:rgba(168,85,247,.25);color:#a855f7;margin-right:2px;">MSS</span>'
        if r.get("bos"):   sigs += '<span style="font-size:6px;padding:1px 4px;border-radius:2px;background:rgba(0,255,136,.20);color:#00ff88;margin-right:2px;">BOS</span>'
        if r.get("choch"): sigs += '<span style="font-size:6px;padding:1px 4px;border-radius:2px;background:rgba(255,165,0,.20);color:#ffa500;margin-right:2px;">CHoCH</span>'
        if r.get("fvg"):   sigs += '<span style="font-size:6px;padding:1px 4px;border-radius:2px;background:rgba(0,212,255,.20);color:#00d4ff;margin-right:2px;">FVG</span>'

        rr_str  = f"{rr:.1f}"
        sc_str  = str(sc)
        bw_str  = str(bw)

        return (
            '<div style="display:flex;flex-direction:column;align-items:center;'
            'background:' + bk + ';border:1px solid ' + dc + '22;'
            'border-top:2px solid ' + dc + ';'
            'border-radius:6px;padding:6px 10px;min-width:115px;gap:3px;">'
                '<div style="font-size:7px;color:' + dc + ';font-weight:700;'
                'letter-spacing:.5px;">' + mkt + ' ' + sym + '</div>'
                '<div style="font-size:9.5px;font-weight:800;color:' + dc + ';'
                'font-family:monospace;letter-spacing:1px;">' + lbl + '</div>'
                '<div style="width:60px;height:3px;background:#0d1c2e;'
                'border-radius:2px;overflow:hidden;">'
                    '<div style="width:' + bw_str + 'px;height:3px;background:' + bc + ';'
                    'border-radius:2px;"></div>'
                '</div>'
                '<div style="font-size:7.5px;color:#cdd6f4;">'
                'S:<b style="color:' + bc + ';">' + sc_str + '</b>'
                '&nbsp;&nbsp;R:1:<b>' + rr_str + '</b>'
                '</div>'
                '<div style="display:flex;gap:2px;flex-wrap:wrap;'
                'justify-content:center;">' + sigs + '</div>'
            '</div>'
        )

    cards_html = "".join(_card(r) for r in top6)

    header = (
        '<div style="display:flex;flex-direction:column;min-width:88px;'
        'border-right:1px solid #0d1c2e;padding-right:10px;margin-right:6px;gap:2px;">'
            '<div style="font-size:7px;color:#3d5a80;letter-spacing:1px;'
            'font-weight:700;">🔥 SCANNER</div>'
            '<div style="font-size:10px;font-weight:800;color:#00d4ff;'
            'font-family:monospace;">' + str(len(results)) + ' FIRSAT</div>'
            '<div style="font-size:7.5px;">'
                '<span style="color:#00ff88;">▲' + str(long_n) + ' LONG</span>'
                '&nbsp;&nbsp;'
                '<span style="color:#ff3355;">▼' + str(short_n) + ' SHORT</span>'
            '</div>'
            '<div style="font-size:6.5px;color:#1a2a3a;">↻ ' + ts + '</div>'
        '</div>'
    )

    st.markdown(
        '<div style="display:flex;align-items:center;gap:6px;'
        'padding:8px 12px;'
        'background:linear-gradient(90deg,rgba(0,212,255,0.05),transparent);'
        'border:1px solid rgba(0,212,255,0.12);'
        'border-radius:8px;margin-bottom:8px;overflow-x:auto;">'
        + header
        + '<div style="display:flex;gap:6px;overflow-x:auto;">'
        + cards_html
        + '</div></div>',
        unsafe_allow_html=True)


_render_scanner_banner()



# ═══════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════
T = st.tabs(["📈 GRAFİK","⚡ STRATEJİ","🔬 SMC ANALİZ","⚙️ BACKTEST","🎲 MONTE CARLO","🔭 SCANNER","🔥 FIRSATLAR","🎯 TAHMİN","🤖 NEXUS AI","📰 HABERLER","📊 CANLI HABERLER","💰 MİLYARDER İZLEYİCİ","📋 LOG"])
t_ch,t_st,t_an,t_bt,t_mc,t_sc,t_fi,t_pr,t_ai,t_nw,t_lv,t_bl,t_lg = T


# ═══════════════════════════════════════════════════
#  TAB 1 — CHART + ICT ÇİZİM + AI ASISTAN
# ═══════════════════════════════════════════════════
with t_ch:
    # Chart mode selector
    ch_mode = st.radio("", ["📈 Grafik","✏️ ICT Çizim Modu","🤖 AI + Grafik"], horizontal=True, key="ch_mode_sel", label_visibility="collapsed")
    
    if ch_mode == "✏️ ICT Çizim Modu":
        # ── ICT DRAWING MODE ─────────────────────────────
        draw_tool = st.radio("Çizim Aracı:", 
            ["🖊 OB (Order Block)","📦 FVG","📏 BOS/MSS","📐 CHoCH","🎯 Buy/Sell Point",
             "📉 Trendline","⬆️ TP1/TP2/TP3","🔵 BSL/SSL","⚡ Sweep","🗑 Sil"],
            horizontal=True, key="draw_tool")
        
        dc1_, dc2_ = st.columns([4, 1])
        with dc1_:
            # Build chart with extra drawing canvas
            _tv_html2 = safe(build_chart, df, smc_, sym_lbl,
                        show_ema, show_bb, show_vwap, show_stoch, show_kz, show_fibs,
                        show_ob, show_fvg, show_liq, show_mss, show_bp, dp_, height=680,
                        show_ha=show_ha,
                        fb="<div style='color:#3d5a80;padding:30px;text-align:center;'>Yükleniyor…</div>")
            
            # Inject drawing overlay into chart HTML
            DRAW_COLORS = {
                "🖊 OB (Order Block)": ("rgba(0,255,136,0.18)", "#00ff88", "OB"),
                "📦 FVG": ("rgba(0,212,255,0.15)", "#00d4ff", "FVG"),
                "📏 BOS/MSS": ("rgba(168,85,247,0.10)", "#a855f7", "BOS"),
                "📐 CHoCH": ("rgba(255,165,0,0.12)", "#ffa500", "CHoCH"),
                "🎯 Buy/Sell Point": ("rgba(0,255,136,0.20)", "#00ff88", "Buy-point"),
                "📉 Trendline": ("rgba(255,214,0,0.15)", "#ffd600", "TL"),
                "⬆️ TP1/TP2/TP3": ("rgba(0,255,136,0.12)", "#00ff88", "TP"),
                "🔵 BSL/SSL": ("rgba(255,51,85,0.12)", "#ff3355", "BSL"),
                "⚡ Sweep": ("rgba(255,51,85,0.08)", "#ff3355", "Sweep"),
                "🗑 Sil": ("transparent", "#ff3355", ""),
            }
            dc = DRAW_COLORS.get(draw_tool, ("rgba(0,212,255,0.15)", "#00d4ff", ""))
            
            draw_overlay = f"""
<div id="draw-overlay" style="position:relative;width:100%;">
  <div id="draw-canvas-wrap" style="position:absolute;top:0;left:0;width:100%;height:680px;z-index:50;pointer-events:{'auto' if draw_tool!='🗑 Sil' else 'auto'};cursor:crosshair;">
    <canvas id="draw-canvas" width="1200" height="680" style="width:100%;height:680px;position:absolute;top:0;left:0;"></canvas>
  </div>
</div>
<script>
(function(){{
  const C = document.getElementById('draw-canvas');
  if(!C) return;
  const ctx = C.getContext('2d');
  const tool = '{draw_tool}';
  const fillCol = '{dc[0]}';
  const strokeCol = '{dc[1]}';
  const lbl = '{dc[2]}';
  let drawings = JSON.parse(localStorage.getItem('apex_drawings')||'[]');
  let drawing = false, sx=0, sy=0, ex=0, ey=0;
  
  function redraw(){{
    ctx.clearRect(0,0,C.width,C.height);
    drawings.forEach(d=>{{
      ctx.fillStyle = d.fill;
      ctx.strokeStyle = d.stroke;
      ctx.lineWidth = d.lw||1.5;
      if(d.type==='rect'){{
        ctx.fillRect(d.x,d.y,d.w,d.h);
        ctx.strokeRect(d.x,d.y,d.w,d.h);
        // Label
        ctx.font='bold 9px JetBrains Mono,monospace';
        ctx.fillStyle=d.stroke;
        ctx.fillText(d.lbl||'',d.x+4,d.y+12);
      }} else if(d.type==='line'){{
        ctx.beginPath();ctx.moveTo(d.x,d.y);ctx.lineTo(d.ex,d.ey);
        ctx.setLineDash([5,3]);ctx.stroke();ctx.setLineDash([]);
        ctx.font='bold 9px JetBrains Mono,monospace';
        ctx.fillStyle=d.stroke;
        ctx.fillText(d.lbl||'', (d.x+d.ex)/2, (d.y+d.ey)/2-4);
      }}
    }});
    // Preview
    if(drawing){{
      ctx.fillStyle=fillCol;ctx.strokeStyle=strokeCol;ctx.lineWidth=1.5;
      if(['🖊 OB (Order Block)','📦 FVG','📐 CHoCH','🎯 Buy/Sell Point','⬆️ TP1/TP2/TP3','🔵 BSL/SSL','⚡ Sweep','📏 BOS/MSS'].includes(tool)){{
        ctx.fillRect(sx,sy,ex-sx,ey-sy);
        ctx.strokeRect(sx,sy,ex-sx,ey-sy);
        ctx.font='bold 9px JetBrains Mono,monospace';
        ctx.fillStyle=strokeCol;
        ctx.fillText(lbl, sx+4, sy+12);
      }} else {{
        ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(ex,ey);
        ctx.setLineDash([5,3]);ctx.stroke();ctx.setLineDash([]);
      }}
    }}
  }}
  
  C.addEventListener('mousedown', e=>{{
    if(tool==='🗑 Sil'){{
      drawings=drawings.filter(d=>{{
        const bx=e.offsetX, by=e.offsetY;
        if(d.type==='rect') return !(bx>=d.x&&bx<=d.x+d.w&&by>=d.y&&by<=d.y+d.h);
        return true;
      }});
      localStorage.setItem('apex_drawings',JSON.stringify(drawings));
      redraw(); return;
    }}
    drawing=true; sx=e.offsetX; sy=e.offsetY; ex=sx; ey=sy;
  }});
  C.addEventListener('mousemove', e=>{{ if(drawing){{ ex=e.offsetX; ey=e.offsetY; redraw(); }} }});
  C.addEventListener('mouseup', e=>{{
    if(!drawing) return; drawing=false; ex=e.offsetX; ey=e.offsetY;
    const isRect=['🖊 OB (Order Block)','📦 FVG','📐 CHoCH','🎯 Buy/Sell Point','⬆️ TP1/TP2/TP3','🔵 BSL/SSL','⚡ Sweep','📏 BOS/MSS'].includes(tool);
    drawings.push(isRect
      ? {{type:'rect',x:Math.min(sx,ex),y:Math.min(sy,ey),w:Math.abs(ex-sx),h:Math.abs(ey-sy),fill:fillCol,stroke:strokeCol,lbl:lbl}}
      : {{type:'line',x:sx,y:sy,ex:ex,ey:ey,fill:fillCol,stroke:strokeCol,lbl:lbl,lw:2}}
    );
    localStorage.setItem('apex_drawings',JSON.stringify(drawings));
    redraw();
  }});
  
  redraw();
}})();
</script>"""
            
            if _tv_html2 and "</body>" in _tv_html2:
                _tv_html2 = _tv_html2.replace("</body>", draw_overlay + "</body>")
            
            st.components.v1.html(_tv_html2, height=690, scrolling=False)
            
            # Drawing controls
            dctl1, dctl2, dctl3 = st.columns(3)
            with dctl1:
                st.markdown('<div style="font-size:8px;color:#3d5a80;">💡 Grafik üzerine sürükle-bırak ile çiz. Çizimler tarayıcıda saklanır.</div>', unsafe_allow_html=True)
            with dctl2:
                st.markdown('<div style="font-size:8px;color:#00d4ff;">🎯 Resimdeki ICT çizimleri: OB kutular, FVG bölgeler, BOS/CHoCH etiketler otomatik yüklendi.</div>', unsafe_allow_html=True)
            with dctl3:
                if st.button("🗑 Tüm Çizimleri Temizle", key="clear_drawings"):
                    st.components.v1.html('<script>localStorage.removeItem("apex_drawings");location.reload();</script>', height=0)
        
        with dc2_:
            st.markdown('<div class="sec">✏️ ÇİZİM ARAÇLARI</div>', unsafe_allow_html=True)
            # Show ICT pattern guide
            ict_patterns = [
                ("🖊 OB","Order Block","#00ff88","Son yön değişimi öncesi güçlü mum"),
                ("📦 FVG","Fair Value Gap","#00d4ff","İki mum arası boşluk"),
                ("📏 BOS","Break of Structure","#a855f7","Yapı kırılması"),
                ("📐 CHoCH","Change of Char.","#ffa500","Karakter değişimi"),
                ("🎯 BP","Buy/Sell Point","#00ff88","Giriş noktası"),
                ("⬆️ TP","Take Profit","#00ff88","Kar hedefi"),
                ("🔵 BSL","BSL/SSL","#ff3355","Likidite seviyeleri"),
            ]
            for short, name, col, desc in ict_patterns:
                st.markdown(
                    f'<div style="border-left:3px solid {col};padding:3px 8px;margin-bottom:3px;'
                    f'background:rgba(0,0,0,0.2);border-radius:0 3px 3px 0;">'
                    f'<div style="font-size:8.5px;font-weight:700;color:{col};">{short}: {name}</div>'
                    f'<div style="font-size:7px;color:#3d5a80;">{desc}</div></div>',
                    unsafe_allow_html=True)
            
            st.markdown('<div class="sec">📊 CANLI SEVİYELER</div>', unsafe_allow_html=True)
            for l,v,c__ in [
                ("BSL",  smc_.get("bsl",0),  "#ff3355"),
                ("SSL",  smc_.get("ssl",0),  "#00ff88"),
                ("PWH",  smc_.get("pwh",0),  "#ffd600"),
                ("PWL",  smc_.get("pwl",0),  "#00d4ff"),
                ("OTE H",smc_.get("ote_hi",0),"#a855f7"),
                ("OTE L",smc_.get("ote_lo",0),"#a855f7"),
            ]:
                if v: kv(l, fmt(v, dp_), c__)
    
    elif ch_mode == "🤖 AI + Grafik":
        # ── AI + CHART SIDE BY SIDE ──────────────────────
        ai_ch_col, ai_chat_col = st.columns([3, 2])
        
        with ai_ch_col:
            _tv_html3 = safe(build_chart, df, smc_, sym_lbl,
                        show_ema, show_bb, show_vwap, show_stoch, show_kz, show_fibs,
                        show_ob, show_fvg, show_liq, show_mss, show_bp, dp_, height=650,
                        show_ha=show_ha,
                        fb="<div style='color:#3d5a80;padding:30px;text-align:center;'>Yükleniyor…</div>")
            st.components.v1.html(_tv_html3, height=660, scrolling=False)
        
        with ai_chat_col:
            st.markdown('<div style="font-family:Bebas Neue,cursive;font-size:1.4rem;letter-spacing:.12em;background:linear-gradient(90deg,#00d4ff,#a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">NEXUS AI ASISTAN</div>', unsafe_allow_html=True)
            
            # Quick analysis buttons
            qa1, qa2 = st.columns(2)
            with qa1:
                if st.button("🔍 Grafik Analizi", key="gai_q1", use_container_width=True):
                    st.session_state["_gai_q"] = f"{sym_lbl} {tf_lbl} grafiğini ICT/SMC ile analiz et. Mevcut durum: Yapı={smc_.get('struct','?')}, HTF={bias_}, RSI={rsi_:.1f}"
            with qa2:
                if st.button("🎯 Entry Planı", key="gai_q2", use_container_width=True):
                    st.session_state["_gai_q"] = f"{sym_lbl} için en iyi entry noktası, SL ve TP1/TP2/TP3 seviyeleri nelerdir? OB={smc_.get('bull_obs',[{}])[0].get('hi',0) if smc_.get('bull_obs') else 0}"
            
            qa3, qa4 = st.columns(2)
            with qa3:
                if st.button("📊 OB/FVG Analiz", key="gai_q3", use_container_width=True):
                    st.session_state["_gai_q"] = f"{sym_lbl} için aktif Order Block ve FVG seviyeleri. BOS={smc_.get('bos_b',False)}, CHoCH={smc_.get('choch_b',False)}"
            with qa4:
                if st.button("⚠️ Risk Analizi", key="gai_q4", use_container_width=True):
                    st.session_state["_gai_q"] = f"{sym_lbl} için risk analizi. ATR={fmt(atr_,dp_)}, R:R={smc_.get('rr',0):.1f}"
            
            # Chat display
            gchat = st.session_state.get("gchat", [])
            chat_html = ""
            for msg in gchat[-6:]:
                if msg["role"] == "user":
                    chat_html += f'<div style="background:linear-gradient(135deg,#1a1040,#2a1a60);border:1px solid rgba(168,85,247,.4);border-radius:10px 10px 3px 10px;padding:8px 12px;margin:3px 0;font-size:8.5px;color:#e9d8fd;">👤 {msg["content"][:200]}</div>'
                else:
                    chat_html += f'<div style="background:#080f1e;border:1px solid rgba(0,212,255,.2);border-top:2px solid rgba(0,212,255,.3);border-radius:10px 10px 10px 3px;padding:8px 12px;margin:3px 0;font-size:8.5px;line-height:1.6;color:#cdd6f4;">{msg["content"][:600]}</div>'
            
            if chat_html:
                st.markdown(chat_html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align:center;padding:20px;color:#3d5a80;font-size:8px;">Yukarıdaki butonlara tıkla veya soru yaz…</div>', unsafe_allow_html=True)
            
            # Input
            with st.form("gai_form", clear_on_submit=True):
                gai_ui = st.text_area("", value=st.session_state.pop("_gai_q", ""),
                    placeholder="Grafik hakkında sor…", height=65, label_visibility="collapsed")
                gai_sub = st.form_submit_button("➤ Sor", use_container_width=True, type="primary")
            
            if gai_sub and gai_ui.strip():
                if "gchat" not in st.session_state: st.session_state["gchat"] = []
                ctx_str = f"[{sym_lbl} {tf_lbl}: {fmt(price_,dp_)}, Yapı:{smc_.get('struct','?')}, HTF:{bias_}, RSI:{rsi_:.1f}, Strateji:{strat_.get('st_type','?')}]"
                st.session_state["gchat"].append({"role":"user","content":gai_ui.strip()})
                with st.spinner("⚡ NEXUS…"):
                    rp_, _ = safe(nexus_ai, ctx_str + "\n\n" + gai_ui.strip(), fb=("⚠ Yanıt alınamadı.",0.0))
                st.session_state["gchat"].append({"role":"assistant","content":rp_})
                if len(st.session_state["gchat"]) > 20:
                    st.session_state["gchat"] = st.session_state["gchat"][-20:]
                st.rerun()
    
    else:
        # ── NORMAL CHART MODE ────────────────────────────
        cc_, cs2_ = st.columns([4, 1])
        with cc_:
            _tv_html = safe(build_chart, df, smc_, sym_lbl,
                        show_ema, show_bb, show_vwap, show_stoch, show_kz, show_fibs,
                        show_ob, show_fvg, show_liq, show_mss, show_bp, dp_, height=730,
                        show_ha=show_ha,
                        fb="<div style='color:#3d5a80;padding:30px;text-align:center;'>Yükleniyor…</div>")
            st.components.v1.html(_tv_html, height=740, scrolling=False)

        with cs2_:
            st.markdown('<div class="sec">📐 YAPI & SİNYAL</div>', unsafe_allow_html=True)
            for l,v,c__ in [
                ("Yapı",   smc_.get("struct","?"), "#00ff88" if is_bull else "#ff3355"),
                ("HTF",    bias_, "#00ff88" if bias_=="BULL" else "#ff3355" if bias_=="BEAR" else "#3d5a80"),
                ("MSS",    "✓" if _mss_ok else "✗", "#00ff88" if _mss_ok else "#ff3355"),
                ("Zone",   "DISCOUNT✓" if (is_bull and not smc_.get("is_prem")) else
                           "PREMIUM✓"  if (not is_bull and smc_.get("is_prem")) else "Yanlış✗",
                 "#00ff88" if ((is_bull and not smc_.get("is_prem")) or
                               (not is_bull and smc_.get("is_prem"))) else "#ff3355"),
                ("OTE",    "İçinde✓" if smc_.get("ote_lo",0) <= price_ <= smc_.get("ote_hi",0) else "Dışında",
                 "#00ff88" if smc_.get("ote_lo",0) <= price_ <= smc_.get("ote_hi",0) else "#3d5a80"),
                ("FVG",    "BULL✓" if smc_.get("fvg_b") else "BEAR✓" if smc_.get("fvg_s") else "—",
                 "#00ff88" if smc_.get("fvg_b") else "#ff3355" if smc_.get("fvg_s") else "#3d5a80"),
            ]: kv(l, v, c__)

            st.markdown('<div class="sec">🎯 İŞLEM PLANI</div>', unsafe_allow_html=True)
            for l,v,c__ in [
                ("YÖN", "🟢 LONG" if is_bull else "🔴 SHORT", "#00ff88" if is_bull else "#ff3355"),
                ("TP3", fmt(smc_.get("tp3",0),dp_), "#00ff88"),
                ("TP2", fmt(smc_.get("tp2",0),dp_), "#68d48a"),
                ("TP1", fmt(smc_.get("tp1",0),dp_), "#3d8a4d"),
                ("SL",  fmt(smc_.get("sl_p",0),dp_),"#ff3355"),
                ("R:R", f"1:{smc_.get('rr',0):.2f}","#00d4ff"),
            ]: kv(l, v, c__)

            st.markdown("<br>", unsafe_allow_html=True)
            if st_type == "LONG":
                st.markdown('<div class="sig-long"><div style="font-family:Bebas Neue,cursive;'
                            'font-size:2rem;color:#00ff88;">🟢 LONG</div>'
                            '<div style="font-size:7.5px;color:#00ff88;letter-spacing:1.5px;">'
                            'ICT SETUP AKTIF</div></div>', unsafe_allow_html=True)
            elif st_type == "SHORT":
                st.markdown('<div class="sig-short"><div style="font-family:Bebas Neue,cursive;'
                            'font-size:2rem;color:#ff3355;">🔴 SHORT</div>'
                            '<div style="font-size:7.5px;color:#ff3355;letter-spacing:1.5px;">'
                            'ICT SETUP AKTIF</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="sig-wait"><div style="font-family:Bebas Neue,cursive;'
                            'font-size:1.8rem;color:#ffd600;">↔ BEKLE</div>'
                            '<div style="font-size:7.5px;color:#ffd600;">NET SİNYAL YOK</div>'
                            '</div>', unsafe_allow_html=True)

            if is_bull and smc_.get("bull_obs"):
                ob1_ = smc_["bull_obs"][0]
                st.markdown(f'<div style="margin-top:6px;"><span class="bp-badge">'
                            f'▶ BUY-POINT @ {fmt(ob1_["mid"],dp_)}</span></div>',
                            unsafe_allow_html=True)
            if not is_bull and smc_.get("bear_obs"):
                ob1_ = smc_["bear_obs"][0]
                st.markdown(f'<div style="margin-top:6px;"><span class="sp-badge">'
                            f'▶ SELL-POINT @ {fmt(ob1_["mid"],dp_)}</span></div>',
                            unsafe_allow_html=True)

            st.markdown('<div class="sec">📊 MTF BİAS</div>', unsafe_allow_html=True)
            for df_m, tf_m in [(df_htf, htf_str),(df_htf2, htf2_str)]:
                if not df_m.empty and "ema9" in df_m.columns:
                    e9_ = cv(df_m,"ema9",0); e21_ = cv(df_m,"ema21",0); cp_ = cv(df_m,"close",0)
                    b_ = ("BULL" if e9_>e21_ and cp_>e21_ else
                          "BEAR" if e9_<e21_ and cp_<e21_ else "NEU")
                    kv(str(tf_m), b_, "#00ff88" if b_=="BULL" else "#ff3355" if b_=="BEAR" else "#3d5a80")

            # Funding (crypto only)
            if market == "crypto":
                fr_ = safe(fetch_funding, sym_api, fb=0.0)
                kv("Funding", f"{fr_:.4f}%",
                   "#ff3355" if fr_>0.05 else "#00ff88" if fr_<-0.02 else "#3d5a80")
                ob_ = safe(fetch_ob, sym_api, fb={})
                if ob_: kv("OB Ratio", f"{ob_.get('ratio',1):.3f}",
                            "#00ff88" if ob_.get("ratio",1)>1.2 else "#ff3355" if ob_.get("ratio",1)<0.8 else "#3d5a80")


# ═══════════════════════════════════════════════════
#  TAB 2 — STRATEJİ PANELİ (MEO PRO Style)
# ═══════════════════════════════════════════════════
with t_st:
    if not strat_:
        st.warning("Strateji analizi için yeterli veri yok. Farklı TF deneyin.")
    else:
        sp1_, sp2_, sp3_ = st.columns([1.1, 1.1, 1])

        with sp1_:
            # Status panel
            rows_html = ""
            for l,v,c__ in [
                ("Trend Durumu",  strat_.get("trend_d","?"), strat_.get("tc","#cdd6f4")),
                ("Trend Gücü",    strat_.get("tg_d","?"),    strat_.get("tg_c","#cdd6f4")),
                ("Volatilite",    strat_.get("vol_d","?"),   strat_.get("vol_c","#cdd6f4")),
                ("Momentum",      strat_.get("mom_d","?"),   strat_.get("mom_c","#cdd6f4")),
                ("MFI Durumu",    strat_.get("mfi_d","?"),   strat_.get("mfi_c","#cdd6f4")),
                ("Hacim",         strat_.get("hacim_d","?"), strat_.get("h_c","#cdd6f4")),
                ("HTF Trend",     f'{strat_.get("htf_d","?")} (240)', strat_.get("htf_c2","#cdd6f4")),
                ("HTF RSI",       strat_.get("htf_rsi_d","?"), strat_.get("htf_c2","#cdd6f4")),
            ]:
                rows_html += (f'<div class="meo-row">'
                              f'<span style="color:#3d5a80;font-size:8px;font-weight:700;">{l}</span>'
                              f'<span style="color:{c__};font-size:8.5px;font-weight:700;">{v}</span></div>')

            st.markdown(f'<div class="meo-panel">'
                        f'<div class="meo-hdr"><span class="meo-lbl">📊 Piyasa Durumu</span>'
                        f'<span class="pill pb">CANLI</span></div>'
                        f'<div class="meo-body">{rows_html}</div></div>', unsafe_allow_html=True)

            # Warnings
            warn_html = ""
            for wtype, wtxt in (strat_.get("warns") or [("g","Normal koşullar")]):
                cls = {"g":"warn-g","r":"warn-r","y":"warn-y"}.get(wtype,"warn-y")
                icon = {"g":"✓","r":"⚠","y":"▲"}.get(wtype,"▲")
                warn_html += f'<div class="{cls}">{icon} {wtxt}</div>'
            st.markdown(f'<div class="meo-panel">'
                        f'<div class="meo-hdr"><span class="meo-lbl">⚠️ Uyarılar</span></div>'
                        f'<div class="meo-body">{warn_html}</div></div>', unsafe_allow_html=True)

        with sp2_:
            # Strategy Plan
            st.markdown(f'<div class="strat-box {strat_.get("st_cls","strat-n")}">'
                        f'<div style="font-family:Rajdhani,sans-serif;font-weight:700;font-size:11px;'
                        f'color:{strat_.get("st_c","#ffd600")};">⚡ Strateji Planı</div>'
                        f'<div style="font-size:9px;font-weight:700;color:{strat_.get("st_c","#ffd600")};'
                        f'margin-top:5px;">{strat_.get("st_d","?")}</div>'
                        f'<pre style="font-size:7.5px;color:#bfcde4;margin-top:5px;'
                        f'white-space:pre-wrap;background:none;border:none;">'
                        f'{strat_.get("st_sub","")}</pre></div>', unsafe_allow_html=True)

            # Alt Senaryo
            alt_dir = "SHORT" if is_bull else "LONG"
            alt_c2  = "#ff3355" if is_bull else "#00ff88"
            st.markdown(f'<div class="strat-box strat-n">'
                        f'<div style="font-family:Rajdhani,sans-serif;font-weight:700;font-size:11px;'
                        f'color:#ffd600;">📐 Alternatif Senaryo</div>'
                        f'<pre style="font-size:7.5px;color:#bfcde4;margin-top:5px;'
                        f'white-space:pre-wrap;background:none;border:none;">'
                        f'• Ana senaryo: {strat_.get("st_type","?")}\n'
                        f'• EMA50 ({fmt(strat_.get("ema50",0),dp_)}) geçilirse\n'
                        f'• <span style="color:{alt_c2};">{alt_dir}</span> değerlendir\n'
                        f'• Önerilen Risk: %{strat_.get("risk_rec",1):.1f} (Skor:{strat_.get("risk_pts",0)}/6)'
                        f'</pre></div>', unsafe_allow_html=True)

            # TP/SL box
            st.markdown(f'<div class="card" style="padding:10px 12px;">'
                        f'<div style="font-size:7px;color:#3d5a80;letter-spacing:1.5px;margin-bottom:6px;">🎯 HEDEF SEVİYELER</div>'
                        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:8.5px;">'
                        f'<div style="color:#00ff88;">TP3: {fmt(smc_.get("tp3"),dp_)}</div>'
                        f'<div style="color:#68d48a;">TP2: {fmt(smc_.get("tp2"),dp_)}</div>'
                        f'<div style="color:#3d8a4d;">TP1: {fmt(smc_.get("tp1"),dp_)}</div>'
                        f'<div style="color:#ff3355;">SL:  {fmt(smc_.get("sl_p"),dp_)}</div>'
                        f'<div style="color:#00d4ff;">R:R 1:{smc_.get("rr",0):.2f}</div>'
                        f'<div style="color:#a855f7;">ATR: {fmt(atr_,dp_)}</div>'
                        f'</div></div>', unsafe_allow_html=True)

            if is_bull and smc_.get("bull_obs"):
                ob1_ = smc_["bull_obs"][0]
                st.markdown(f'<div class="strat-box strat-l" style="text-align:center;">'
                            f'<span class="bp-badge" style="font-size:11px;padding:5px 16px;">'
                            f'▶ BUY-POINT A @ {fmt(ob1_["mid"],dp_)}</span>'
                            f'<div style="font-size:7.5px;color:#00ff88;margin-top:4px;">'
                            f'{fmt(ob1_["hi"],dp_)} — {fmt(ob1_["lo"],dp_)} | Score:{ob1_["score"]}</div>'
                            f'</div>', unsafe_allow_html=True)
            elif not is_bull and smc_.get("bear_obs"):
                ob1_ = smc_["bear_obs"][0]
                st.markdown(f'<div class="strat-box strat-s" style="text-align:center;">'
                            f'<span class="sp-badge" style="font-size:11px;padding:5px 16px;">'
                            f'▶ SELL-POINT A @ {fmt(ob1_["mid"],dp_)}</span>'
                            f'<div style="font-size:7.5px;color:#ff3355;margin-top:4px;">'
                            f'{fmt(ob1_["hi"],dp_)} — {fmt(ob1_["lo"],dp_)} | Score:{ob1_["score"]}</div>'
                            f'</div>', unsafe_allow_html=True)

        with sp3_:
            # Indicator table
            ind_ = strat_.get("ind", {})
            buy_c  = sum(1 for v in ind_.values() if v[2])
            sell_c = len(ind_) - buy_c
            pct_   = round(buy_c/max(len(ind_),1)*100)
            sig_c_ = "#00ff88" if pct_>=65 else "#ff3355" if pct_<=35 else "#ffd600"

            tbl_rows = ""
            for iname, (ival, isig, ibull) in ind_.items():
                cls_ = "ind-buy" if ibull else "ind-sell"
                arr_ = "▲" if ibull else "▼"
                tbl_rows += (f'<tr><td style="color:#3d5a80;">{iname}</td>'
                             f'<td>{ival}</td>'
                             f'<td class="{cls_}">{isig}</td>'
                             f'<td class="{cls_}">{arr_}</td></tr>')

            st.markdown(f'<div class="meo-panel">'
                        f'<div class="meo-hdr"><span class="meo-lbl">📋 İndikatörler</span>'
                        f'<span style="display:flex;gap:3px;">'
                        f'<span class="pill pg" style="font-size:6px;">▲{buy_c}</span>'
                        f'<span class="pill pr" style="font-size:6px;">▼{sell_c}</span>'
                        f'</span></div>'
                        f'<div class="meo-body" style="padding:3px 0;">'
                        f'<table class="ind-tbl"><thead><tr>'
                        f'<th>İND.</th><th>Değer</th><th>Sinyal</th><th>Yön</th>'
                        f'</tr></thead><tbody>{tbl_rows}</tbody></table>'
                        f'</div></div>', unsafe_allow_html=True)

            # Summary signal
            sig_lbl = ("🟢 GÜÇLÜ ALIŞ" if pct_>=65 else
                       "🔴 GÜÇLÜ SATIŞ" if pct_<=35 else "⚡ KARMA SİNYAL")
            st.markdown(f'<div style="background:{sig_c_}10;border:1.5px solid {sig_c_}44;'
                        f'border-radius:8px;padding:10px;text-align:center;margin-top:4px;">'
                        f'<div style="font-size:11px;font-weight:700;color:{sig_c_};">{sig_lbl}</div>'
                        f'<div style="margin:5px 0;">{pbar(pct_,sig_c_,6)}</div>'
                        f'<div style="font-size:8px;color:{sig_c_};">{buy_c} Alış / {sell_c} Satış ({pct_}%)</div>'
                        f'</div>', unsafe_allow_html=True)

            # Backtest stats (Long/Short stats table — image 4 style)
            bt_ = st.session_state.get("bt")
            if bt_ and bt_.get("long_stats") and bt_.get("short_stats"):
                ls_ = bt_["long_stats"]; ss_ = bt_["short_stats"]
                def wr_cls(w):
                    return "wr100" if w==100 else "wr80" if w>=80 else "wr60" if w>=60 else "wrbad"

                lt_rows = "".join(
                    f'<tr><td>{lbl}</td><td>{bt_["long_stats"].get(k,{}).get("times",0)}</td>'
                    f'<td>{bt_["long_stats"].get(k,{}).get("best",0):.1f}%</td>'
                    f'<td>{bt_["long_stats"].get(k,{}).get("now",0):.2f}%</td>'
                    f'<td class="{wr_cls(bt_["long_stats"].get(k,{}).get("wr",0))}">'
                    f'{bt_["long_stats"].get(k,{}).get("wr",0)}%</td></tr>'
                    for k, lbl in [("tp1","TP1✓"),("tp2","TP2✓"),("tp3","TP3✓")]
                )
                st_rows = "".join(
                    f'<tr><td>{lbl}</td><td>{bt_["short_stats"].get(k,{}).get("times",0)}</td>'
                    f'<td>{bt_["short_stats"].get(k,{}).get("best",0):.1f}%</td>'
                    f'<td>{bt_["short_stats"].get(k,{}).get("now",0):.2f}%</td>'
                    f'<td class="{wr_cls(bt_["short_stats"].get(k,{}).get("wr",0))}">'
                    f'{bt_["short_stats"].get(k,{}).get("wr",0)}%</td></tr>'
                    for k, lbl in [("tp1","TP1✓"),("tp2","TP2✓"),("tp3","TP3✓")]
                )
                hdr = '<thead><tr><th>TP</th><th>İşlem</th><th>Best%</th><th>Now%</th><th>WR%</th></tr></thead>'
                st.markdown(
                    f'<div class="meo-panel" style="margin-top:5px;">'
                    f'<div class="meo-hdr"><span class="meo-lbl">📊 Backtest Stats</span></div>'
                    f'<div class="meo-body" style="padding:3px 0;">'
                    f'<div class="shdr-l">LONG — Toplam:{ls_.get("total",0)}</div>'
                    f'<table class="stat-tbl">{hdr}<tbody>{lt_rows}</tbody></table>'
                    f'<div class="shdr-s" style="margin-top:4px;">SHORT — Toplam:{ss_.get("total",0)}</div>'
                    f'<table class="stat-tbl">{hdr}<tbody>{st_rows}</tbody></table>'
                    f'</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="border:1px solid #0d1c2e;border-radius:6px;padding:14px;'
                            'text-align:center;margin-top:5px;">'
                            '<div style="font-size:8px;color:#3d5a80;">Backtest çalıştırın →<br>'
                            'Long/Short Stats burada görünür</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  TAB 3 — SMC ANALİZ
# ═══════════════════════════════════════════════════
with t_an:
    a1_, a2_, a3_ = st.columns(3)
    with a1_:
        st.markdown('<div class="sec">📐 LİKİDİTE HARİTASI</div>', unsafe_allow_html=True)
        for l,k_,c__ in [("BSL","bsl","#ff3355"),("SSL","ssl","#00ff88"),
                          ("PWH","pwh","#ffd600"),("PWL","pwl","#00d4ff")]:
            v_ = smc_.get(k_, 0)
            sw_ = smc_.get(f"{k_}_sw", False)
            q_  = smc_.get(f"{k_}_q", "") or ""
            if v_: kv(l, f"{fmt(v_,dp_)} {'✓swept' if sw_ else '●intact'} {q_}", c__)

        st.markdown('<div class="sec">🔲 ORDER BLOCKS</div>', unsafe_allow_html=True)
        for obs_, lbl_, c__ in [(smc_.get("bull_obs",[]),"BULL OB","#00ff88"),
                                 (smc_.get("bear_obs",[]),"BEAR OB","#ff3355")]:
            for ob_ in (obs_ or [])[:3]:
                st.markdown(
                    f'<div class="rw" style="border-left:3px solid {c__}44;">'
                    f'<span style="color:{c__};font-size:7.5px;">{lbl_}</span>'
                    f'<span style="font-size:8px;">{fmt(ob_.get("hi"),dp_)} — {fmt(ob_.get("lo"),dp_)}</span>'
                    f'<span style="color:#a855f7;font-size:7.5px;">S:{ob_.get("score",0)}</span>'
                    f'</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">📋 SMC OLAYLARI</div>', unsafe_allow_html=True)
        events = [
            (smc_.get("bos_b"),  "BOS Bullish ✓",   "#00ff88"),
            (smc_.get("bos_s"),  "BOS Bearish ✓",   "#ff3355"),
            (smc_.get("choch_b"),"CHoCH Bullish ✓",  "#a855f7"),
            (smc_.get("choch_s"),"CHoCH Bearish ✓",  "#ffd600"),
            (smc_.get("mss_b"),  "MSS Bullish ✓",   "#00ff88"),
            (smc_.get("mss_s"),  "MSS Bearish ✓",   "#ff3355"),
            (smc_.get("fvg_b"),  "FVG Bull aktif ✓", "#00ff88"),
            (smc_.get("fvg_s"),  "FVG Bear aktif ✓", "#ff3355"),
        ]
        any_ev = False
        for ev_, txt_, c__ in events:
            if ev_:
                any_ev = True
                st.markdown(f'<div style="font-size:8.5px;color:{c__};padding:1.5px 0;">▸ {txt_}</div>',
                            unsafe_allow_html=True)
        if not any_ev:
            st.markdown('<div style="font-size:8px;color:#3d5a80;">Belirgin olay yok</div>',
                        unsafe_allow_html=True)

    with a2_:
        st.markdown('<div class="sec">📊 FULL İNDİKATÖR DEĞERLERİ</div>', unsafe_allow_html=True)
        ind_vals = [
            ("RSI (14)",    cv(df,"rsi",50),    70, 30),
            ("MFI (14)",    cv(df,"mfi",50),    80, 20),
            ("ADX",         cv(df,"adx",20),    None, None),
            ("Stoch K",     cv(df,"stoch_k",50),80, 20),
            ("CCI (20)",    cv(df,"cci",0),     100,-100),
            ("Williams %R", cv(df,"willr",-50), -20,-80),
            ("CMF",         cv(df,"cmf",0),     0,  0),
            ("Momentum",    cv(df,"mom",0),     0,  0),
            ("BB Width",    cv(df,"bb_w",2),    None,None),
            ("ATR %",       cv(df,"atr_pct",1), None,None),
            ("Vol Ratio",   cv(df,"vol_r",1),   None,None),
        ]
        for nm_, v_, hi_, lo_ in ind_vals:
            if hi_ is not None and lo_ is not None:
                if nm_ in ("CMF","Momentum"):
                    c__ = "#00ff88" if v_ > 0 else "#ff3355"
                else:
                    c__ = "#ff3355" if v_ > hi_ else "#00ff88" if v_ < lo_ else "#00d4ff"
            elif nm_ in ("ADX","BB Width","ATR %","Vol Ratio"):
                c__ = "#ffd600" if v_ > 30 else "#3d5a80"
            else:
                c__ = "#00d4ff"
            kv(nm_, f"{v_:.2f}", c__)

        if market == "crypto":
            fr_ = safe(fetch_funding, sym_api, fb=0.0)
            kv("Funding Rate", f"{fr_:.4f}%",
               "#ff3355" if fr_>0.05 else "#00ff88" if fr_<-0.02 else "#3d5a80")

    with a3_:
        st.markdown('<div class="sec">💡 KURUMSAL KARAR ENGİNE</div>', unsafe_allow_html=True)
        votes_l = sum([
            is_bull and strat_.get("st_type")=="LONG",
            strat_.get("trend_d","").startswith("Güçlü Yüksel"),
            bool(smc_.get("mss_b")), bool(smc_.get("fvg_b")),
            bias_ == "BULL",
            not smc_.get("is_prem") if is_bull else False,
            bool(smc_.get("bull_obs")),
            30 < rsi_ < 65,
        ])
        votes_s = sum([
            not is_bull and strat_.get("st_type")=="SHORT",
            strat_.get("trend_d","").startswith("Güçlü Düş"),
            bool(smc_.get("mss_s")), bool(smc_.get("fvg_s")),
            bias_ == "BEAR",
            smc_.get("is_prem") if not is_bull else False,
            bool(smc_.get("bear_obs")),
            rsi_ > 50,
        ])
        tot_v = 8
        for lbl_,v_,c__ in [("LONG",votes_l,"#00ff88"),("SHORT",votes_s,"#ff3355"),
                              ("Nötr",max(0,tot_v-votes_l-votes_s),"#3d5a80")]:
            st.markdown(
                f'<div class="rw"><span style="color:#3d5a80;font-size:7.5px;min-width:40px;">{lbl_}</span>'
                f'<div style="flex:1;margin:0 6px;">{pbar(v_/tot_v*100,c__,5)}</div>'
                f'<span style="color:{c__};font-size:8.5px;font-weight:700;">{v_}/{tot_v}</span></div>',
                unsafe_allow_html=True)

        if   votes_l >= 6: fc2_="#00ff88"; fd_="🟢 GÜÇLÜ LONG KONSENSÜS"
        elif votes_s >= 6: fc2_="#ff3355"; fd_="🔴 GÜÇLÜ SHORT KONSENSÜS"
        elif votes_l >= 5: fc2_="#68d48a"; fd_="🟢 HAFIF LONG"
        elif votes_s >= 5: fc2_="#ff7088"; fd_="🔴 HAFIF SHORT"
        else:              fc2_="#3d5a80"; fd_="⚪ NÖTR — BEKLE"

        st.markdown(f'<div style="background:{fc2_}10;border:1.5px solid {fc2_}44;'
                    f'border-radius:7px;padding:10px;text-align:center;margin-top:6px;'
                    f'font-size:11px;font-weight:700;color:{fc2_};">{fd_}</div>',
                    unsafe_allow_html=True)

        # Fibonacci levels
        if smc_.get("fibs"):
            st.markdown('<div class="sec" style="margin-top:10px;">📐 FİBONACCİ</div>',
                        unsafe_allow_html=True)
            fc = {"61.8%":"#a855f7","78.6%":"#8b45cc","50%":"#ffd600",
                  "38.2%":"#00d4ff","23.6%":"#4a90a4","0%":"#ff3355","100%":"#00ff88"}
            for lbl_, val_ in smc_["fibs"].items():
                if val_ and val_ > 0:
                    c__ = fc.get(lbl_, "#3d5a80")
                    in_ote = smc_.get("ote_lo",0) <= val_ <= smc_.get("ote_hi",0)
                    kv(lbl_, fmt(val_, dp_) + (" ◀OTE" if in_ote else ""), c__)


# ═══════════════════════════════════════════════════
#  TAB 4 — BACKTEST
# ═══════════════════════════════════════════════════
with t_bt:
    bt_ = st.session_state.get("bt")
    if not st.session_state.get("bt_done"):
        st.markdown('<div style="text-align:center;padding:60px;">'
                    '<div style="font-family:Bebas Neue,cursive;font-size:3rem;'
                    'color:#0d1c2e;letter-spacing:.1em;">BACKTEST</div>'
                    '<div style="color:#3d5a80;font-size:9px;margin-top:8px;">'
                    'Sidebar → ▶ BACKTEST</div></div>', unsafe_allow_html=True)
    elif bt_ and bt_.get("error"):
        st.warning(f"⚠ {bt_['error']}")
    elif bt_ and bt_.get("metrics"):
        m_ = bt_["metrics"]; trades_ = bt_.get("trades",[])
        r1c1,r1c2,r1c3,r1c4,r1c5,r1c6,r1c7,r1c8 = st.columns(8)
        for col_, lbl_, v_ in [
            (r1c1,"İşlem",m_.get("total",0)), (r1c2,"Win Rate",f"{m_.get('win_rate',0):.1f}%"),
            (r1c3,"Net P&L",f"${m_.get('net_pnl',0):+,.2f}"), (r1c4,"Pf",f"{m_.get('profit_factor',0):.2f}"),
            (r1c5,"Max DD",f"{m_.get('max_dd',0):.1f}%"), (r1c6,"Sharpe",f"{m_.get('sharpe',0):.2f}"),
            (r1c7,"Sortino",f"{m_.get('sortino',0):.2f}"), (r1c8,"ROI",f"{m_.get('roi',0):.1f}%"),
        ]:
            with col_: st.metric(lbl_, v_)

        st.markdown("<hr>", unsafe_allow_html=True)
        bc1_, bc2_ = st.columns([3,1])
        with bc1_:
            eq_ = bt_.get("eq",[capital])
            fig_eq = go.Figure()
            fig_eq.add_scatter(x=list(range(len(eq_))), y=eq_, mode="lines",
                               line=dict(color="#00ff88",width=1.5),
                               fill="tozeroy", fillcolor="rgba(0,255,136,0.04)")
            fig_eq.add_scatter(x=[0,len(eq_)-1], y=[capital,capital], mode="lines",
                               line=dict(color="rgba(255,255,255,0.12)",width=0.8,dash="dash"))
            pk_ = capital; dd_arr = []
            for e__ in eq_:
                if e__ > pk_: pk_ = e__
                dd_arr.append(-(pk_-e__)/max(pk_,1e-9)*100)
            fig_eq.add_scatter(x=list(range(len(dd_arr))), y=dd_arr, mode="lines",
                               line=dict(color="rgba(255,51,85,0.3)",width=0.8),
                               fill="tozeroy", fillcolor="rgba(255,51,85,0.05)", yaxis="y2")
            fig_eq.update_layout(height=300, margin=dict(l=0,r=60,t=18,b=0),
                paper_bgcolor="#040810", plot_bgcolor="#040810",
                font=dict(color="#3d5a80",size=8), showlegend=False,
                title=dict(text="📈 Equity + Drawdown", font=dict(size=9,color="#00d4ff"),x=0),
                yaxis=dict(side="right",gridcolor="#091525"),
                yaxis2=dict(side="left",overlaying="y",showgrid=False,range=[-100,0],
                            tickfont=dict(color="#ff3355",size=8)),
                xaxis=dict(gridcolor="#091525"))
            st.plotly_chart(fig_eq, use_container_width=True, config={"displayModeBar":False})

            # Trade log
            st.markdown('<div class="sec">📋 İŞLEM LOGU (son 30)</div>', unsafe_allow_html=True)
            for t__ in list(reversed(trades_))[:30]:
                cls_ = "trow-w" if t__.get("win") else "trow-l"
                d_   = "🟢" if t__.get("dir")=="LONG" else "🔴"
                st.markdown(
                    f'<div class="{cls_}">{d_} {t__.get("dir","?")} | {t__.get("time","?")} | '
                    f'E:{fmt(t__.get("entry"),dp_)} X:{fmt(t__.get("exit"),dp_)} | '
                    f'{t__.get("outcome","?")} R:{t__.get("rr",0):.1f} | '
                    f'<b>${t__.get("pnl",0):+,.4f}</b></div>', unsafe_allow_html=True)

        with bc2_:
            st.markdown('<div class="sec">📊 METRIKLER</div>', unsafe_allow_html=True)
            for l_,v_,c__ in [
                ("Toplam", str(m_.get("total",0)), "#00d4ff"),
                ("Win Rate", f"{m_.get('win_rate',0):.1f}%",
                 "#00ff88" if m_.get("win_rate",0)>=55 else "#ff3355"),
                ("Net P&L", f"${m_.get('net_pnl',0):+,.2f}",
                 "#00ff88" if m_.get("net_pnl",0)>0 else "#ff3355"),
                ("Prof.Factor", f"{m_.get('profit_factor',0):.2f}",
                 "#00ff88" if m_.get("profit_factor",0)>=1.5 else "#ff3355"),
                ("Max DD", f"{m_.get('max_dd',0):.1f}%",
                 "#00ff88" if m_.get("max_dd",0)<=10 else "#ff3355"),
                ("Sharpe", f"{m_.get('sharpe',0):.2f}", "#00d4ff"),
                ("Sortino", f"{m_.get('sortino',0):.2f}", "#00d4ff"),
                ("Avg Win", f"${m_.get('avg_win',0):.4f}", "#00ff88"),
                ("Avg Loss", f"${m_.get('avg_loss',0):.4f}", "#ff3355"),
                ("Final Eq", f"${m_.get('final_eq',0):,.2f}",
                 "#00ff88" if m_.get("roi",0)>0 else "#ff3355"),
                ("ROI", f"{m_.get('roi',0):.2f}%",
                 "#00ff88" if m_.get("roi",0)>0 else "#ff3355"),
            ]: kv(l_, v_, c__)

            if trades_:
                buf_ = io.StringIO()
                w_ = csv.DictWriter(buf_, fieldnames=list(trades_[0].keys()))
                w_.writeheader(); w_.writerows(trades_)
                st.markdown(dlbtn(buf_.getvalue(), f"bt_{sym_lbl}.csv","📥 CSV İndir"),
                            unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎲 Monte Carlo Çalıştır", use_container_width=True):
                with st.spinner("Simüle ediliyor…"):
                    mc_r = safe(run_mc, trades_, capital, 1000, 60, fb={})
                st.session_state["mc"] = mc_r; st.rerun()

# ═══════════════════════════════════════════════════
#  TAB 5 — MONTE CARLO
# ═══════════════════════════════════════════════════
with t_mc:
    mc1_, mc2_, mc3_ = st.columns(3)
    with mc1_:
        k_wr = st.slider("Win Rate (%)", 10, 90, 55, 5, key="kwr")
        k_aw = st.slider("Avg Win (%)",  0.5, 20.0, 2.0, 0.5, key="kaw")
        k_al = st.slider("Avg Loss (%)", 0.5, 20.0, 1.0, 0.5, key="kal")
        k_cap= st.number_input("Sermaye", value=capital, min_value=100, key="kcap")
    with mc2_:
        b = k_aw / max(k_al, 1e-9); p = k_wr/100; q = 1-p
        kk = (b*p - q) / max(b, 1e-9)
        st.markdown('<div class="sec">KELLY SONUÇLARI</div>', unsafe_allow_html=True)
        kv("Full Kelly",        f"{kk*100:.1f}%",   "#ffd600")
        kv("Half Kelly (Öner)", f"{kk/2*100:.1f}%", "#00ff88")
        kv("Edge",              f"{(b*p-q)*100:.1f}%","#a855f7")
        if st.button("🎲 Kelly MC", use_container_width=True, key="kmc_btn"):
            sims_k = np.zeros((500,51)); sims_k[:,0] = k_cap; np.random.seed(42)
            for s_ in range(500):
                eq_k = k_cap
                for j_ in range(50):
                    eq_k *= (1+k_aw/100) if np.random.random()<k_wr/100 else (1-k_al/100)
                    sims_k[s_,j_+1] = max(0, eq_k)
            st.session_state["mc"] = {
                "p50":np.percentile(sims_k,50,axis=0).tolist(),
                "p10":np.percentile(sims_k,10,axis=0).tolist(),
                "p90":np.percentile(sims_k,90,axis=0).tolist(),
                "ruin":round((sims_k[:,-1]<k_cap*.5).mean()*100,1),
                "med":round(float(np.median(sims_k[:,-1])),2)}
            st.rerun()
    with mc3_:
        ret_ = df["close"].pct_change().dropna()
        if len(ret_) >= 20:
            vp_ = abs(np.percentile(ret_, 5))
            cvp_ = abs(ret_[ret_ <= -vp_].mean()) if (ret_ <= -vp_).any() else vp_
            st.markdown('<div class="sec">VaR ANALİZİ</div>', unsafe_allow_html=True)
            kv("VaR 95%",    f"{vp_*100:.3f}%",    "#ff3355")
            kv("VaR $",      f"${capital*vp_:,.2f}","#ff3355")
            kv("CVaR",       f"{cvp_*100:.3f}%",   "#ffd600")
            kv("CVaR $",     f"${capital*cvp_:,.2f}","#ffd600")
            kv("Vol Günlük", f"{ret_.std()*100:.3f}%","#3d5a80")
            kv("Vol Yıllık", f"{ret_.std()*np.sqrt(252)*100:.1f}%","#3d5a80")

    mc_r_ = st.session_state.get("mc")
    if mc_r_:
        st.markdown("<hr>", unsafe_allow_html=True)
        fig_mc = go.Figure()
        x_mc = list(range(len(mc_r_["p50"])))
        fig_mc.add_scatter(x=x_mc, y=mc_r_["p90"], mode="lines",
                           line=dict(color="rgba(0,255,136,0.2)",width=0.5))
        fig_mc.add_scatter(x=x_mc, y=mc_r_["p10"], mode="lines",
                           fill="tonexty", fillcolor="rgba(0,255,136,0.06)",
                           line=dict(color="rgba(255,51,85,0.2)",width=0.5))
        fig_mc.add_scatter(x=x_mc, y=mc_r_["p50"], mode="lines",
                           line=dict(color="#00ff88",width=2.5))
        fig_mc.add_scatter(x=[0,len(x_mc)-1], y=[capital,capital], mode="lines",
                           line=dict(color="rgba(255,255,255,0.12)",width=0.8,dash="dash"))
        fig_mc.update_layout(height=280, margin=dict(l=0,r=60,t=18,b=0),
            paper_bgcolor="#040810", plot_bgcolor="#040810",
            font=dict(color="#3d5a80",size=8), showlegend=False,
            title=dict(text="🎲 Monte Carlo (1000 sim)", font=dict(size=9,color="#00d4ff"),x=0),
            yaxis=dict(side="right",gridcolor="#091525"),xaxis=dict(gridcolor="#091525"))
        st.plotly_chart(fig_mc, use_container_width=True, config={"displayModeBar":False})
        mc_c1,mc_c2,mc_c3,mc_c4 = st.columns(4)
        with mc_c1: st.metric("Medyan Son",  f"${mc_r_.get('med',0):,.0f}")
        with mc_c2: st.metric("P10 (Kötü)",  f"${mc_r_['p10'][-1]:,.0f}")
        with mc_c3: st.metric("P90 (İyi)",   f"${mc_r_['p90'][-1]:,.0f}")
        with mc_c4: st.metric("Ruin Riski",  f"{mc_r_.get('ruin',0):.1f}%")


# ═══════════════════════════════════════════════════
#  TAB 6 — ULTRA SCANNER (Yüksek Potansiyel Tarama)
# ═══════════════════════════════════════════════════
with t_sc:
    # ── Üst kontrol satırı ────────────────────────
    sc_top1, sc_top2, sc_top3, sc_top4 = st.columns([2,2,2,2])
    with sc_top1:
        sc_market = st.selectbox("📊 Piyasa", ["🪙 Kripto","💱 Forex","🏛 US Hisse","🇹🇷 BIST"], key="scmkt")
    with sc_top2:
        if "Kripto" in sc_market:
            sc_scope = st.selectbox("Kapsam", ["Top20","Top50","Top100","Custom"], key="scscope")
        elif "Forex" in sc_market:
            sc_scope = st.selectbox("Kapsam", ["Tüm Forex","Major","Custom"], key="scscope")
        elif "US" in sc_market:
            sc_scope = st.selectbox("Kapsam", ["Top20","Top40","Custom"], key="scscope")
        else:
            sc_scope = st.selectbox("Kapsam", ["Top20","Top40","Tümü"], key="scscope")
    with sc_top3:
        _sc_tf_opts_common = ["1m","3m","5m","10m","15m","30m","1s","4s","1g"]
        _sc_tf_def = {"Kripto":4,"Forex":4,"US":4,"BIST":6}
        _sc_def_idx = next((v for k,v in _sc_tf_def.items() if k in sc_market), 4)
        sc_tf = st.selectbox("⏱ Zaman Dilimi",
                              _sc_tf_opts_common,
                              index=_sc_def_idx,
                              key="sctf",
                              format_func=lambda x: f"{x} · {CFG.TF_DISPLAY.get(x,'')}" if hasattr(CFG,'TF_DISPLAY') else x)
    with sc_top4:
        sc_min_score = st.slider("Min Skor", 30, 85, 55, key="sc_min_score")

    # Custom sembol girişi
    if sc_scope == "Custom":
        sc_custom = st.text_input("Özel semboller (virgülle ayır)", "BTC,ETH,SOL,AAPL", key="sccust")
    else:
        sc_custom = ""

    # Filtreler satırı
    fc1, fc2, fc3, fc4, fc5 = st.columns(5)
    with fc1: sc_need_mss = st.checkbox("MSS Gerekli",  False, key="sc_mss")
    with fc2: sc_need_bos = st.checkbox("BOS Gerekli",  False, key="sc_bos")
    with fc3: sc_need_fvg = st.checkbox("FVG Gerekli",  False, key="sc_fvg")
    with fc4: sc_dir_only = st.selectbox("Yön", ["Hepsi","Sadece LONG","Sadece SHORT"], key="sc_dir")
    with fc5: sc_min_rr   = st.number_input("Min R:R", 0.0, 5.0, 1.5, 0.1, key="sc_rr")

    # Başlat butonu
    if st.button("🔭 ULTRA SCANNER BAŞLAT", use_container_width=True, type="primary", key="scrun"):
        # Sembol listesini oluştur
        if "Kripto" in sc_market:
            sc_mkt = "crypto"
            if sc_scope == "Custom":
                scan_syms = [s.strip().upper()+"USDT" for s in sc_custom.split(",") if s.strip()]
            else:
                n_ = {"Top20":20,"Top50":50,"Top100":100}.get(sc_scope,20)
                scan_syms = [TOP100[k]["sym"] for k in list(TOP100.keys())[:n_]]
        elif "Forex" in sc_market:
            sc_mkt = "forex"
            if sc_scope == "Custom":
                scan_syms = [s.strip() for s in sc_custom.split(",") if s.strip()]
            elif sc_scope == "Major":
                scan_syms = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CHF","XAU/USD","GBP/JPY","EUR/JPY"]
            else:
                scan_syms = list(CFG.FOREX.keys())
        elif "US" in sc_market:
            sc_mkt = "stock_us"
            if sc_scope == "Custom":
                scan_syms = [s.strip().upper() for s in sc_custom.split(",") if s.strip()]
            else:
                n_ = {"Top20":20,"Top40":40}.get(sc_scope,20)
                scan_syms = CFG.US_STOCKS[:n_]
        else:
            sc_mkt = "stock_bist"
            if sc_scope == "Top20":
                scan_syms = [s+".IS" for s in CFG.BIST[:20]]
            elif sc_scope == "Top40":
                scan_syms = [s+".IS" for s in CFG.BIST[:40]]
            else:
                scan_syms = [s+".IS" for s in CFG.BIST]

        with st.spinner(f"🔭 {len(scan_syms)} sembol Ultra ICT/SMC taranıyor…"):
            res_ = safe(run_scanner, scan_syms, sc_tf, sc_mkt, sc_min_score, fb=[])
        st.session_state["scan"] = res_ or []
        st.session_state["scan_params"] = {
            "market":sc_market,"tf":sc_tf,"count":len(scan_syms),"min_score":sc_min_score
        }

    # ── Sonuçlar bölümü ──────────────────────────────
    scan_res = st.session_state.get("scan", [])
    sp_ = st.session_state.get("scan_params", {})

    # Filtrele
    if scan_res:
        scan_filt = []
        for r_ in scan_res:
            if sc_need_mss and not r_.get("mss"): continue
            if sc_need_bos and not r_.get("bos"): continue
            if sc_need_fvg and not r_.get("fvg"): continue
            if sc_dir_only == "Sadece LONG"  and r_.get("dir") != "LONG":  continue
            if sc_dir_only == "Sadece SHORT" and r_.get("dir") != "SHORT": continue
            if r_.get("rr",0) < sc_min_rr: continue
            scan_filt.append(r_)
    else:
        scan_filt = []

    if not scan_res:
        st.markdown(
            '''<div style="text-align:center;padding:60px;color:#3d5a80;font-size:9px;">
            <div style="font-size:2rem;margin-bottom:10px;">🔭</div>
            Ultra Scanner başlatın — Forex · Kripto · US Hisse · BIST<br>
            ICT/SMC: MSS · BOS · CHoCH · OB · FVG · Liquidity
            </div>''', unsafe_allow_html=True)
    else:
        # Özet başlık
        long_cnt  = sum(1 for r in scan_filt if r.get("dir")=="LONG")
        short_cnt = sum(1 for r in scan_filt if r.get("dir")=="SHORT")
        avg_sc    = sum(r.get("score",0) for r in scan_filt)/max(len(scan_filt),1)
        st.markdown(
            f'''<div style="display:flex;gap:8px;margin-bottom:8px;font-size:8.5px;">
            <div style="background:rgba(0,212,255,0.07);border:1px solid rgba(0,212,255,0.2);
              border-radius:5px;padding:5px 14px;color:#00d4ff;">
              📊 {sp_.get("market","?")} · {sp_.get("tf","?")} · {sp_.get("count","?")} sembol</div>
            <div style="background:rgba(0,255,136,0.07);border:1px solid rgba(0,255,136,0.2);
              border-radius:5px;padding:5px 14px;color:#00ff88;">▲ LONG: {long_cnt}</div>
            <div style="background:rgba(255,51,85,0.07);border:1px solid rgba(255,51,85,0.2);
              border-radius:5px;padding:5px 14px;color:#ff3355;">▼ SHORT: {short_cnt}</div>
            <div style="background:rgba(255,214,0,0.07);border:1px solid rgba(255,214,0,0.2);
              border-radius:5px;padding:5px 14px;color:#ffd600;">Ort Skor: {avg_sc:.0f}</div>
            <div style="background:rgba(168,85,247,0.07);border:1px solid rgba(168,85,247,0.2);
              border-radius:5px;padding:5px 14px;color:#a855f7;">{len(scan_filt)} setup</div>
            </div>''', unsafe_allow_html=True)

        # Tablo başlığı
        st.markdown(
            '''<div style="display:grid;grid-template-columns:100px 60px 55px 50px 50px 50px 55px 70px 1fr;
              gap:4px;padding:5px 10px;background:rgba(0,212,255,0.06);
              border:1px solid rgba(0,212,255,0.12);border-radius:5px;
              font-size:7.5px;font-weight:700;color:#3d5a80;letter-spacing:0.8px;margin-bottom:3px;">
              <span>SEMBOL</span><span>YÖN</span><span>SKOR</span><span>R:R</span>
              <span>ADX</span><span>RSI</span><span>VOL</span><span>SINYALLER</span><span>GÜÇLÜ TARAF</span>
            </div>''', unsafe_allow_html=True)

        for r_ in scan_filt[:30]:
            dc_ = "#00ff88" if r_.get("dir")=="LONG" else "#ff3355"
            bc_ = "rgba(0,255,136,0.06)" if r_.get("dir")=="LONG" else "rgba(255,51,85,0.06)"
            score_ = r_.get("score",0)
            # Sinyal badges
            sig_html = ""
            if r_.get("mss"): sig_html += '<span style="background:rgba(168,85,247,0.2);color:#a855f7;padding:1px 4px;border-radius:3px;font-size:7px;margin-right:2px;">MSS</span>'
            if r_.get("bos"): sig_html += '<span style="background:rgba(0,255,136,0.2);color:#00ff88;padding:1px 4px;border-radius:3px;font-size:7px;margin-right:2px;">BOS</span>'
            if r_.get("choch"): sig_html += '<span style="background:rgba(255,165,0,0.2);color:#ffa500;padding:1px 4px;border-radius:3px;font-size:7px;margin-right:2px;">CHoCH</span>'
            if r_.get("fvg"): sig_html += '<span style="background:rgba(0,212,255,0.2);color:#00d4ff;padding:1px 4px;border-radius:3px;font-size:7px;margin-right:2px;">FVG</span>'
            # Skor bar
            bar_w = int(score_ * 0.6)
            bar_color = "#00ff88" if score_>=75 else "#ffd600" if score_>=55 else "#ff6b35"
            st.markdown(
                f'''<div class="scan-row" style="display:grid;grid-template-columns:100px 60px 55px 50px 50px 50px 55px 70px 1fr;
                  gap:4px;align-items:center;padding:6px 10px;margin-bottom:3px;
                  background:{bc_};border:1px solid rgba(255,255,255,0.04);border-left:3px solid {dc_};
                  border-radius:6px;font-size:8.5px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.2);"
                  onclick="navigator.clipboard&&navigator.clipboard.writeText('{r_.get("sym","")}').then(()=>this.style.borderLeftWidth='5px')">
                  <span style="font-weight:700;color:{dc_};">{r_.get("sym","?")}</span>
                  <span style="color:{dc_};font-weight:700;font-size:9px;">{"▲ LONG" if r_.get("dir")=="LONG" else "▼ SHORT"}</span>
                  <span>
                    <div style="background:#0a1828;border-radius:3px;height:4px;width:60px;overflow:hidden;">
                      <div style="background:{bar_color};height:4px;width:{bar_w}px;border-radius:3px;transition:.3s;"></div>
                    </div>
                    <span style="color:{bar_color};font-size:7.5px;">{score_}</span>
                  </span>
                  <span style="color:{"#00ff88" if r_.get("rr",0)>=2 else "#ffd600" if r_.get("rr",0)>=1.5 else "#ff6b35"};">
                    1:{r_.get("rr",0):.1f}</span>
                  <span style="color:{"#00ff88" if r_.get("adx",0)>=25 else "#ffd600"};">{r_.get("adx",0):.0f}</span>
                  <span style="color:{"#ff3355" if r_.get("rsi",50)>65 else "#00ff88" if r_.get("rsi",50)<35 else "#c8d8f0"};">
                    {r_.get("rsi",0):.0f}</span>
                  <span style="color:{"#00ff88" if r_.get("vol_r",1)>=1.5 else "#3d5a80"};">{r_.get("vol_r",1):.1f}x</span>
                  <span>{sig_html}</span>
                  <span style="color:#3d5a80;font-size:7.5px;">{r_.get("reasons","")}</span>
                </div>''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  TAB 7 — FIRSATLAR  (Async Arka Plan Tarayici)
# ═══════════════════════════════════════════════════
with t_fi:
    fi_ts  = st.session_state.get("firsatlar_ts", "—")
    fi_res = st.session_state.get("firsatlar", [])

    h1_fi, h2_fi, h3_fi = st.columns([3, 1, 1])
    with h1_fi:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:12px;">' +
            '<div class="apex-logo" style="font-size:1.4rem;">FIRSATLAR</div>' +
            '<div style="font-size:8px;color:#3d5a80;">Skor &gt; 80 · 20 Forex + 20 Kripto · 1h · 5dk auto</div>' +
            '</div>', unsafe_allow_html=True)
    with h2_fi:
        _bg_ok = st.session_state.get("_bg_started", False)
        st.markdown(
            f'<div style="font-size:8px;color:#3d5a80;padding-top:4px;">' +
            f'Thread: <b style="color:{"#00ff88" if _bg_ok else "#ff3355"};">{"Aktif" if _bg_ok else "Bekliyor"}</b>' +
            f'</div>', unsafe_allow_html=True)
    with h3_fi:
        st.markdown(
            f'<div style="font-size:8px;color:#3d5a80;padding-top:4px;">' +
            f'Son: <b style="color:#00d4ff;">{fi_ts}</b></div>', unsafe_allow_html=True)

    fi_btn_col, fi_info_col = st.columns([1, 5])
    with fi_btn_col:
        if st.button("Hemen Tara", key="fi_manual", use_container_width=True):
            with st.spinner("40 sembol taranıyor (1h)..."):
                _manual_res = []
                _syms_mkt = [(s,"forex") for s in _BG_FOREX] + [(s,"crypto") for s in _BG_CRYPTO]
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as _ex_fi:
                    _futs_fi = {_ex_fi.submit(scan_one, sm[0], "1h", sm[1]): sm for sm in _syms_mkt}
                    for _f_fi in concurrent.futures.as_completed(_futs_fi, timeout=90):
                        try:
                            _r_fi = _f_fi.result()
                            if _r_fi and _r_fi.get("score", 0) > 80:
                                _manual_res.append(_r_fi)
                        except: pass
                _manual_res.sort(key=lambda x: x["score"], reverse=True)
                st.session_state["firsatlar"]    = _manual_res
                st.session_state["firsatlar_ts"] = datetime.now().strftime("%H:%M:%S")
                fi_res = _manual_res
                st.rerun()
    with fi_info_col:
        st.markdown(
            '<div style="font-size:8px;color:#3d5a80;padding:6px 10px;">' +
            'Daemon thread arka planda 5 dakikada bir tarar. Anlik tarama icin "Hemen Tara" butonuna basin.</div>',
            unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#091525;margin:4px 0;'>", unsafe_allow_html=True)

    if not fi_res:
        st.markdown(
            '<div style="text-align:center;padding:60px 20px;">' +
            '<div style="font-size:11px;color:#3d5a80;margin-bottom:8px;">Arka plan tarayicisi ilk taramayi tamamliyor...</div>' +
            '<div style="font-size:9px;color:#1a2a3a;">Skor &gt; 80 olan ICT/SMC setupleri burada gorunecek.</div>' +
            '</div>', unsafe_allow_html=True)
    else:
        fi_long  = [r for r in fi_res if r.get("dir") == "LONG"]
        fi_short = [r for r in fi_res if r.get("dir") == "SHORT"]
        fi_avg   = sum(r.get("score",0) for r in fi_res) / max(len(fi_res), 1)

        fm1, fm2, fm3, fm4, fm5 = st.columns(5)
        with fm1: st.metric("Firsat", len(fi_res))
        with fm2: st.metric("LONG",  len(fi_long))
        with fm3: st.metric("SHORT", len(fi_short))
        with fm4: st.metric("Ort Skor", f"{fi_avg:.0f}")
        with fm5: st.metric("En Iyi",  fi_res[0].get("sym","—") if fi_res else "—")

        st.markdown(
            '<div style="display:grid;grid-template-columns:95px 70px 58px 52px 52px 52px 60px 80px 1fr;' +
            'gap:4px;padding:5px 10px;background:rgba(0,212,255,0.07);' +
            'border:1px solid rgba(0,212,255,0.15);border-radius:5px;margin:6px 0 3px;' +
            'font-size:7.5px;font-weight:700;color:#3d5a80;letter-spacing:0.8px;">' +
            '<span>SEMBOL</span><span>YON</span><span>SKOR</span><span>R:R</span>' +
            '<span>ADX</span><span>RSI</span><span>VOL</span><span>SINYAL</span><span>ACIKLAMA</span>' +
            '</div>', unsafe_allow_html=True)

        for _r in fi_res[:40]:
            _dc  = "#00ff88" if _r.get("dir")=="LONG" else "#ff3355"
            _bc  = "rgba(0,255,136,0.05)" if _r.get("dir")=="LONG" else "rgba(255,51,85,0.05)"
            _sc  = _r.get("score",0)
            _rr  = _r.get("rr",0)
            _adx = _r.get("adx",0)
            _rsi = _r.get("rsi",50)
            _vol = _r.get("vol_r",1)
            _mkt = _r.get("market","")
            _bw  = int(_sc * 0.56)
            _bc2 = "#00ff88" if _sc>=90 else "#ffd600" if _sc>=85 else "#ff6b35"
            _mkt_c = "#a855f7" if _mkt=="forex" else "#00d4ff"
            _mkt_l = "FX" if _mkt=="forex" else "BTC"
            _sigs  = ""
            if _r.get("mss"):   _sigs += '<span style="background:rgba(168,85,247,.2);color:#a855f7;padding:1px 4px;border-radius:3px;font-size:7px;margin-right:2px;">MSS</span>'
            if _r.get("bos"):   _sigs += '<span style="background:rgba(0,255,136,.2);color:#00ff88;padding:1px 4px;border-radius:3px;font-size:7px;margin-right:2px;">BOS</span>'
            if _r.get("choch"): _sigs += '<span style="background:rgba(255,165,0,.2);color:#ffa500;padding:1px 4px;border-radius:3px;font-size:7px;margin-right:2px;">CHoCH</span>'
            if _r.get("fvg"):   _sigs += '<span style="background:rgba(0,212,255,.2);color:#00d4ff;padding:1px 4px;border-radius:3px;font-size:7px;margin-right:2px;">FVG</span>'
            _adx_c = "#00ff88" if _adx>=30 else "#ffd600" if _adx>=20 else "#3d5a80"
            _rsi_c = "#ff3355" if _rsi>65 else "#00ff88" if _rsi<35 else "#cdd6f4"
            _rr_c  = "#00ff88" if _rr>=3 else "#ffd600" if _rr>=2 else "#ff6b35"
            _vol_c = "#00ff88" if _vol>=1.5 else "#3d5a80"
            _dir_lbl = "LONG" if _r.get("dir")=="LONG" else "SHORT"
            st.markdown(
                f'<div style="display:grid;grid-template-columns:95px 70px 58px 52px 52px 52px 60px 80px 1fr;' +
                f'gap:4px;align-items:center;padding:6px 10px;margin-bottom:2px;' +
                f'background:{_bc};border:1px solid #0d1c2e;border-left:3px solid {_dc};border-radius:5px;font-size:8.5px;">' +
                f'<span style="font-weight:700;color:{_dc};">{_r.get("sym","?")} <span style="font-size:7px;color:{_mkt_c};">[{_mkt_l}]</span></span>' +
                f'<span style="color:{_dc};font-weight:700;">{_dir_lbl}</span>' +
                f'<span><div style="background:#091525;border-radius:3px;height:4px;width:56px;overflow:hidden;margin-bottom:2px;">' +
                f'<div style="background:{_bc2};height:4px;width:{_bw}px;border-radius:3px;"></div></div>' +
                f'<span style="color:{_bc2};font-size:7.5px;font-weight:700;">{_sc}</span></span>' +
                f'<span style="color:{_rr_c};">1:{_rr:.1f}</span>' +
                f'<span style="color:{_adx_c};">{_adx:.0f}</span>' +
                f'<span style="color:{_rsi_c};">{_rsi:.0f}</span>' +
                f'<span style="color:{_vol_c};">{_vol:.1f}x</span>' +
                f'<span>{_sigs}</span>' +
                f'<span style="color:#3d5a80;font-size:7.5px;">{_r.get("reasons","")}</span>' +
                f'</div>', unsafe_allow_html=True)

        if fi_long or fi_short:
            st.markdown("<br>", unsafe_allow_html=True)
            _lc2, _rc2 = st.columns(2)
            with _lc2:
                st.markdown('<div class="sec">LONG FIRSATLAR</div>', unsafe_allow_html=True)
                for _r in fi_long[:10]:
                    st.markdown(
                        f'<div class="rw">' +
                        f'<span style="color:#00ff88;font-weight:700;">{_r.get("sym","")}</span>' +
                        f'<span style="color:#3d5a80;font-size:8px;">Skor:{_r.get("score",0)} 1:{_r.get("rr",0):.1f}</span>' +
                        f'<span style="color:#a855f7;font-size:7.5px;">{"MSS" if _r.get("mss") else ""}</span>' +
                        f'</div>', unsafe_allow_html=True)
            with _rc2:
                st.markdown('<div class="sec">SHORT FIRSATLAR</div>', unsafe_allow_html=True)
                for _r in fi_short[:10]:
                    st.markdown(
                        f'<div class="rw">' +
                        f'<span style="color:#ff3355;font-weight:700;">{_r.get("sym","")}</span>' +
                        f'<span style="color:#3d5a80;font-size:8px;">Skor:{_r.get("score",0)} 1:{_r.get("rr",0):.1f}</span>' +
                        f'<span style="color:#a855f7;font-size:7.5px;">{"MSS" if _r.get("mss") else ""}</span>' +
                        f'</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# ═══════════════════════════════════════════════════
#  TAB 8 — TAHMİN  (Yükseliş / Düşüş Beklentisi)
# ═══════════════════════════════════════════════════
with t_pr:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;padding:8px 14px;'
        'background:linear-gradient(90deg,rgba(255,214,0,0.06),transparent);'
        'border:1px solid rgba(255,214,0,0.15);border-radius:8px;margin-bottom:10px;">'
        '<span style="font-size:1.4rem;">🎯</span>'
        '<div><div style="font-size:11px;font-weight:800;color:#ffd600;letter-spacing:1px;">TAHMİN MOTORU</div>'
        '<div style="font-size:8px;color:#3d5a80;">Teknik analiz bazlı yükseliş/düşüş beklentisi · Forex · Kripto · BIST</div></div>'
        '</div>',
        unsafe_allow_html=True)

    pr_c1, pr_c2, pr_c3, pr_c4 = st.columns([2,2,2,2])
    with pr_c1:
        pr_market = st.selectbox("📊 Piyasa", ["🪙 Kripto","💱 Forex","🇹🇷 BIST","🏛 US"], key="pr_mkt")
    with pr_c2:
        pr_tf = st.selectbox("⏱ Zaman Dilimi", ["1h","4h","1d","15m"], key="pr_tf")
    with pr_c3:
        pr_scope = st.selectbox("Kapsam", ["Top20","Top10","Top5","Custom"], key="pr_scope")
    with pr_c4:
        pr_min_conf = st.slider("Min Güven %", 10, 80, 30, key="pr_conf")

    if pr_scope == "Custom":
        pr_custom = st.text_input("Özel semboller (virgülle)", "BTC,ETH,SOL,EUR/USD,GBP/USD", key="pr_cust")
    else:
        pr_custom = ""

    if st.button("🎯 TAHMİN TARAMASI BAŞLAT", use_container_width=True, type="primary", key="pr_run"):
        # Sembol listesi oluştur
        if "Kripto" in pr_market:
            _pr_mkt = "crypto"
            n_ = {"Top5":5,"Top10":10,"Top20":20}.get(pr_scope,20)
            _pr_syms = [(s, "crypto") for s in [
                "BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BNBUSDT",
                "ADAUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT",
                "MATICUSDT","LTCUSDT","UNIUSDT","ATOMUSDT","NEARUSDT",
                "APTUSDT","ARBUSDT","OPUSDT","INJUSDT","SUIUSDT"
            ][:n_]]
        elif "Forex" in pr_market:
            _pr_mkt = "forex"
            n_ = {"Top5":5,"Top10":10,"Top20":20}.get(pr_scope,20)
            _pr_syms = [(s, "forex") for s in list(CFG.FOREX.keys())[:n_]]
        elif "BIST" in pr_market:
            _pr_mkt = "stock_bist"
            n_ = {"Top5":5,"Top10":10,"Top20":20}.get(pr_scope,20)
            _pr_syms = [(s, "stock_bist") for s in CFG.BIST[:n_]]
        else:
            _pr_mkt = "stock_us"
            n_ = {"Top5":5,"Top10":10,"Top20":20}.get(pr_scope,20)
            _pr_syms = [(s, "stock_us") for s in CFG.US_STOCKS[:n_]]

        if pr_scope == "Custom" and pr_custom:
            _pr_syms = []
            for raw_s in pr_custom.split(","):
                raw_s = raw_s.strip()
                if not raw_s: continue
                if "Kripto" in pr_market: _pr_syms.append((fix_symbol(raw_s,"crypto"), "crypto"))
                elif "Forex" in pr_market: _pr_syms.append((fix_symbol(raw_s,"forex"), "forex"))
                elif "BIST" in pr_market: _pr_syms.append((fix_symbol(raw_s,"stock_bist"), "stock_bist"))
                else: _pr_syms.append((raw_s.upper(), "stock_us"))

        with st.spinner(f"🎯 {len(_pr_syms)} sembol analiz ediliyor..."):
            _bull, _bear = safe(run_prediction_scan, _pr_syms, pr_tf, pr_min_conf,
                                fb=([], []))
        st.session_state["pr_bull"] = _bull
        st.session_state["pr_bear"] = _bear
        st.session_state["pr_done"] = True

    # ── Sonuçlar ────────────────────────────────────────
    pr_bull = st.session_state.get("pr_bull", [])
    pr_bear = st.session_state.get("pr_bear", [])

    if not st.session_state.get("pr_done"):
        st.markdown(
            '<div style="text-align:center;padding:60px;color:#3d5a80;font-size:9px;">'
            '<div style="font-size:3rem;margin-bottom:10px;">🎯</div>'
            'Tahmin Motoru — Forex · Kripto · BIST · US<br>'
            'EMA Stack · RSI Momentum · MACD · SMC Yapısı · OB/FVG<br>'
            '<span style="color:#ffd600;">Yükseliş/Düşüş beklentisi %100 teknik analiz bazlı hesaplanır</span>'
            '</div>',
            unsafe_allow_html=True)
    else:
        # Özet satırı
        st.markdown(
            '<div style="display:flex;gap:8px;margin-bottom:10px;font-size:8.5px;">'
            '<div style="background:rgba(0,255,136,0.08);border:1px solid rgba(0,255,136,0.2);'
            'border-radius:5px;padding:6px 14px;color:#00ff88;">'
            '▲ YÜKSELİŞ BEKLENTİSİ: ' + str(len(pr_bull)) + ' sembol</div>'
            '<div style="background:rgba(255,51,85,0.08);border:1px solid rgba(255,51,85,0.2);'
            'border-radius:5px;padding:6px 14px;color:#ff3355;">'
            '▼ DÜŞÜŞ BEKLENTİSİ: ' + str(len(pr_bear)) + ' sembol</div>'
            '</div>',
            unsafe_allow_html=True)

        def _pred_table(lst, direction):
            if not lst:
                st.markdown(
                    '<div style="color:#3d5a80;text-align:center;padding:20px;font-size:9px;">'
                    'Bu yönde sonuç yok</div>',
                    unsafe_allow_html=True)
                return
            is_bull = direction == "BULL"
            dc = "#00ff88" if is_bull else "#ff3355"
            hdr = "YÜKSELİŞ BEKLENTİSİ" if is_bull else "DÜŞÜŞ BEKLENTİSİ"
            arrow = "▲" if is_bull else "▼"
            col_pct = "bull_pct" if is_bull else "bear_pct"

            st.markdown(
                '<div style="display:grid;grid-template-columns:90px 60px 55px 60px 60px 60px 1fr;'
                'gap:4px;padding:5px 10px;'
                'background:rgba(0,0,0,0.3);border-radius:5px;'
                'font-size:7.5px;font-weight:700;color:#3d5a80;letter-spacing:.8px;margin-bottom:3px;">'
                '<span>SEMBOL</span><span>YÖN %</span><span>GÜVEN</span>'
                '<span>HEDEF</span><span>SL RİSK</span><span>HAREKET</span><span>SİNYALLER</span>'
                '</div>',
                unsafe_allow_html=True)

            for r in lst[:15]:
                pct   = r.get(col_pct, 0)
                conf  = r.get("confidence", 0)
                tp    = r.get("tp_target", 0)
                sl    = r.get("sl_risk", 0)
                move  = r.get("expected_move_pct", 0)
                price = r.get("price", 0)
                sigs  = (r.get("signals_bull") if is_bull else r.get("signals_bear")) or []
                bw    = int(pct * 0.55)
                bc    = "#00ff88" if pct >= 70 else "#ffd600" if pct >= 55 else "#ff6b35"
                dp_   = 5 if price < 0.01 else 4 if price < 1 else 2 if price < 100 else 0

                sig_html = "".join(
                    '<span style="font-size:6px;padding:1px 4px;border-radius:2px;'
                    'background:' + dc + '18;color:' + dc + ';margin-right:3px;">'
                    + s + '</span>'
                    for s in sigs[:3]
                )

                st.markdown(
                    '<div style="display:grid;grid-template-columns:90px 60px 55px 60px 60px 60px 1fr;'
                    'gap:4px;align-items:center;padding:5px 10px;margin-bottom:2px;'
                    'background:' + ('rgba(0,255,136,0.04)' if is_bull else 'rgba(255,51,85,0.04)') + ';'
                    'border:1px solid #0d1c2e;border-left:3px solid ' + dc + ';'
                    'border-radius:5px;font-size:8.5px;">'
                    '<span style="font-weight:800;color:' + dc + ';">'
                    + r.get("sym","?") + '</span>'
                    '<span>'
                    '<div style="background:#0d1c2e;border-radius:3px;height:4px;width:55px;overflow:hidden;">'
                    '<div style="background:' + bc + ';height:4px;width:' + str(bw) + 'px;border-radius:3px;"></div>'
                    '</div>'
                    '<span style="color:' + bc + ';font-size:7.5px;">' + str(pct) + '%</span>'
                    '</span>'
                    '<span style="color:' + ('#00ff88' if conf >= 60 else '#ffd600') + ';">'
                    + str(conf) + '%</span>'
                    '<span style="color:' + dc + ';font-size:8px;">'
                    + (f"{tp:.{dp_}f}" if tp else "—") + '</span>'
                    '<span style="color:#ff3355;font-size:8px;">'
                    + (f"{sl:.{dp_}f}" if sl else "—") + '</span>'
                    '<span style="color:#ffd600;">' + arrow + f"{move:.1f}%" + '</span>'
                    '<span>' + sig_html + '</span>'
                    '</div>',
                    unsafe_allow_html=True)

        pr_col1, pr_col2 = st.columns(2)
        with pr_col1:
            st.markdown(
                '<div style="font-size:9px;font-weight:800;color:#00ff88;'
                'padding:6px 10px;background:rgba(0,255,136,0.06);'
                'border:1px solid rgba(0,255,136,0.15);border-radius:6px;margin-bottom:6px;">'
                '▲ YÜKSELİŞ BEKLENTİSİ</div>',
                unsafe_allow_html=True)
            _pred_table(pr_bull, "BULL")
        with pr_col2:
            st.markdown(
                '<div style="font-size:9px;font-weight:800;color:#ff3355;'
                'padding:6px 10px;background:rgba(255,51,85,0.06);'
                'border:1px solid rgba(255,51,85,0.15);border-radius:6px;margin-bottom:6px;">'
                '▼ DÜŞÜŞ BEKLENTİSİ</div>',
                unsafe_allow_html=True)
            _pred_table(pr_bear, "BEAR")


#  TAB 7 — NEXUS AI
# ═══════════════════════════════════════════════════
with t_ai:
    ai1_, ai2_ = st.columns([3, 1])
    with ai2_:
        st.markdown('<div class="sec">⚡ NEXUS AI</div>', unsafe_allow_html=True)
        kv("Model", sel_m.split(" ",1)[-1] if " " in sel_m else sel_m, "#00d4ff")
        kv("Mod",   st.session_state.get("ai_mode","?"), "#a855f7")
        kv("Tur",   str(len([m for m in st.session_state.get("chat",[]) if m.get("role")=="user"])), "#00d4ff")
        if st.button("🗑 Sohbeti Sil", use_container_width=True, key="ai_clr"):
            st.session_state["chat"] = []; st.rerun()
        st.markdown('<div class="sec">💡 HIZLI SORULAR</div>', unsafe_allow_html=True)
        quick_qs = [
            f"🔍 {sym_lbl} için ICT entry planı",
            f"📊 {sym_lbl} BOS/MSS/OB analiz",
            f"🎯 ${capital} ile risk hesapla {sym_lbl}",
            "⚠️ Trend dönüş sinyalleri neler?",
            "📈 OB+FVG confluence nasıl kullanılır?",
        ]
        for q_ in quick_qs:
            if st.button(q_[:40]+"…" if len(q_)>40 else q_, use_container_width=True, key=f"q_{q_[:8]}"):
                st.session_state["_pend_q"] = q_; st.rerun()

    with ai1_:
        chat_ = st.session_state.get("chat", [])
        if not chat_:
            ctx_str = " | ".join(f"{k}:{v}" for k,v in st.session_state.get("live_ctx",{}).items())
            st.markdown(
                f'<div style="text-align:center;padding:24px;">'
                f'<div class="apex-logo" style="font-size:3rem;">NEXUS</div>'
                f'<div style="font-size:7px;color:#3d5a80;letter-spacing:.12em;margin-top:2px;">'
                f'SUPREME INTELLIGENCE ENGINE</div>'
                f'<div style="font-size:8px;color:#3d5a80;margin-top:10px;background:#080f1e;'
                f'border:1px solid rgba(0,212,255,.1);border-radius:6px;padding:8px;">{ctx_str}</div>'
                f'</div>', unsafe_allow_html=True)

        for msg_ in chat_:
            if msg_["role"] == "user":
                st.markdown(f'<div class="ubub">👤 {msg_["content"]}</div>'
                            f'<div style="font-size:.57rem;color:#3d5a80;">{msg_.get("time","")}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="abub">', unsafe_allow_html=True)
                st.markdown(msg_["content"])
                st.markdown(f'</div><div style="font-size:.57rem;color:#3d5a80;">'
                            f'{msg_.get("time","")} · {msg_.get("el",0):.1f}s</div>',
                            unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        pend_q = st.session_state.pop("_pend_q", "")
        with st.form("ai_form", clear_on_submit=True):
            ui_ = st.text_area("", value=pend_q,
                               placeholder=f"{sym_lbl} hakkında ICT/SMC, risk, makro her şeyi sor…",
                               height=75, label_visibility="collapsed")
            f1_, f2_ = st.columns([1,4])
            sub_ = f1_.form_submit_button("➤ GÖNDER", use_container_width=True, type="primary")

        if sub_ and ui_.strip():
            now_ = datetime.utcnow().strftime("%H:%M")
            ctx_px = ""
            if not chat_:
                ctx_px = (f"[{sym_lbl} {tf_lbl}: {fmt(price_,dp_)}, HTF:{bias_}, "
                          f"Yapı:{smc_.get('struct','?')}, Strat:{strat_.get('st_type','?')}, RSI:{rsi_:.1f}]\n\n")
            st.session_state["chat"].append({"role":"user","content":ui_.strip(),"time":now_})
            with st.spinner("⚡ NEXUS…"):
                rp_, el_ = safe(nexus_ai, ctx_px + ui_.strip(), fb=("⚠ Yanıt alınamadı.",0.0))
            st.session_state["chat"].append({"role":"assistant","content":rp_,"time":datetime.utcnow().strftime("%H:%M"),"el":el_})
            st.session_state["ai_t"] += el_; st.session_state["ai_n"] += 1
            st.rerun()

# ═══════════════════════════════════════════════════
#  TAB 8 — HABERLER
# ═══════════════════════════════════════════════════
with t_nw:
    nw1_, nw2_ = st.columns([3,1])
    with nw2_:
        if st.button("🔄 Yenile", key="nwref", use_container_width=True):
            fetch_news.clear(); st.rerun()
        fg2_ = safe(fetch_fg, fb={"value":50,"label":"Nötr"})
        fgv_ = fg2_.get("value",50)
        fgc_ = "#00ff88" if fgv_>60 else "#ff3355" if fgv_<40 else "#ffd600"
        st.markdown(
            f'<div class="card" style="text-align:center;padding:14px;">'
            f'<div style="font-size:7px;color:#3d5a80;letter-spacing:1px;">FEAR & GREED</div>'
            f'<div style="font-family:Bebas Neue,cursive;font-size:2.5rem;color:{fgc_};">{fgv_}</div>'
            f'<div style="font-size:8.5px;color:{fgc_};">{fg2_.get("label","?")}</div>'
            f'<div style="margin-top:6px;">{pbar(fgv_,fgc_,6)}</div>'
            f'</div>', unsafe_allow_html=True)

    with nw1_:
        BULL_W = ["rally","surge","bullish","gain","rise","record","buy","breakout","recovery","green","pump"]
        BEAR_W = ["crash","dump","bear","sell","drop","fall","ban","liquidation","red","loss","concern"]
        news_items = safe(fetch_news, fb=[])
        if not news_items:
            st.markdown('<div style="color:#3d5a80;font-size:9px;padding:20px;">Haberler yüklenemedi.</div>',
                        unsafe_allow_html=True)
        else:
            for item_ in news_items:
                t__ = item_["title"].lower()
                bull_ = any(k in t__ for k in BULL_W)
                bear_ = any(k in t__ for k in BEAR_W)
                nc_  = "#00ff88" if bull_ else "#ff3355" if bear_ else "#00d4ff"
                nb_  = f"rgba({'0,255,136' if bull_ else '255,51,85' if bear_ else '0,212,255'},.05)"
                sl_  = "▲ BULLISH" if bull_ else "▼ BEARISH" if bear_ else "● NÖTR"
                ln_  = f'<a href="{item_["link"]}" target="_blank" style="color:inherit;text-decoration:none;">' if item_.get("link") else ""
                lnc_ = "</a>" if item_.get("link") else ""
                st.markdown(
                    f'<div style="background:{nb_};border:1px solid rgba(0,212,255,.1);'
                    f'border-left:3px solid {nc_};border-radius:7px;padding:10px 12px;margin-bottom:6px;">'
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:3px;">'
                    f'<span style="font-size:7.5px;color:{nc_};">{item_["icon"]} {item_["src"]}</span>'
                    f'<span style="font-size:7.5px;color:{nc_};font-weight:700;">{sl_}</span></div>'
                    f'{ln_}<div style="font-weight:600;font-size:9.5px;line-height:1.4;margin-bottom:2px;">'
                    f'{item_["title"][:130]}</div>{lnc_}'
                    f'<div style="font-size:8px;color:#3d5a80;">{item_.get("pub","")[:22]}</div>'
                    f'</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
#  TAB 11 — CANLI HABER PANELİ (Live News Panel)
# ═══════════════════════════════════════════════════
with t_lv:
    st.markdown('<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
                '<div class="apex-logo" style="font-size:1.3rem;">CANLI HABERLER</div>'
                '<div style="font-size:8px;color:#3d5a80;">Kripto · Forex · Makro · Piyasalar — Canlı RSS Akışı</div>'
                '</div>', unsafe_allow_html=True)
    
    lv1_, lv2_, lv3_ = st.columns([1,1,1])
    with lv1_:
        lv_filter = st.selectbox("Kategori", ["🌐 Tümü","🪙 Kripto","💱 Forex","📈 Hisse","🏛 Makro"], key="lv_filt")
    with lv2_:
        lv_sentiment = st.selectbox("Duygu", ["Tümü","▲ Bullish","▼ Bearish","● Nötr"], key="lv_sent")
    with lv3_:
        if st.button("🔄 Yenile", key="lv_ref", use_container_width=True):
            fetch_news.clear(); st.rerun()

    # Extended RSS feeds
    @st.cache_data(ttl=120, show_spinner=False)
    def fetch_live_news():
        import xml.etree.ElementTree as ET
        feeds = [
            ("CoinDesk",    "https://www.coindesk.com/arc/outboundfeeds/rss/",       "🪙","crypto"),
            ("CoinTelegraph","https://cointelegraph.com/rss",                          "📡","crypto"),
            ("Reuters Biz", "https://feeds.reuters.com/reuters/businessNews",          "📰","macro"),
            ("BBC Biz",     "https://feeds.bbci.co.uk/news/business/rss.xml",         "🌍","macro"),
            ("Investing",   "https://www.investing.com/rss/news.rss",                 "📊","stock"),
            ("FXStreet",    "https://www.fxstreet.com/rss/news",                      "💱","forex"),
            ("Benzinga",    "https://www.benzinga.com/feed",                           "🏛","stock"),
            ("Decrypt",     "https://decrypt.co/feed",                                "🔑","crypto"),
        ]
        items = []
        for name, url, icon, cat in feeds:
            try:
                r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
                if not r.ok: continue
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:6]:
                    t_ = item.findtext("title","").strip()
                    l_ = item.findtext("link","").strip()
                    pub = item.findtext("pubDate","")[:25]
                    if t_:
                        items.append({"title":t_,"link":l_,"src":name,"icon":icon,"cat":cat,"pub":pub})
            except: continue
        return sorted(items, key=lambda x: x.get("pub",""), reverse=True)
    
    live_news = safe(fetch_live_news, fb=[])
    
    BULL_W = ["rally","surge","bullish","gain","rise","record","buy","breakout","recovery","green","pump","soar","jump","upside","positive","growth","beat","all-time"]
    BEAR_W = ["crash","dump","bear","sell","drop","fall","ban","liquidation","red","loss","concern","fear","warning","decline","plunge","tumble","weak","miss","downside"]
    
    cat_map = {"🌐 Tümü": None, "🪙 Kripto":"crypto","💱 Forex":"forex","📈 Hisse":"stock","🏛 Makro":"macro"}
    cat_filt = cat_map.get(lv_filter)
    
    displayed = 0
    lv_cols = st.columns(2)
    col_idx = 0
    
    for item_ in (live_news or []):
        if cat_filt and item_.get("cat") != cat_filt: continue
        t__ = item_["title"].lower()
        bull_ = any(k in t__ for k in BULL_W)
        bear_ = any(k in t__ for k in BEAR_W)
        sent = "▲ Bullish" if bull_ else "▼ Bearish" if bear_ else "● Nötr"
        if lv_sentiment != "Tümü" and sent != lv_sentiment: continue
        
        nc_ = "#00ff88" if bull_ else "#ff3355" if bear_ else "#00d4ff"
        nb_ = f"rgba({'0,255,136' if bull_ else '255,51,85' if bear_ else '0,212,255'},.05)"
        
        with lv_cols[col_idx % 2]:
            st.markdown(
                f'<div class="news-card" style="background:linear-gradient(135deg,{nb_},rgba(0,0,0,0));'
                f'border:1px solid rgba(255,255,255,0.05);'
                f'border-left:3px solid {nc_};border-radius:9px;padding:11px 13px;margin-bottom:7px;'
                f'box-shadow:0 2px 10px rgba(0,0,0,.3);">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
                f'<span style="font-size:7px;color:{nc_};font-weight:700;letter-spacing:.5px;">{item_["icon"]} {item_["src"].upper()}</span>'
                f'<span style="font-size:6.5px;padding:2px 7px;border-radius:10px;background:{nc_}18;color:{nc_};font-weight:700;">{sent}</span>'
                f'</div>'
                f'<a href="{item_.get("link","#")}" target="_blank" style="text-decoration:none;">'
                f'<div style="font-weight:600;font-size:9px;line-height:1.5;color:#c8d8f0;margin-bottom:4px;'
                f'transition:.2s;">'
                f'{item_["title"][:155]}</div></a>'
                f'<div style="font-size:6.5px;color:#3d5a80;">{item_.get("pub","")[:25]}</div>'
                f'</div>', unsafe_allow_html=True)
        col_idx += 1
        displayed += 1
        if displayed >= 40: break
    
    if not displayed:
        st.markdown('<div style="text-align:center;padding:40px;color:#3d5a80;font-size:9px;">Haberler yükleniyor veya filtre sonuç bulunamadı.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  TAB 12 — MİLYARDER İZLEYİCİ (Billionaire Tracker)
# ═══════════════════════════════════════════════════
with t_bl:
    st.markdown('<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
                '<div class="apex-logo" style="font-size:1.3rem;">MİLYARDER İZLEYİCİ</div>'
                '<div style="font-size:8px;color:#3d5a80;">Dünya Milyarderlerinin Kripto & Piyasa Açıklamaları</div>'
                '</div>', unsafe_allow_html=True)
    
    bl1_, bl2_ = st.columns([2,1])
    with bl1_:
        bl_filter = st.selectbox("Kişi", ["🌐 Tümü","🟠 Elon Musk","💎 Michael Saylor","📊 Warren Buffett",
                                           "⚡ Cathie Wood","🔮 Mark Zuckerberg","🌙 Vitalik Buterin",
                                           "💰 Ray Dalio","🦁 Paul Tudor Jones"], key="bl_filt")
    with bl2_:
        if st.button("🔄 Güncelle", key="bl_ref", use_container_width=True):
            st.rerun()
    
    # Simulated billionaire market comments (real data would need Twitter/X API)
    # Uses AI to generate realistic summaries based on known positions
    
    BILLIONAIRES = [
        {
            "name": "Elon Musk",
            "icon": "🟠",
            "handle": "@elonmusk",
            "known_holdings": "DOGE, BTC, TSLA",
            "stance": "bullish",
            "color": "#ffd600",
            "recent_topics": ["DOGE", "Bitcoin", "FED","AI","TSLA"],
            "bio": "Tesla & SpaceX CEO, Twitter/X sahibi. Kripto destekçisi.",
        },
        {
            "name": "Michael Saylor",
            "icon": "💎",
            "handle": "@saylor",
            "known_holdings": "BTC (500,000+ BTC)",
            "stance": "ultra-bullish BTC",
            "color": "#00ff88",
            "recent_topics": ["Bitcoin","Digital Gold","BTC","Institutional"],
            "bio": "MicroStrategy CEO. Bitcoin maximalist.",
        },
        {
            "name": "Warren Buffett",
            "icon": "📊",
            "handle": "Berkshire Hathaway",
            "known_holdings": "AAPL, BRK.A, KO, BAC",
            "stance": "bearish crypto / bullish value stocks",
            "color": "#00d4ff",
            "recent_topics": ["Inflation","Fed","S&P500","Berkshire"],
            "bio": "Berkshire Hathaway CEO. Value investor.",
        },
        {
            "name": "Cathie Wood",
            "icon": "⚡",
            "handle": "@CathieDWood",
            "known_holdings": "ARKK, BTC, ETH, TSLA",
            "stance": "bullish disruptive tech & crypto",
            "color": "#a855f7",
            "recent_topics": ["Innovation","BTC","AI","TSLA"],
            "bio": "ARK Invest CEO. Disruptive innovation uzmanı.",
        },
        {
            "name": "Vitalik Buterin",
            "icon": "🔮",
            "handle": "@VitalikButerin",
            "known_holdings": "ETH, crypto ecosystem",
            "stance": "ETH bullish, DeFi advocate",
            "color": "#627eea",
            "recent_topics": ["Ethereum","L2","DeFi","ZK","Scaling"],
            "bio": "Ethereum yaratıcısı.",
        },
        {
            "name": "Ray Dalio",
            "icon": "💰",
            "handle": "Bridgewater Associates",
            "known_holdings": "Gold, Bonds, Global equities",
            "stance": "macro hedge, cautious",
            "color": "#ffd600",
            "recent_topics": ["Debt cycle","Gold","China","Fed","Macro"],
            "bio": "Bridgewater Associates kurucusu.",
        },
        {
            "name": "Paul Tudor Jones",
            "icon": "🦁",
            "handle": "Tudor BVI",
            "known_holdings": "BTC (portfolio hedge), Gold",
            "stance": "BTC as inflation hedge",
            "color": "#ff6b35",
            "recent_topics": ["Inflation","Bitcoin","Gold","Portfolio"],
            "bio": "Tudor Investment Corp kurucusu.",
        },
        {
            "name": "Mark Zuckerberg",
            "icon": "🌙",
            "handle": "@Meta",
            "known_holdings": "META, crypto (Diem cancelled)",
            "stance": "neutral crypto, bullish AI/metaverse",
            "color": "#1877f2",
            "recent_topics": ["Meta","AI","Metaverse","VR","Llama"],
            "bio": "Meta CEO.",
        },
    ]
    
    bl_name_filter = bl_filter.split(" ",1)[-1] if " " in bl_filter else None
    if bl_name_filter == "Tümü": bl_name_filter = None
    
    # For each billionaire, show their known position and AI-generated sentiment summary
    for person in BILLIONAIRES:
        if bl_name_filter and person["name"] != bl_name_filter: continue
        
        c_ = person["color"]
        stance_icon = "▲" if "bullish" in person["stance"] else "▼" if "bearish" in person["stance"] else "↔"
        stance_col = "#00ff88" if "bullish" in person["stance"] else "#ff3355" if "bearish" in person["stance"] else "#ffd600"
        
        with st.expander(f"{person['icon']} {person['name']} — {person['handle']}", expanded=(bl_name_filter is not None)):
            bl_e1, bl_e2 = st.columns([2,1])
            with bl_e1:
                st.markdown(
                    f'<div style="background:rgba(0,0,0,0.25);border:1px solid {c_}33;border-left:3px solid {c_};'
                    f'border-radius:7px;padding:10px 14px;margin-bottom:6px;">'
                    f'<div style="font-size:8px;color:#3d5a80;margin-bottom:4px;">{person["bio"]}</div>'
                    f'<div style="font-size:8.5px;margin-bottom:3px;">'
                    f'<span style="color:#3d5a80;">Bilinen Varlıklar: </span>'
                    f'<span style="color:{c_};font-weight:700;">{person["known_holdings"]}</span></div>'
                    f'<div style="font-size:8.5px;margin-bottom:3px;">'
                    f'<span style="color:#3d5a80;">Genel Duruş: </span>'
                    f'<span style="color:{stance_col};font-weight:700;">{stance_icon} {person["stance"].title()}</span></div>'
                    f'<div style="font-size:8px;color:#3d5a80;">📌 Güncel Konular: '
                    f'<span style="color:#00d4ff;">{", ".join(person["recent_topics"])}</span></div>'
                    f'</div>', unsafe_allow_html=True)
                
                # AI Summary Button
                ai_key_ = f"bl_ai_{person['name'].replace(' ','_')}"
                if st.button(f"🤖 AI Özet: {person['name']}", key=ai_key_, use_container_width=True):
                    with st.spinner("NEXUS analiz yapıyor…"):
                        prompt = (f"{person['name']} ({person['handle']}) hakkında piyasa perspektifinden kısa bir özet yap. "
                                 f"Bilinen varlıkları: {person['known_holdings']}. "
                                 f"Genel duruşu: {person['stance']}. "
                                 f"Son konuları: {', '.join(person['recent_topics'])}. "
                                 f"Bu kişinin son dönem kripto ve piyasa görüşlerini 3-4 cümleyle özetle. Türkçe yaz.")
                        rp_, _ = safe(nexus_ai, prompt, fb=("AI yanıtı alınamadı.",0.0))
                    st.session_state[f"bl_sum_{person['name']}"] = rp_
                
                # Show AI summary if exists
                bl_sum = st.session_state.get(f"bl_sum_{person['name']}")
                if bl_sum:
                    st.markdown(
                        f'<div style="background:rgba(168,85,247,0.07);border:1px solid rgba(168,85,247,0.2);'
                        f'border-radius:7px;padding:10px 12px;margin-top:4px;font-size:8.5px;line-height:1.6;">'
                        f'<div style="font-size:7px;color:#a855f7;font-weight:700;margin-bottom:4px;">🤖 NEXUS AI ÖZETİ</div>'
                        f'{bl_sum}</div>', unsafe_allow_html=True)
            
            with bl_e2:
                # Stance gauge
                is_bull_bl = "bullish" in person["stance"]
                gauge_val = 80 if is_bull_bl else 25 if "bearish" in person["stance"] else 50
                gauge_c = "#00ff88" if gauge_val > 60 else "#ff3355" if gauge_val < 40 else "#ffd600"
                
                st.markdown(
                    f'<div style="background:#080f1e;border:1px solid rgba(0,212,255,.1);border-radius:7px;'
                    f'padding:12px;text-align:center;">'
                    f'<div style="font-size:7px;color:#3d5a80;letter-spacing:1px;margin-bottom:6px;">BULLISH SKORU</div>'
                    f'<div style="font-family:Bebas Neue,cursive;font-size:2.5rem;color:{gauge_c};">{gauge_val}</div>'
                    f'<div style="background:#0d1c2e;border-radius:4px;height:6px;margin:6px 0;">'
                    f'<div style="background:{gauge_c};height:6px;width:{gauge_val}%;border-radius:4px;"></div></div>'
                    f'<div style="font-size:7.5px;color:{stance_col};">{stance_icon} {person["stance"][:25]}</div>'
                    f'</div>', unsafe_allow_html=True)
                
                # Market impact
                st.markdown('<div style="font-size:7px;color:#3d5a80;margin-top:8px;font-weight:700;letter-spacing:1px;">ETKİLEDİĞİ VARLIKLAR</div>', unsafe_allow_html=True)
                for topic in person["recent_topics"][:4]:
                    topic_c = "#ffd600" if topic in ["BTC","Bitcoin"] else "#627eea" if topic in ["ETH","Ethereum"] else "#00d4ff"
                    st.markdown(f'<div style="font-size:8px;padding:2px 7px;background:rgba(0,212,255,0.07);border-radius:3px;margin-bottom:2px;color:{topic_c};">#{topic}</div>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:7.5px;color:#3d5a80;text-align:center;">⚠️ Bilgiler kamuya açık kaynaklara dayanmaktadır. Gerçek zamanlı sosyal medya izlemek için Twitter/X API gerekir. Yatırım tavsiyesi değildir.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  TAB 13 — LOG
# ═══════════════════════════════════════════════════
with t_lg:
    lg1_, lg2_ = st.columns([3,1])
    with lg2_:
        if st.button("🗑 Log Temizle", use_container_width=True, key="cll"):
            st.session_state["elog"] = []; st.rerun()
        bt__ = st.session_state.get("bt")
        if bt__ and bt__.get("trades"):
            buf__ = io.StringIO()
            w__ = csv.DictWriter(buf__, fieldnames=list(bt__["trades"][0].keys()))
            w__.writeheader(); w__.writerows(bt__["trades"])
            st.markdown(dlbtn(buf__.getvalue(), f"apex_{sym_lbl}.csv","📥 CSV"), unsafe_allow_html=True)
    with lg1_:
        errs_ = st.session_state.get("elog",[])
        st.markdown('<div class="sec">❌ HATA LOGU</div>', unsafe_allow_html=True)
        if not errs_:
            st.markdown('<div style="font-size:9px;color:#3d5a80;">✓ Hata yok</div>', unsafe_allow_html=True)
        for e_ in reversed(errs_[-25:]):
            st.markdown(
                f'<div style="background:rgba(255,51,85,.04);border-left:3px solid #ff3355;'
                f'padding:3px 8px;border-radius:2px;margin-bottom:2px;font-size:8px;color:#ff3355;">'
                f'[{e_.get("t","?")}] {e_.get("fn","?")} → {e_.get("msg","")}</div>',
                unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="sec">📊 SİSTEM DURUMU</div>', unsafe_allow_html=True)
        cs__ = cstat()
        kv("Cache",     f'{cs__["alive"]}/{cs__["total"]}', "#00d4ff")
        kv("Hits",      str(cs__["hits"]),                  "#a855f7")
        kv("Yükleme",   f"{load_ms}ms",                     "#00d4ff")
        kv("Mum Sayısı",str(len(df)),                       "#3d5a80")
        kv("Market",    market_type,                        "#00d4ff")
        kv("F&G",       f'{fg_.get("value",50)} {fg_.get("label","")}', "#ffd600")

# ═══════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════
st.markdown("""
<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,212,255,.2),rgba(0,255,136,.15),transparent);margin:8px 0;"></div>
<div style="text-align:center;padding:8px;font-size:6.5px;color:#1a2840;letter-spacing:.08em;">
APEX PRO v10.0 ◈ SUPREME ICT/SMC ENGINE ◈ Kripto · Forex · US Hisse · BIST
◈ TF: 1m·3m·5m·10m·15m·30m·1s·4s·1g  ◈  ICT Çizim · AI Asistan · Canlı Haberler · Milyarder Tracker
◈ Eğitim amaçlıdır — yatırım tavsiyesi değildir.
</div>""", unsafe_allow_html=True)
