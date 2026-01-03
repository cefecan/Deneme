import pandas as pd
import yfinance as yf
import requests
import io

def get_bist100_list():
    """
    Fetches the BIST 100 stock list from a reliable source.
    """
    url = "https://uzmanpara.milliyet.com.tr/canli-borsa/bist-100-hisseleri/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        dfs = pd.read_html(io.StringIO(response.text))
        stock_list = []
        
        for df in dfs:
            df = df.astype(str)
            for col in df.columns:
                sample = df[col].dropna().sample(min(5, len(df[col]))).values
                if all(s.isupper() and 4 <= len(s) <= 5 and s.isalpha() for s in sample):
                   stock_list.extend(df[col].tolist())
                   
        stock_list = sorted(list(set(stock_list)))
        stock_list = [s for s in stock_list if s.isalpha() and len(s) >= 4]

        return stock_list

    except Exception as e:
        print(f"Error fetching list: {e}")
        return []

def get_stock_data_single(ticker):
    """
    Fetches data for a single ticker. Returns (ticker, price, change, status).
    Used for threaded execution in GUI.
    """
    try:
        full_ticker = f"{ticker}.IS"
        stock = yf.Ticker(full_ticker)
        # Fetch slightly more than 5 days to be safe on holidays
        hist = stock.history(period="1mo") 
        
        if isinstance(hist, pd.DataFrame) and not hist.empty:
            # Get last 5 business days
            hist_5d = hist.tail(5)
            if len(hist_5d) < 2:
                return (ticker, 0, 0, "Insufficient Data")
                
            last_price = hist_5d['Close'].iloc[-1]
            first_price = hist_5d['Close'].iloc[0]
            
            if first_price == 0: change = 0
            else: change = ((last_price - first_price) / first_price) * 100
            
            return (ticker, last_price, change, "OK")
        else:
            return (ticker, 0, 0, "No Data")
            
    except Exception as e:
        return (ticker, 0, 0, str(e))
