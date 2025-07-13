# app.py
import streamlit as st
import pandas as pd
import sys
import os

# Add src to the Python path to allow importing modules from the src directory
# This is crucial for Streamlit to locate our custom modules like sicbo_oracle.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the main SicBoOracle class and data handling functions
from sicbo_oracle import SicBoOracle, SicBoOutcome # SicBoOutcome is defined in sicbo_oracle
from data_generator import load_data, save_data

# --- Streamlit Page Configuration ---
# Sets the page title and layout for the Streamlit application.
st.set_page_config(page_title="🎲 Sic Bo Oracle", layout="centered")

# --- Custom CSS Styling ---
# This block defines the visual appearance of the application using Markdown and HTML.
st.markdown("""
<style>
/* Set 'Sarabun' as the primary font for all text elements */
html, body, [class*="css"] {
    font-family: 'Sarabun', sans-serif !important;
}
/* Styling for the main title of the application */
.big-title {
    font-size: 28px;
    text-align: center;
    font-weight: bold;
    color: #FFD700; /* Gold color for a premium look */
}
/* Styling for the prediction display box */
.predict-box {
    padding: 15px;
    background-color: #2a2a2a; /* Dark background for contrast */
    border-radius: 12px; /* Rounded corners for a modern feel */
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3); /* Subtle shadow for depth */
}
/* Styling for the main prediction text (e.g., "สูง" or "ต่ำ") */
.predict-box h2 {
    font-size: 36px;
    margin: 0;
    padding: 0;
    text-align: center;
}
/* Styling for smaller caption text within the prediction box (e.g., module source, confidence) */
.predict-box caption {
    font-size: 14px;
    color: #bbb; /* Lighter grey for readability */
    text-align: center;
    display: block;
    margin-top: 5px;
}
/* Container for the "Big Road" visualization, enabling horizontal scrolling */
.big-road-container {
    width: 100%;
    overflow-x: auto; /* Allows horizontal scrolling if content exceeds width */
    border: 1px solid #444; /* Border around the display */
    padding: 4px;
    background: #1c1c1c; /* Dark background */
    white-space: nowrap; /* Prevents columns from wrapping to the next line */
    border-radius: 8px;
}
/* Styling for each vertical column in the Big Road */
.big-road-column {
    display: inline-block;
    vertical-align: top;
    margin-right: 4px; /* Spacing between columns */
}
/* Styling for individual cells within the Big Road columns */
.big-road-cell {
    width: 28px; /* Fixed width for consistent cell size */
    height: 28px; /* Fixed height */
    text-align: center;
    line-height: 28px; /* Vertically center the text */
    font-size: 18px; /* Font size for outcome text (e.g., 'ส', 'ต') */
    margin-bottom: 2px;
    color: white; /* White text color */
    font-weight: bold;
    border-radius: 50%; /* Makes cells circular */
    display: flex; /* Use flexbox for perfect centering of content */
    align-items: center;
    justify-content: center;
}
/* Specific background colors for different Sic Bo outcomes in Big Road */
.cell-high { background-color: #28a745; } /* Green for 'สูง' */
.cell-low { background-color: #dc3545; } /* Red for 'ต่ำ' */
.cell-triplet { background-color: #ffc107; color: #333;} /* Yellow for 'ตอง', with dark text for contrast */
.cell-odd { background-color: #6f42c1; } /* Purple for 'คี่' */
.cell-even { background-color: #007bff; } /* Blue for 'คู่' */

/* Styling for Streamlit buttons */
.stButton>button {
    width: 100%; /* Make buttons take full width of their container */
    border-radius: 8px; /* Rounded corners for buttons */
    padding: 10px 0; /* Vertical padding */
    font-size: 18px;
    font-weight: bold;
    transition: all 0.2s ease-in-out; /* Smooth transition for hover effects */
    background-color: #444; /* Darker grey background */
    color: white; /* White text */
    border: none; /* No border */
}
.stButton>button:hover {
    transform: translateY(-2px); /* Slight lift effect on hover */
    box-shadow: 0 4px 8px rgba(0,0,0,0.2); /* Add shadow on hover */
    background-color: #555; /* Slightly lighter on hover */
}
/* Styling for Streamlit markdown headers (h3) */
.stMarkdown h3 {
    color: #FFD700; /* Gold color for section headers */
}
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
# Initialize the SicBoOracle instance and other state variables.
# st.session_state is crucial for persisting data across Streamlit reruns.
if 'oracle' not in st.session_state:
    st.session_state.oracle = SicBoOracle()
    # Attempt to load existing data from CSV when the application starts.
    initial_df = load_data()
    if not initial_df.empty:
        # Add historical rolls to the oracle to build its internal history.
        # This ensures that analysis and predictions are based on past data.
        for _, row in initial_df.iterrows():
            st.session_state.oracle.add_roll(row['Die1'], row['Die2'], row['Die3'])
        st.session_state.initial_data_loaded = True
        st.sidebar.success(f"โหลดข้อมูล {len(initial_df)} แถวจาก 'data/sicbo_data.csv'")
    else:
        st.session_state.initial_data_loaded = False
        st.sidebar.warning("ไม่พบไฟล์ข้อมูลเก่า หรือมีข้อผิดพลาดในการโหลด")

# Initialize state variables for the current prediction and related information.
# These will be updated dynamically as new rolls are added or history is modified.
if 'sicbo_prediction' not in st.session_state:
    st.session_state.sicbo_prediction = None
if 'sicbo_source' not in st.session_state:
    st.session_state.sicbo_source = None
if 'sicbo_confidence' not in st.session_state:
    st.session_state.sicbo_confidence = None
if 'sicbo_pattern_name' not in st.session_state:
    st.session_state.sicbo_pattern_name = None
if 'sicbo_miss_streak' not in st.session_state:
    st.session_state.sicbo_miss_streak = 0
# Flag to control the display of the initial waiting message.
if 'initial_wait_message_shown' not in st.session_state:
    st.session_state.initial_wait_message_shown = True

# Create a convenient reference to the oracle instance.
oracle = st.session_state.oracle

# --- UI Logic Functions ---
# Helper function to update the prediction state after any change in history.
def update_prediction_state():
    # Call the oracle to get the latest prediction based on the current history.
    prediction, source, confidence, pattern_code, current_miss_streak = oracle.predict_next_outcome()
    # Update all relevant session state variables.
    st.session_state.sicbo_prediction = prediction
    st.session_state.sicbo_source = source
    st.session_state.sicbo_confidence = confidence
    st.session_state.sicbo_pattern_name = pattern_code
    st.session_state.sicbo_miss_streak = current_miss_streak

# Handler function for adding a new roll.
def handle_add_roll(d1: int, d2: int, d3: int):
    oracle.add_roll(d1, d2, d3) # Add the new roll to the oracle's history.
    save_data(oracle.history) # Persist the updated history to the CSV file.
    update_prediction_state() # Recalculate and update the prediction display.
    st.session_state.initial_wait_message_shown = False # Hide the initial waiting message.
    st.rerun() # Rerun the app to refresh the UI.

# Handler function for removing the last roll from history.
def handle_remove_last_roll():
    oracle.remove_last_roll() # Remove from oracle's history
    save_data(oracle.history) # Persist the updated history
    update_prediction_state() # Update prediction
    st.rerun() # Rerun the app to refresh the UI.

# Handler function for resetting all history.
def handle_reset_all():
    oracle.reset_history() # Clear all history within the oracle.
    save_data(oracle.history) # Clear the CSV file as well.
    # Reset all prediction-related session state variables to their initial values.
    st.session_state.sicbo_prediction = None
    st.session_state.sicbo_source = None
    st.session_state.sicbo_confidence = None
    st.session_state.sicbo_pattern_name = None
    st.session_state.sicbo_miss_streak = 0
    st.session_state.initial_wait_message_shown = True # Show the initial waiting message again.
    st.rerun() # Rerun the app to refresh the UI.

# Map for displaying user-friendly pattern names based on the short codes from scorer.py.
pattern_name_map = {
    "HLHL": "ปิงปอง",         # High-Low-High-Low
    "LHLH": "ปิงปอง",         # Low-High-Low-High
    "HHL_LL": "สองตัด",       # High-High-Low-Low
    "LLH_HH": "สองตัด",       # Low-Low-High-High
    "HHH": "มังกรสูง",        # Three or more consecutive Highs
    "LLL": "มังกรต่ำ",        # Three or more consecutive Lows
    # You can add more mappings as you define new patterns in src/scorer.py
}

# --- Main Application UI ---
st.markdown('<div class="big-title">🎲 SIC BO ORACLE 🎲</div>', unsafe_allow_html=True)

# --- Prediction Display Section ---
st.markdown("<div class='predict-box'>", unsafe_allow_html=True)
st.markdown("<b>📍 คำทำนาย:</b>", unsafe_allow_html=True)
if st.session_state.sicbo_prediction:
    # Determine the appropriate emoji and color based on the predicted outcome.
    emoji = ""
    color = ""
    if st.session_state.sicbo_prediction == "สูง":
        emoji = "🟢" # Green circle emoji
        color = "#28a745" # Green color
    elif st.session_state.sicbo_prediction == "ต่ำ":
        emoji = "🔴" # Red circle emoji
        color = "#dc3545" # Red color
    elif st.session_state.sicbo_prediction == "คู่":
        emoji = "🔵" # Blue circle emoji
        color = "#007bff" # Blue color
    elif st.session_state.sicbo_prediction == "คี่":
        emoji = "🟣" # Purple circle emoji
        color = "#6f42c1" # Purple color
    elif st.session_state.sicbo_prediction == "ตอง":
        emoji = "🟡" # Yellow circle emoji
        color = "#ffc107" # Yellow color (for triplet prediction)
    
    # Display the predicted outcome with its emoji and color.
    st.markdown(f"<h2 style='color: {color};'>{emoji} <b>{st.session_state.sicbo_prediction}</b></h2>", unsafe_allow_html=True)
    
    # Display additional prediction details if available.
    if st.session_state.sicbo_source:
        st.caption(f"🧠 โมดูล: {st.session_state.sicbo_source}")
    if st.session_state.sicbo_pattern_name:
        # Get the user-friendly pattern name from the map.
        display_pattern_name = pattern_name_map.get(st.session_state.sicbo_pattern_name, st.session_state.sicbo_pattern_name)
        st.caption(f"📊 เค้าไพ่: {display_pattern_name}")
    if st.session_state.sicbo_confidence is not None:
        st.caption(f"🔎 ความมั่นใจ: {st.session_state.sicbo_confidence}%")
else:
    # Display initial waiting message or a general analysis message.
    if st.session_state.initial_wait_message_shown and len(oracle.history) < oracle.min_history_for_prediction:
        st.warning(f"⚠️ รอข้อมูลครบ {oracle.min_history_for_prediction} ตา ก่อนเริ่มทำนาย")
    else:
        st.info("⏳ กำลังวิเคราะห์ข้อมูล หรือยังไม่พบรูปแบบที่ชัดเจน")
st.markdown("</div>", unsafe_allow_html=True)

# --- Miss Streak Display ---
# Shows the current streak of incorrect predictions.
miss = st.session_state.sicbo_miss_streak
st.markdown(f"**❌ พลาดติดกัน: {miss} ครั้ง**")
if miss > 0:
    if miss == 3:
        st.warning("🧪 เริ่มกระบวนการฟื้นฟู (อาจมีการปรับกลยุทธ์)")
    elif miss >= 6:
        st.error("🚫 หยุดระบบชั่วคราว (พลาด 6 ครั้งติด)")

# --- Big Road (High/Low) Visualization ---
# Displays the history of High/Low outcomes in a Big Road format.
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<b>🕒 Big Road (สูง/ต่ำ):</b>", unsafe_allow_html=True)
# Filter history to only include 'สูง' or 'ต่ำ' for the Big Road display.
# 'ตอง' results are excluded from this specific visualization to focus on High/Low patterns.
history_for_big_road = [h for h in oracle.history['HighLow'].tolist() if h in ("สูง", "ต่ำ")]

if history_for_big_road:
    max_row = 6 # Maximum number of cells in a vertical column of the Big Road.
    columns, col, last = [], [], None # Initialize lists to build the Big Road structure.
    
    # Logic to group consecutive outcomes into vertical columns.
    for result in history_for_big_road:
        # If the current result is the same as the last and the column is not full, add to current column.
        if result == last and len(col) < max_row:
            col.append(result)
        else:
            # If the column has data, add it to the list of columns.
            if col:
                columns.append(col)
            col = [result] # Start a new column with the current result.
            last = result # Update the last result observed.
    
    if col: # Add the last incomplete column if it exists after the loop.
        columns.append(col)

    # Generate HTML for the Big Road display using the custom CSS classes.
    html = "<div class='big-road-container'>"
    for current_col_data in columns:
        html += "<div class='big-road-column'>"
        for cell_outcome in current_col_data:
            cell_class = ""
            cell_text = ""
            # Assign CSS class and text based on the outcome ('สูง' or 'ต่ำ').
            if cell_outcome == "สูง":
                cell_class = "cell-high"
                cell_text = "ส" # 'ส' for สูง (High)
            elif cell_outcome == "ต่ำ":
                cell_class = "cell-low"
                cell_text = "ต" # 'ต' for ต่ำ (Low)
            # You can extend this to include 'ตอง' or other outcomes if desired in the Big Road.
            html += f"<div class='big-road-cell {cell_class}'>{cell_text}</div>"
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
else:
    st.info("🔄 ยังไม่มีข้อมูลสำหรับ Big Road (สูง/ต่ำ)")

# --- Input for Current Roll ---
# Section for users to input the results of a new Sic Bo roll.
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<b>🎲 บันทึกผลลูกเต๋า:</b>", unsafe_allow_html=True)
# Number inputs for each of the three dice.
col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    die1_input = st.number_input("ลูกเต๋า 1:", min_value=1, max_value=6, value=1, key="input_d1")
with col_d2:
    die2_input = st.number_input("ลูกเต๋า 2:", min_value=1, max_value=6, value=1, key="input_d2")
with col_d3:
    die3_input = st.number_input("ลูกเต๋า 3:", min_value=1, max_value=6, value=1, key="input_d3")

# Display the calculated total score for the current input.
current_total_input = die1_input + die2_input + die3_input
st.markdown(f"**แต้มรวม: {current_total_input}**")

# --- Control Buttons (Add, Remove, Reset) ---
# Buttons for managing the history of rolls.
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
with col_ctrl1:
    # Button to add the current dice input to history.
    st.button("✅ บันทึกผลทอย", on_click=handle_add_roll, args=(die1_input, die2_input, die3_input,), use_container_width=True)
with col_ctrl2:
    # Button to remove the last recorded roll.
    st.button("↩️ ลบรายการล่าสุด", on_click=handle_remove_last_roll, use_container_width=True)
with col_ctrl3:
    # Button to clear all history and reset the oracle.
    st.button("🔄 เริ่มใหม่ทั้งหมด", on_click=handle_reset_all, use_container_width=True)

# --- Module Accuracy Display ---
# Shows the accuracy of each individual prediction module.
st.markdown("<hr>")
st.markdown("### 📈 ความแม่นยำรายโมดูล (จากประวัติปัจจุบัน)")
modules_accuracy = oracle.get_module_accuracies() # Retrieve accuracies from the oracle.
if modules_accuracy:
    # Display accuracies in a formatted way.
    for name, acc in modules_accuracy.items():
        st.write(f"✅ {name}: {acc:.1f}%")
else:
    st.info("ยังไม่มีข้อมูลความแม่นยำ (ต้องการข้อมูลมากขึ้น)")

st.markdown("---")
st.markdown("พัฒนาโดย: [ชื่อของคุณ/GitHub Profile]")
