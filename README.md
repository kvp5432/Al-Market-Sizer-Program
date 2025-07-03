# Al-Market-Sizer-Program
A GPT-powered tool to estimate market size and growth from live news

This Streamlit app estimates **market size (TAM)** and **growth (CAGR)** for any industry or business idea by analyzing real-time news articles using **LLMs (Large Language Models)** like Hugging Face's FLAN-T5 or OpenAI's GPT.

It’s designed to help founders, analysts, and students quickly assess market potential using fresh, accessible information — without needing access to premium market reports.

## 🚀 Live Demo

👉 [Try the app here](https://ai-market-sizer-program-4obayyakvjb8j22dmipcay.streamlit.app/)


## 🧠 How It Works

1. **User enters a market or idea** 
2. App pulls recent articles via **Google News RSS**
3. Extracts article content using `newspaper3k` or `BeautifulSoup`
4. Sends summaries to **Hugging Face or OpenAI** for:
   - Total Addressable Market (TAM)
   - Compound Annual Growth Rate (CAGR)
5. Displays metrics + actionable **business advice**
6. Shows article titles, raw snippets, and extracted data

## 🛠 Built With

- [Streamlit](https://streamlit.io/) – Web app framework
- [Hugging Face Transformers](https://huggingface.co/) – LLM integration
- [OpenAI API](https://platform.openai.com/) – GPT fallback for analysis
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) – Web scraping
- [newspaper3k](https://newspaper.readthedocs.io/en/latest/) – Article parsing
- [Google News RSS](https://news.google.com/rss) – Real-time news feeds

## 📦 Installation

```bash
git clone https://github.com/your-username/ai-market-sizer.git
cd ai-market-sizer
pip install -r requirements.txt
streamlit run app.py
