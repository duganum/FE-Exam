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

# Load Problems
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
            st.error("Problem bank not found. Please check your JSON file.")

# --- Page 2: Socratic Chat ---
elif st.session_state.page == "chat":
    prob = st.session_state.current_prob
    p_id = prob['id']
    
    # Initialize grading for this specific instance
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
        st.write("### Tutor Tools")
        st.metric("Variables Found", f"{len(solved)} / {len(prob['targets'])}")
        st.progress(len(solved) / len(prob['targets']) if len(prob['targets']) > 0 else 0)
        
        feedback = st.text_area("Notes for the Professor:", placeholder="What concept was most challenging?", height=150)
        
        # Action Button: Submit
        if st.button("⬅️ Submit & View Report", use_container_width=True):
            history_text = ""
            if p_id in st.session_state.chat_sessions:
                for msg in st.session_state.chat_sessions[p_id].history:
                    role = "Tutor" if msg.role == "model" else "Student"
                    history_text += f"{role}: {msg.parts[0].text}\n"
            
            with st.spinner("Generating mastery report..."):
                report = analyze_and_send_report(
                    st.session_state.user_name, 
                    prob['category'], 
                    history_text + f"\n--- STUDENT FEEDBACK ---\n{feedback}"
                )
                st.session_state.last_report = report
                st.session_state.page = "report_view"
                st.rerun()
                
# --- [수정] 즉각적인 화면 전환이 보장된 Skip 로직 ---
        if st.button("New Problem (Skip)", use_container_width=True):
            student_name = st.session_state.user_name
            current_prob_id = st.session_state.current_prob['id']
            
            # 1. 다음 문제 후보군 확보
            parts = current_prob_id.split('_')
            prefix = f"{parts[0]}_{parts[1]}"
            cat_probs = [p for p in PROBLEMS if p['id'].startswith(prefix)]
            
            if cat_probs:
                # 2. 이메일 발송 (이메일 발송 때문에 화면이 멈추지 않도록 예외 처리 강화)
                import smtplib
                from email.mime.text import MIMEText
                
                try:
                    sender = st.secrets["EMAIL_SENDER"]
                    password = st.secrets["EMAIL_PASSWORD"]
                    receiver = "dugan.um@gmail.com"
                    
                    msg = MIMEText(f"Student: {student_name}\nProblem ID: {current_prob_id}")
                    msg['Subject'] = f"SKIP: {student_name} - {current_prob_id}"
                    msg['From'] = sender
                    msg['To'] = receiver
                    
                    # 타임아웃 설정을 추가하여 이메일 때문에 무한 대기하는 것을 방지
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=5) as server:
                        server.login(sender, password)
                        server.send_message(msg)
                except Exception as e:
                    # 메일 오류가 나더라도 학생 화면은 넘어가야 함
                    st.write(f"", unsafe_allow_html=True)

                # 3. 세션 데이터 초기화 및 강제 전환
                if current_prob_id in st.session_state.chat_sessions:
                    del st.session_state.chat_sessions[current_prob_id]
                
                # 새로운 랜덤 문제 할당
                st.session_state.current_prob = random.choice(cat_probs)
                
                # [핵심] 모든 데이터를 바꾼 후 즉시 리런
                st.rerun()
            else:
                st.warning("No other problems in this category.")
                
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
        st.session_state.current_prob = None
        st.session_state.page = "landing"
        st.rerun()



