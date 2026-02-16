import streamlit as st
import random
import json
import time
from google.api_core import exceptions  # Added for robust rate limit handling
from logic_v2_GitHub import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report

# 1. Page Configuration
st.set_page_config(page_title="FE Exam AI Tutor", layout="wide")

# 2. CSS for UI consistency, status badge, and padding
st.markdown("""
    <style>
    div.stButton > button {
        height: 60px;
        border-radius: 12px;
        font-weight: bold;
    }
    .status-badge {
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        border: 1px solid rgba(0,0,0,0.1);
        margin-top: 10px;
    }
    .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize Session State
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}
if "user_name" not in st.session_state: st.session_state.user_name = None
if "current_prob" not in st.session_state: st.session_state.current_prob = None
if "api_busy" not in st.session_state: st.session_state.api_busy = False

# Load Problems
PROBLEMS = load_problems()

# --- Helper: Activity Indicator in Header ---
def draw_header_with_status(title_text):
    head_col1, head_col2 = st.columns([4, 1])
    with head_col1:
        st.title(title_text)
    with head_col2:
        if st.session_state.api_busy:
            st.markdown('<div class="status-badge" style="background-color: #ff4b4b; color: white;">🔴 Professor Busy</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge" style="background-color: #28a745; color: white;">🟢 Professor Ready</div>', unsafe_allow_html=True)

# --- Page 0: Name Entry ---
if st.session_state.user_name is None:
    st.title("🎓 FE Exam Prep Portal")
    st.markdown("### Texas A&M University - Corpus Christi")
    with st.form("name_form"):
        name_input = st.text_input("Enter your Full Name to begin")
        if st.form_submit_button("Access Tutor"):
            if name_input.strip():
                st.session_state.user_name = name_input.strip()
                st.rerun()
            else:
                st.warning("Identification is required for academic reporting.")
    st.stop()

# --- Page 1: Main Dashboard ---
if st.session_state.page == "landing":
    draw_header_with_status("🚀 FE Exam AI Tutor") 
    st.subheader(f"Welcome, {st.session_state.user_name}!")
    st.info("Texas A&M University - Corpus Christi | Instinct Economy AI Lab | Dr. Dugan Um")
    
    st.markdown("---")
    st.write("Click below to generate a random challenge from the FE Mechanical problem bank.")
    
    if st.button("🎯 Start Random Practice Problem", use_container_width=True):
        if PROBLEMS:
            st.session_state.current_prob = random.choice(PROBLEMS)
            st.session_state.page = "chat"
            st.rerun()
        else:
            st.error("Problem bank not found. Please check your JSON file.")

# --- Page 2: Socratic Chat ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']
    
    if p_id not in st.session_state.grading_data: 
        st.session_state.grading_data[p_id] = {'solved': set()}
    
    solved = st.session_state.grading_data[p_id]['solved']
    draw_header_with_status(f"📌 {prob['category']}")
    
    cols = st.columns([2, 1])
    
    with cols[0]:
        st.info(prob['statement'])
        st.markdown("---")
        
        # Chat History Display
        chat_container = st.container(height=500)
        with chat_container:
            if p_id in st.session_state.chat_sessions:
                for message in st.session_state.chat_sessions[p_id].history:
                    with st.chat_message("assistant" if message.role == "model" else "user"):
                        st.markdown(message.parts[0].text)
            else:
                st.write("👋 **FE Tutor Ready.** How would you begin solving this using the FE Reference Handbook?")

    with cols[1]:
        st.write("### Tutor Tools")
        st.metric("Variables Found", f"{len(solved)} / {len(prob['targets'])}")
        st.progress(len(solved) / len(prob['targets']) if len(prob['targets']) > 0 else 0)
        
        feedback = st.text_area("Notes for the Professor:", placeholder="What concept was most challenging?", height=150)
        
        if st.button("⬅️ Submit & View Report", use_container_width=True):
            st.session_state.api_busy = True
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("Generating mastery report..."):
                try:
                    report = analyze_and_send_report(
                        st.session_state.user_name, 
                        prob['category'], 
                        history_text + f"\n--- STUDENT FEEDBACK ---\n{feedback}"
                    )
                    st.session_state.last_report = report
                    st.session_state.page = "report_view"
                    st.session_state.api_busy = False
                    st.rerun()
                except exceptions.ResourceExhausted:
                    st.session_state.api_busy = False
                    st.error("Professor busy (Rate Limit). Please wait 60 seconds.")

        # REMOVED SMTP LOGIC FROM SKIP BUTTON TO PREVENT INCORRECT EMAILS
        if st.button("New Problem (Skip)", use_container_width=True):
            if PROBLEMS:
                current_prob_id = st.session_state.current_prob['id']
                
                # Cleanup current session
                if current_prob_id in st.session_state.chat_sessions:
                    del st.session_state.chat_sessions[current_prob_id]
                
                # Reroll to a new random problem
                st.session_state.current_prob = random.choice(PROBLEMS)
                st.rerun()

    # Chat Logic Integration
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = (
            f"You are the professional FE Exam Tutor for {st.session_state.user_name} at TAMUCC. "
            f"REFERENCE DATA: {prob['statement']}. "
            "### CORE INSTRUCTIONS:\n"
            "1. LITERAL SOURCE OF TRUTH: Treat the REFERENCE DATA as the absolute authority. "
            "If the problem specifies non-standard setups, do not 'correct' them.\n"
            "2. GEOMETRIC VALIDATION: Before critiquing student math, re-verify data in the problem text.\n"
            "3. SOCRATIC METHOD: NEVER give a full explanation. Guide step-by-step.\n"
            "4. PRECISION: Use LaTeX for all math. Reference FE Handbook values where applicable."
        )
        try:
            model = get_gemini_model(sys_prompt)
            st.session_state.chat_sessions[p_id] = model.start_chat(history=[])
        except Exception:
            st.error("Failed to initialize Tutor. Please refresh.")

    if user_input := st.chat_input("Enter your analysis or calculation..."):
        st.session_state.api_busy = True
        for target, val in prob['targets'].items():
            if target not in solved and check_numeric_match(user_input, val):
                st.session_state.grading_data[p_id]['solved'].add(target)
                st.toast(f"Correct variable identified: {target}!")
        
        try:
            st.session_state.chat_sessions[p_id].send_message(user_input)
            st.session_state.api_busy = False
            st.rerun()
        except exceptions.ResourceExhausted:
            st.session_state.api_busy = False
            st.error("⚠️ System limit reached. Please wait 60 seconds before trying again.")
        except Exception as e:
            st.session_state.api_busy = False
            st.error(f"Connection pause: {e}")

# --- Page 3: Report View ---
elif st.session_state.page == "report_view":
    st.title("📊 Mastery Report")
    st.markdown(st.session_state.get("last_report", "No report available."))
    st.markdown("---")
    if st.button("Return to Dashboard for Next Problem"):
        st.session_state.current_prob = None
        st.session_state.page = "landing"
        st.rerun()
