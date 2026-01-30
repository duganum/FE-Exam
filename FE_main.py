import streamlit as st
import random
import json
from logic_v2_GitHub import get_gemini_model, load_problems, check_numeric_match, analyze_and_send_report

# 1. Page Configuration
st.set_page_config(page_title="FE Exam AI Tutor", layout="wide")

# 2. CSS for UI consistency
st.markdown("""
    <style>
    div.stButton > button {
        height: 60px;
        border-radius: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize Session State
if "page" not in st.session_state: st.session_state.page = "landing"
if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "grading_data" not in st.session_state: st.session_state.grading_data = {}
if "user_name" not in st.session_state: st.session_state.user_name = None
if "current_prob" not in st.session_state: st.session_state.current_prob = None

PROBLEMS = load_problems()

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

# --- Page 1: Main Dashboard (Random Problem Launcher) ---
if st.session_state.page == "landing":
    st.title("🚀 FE Exam AI Tutor") 
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
            st.error("Problem bank not found. Please check fe_problems_100.json.")

# --- Page 2: Socratic Chat ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']
    
    # Initialize grading and chat for this specific instance
    if p_id not in st.session_state.grading_data: 
        st.session_state.grading_data[p_id] = {'solved': set()}
    
    solved = st.session_state.grading_data[p_id]['solved']
    
    cols = st.columns([2, 1])
    
    with cols[0]:
        st.subheader(f"📌 {prob['category']}")
        st.info(prob['statement'])
        st.markdown("---")
        
        # Chat History Display
        if p_id in st.session_state.chat_sessions:
            for message in st.session_state.chat_sessions[p_id].history:
                with st.chat_message("assistant" if message.role == "model" else "user"):
                    st.markdown(message.parts[0].text)
        else:
            st.write("👋 **FE Tutor Ready.** How would you begin solving this using the FE Reference Handbook?")

    with cols[1]:
        st.metric("Variables Found", f"{len(solved)} / {len(prob['targets'])}")
        st.progress(len(solved) / len(prob['targets']) if len(prob['targets']) > 0 else 0)
        
        feedback = st.text_area("Notes for the Professor:", placeholder="What concept was most challenging?", height=150)
        
        # Action Buttons
        if st.button("⬅️ Submit & View Report", use_container_width=True):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("Generating mastery report..."):
                report = analyze_and_send_report(st.session_state.user_name, prob['category'], history_text + f"\n--- STUDENT FEEDBACK ---\n{feedback}")
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()
        
# --- 수정된 New Problem (Skip) 버튼 로직 (간편 모니터링용) ---
        if st.button("New Problem (Skip)", use_container_width=True):
            # 1. 전송할 최소 정보 구성
            student_name = st.session_state.user_name
            problem_id = prob['id']
            category = prob['category']
            
            # 2. 교수님께 간단한 보고서 전송 (이름과 문항 정보만)
            with st.spinner("Recording skip event..."):
                # 간결한 리포트 작성을 위한 텍스트 구성
                simple_report = f"Student '{student_name}' skipped the problem: {problem_id} ({category})."
                
                # 기존 함수 호출 (주제와 간단한 내용만 전송)
                analyze_and_send_report(
                    user_name=student_name, 
                    topic_title=f"SKIP EVENT: {problem_id}", 
                    chat_history=simple_report
                )
            
            # 3. 새로운 랜덤 문제 선택 후 리런
            prefix = prob['id'].split('_')[0] + "_" + prob['id'].split('_')[1]
            cat_probs = [p for p in PROBLEMS if p['id'].startswith(prefix)]
            st.session_state.current_prob = random.choice(cat_probs)
            st.rerun()
    # Chat Logic Integration
    if p_id not in st.session_state.chat_sessions:
        sys_prompt = (
            f"You are the professional FE Exam Tutor for {st.session_state.user_name} at TAMUCC. "
            f"Context: {prob['statement']}. Use LaTeX for all math. "
            "STRICT RULES: 1. Use the Socratic method to guide the student. "
            "2. Reference the FE Reference Handbook values where applicable. "
            "3. Respond ONLY after the student types something. 4. Use English only."
        )
        model = get_gemini_model(sys_prompt)
        st.session_state.chat_sessions[p_id] = model.start_chat(history=[])

    if user_input := st.chat_input("Enter your analysis or calculation..."):
        # Check for numeric matches in the background
        for target, val in prob['targets'].items():
            if target not in solved and check_numeric_match(user_input, val):
                st.session_state.grading_data[p_id]['solved'].add(target)
        
        st.session_state.chat_sessions[p_id].send_message(user_input)
        st.rerun()

# --- Page 3: Report View ---
elif st.session_state.page == "report_view":
    st.title("📊 Mastery Report")
    st.markdown(st.session_state.get("last_report", "No report available."))
    st.markdown("---")
    if st.button("Return to Dashboard for Next Problem"):
        # Reset current problem to force a new random selection on landing
        st.session_state.current_prob = None
        st.session_state.page = "landing"
        st.rerun()

