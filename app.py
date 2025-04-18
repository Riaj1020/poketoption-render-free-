import telebot
import yfinance as yf
import pandas as pd
import talib
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import os
import time
import threading

# Telegram bot setup
API_TOKEN = '7482443496:AAHwtKK-FLpAaJP9vxc0V_NlDiunvhBFK4g'  # Your Telegram Bot Token
CHAT_ID = '-1002512649422'  # Your Telegram Chat ID
bot = telebot.TeleBot(API_TOKEN)

# Function to fetch data and calculate indicators
def fetch_and_analyze(pair="EURUSD=X"):
    # Fetch 1-minute data from Yahoo Finance
    data = yf.download(pair, period="1d", interval="1m")
    
    # Ensure data is not empty
    if data.empty:
        print("No data found")
        return None

    # Calculate technical indicators
    data['EMA'] = talib.EMA(data['Close'], timeperiod=14)
    data['RSI'] = talib.RSI(data['Close'], timeperiod=14)
    data['MACD'], data['MACD_signal'], _ = talib.MACD(data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    data['Bollinger_upper'], data['Bollinger_middle'], data['Bollinger_lower'] = talib.BBANDS(data['Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    data['Stochastic_K'], data['Stochastic_D'] = talib.STOCH(data['High'], data['Low'], data['Close'], fastk_period=14, slowk_period=3, slowd_period=3)

    # Get the most recent row for analysis
    last_row = data.iloc[-1]

    # Perform analysis based on indicators
    analysis = ""
    if last_row['RSI'] > 70:
        analysis += "RSI suggests overbought condition. "
    elif last_row['RSI'] < 30:
        analysis += "RSI suggests oversold condition. "
    
    if last_row['MACD'] > last_row['MACD_signal']:
        analysis += "MACD is bullish. "
    else:
        analysis += "MACD is bearish. "
    
    if last_row['Close'] > last_row['Bollinger_upper']:
        analysis += "Price is above the upper Bollinger Band. "
    elif last_row['Close'] < last_row['Bollinger_lower']:
        analysis += "Price is below the lower Bollinger Band. "
    
    if last_row['Stochastic_K'] > last_row['Stochastic_D']:
        analysis += "Stochastic is bullish. "
    else:
        analysis += "Stochastic is bearish. "

    # Prepare the signal message
    signal_message = f"Signal for {pair}: {analysis}\nSignal Time: {datetime.now()}\nExpiry Time: {datetime.now() + timedelta(minutes=1)}"
    
    return signal_message

# Function to plot chart and send it
def send_chart(pair="EURUSD=X"):
    # Fetch data for the chart
    data = yf.download(pair, period="1d", interval="1m")
    
    # Plot the closing price with indicators
    plt.figure(figsize=(10, 6))
    plt.plot(data['Close'], label='Close Price', color='blue')
    plt.plot(data['EMA'], label='EMA (14)', color='orange')
    plt.plot(data['Bollinger_upper'], label='Upper Bollinger Band', color='green')
    plt.plot(data['Bollinger_lower'], label='Lower Bollinger Band', color='red')
    plt.title(f'{pair} Price Chart with Indicators')
    plt.legend()

    # Save the chart to a BytesIO object
    chart_io = io.BytesIO()
    plt.savefig(chart_io, format='png')
    chart_io.seek(0)

    # Send the chart as an image to Telegram
    bot.send_photo(CHAT_ID, chart_io)

# Telegram Command Handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome! The Pocket Option Signal Bot is now active. Use /signal to get signals.")

@bot.message_handler(commands=['signal'])
def signal(message):
    signal_msg = fetch_and_analyze("EURUSD=X")
    if signal_msg:
        bot.send_message(CHAT_ID, signal_msg)
        send_chart("EURUSD=X")
    else:
        bot.send_message(CHAT_ID, "No signal available at the moment.")

@bot.message_handler(commands=['stop'])
def stop(message):
    bot.reply_to(message, "The bot is stopped.")
    # You can implement logic to stop fetching new data here if needed.

@bot.message_handler(commands=['selectpair'])
def selectpair(message):
    bot.reply_to(message, "Please select a trading pair, e.g., EUR/USD.")

# Function to keep the bot running continuously
def run_bot():
    bot.polling(non_stop=True)

# Start the bot in a new thread
threading.Thread(target=run_bot).start()

# Fetch and send signals continuously every minute
while True:
    signal_msg = fetch_and_analyze("EURUSD=X")
    if signal_msg:
        bot.send_message(CHAT_ID, signal_msg)
        send_chart("EURUSD=X")
    time.sleep(60)  # Wait for 1 minute before sending the next signal
