import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Style Rotation Board", layout="wide")
st.title("Market Sentiment & Style Rotation Board")
st.write("""
This dashboard monitors global market momentum to determine risk aversion. 
* **Favor Relative Strength (Momentum):** When recent market success is above the historical average (investors are risk-tolerant).
* **Favor Relative Value:** When recent market success is below the historical average (investors are risk-averse).
""")

# ---------------------------------------------------------
# 2. DATA FETCHING & PROCESSING (Cached for performance)
# ---------------------------------------------------------
@st.cache_data(ttl=3600) 
def load_and_process_data(ticker="VT"):
    # Use Ticker.history() instead of download() to avoid yfinance formatting bugs
    stock = yf.Ticker(ticker)
    
    # Fetch monthly data
    data = stock.history(start="2010-01-01", interval="1mo")
    
    # history() automatically adjusts prices, so 'Close' is the adjusted close
    df = data[['Close']].copy()
    df.columns = ['Global_Market']
    
    # Calculate the 12-month rolling return
    df['12M_Return'] = df['Global_Market'].pct_change(periods=12)
    
    # Calculate the historical average of the 12-month return (expanding mean)
    df['Historical_Avg_Return'] = df['12M_Return'].expanding().mean()
    
    # Clean NaN values caused by the rolling calculation
    df.dropna(inplace=True)
    
    # Apply the rotation logic
    def determine_style(row):
        if row['12M_Return'] > row['Historical_Avg_Return']:
            return 'Relative Strength (Momentum)'
        elif row['12M_Return'] < row['Historical_Avg_Return']:
            return 'Relative Value'
        else:
            return 'Neutral'
            
    df['Favored_Style'] = df.apply(determine_style, axis=1)
    
    return df
# ---------------------------------------------------------
# 3. DASHBOARD METRICS (CURRENT STATUS)
# ---------------------------------------------------------
st.markdown("### **Current Market Signal**")
latest_data = df.iloc[-1]
latest_date = df.index[-1].strftime("%B %Y")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("As of Date", latest_date)
with col2:
    st.metric("Current 12M Return", f"{latest_data['12M_Return'] * 100:.2f}%")
with col3:
    # Color code the recommended style
    style_color = "green" if latest_data['Favored_Style'] == 'Relative Strength (Momentum)' else "red"
    st.markdown(f"**Target Style:** <span style='color:{style_color}; font-size: 24px;'>{latest_data['Favored_Style']}</span>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# 4. VISUALIZATION (THE SENTIMENT BOARD)
# ---------------------------------------------------------
st.markdown("### **Historical Rotation Chart**")

# Set up matplotlib figure
fig, ax = plt.subplots(figsize=(14, 6))

# Plot lines
ax.plot(df.index, df['12M_Return'], label='12-Month Global Return', color='blue', linewidth=1.5)
ax.plot(df.index, df['Historical_Avg_Return'], label='Historical Avg Return', color='black', linestyle='--', linewidth=1.5)

# Fill areas to show the dominant regime
ax.fill_between(df.index, df['12M_Return'], df['Historical_Avg_Return'], 
                 where=(df['12M_Return'] > df['Historical_Avg_Return']), 
                 interpolate=True, color='green', alpha=0.2, label='Favor Momentum (Low Risk Aversion)')

ax.fill_between(df.index, df['12M_Return'], df['Historical_Avg_Return'], 
                 where=(df['12M_Return'] < df['Historical_Avg_Return']), 
                 interpolate=True, color='red', alpha=0.2, label='Favor Value (High Risk Aversion)')

# Chart styling
ax.set_ylabel('Return')
ax.axhline(0, color='grey', linewidth=0.8)
ax.legend(loc='upper left')
ax.grid(alpha=0.3)

# Display the plot in Streamlit
st.pyplot(fig)

# ---------------------------------------------------------
# 5. RAW DATA VIEWER
# ---------------------------------------------------------
with st.expander("View Raw Data Log"):
    # Reverse dataframe to show newest dates at the top
    st.dataframe(df.sort_index(ascending=False))