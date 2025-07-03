#!/usr/bin/env python3
"""
Streamlit Market Sizer App

• Fetch news headlines via Google News RSS
• Extract article text with Newspaper3k (or BeautifulSoup fallback)
• Aggregate headlines + snippets per topic
• Use Hugging Face Inference API for metric extraction, falling back to OpenAI
• Display results in a Streamlit UI with business advice and numerical metrics

NOTE: Paste your tokens below before running.
"""
import re
import requests
import urllib.parse
import json
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

# Optional newspaper3k
try:
    from newspaper import Article
except ImportError:
    Article = None

# --- Hugging Face Setup ---
from huggingface_hub import InferenceApi
HUGGINGFACE_MODEL = "google/flan-t5-xl"
# Paste your Hugging Face token here:
HF_TOKEN = "hf_your_token_here"
# Initialize HF API client
try:
    hf_api = InferenceApi(repo_id=HUGGINGFACE_MODEL, token=HF_TOKEN)
    hf_available = True
except Exception as e:
    print("❌ Hugging Face auth failed:", e)
    hf_api = None
    hf_available = False

# --- OpenAI Fallback Setup ---
import openai
# Paste your OpenAI API key here:
openai.api_key = "sk_your_openai_key_here"

# --- Helper Functions ---
def fetch_news(topic: str, max_results: int = 5) -> pd.DataFrame:
    q = urllib.parse.quote(f"{topic} market size")
    rss_url = f"https://news.google.com/rss/search?q={q}"
    r = requests.get(rss_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "xml")
    items = soup.find_all("item")[:max_results]
    rows = []
    for it in items:
        rows.append({
            "title": it.title.text if it.title else "",
            "link":  it.link.text if it.link else ""
        })
    return pd.DataFrame(rows)


def extract_text(url: str) -> str:
    if Article:
        try:
            art = Article(url)
            art.download(); art.parse()
            if art.text.strip():
                return art.text
        except:
            pass
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    return ' '.join(p.get_text() for p in soup.find_all('p'))


def call_ai(prompt: str) -> str:
    """Use HF if available, else fallback to OpenAI"""
    # Try HF
    if hf_available and hf_api:
        try:
            res = hf_api(prompt, raw_response=True)
            print("➡️ HF status:", res.status_code)
            print("➡️ HF resp:", res.text[:200].replace("\n"," "))
            payload = res.json()
            txt = payload.get('generated_text','').strip()
            if txt:
                return txt
        except Exception as e:
            print("🚨 HF error:", e)
    # Fallback to OpenAI
    if openai.api_key:
        try:
            oa = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"system","content":"You are a helpful business consultant."},
                          {"role":"user","content":prompt}],
                temperature=0
            )
            resp = oa.choices[0].message.content.strip()
            print("➡️ OpenAI resp:", resp[:200].replace("\n"," "))
            if resp:
                return resp
        except Exception as e:
            print("❌ OpenAI error:", e)
    # Generic fallback
    return ''


def regex_metrics_from_title(title: str) -> tuple[str,str]:
    tam,cagr = '',''
    m = re.search(r"\$?[\d,\.]+\s*(billion|million)", title, re.IGNORECASE)
    if m: tam = m.group(0)
    m2 = re.search(r"(\d+(?:\.\d+)?)%", title)
    if m2: cagr = m2.group(0)
    return tam,cagr


def parse_metrics(js: str) -> tuple[str,str]:
    try:
        d=json.loads(js)
        return d.get('TAM',''), d.get('CAGR','')
    except:
        return '',''

# --- Streamlit UI ---
st.set_page_config(page_title="AI Market Sizer", layout="wide")
st.title("🔍 AI-Powered Market Sizing Tool")

topic = st.text_input("Enter a market or idea (e.g., 'Smartphones')")
if st.button("Analyze Market") and topic:
    st.info(f"Analyzing market: {topic}")
    # 1) Fetch news
    df = fetch_news(topic)
    if df.empty:
        st.error("No news found for this topic.")
        st.stop()
    # 2) Extract snippets
    df['snippet'] = df['link'].apply(lambda u: extract_text(u)[:1000])
    # 3) Build prompts
    df['prompt'] = df.apply(lambda r: "Headline: " + r.title + "\nSnippet: " + r.snippet + "\n\nExtract the Total Addressable Market (TAM) and CAGR as JSON with keys 'TAM','CAGR'.", axis=1)
    # 4) Call AI for metrics
    df['raw'] = df['prompt'].apply(call_ai)
    # 5) Parse JSON
    df[['TAM','CAGR']] = pd.DataFrame(df['raw'].apply(parse_metrics).tolist(), index=df.index)
    # 6) Regex fallback
    df[['TAM','CAGR']] = df.apply(lambda r: pd.Series(regex_metrics_from_title(r.title)) if (not r.TAM and not r.CAGR) else pd.Series((r.TAM,r.CAGR)), axis=1)
    # 7) Business Advice
    context = "\n\n".join([f"- {t}: {s}" for t,s in zip(df.title, df.snippet)])
    advice_prompt = (
        "You are a senior business consultant advising on the '" + topic + "' market.\n" +
        "Using the context and metrics below, provide actionable strategic advice, including opportunities, risks, and next steps.\n\n" +
        "Context:\n" + context + "\n\n" +
        "Metrics: TAM=" + (", ".join([t for t in df.TAM if t]) or "N/A") + "; CAGR=" + (", ".join([c for c in df.CAGR if c]) or "N/A")
    )
    advice_text = call_ai(advice_prompt)
    if not advice_text:
        tams=[t for t in df.TAM if t]
        cagrs=[c for c in df.CAGR if c]
        if tams or cagrs:
            advice_text = (
                "Based on the metrics, the market size is " + (", ".join(tams) or "N/A") +
                " with growth rates of " + (", ".join(cagrs) or "N/A") +
                ". This indicates a significant market opportunity. " +
                "Consider validating demand with customer interviews, assessing key competitors, " +
                "and planning a go-to-market strategy that addresses pain points and leverages growth trends."
            )
        else:
            advice_text = (
                "We couldn't extract clear market metrics. " +
                "Consider researching industry reports or public data to determine TAM and CAGR, " +
                "then revisit this tool for insights."
            )
    st.subheader("Business Advice")
    st.write(advice_text)
    st.markdown("---")
    # 8) Metrics table
    st.subheader("Market Metrics by Article")
    st.table(df[['title','TAM','CAGR']])
    # 9) Raw Data Expander
    with st.expander("Show Raw Snippets & JSON"):
        st.write(df[['title','snippet','raw']])
    st.success("Done!")
