import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh  # pip install streamlit-autorefresh

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []

if 'autoupdate' not in st.session_state:
    st.session_state.autoupdate = False

if 'max_history' not in st.session_state:
    st.session_state.max_history = 100

st.set_page_config(page_title="Battery Monitoring Dashboard", layout="wide")

# Header
st.markdown("""
    <h1 style='text-align: center; color: #00c6ff;'>🔋 Battery Monitoring Dashboard</h1>
    <p style='text-align: center; color: #4f4f4f;'>Track real-time metrics of your battery cells with interactive visuals and alerts</p>
    <hr style='border-top: 3px solid #00c6ff;'>
""", unsafe_allow_html=True)

# Sidebar configuration
st.sidebar.markdown("## ⚙ Configuration Panel")
num_cells = st.sidebar.slider("Select Number of Cells", min_value=1, max_value=10, value=8)

# Alert thresholds
temp_threshold = st.sidebar.number_input("🔥 Temperature Alert Threshold (°C)", min_value=0, max_value=100, value=40)
volt_threshold = st.sidebar.number_input("⚡ Voltage Alert Threshold (V)", min_value=0.0, max_value=5.0, value=3.5)

autoupdate = st.sidebar.checkbox("🔄 Enable Auto Refresh", value=st.session_state.autoupdate)
st.session_state.autoupdate = autoupdate

# Auto refresh
if autoupdate:
    count = st_autorefresh(interval=1000, limit=None, key="autorefresh")

# Input cells data with expanders
voltages, currents, temperatures, capacities, modes = [], [], [], [], []
mode_options = ['Charging', 'Discharging', 'Idle']

for i in range(num_cells):
    with st.sidebar.expander(f"🔋 Cell {i+1} Input", expanded=False):
        st.number_input(f"Voltage (V) - Cell {i+1}", value=3.7, step=0.01, key=f"voltage_{i}")
        st.number_input(f"Current (A) - Cell {i+1}", value=0.0, step=0.01, key=f"current_{i}")
        st.number_input(f"Temperature (°C) - Cell {i+1}", value=25.0, step=0.1, key=f"temp_{i}")
        st.number_input(f"Capacity (%) - Cell {i+1}", min_value=0, max_value=100, value=100, key=f"cap_{i}")
        st.selectbox(f"Mode - Cell {i+1}", options=mode_options, index=2, key=f"mode_{i}")

    # Store in local lists
    voltages.append(st.session_state[f"voltage_{i}"])
    currents.append(st.session_state[f"current_{i}"])
    temperatures.append(st.session_state[f"temp_{i}"])
    capacities.append(st.session_state[f"cap_{i}"])
    modes.append(st.session_state[f"mode_{i}"])

# Update dashboard or auto refresh
if st.sidebar.button("🚀 Update Dashboard") or autoupdate:
    timestamp = datetime.now()
    st.session_state.history.append({
        'timestamp': timestamp,
        'voltages': voltages.copy(),
        'currents': currents.copy(),
        'temperatures': temperatures.copy(),
        'capacities': capacities.copy(),
        'modes': modes.copy()
    })
    if len(st.session_state.history) > st.session_state.max_history:
        st.session_state.history = st.session_state.history[-st.session_state.max_history:]

# Alerts
alert_msgs = []
for i in range(num_cells):
    if temperatures[i] > temp_threshold:
        alert_msgs.append(f"🔥 Cell {i+1} Overheating! Temp: {temperatures[i]:.1f} °C")
    if voltages[i] < volt_threshold:
        alert_msgs.append(f"⚡ Low Voltage on Cell {i+1}: {voltages[i]:.2f} V")

if alert_msgs:
    st.warning("\n".join(alert_msgs))

# Cell status cards
st.markdown("### 📊 Cell Status Overview")
cell_rows = [st.columns(4) for _ in range((num_cells + 3) // 4)]
mode_colors = {
    'Charging': '#28a745',
    'Discharging': '#dc3545',
    'Idle': '#6c757d'
}

for i in range(num_cells):
    with cell_rows[i // 4][i % 4]:
        status_color = mode_colors.get(modes[i], '#6c757d')
        st.markdown(f"""
        <div style='border-radius: 15px; padding: 20px; background: linear-gradient(135deg, #d0f0fd, #ffffff); box-shadow: 0 4px 8px rgba(0,0,0,0.15); margin-bottom: 20px; transition: all 0.3s ease;'>
            <h4 style='color:#006fa6; text-align:center;'>🔋 Cell {i+1}</h4>
            <ul style='list-style:none; padding-left:0; font-size: 15px;'>
                <li>🔌 Voltage: <strong>{voltages[i]:.2f} V</strong></li>
                <li>⚡ Current: <strong>{currents[i]:.2f} A</strong></li>
                <li>🌡 Temperature: <strong>{temperatures[i]:.1f} °C</strong></li>
                <li>📈 Capacity: <strong>{capacities[i]} %</strong></li>
                <li style='color:{status_color}; font-weight:bold;'>{modes[i]}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# Create DataFrame safely for plotting
expanded_rows = []
for row in st.session_state.history:
 
    timestamp = row['timestamp']
    cell_count = len(row['voltages'])  # dynamically handle cell count
    for i in range(cell_count):
        expanded_rows.append({
            'timestamp': timestamp,
            'cell': f'Cell {i+1}',
            'voltage': row['voltages'][i],
            'current': row['currents'][i],
            'temperature': row['temperatures'][i],
            'capacity': row['capacities'][i],
            'mode': row['modes'][i]
        })

df_expanded = pd.DataFrame(expanded_rows)

# Capacity Tracking
if not df_expanded.empty:
    volt_series = []
    # Voltage
    st.markdown("### 📈 Voltage Tracking Over Time")
    fig_v = go.Figure()
    for i in range(num_cells-1):
        volt_series = [entry['voltages'][i] for entry in st.session_state.history]
        time_series = [entry['timestamp'] for entry in st.session_state.history]
        fig_v.add_trace(go.Scatter(x=time_series, y=volt_series, mode='lines+markers', name=f'Cell {i+1}'))
    fig_v.update_layout(xaxis_title='Time', yaxis_title='Voltage (V)', legend_title='Cells', template='plotly_white', height=350)
    st.plotly_chart(fig_v, use_container_width=True)

    # Current
    st.markdown("### ⚡ Current Tracking Over Time")
    fig_c = go.Figure()
    for i in range(num_cells-1):
        curr_series = [entry['currents'][i] for entry in st.session_state.history]
        time_series = [entry['timestamp'] for entry in st.session_state.history]
        fig_c.add_trace(go.Scatter(x=time_series, y=curr_series, mode='lines+markers', name=f'Cell {i+1}'))
    fig_c.update_layout(xaxis_title='Time', yaxis_title='Current (A)', legend_title='Cells', template='plotly_white', height=350)
    st.plotly_chart(fig_c, use_container_width=True)

    # Temperature
    st.markdown("### 🌡 Temperature Tracking Over Time")
    fig_t = go.Figure()
    for i in range(num_cells-1):
        temp_series = [entry['temperatures'][i] for entry in st.session_state.history]
        time_series = [entry['timestamp'] for entry in st.session_state.history]
        fig_t.add_trace(go.Scatter(x=time_series, y=temp_series, mode='lines+markers', name=f'Cell {i+1}'))
    fig_t.update_layout(xaxis_title='Time', yaxis_title='Temperature (°C)', legend_title='Cells', template='plotly_white', height=350)
    st.plotly_chart(fig_t, use_container_width=True)

    st.markdown("### 📈 Capacity Tracking Over Time")
    fig_cap = go.Figure()
    for cell_id in df_expanded['cell'].unique():
        cell_data = df_expanded[df_expanded['cell'] == cell_id]
        fig_cap.add_trace(go.Scatter(
            x=cell_data['timestamp'],
            y=cell_data['capacity'],
            mode='lines+markers',
            name=cell_id
        ))

    fig_cap.update_layout(
        xaxis_title='Time',
        yaxis_title='Capacity (%)',
        legend_title='Cells',
        template='plotly_white',
        height=400
    )

    st.plotly_chart(fig_cap, use_container_width=True)
else:
    st.info("No data to display yet. Please enter values and update the dashboard.")

# Footer
st.markdown("""
---
<p style='text-align: center;'>Made with ❤ using Streamlit · 2025</p>
""", unsafe_allow_html=True)