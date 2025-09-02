import streamlit as st
import ccxt
import pandas as pd
import threading
import time

st.set_page_config(page_title="Crypto Arbitrage Bot", layout="wide")

trade_log = []
bot_running = False

def create_exchange(name, api_key, secret):
    if name.lower() == "binance":
        return ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True
        })
    elif name.lower() == "kraken":
        return ccxt.kraken({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True
        })
    return None

def fetch_prices(binance, kraken):
    try:
        binance_price = binance.fetch_ticker('ETH/USDT')['last']
    except:
        binance_price = None
    try:
        kraken_price = kraken.fetch_ticker('ETH/USD')['last']
    except:
        kraken_price = None
    return binance_price, kraken_price

def execute_trade(buy_exchange, sell_exchange, buy_symbol, sell_symbol, amount):
    try:
        buy_order = buy_exchange.create_market_buy_order(buy_symbol, amount)
        sell_order = sell_exchange.create_market_sell_order(sell_symbol, amount)
        buy_price = buy_order['average']
        sell_price = sell_order['average']
        profit = (sell_price - buy_price) * amount
        trade_log.append({
            'time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'buy_from': buy_exchange.name,
            'sell_to': sell_exchange.name,
            'buy_price': round(buy_price, 2),
            'sell_price': round(sell_price, 2),
            'amount': amount,
            'profit': round(profit, 2)
        })
        return profit
    except Exception as e:
        trade_log.append({
            'time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'buy_from': buy_exchange.name,
            'sell_to': sell_exchange.name,
            'error': str(e)
        })
        return 0

def arbitrage_logic(binance, kraken, threshold, amount, delay):
    global bot_running
    while bot_running:
        binance_price, kraken_price = fetch_prices(binance, kraken)
        if binance_price and kraken_price:
            if binance_price + threshold < kraken_price:
                execute_trade(binance, kraken, 'ETH/USDT', 'ETH/USD', amount)
            elif kraken_price + threshold < binance_price:
                execute_trade(kraken, binance, 'ETH/USD', 'ETH/USDT', amount)
        time.sleep(delay)

def start_bot(binance, kraken, threshold, amount, delay):
    global bot_running
    bot_running = True
    threading.Thread(target=arbitrage_logic, args=(binance, kraken, threshold, amount, delay), daemon=True).start()

def stop_bot():
    global bot_running
    bot_running = False

with st.sidebar:
    st.title("⚙️ Bot Configuration")
    binance_key = st.text_input("Binance API Key", type="password")
    binance_secret = st.text_input("Binance Secret", type="password")
    kraken_key = st.text_input("Kraken API Key", type="password")
    kraken_secret = st.text_input("Kraken Secret", type="password")

    threshold = st.slider("Minimum Profit Threshold ($)", 1, 50, 10)
    amount = st.number_input("Trade Volume (ETH)", 0.01, 10.0, 0.1, step=0.01)
    delay = st.slider("Refresh Interval (seconds)", 2, 10, 3)

    if st.button("▶️ Start Bot") and not bot_running:
        try:
            binance = create_exchange("binance", binance_key, binance_secret)
            kraken = create_exchange("kraken", kraken_key, kraken_secret)
            binance.load_markets()
            kraken.load_markets()
            start_bot(binance, kraken, threshold, amount, delay)
            st.success("Bot started successfully.")
        except Exception as e:
            st.error(f"Error starting bot: {e}")

    if st.button("⏹ Stop Bot") and bot_running:
        stop_bot()
        st.warning("Bot stopped.")

st.title("📈 ETH/USD Arbitrage Bot Dashboard")

col1, col2, col3 = st.columns(3)
if 'binance' in locals() and 'kraken' in locals():
    b_price, k_price = fetch_prices(binance, kraken)
    with col1:
        st.metric("Binance ETH/USDT", f"${b_price:.2f}" if b_price else "N/A")
    with col2:
        st.metric("Kraken ETH/USD", f"${k_price:.2f}" if k_price else "N/A")
    with col3:
        if b_price and k_price:
            spread = abs(b_price - k_price)
            st.metric("Current Spread", f"${spread:.2f}")
        else:
            st.metric("Current Spread", "N/A")
else:
    st.warning("Enter API keys and start bot to view prices.")

st.subheader("📋 Trade Log")
if trade_log:
    df = pd.DataFrame(trade_log[::-1])
    st.dataframe(df, use_container_width=True)
    if 'profit' in df.columns:
        df['cumulative'] = df['profit'].cumsum()
        st.subheader("📊 Cumulative Profit")
        st.line_chart(df['cumulative'])
else:
    st.info("No trades executed yet.")
