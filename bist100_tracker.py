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
    
    print(f"Fetching stock list from {url}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse tables
        dfs = pd.read_html(io.StringIO(response.text))
        
        # Inspect tables to find the one with stock codes
        # The site usually has a big table. We look for a table formatted likely with tickers.
        stock_list = []
        
        for df in dfs:
            # Heuristic: Check for common columns or data looking like tickers (e.g., uppercase, 4-5 chars)
            # This specific site often has the ticker in the first column or 'Menkul'
            # Let's clean the dataframe and check
            
            # Convert to string to avoid object type issues
            df = df.astype(str)
            
            for col in df.columns:
                # Check 5 random non-empty items in column to see if they look like tickers
                sample = df[col].dropna().sample(min(5, len(df[col]))).values
                # Basic check: All uppercase, usually 4-5 chars
                if all(s.isupper() and 4 <= len(s) <= 5 and s.isalpha() for s in sample):
                   # Found a candidate column
                   possible_tickers = df[col].tolist()
                   # Add to our list if unique
                   stock_list.extend(possible_tickers)
                   
        # Remove duplicates and ensure unique
        stock_list = sorted(list(set(stock_list)))
        
        # Filter for known invalid strings if any scraping noise occurred
        stock_list = [s for s in stock_list if s.isalpha() and len(s) >= 4]

        if not stock_list:
            print("Could not automatically identify ticker column. Returning fallback list or empty.")
            # Fallback or error
            return []
            
        print(f"Found {len(stock_list)} potential symbols.")
        return stock_list

    except Exception as e:
        print(f"Error fetching list: {e}")
        return []

def get_stock_data(tickers):
    """
    Fetches the last 5 days of data for the given tickers using yfinance.
    """
    if not tickers:
        print("No tickers provided.")
        return

    # Append .IS for Yahoo Finance
    yf_tickers = [f"{t}.IS" for t in tickers]
    
    print(f"Downloading data for {len(yf_tickers)} stocks...")
    
    # Batch download
    # period='5d' gets the last 5 days
    data = yf.download(yf_tickers, period="5d", group_by='ticker', auto_adjust=True, threads=True)
    
    return data

def display_data(tickers, data):
    print("\n" + "="*50)
    print("BIST 100 STOCK PRICES (LAST 5 DAYS)")
    print("="*50 + "\n")
    
    for ticker in tickers:
        yf_ticker = f"{ticker}.IS"
        try:
            # Access the dataframe for this ticker
            # yfinance structure varies depending on single vs multi ticker
            # If multi-ticker, data columns are MultiIndex (Ticker, PriceType)
            
            if len(tickers) > 1:
                df = data[yf_ticker]
            else:
                df = data
            
            # Check if empty
            if df.empty:
                print(f"{ticker}: No data found.")
                continue
                
            last_price = df['Close'].iloc[-1]
            first_price_5d = df['Close'].iloc[0]
            change = ((last_price - first_price_5d) / first_price_5d) * 100
            
            print(f"--- {ticker} ---")
            print(df[['Close']].tail(5)) # Show last 5 rows of Close
            print(f"Change (5d): {change:.2f}%\n")
            
        except KeyError:
            print(f"{ticker}: Data fetch failed or key error.")
        except Exception as e:
            pass # print(f"{ticker}: Error {e}")

if __name__ == "__main__":
    print("Starting BIST 100 Tracker...")
    
    # 1. Get List
    symbols = get_bist100_list()
    
    # Truncate if too many for a simple demo or keep all?
    # User asked for active BIST 100, so we try to get all.
    # But scraping might be messy, so let's safeguard against empty lists.
    if not symbols:
        print("Failed to get symbol list. Using a small hardcoded sample for demonstration.")
        symbols = ['THYAO', 'GARAN', 'AKBNK', 'ASELS', 'EREGL']
    else:
        # Sometimes scraped lists might contain junk. verify briefly.
        # Clean up very long lists (BIST 100 should be ~100)
        if len(symbols) > 120:
            print(f"Warning: Found {len(symbols)} symbols. Truncating to likely top 100 alphabetically/length logic if needed, but proceeding with all.")
            
    # 2. Get Data
    df_data = get_stock_data(symbols)
    
    # 3. Display
    if df_data is not None and not df_data.empty:
        display_data(symbols, df_data)
    else:
        print("No stock data retrieved.")
