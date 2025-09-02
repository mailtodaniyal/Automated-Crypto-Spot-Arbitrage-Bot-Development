import streamlit as st
import pandas as pd
import time
import random

st.set_page_config(page_title="Crypto Arbitrage Bot (Demo)", layout="wide")

trade_log = []
bot_running = False

def simulate_prices():
    binance_price = round(random.uniform(3400, 3600), 2)
    kraken_price = round(binance_price + random.uniform(-20, 20), 2)
    return binance_price, kraken_price

def simulate_trade(buy_exchange, sell_exchange, buy_price, sell_price, amount):
    profit = (sell_price - buy_price) * amount
    trade_log.append({
        'time': time.strftime("%Y-%m-%d %H:%M:%S"),
        'buy_from': buy_exchange,
        'sell_to': sell_exchange,
        'buy_price': buy_price,
        'sell_price': sell_price,
        'amount': amount,
        'profit': round(profit, 2)
    })

def arbitrage_logic(threshold, amount, delay):
    global bot_running
    while bot_running:
        binance_price, kraken_price = simulate_prices()
        if binance_price + threshold < kraken_price:
            simulate_trade('Binance', 'Kraken', binance_price, kraken_price, amount)
        elif kraken_price + threshold < binance_price:
            simulate_trade('Kraken', 'Binance', kraken_price, binance_price, amount)
        time.sleep(delay)

def start_bot(threshold, amount, delay):
    global bot_running
    bot_running = True
    import threading
    threading.Thread(target=arbitrage_logic, args=(threshold, amount, delay), daemon=True).start()

def stop_bot():
    global bot_running
    bot_running = False

with st.sidebar:
    st.title("⚙️ Demo Settings")
    threshold = st.slider("Minimum Profit Threshold ($)", 1, 50, 10)
    amount = st.number_input("Trade Volume (ETH)", 0.01, 10.0, 0.5, step=0.01)
    delay = st.slider("Refresh Interval (seconds)", 1, 5, 2)

    if st.button("▶️ Start Demo Bot") and not bot_running:
        start_bot(threshold, amount, delay)
        st.success("Demo bot started.")

    if st.button("⏹ Stop Demo Bot") and bot_running:
        stop_bot()
        st.warning("Demo bot stopped.")

st.title("📈 ETH/USD Arbitrage Bot – Demo Mode")

if trade_log:
    latest = trade_log[-1]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Binance ETH/USDT", f"${latest['buy_price']:.2f}" if latest['buy_from'] == 'Binance' else f"${latest['sell_price']:.2f}")
    with col2:
        st.metric("Kraken ETH/USD", f"${latest['sell_price']:.2f}" if latest['sell_to'] == 'Kraken' else f"${latest['buy_price']:.2f}")
    with col3:
        spread = abs(latest['sell_price'] - latest['buy_price'])
        st.metric("Current Spread", f"${spread:.2f}")
else:
    st.info("Start the bot to see live simulated data.")

st.subheader("📋 Trade Log")
if trade_log:
    df = pd.DataFrame(trade_log[::-1])
    st.dataframe(df, use_container_width=True)
    st.subheader("📊 Cumulative Profit")
    df['cumulative'] = df['profit'].cumsum()
    st.line_chart(df['cumulative'])
else:
    st.write("No trades simulated yet.")
