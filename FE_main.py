import streamlit as st
import requests
import time

# ==========================================
# SECTION 1: PROBLEM BANK
# ==========================================
PROBLEM_BANK = [
    {
        "id": 1,
        "category": "Dynamics",
        "question": "A car accelerates at a(t) = 2t² + 2 with an initial velocity of 10 m/s. How fast is the car traveling after 3 s?",
        "options": ["34 m/s", "50 m/s", "60 m/s", "97 m/s"],
        "correctAnswer": "34 m/s",
        "explanation": "Integrate a(t) to find v(t) = (2/3)t³ + 2t + C. With v(0)=10, C=10. At t=3, v = (2/3)(27) + 2(3) + 10 = 18 + 6 + 10 = 34."
    },
    {
        "id": 2,
        "category": "Thermodynamics",
        "question": "A parallel flow heat exchanger has ΔT₁ = 250 K and ΔT₂ = 50 K. What is the log mean temperature difference (LMTD)?",
        "options": ["124.3 K", "150.0 K", "200.0 K", "100.0 K"],
        "correctAnswer": "124.3 K",
        "explanation": "LMTD = (ΔT₁ - ΔT₂) / ln(ΔT₁ / ΔT₂) = (250 - 50) / ln(250 / 50) = 200 / ln(5) ≈ 124.27 K."
    },
    {
        "id": 3,
        "category": "Mechanics of Materials",
        "question": "An aluminum rod (d = 12 mm, ν = 0.35) experiences a longitudinal strain of ε = -0.002. What is the increase in diameter?",
        "options": ["8.4 μm", "4.2 μm", "12.0 μm", "0.35 μm"],
        "correctAnswer": "8.4 μm",
        "explanation": "Lateral strain ε_lat = -ν * ε = -0.35 * (-0.002) = 0.0007. Δd = ε_lat * d = 0.0007 * 12 mm = 0.0084 mm = 8.4 μm."
    }
]

# Populate remaining 30 problems
for i in range(4, 31):
    cat = ["Mathematics", "Engineering Econ", "Ethics", "Statics", "Fluid Mechanics"][i % 5]
    PROBLEM_BANK.append({
        "id": i,
        "category": cat,
        "question": f"FE Practice Problem #{i}: Solve the {cat} unknown using Handbook formulas.",
        "options": ["Correct Option", "Incorrect B", "Incorrect C", "Incorrect D"],
        "correctAnswer": "Correct Option",
        "explanation": "Reference the FE Handbook for this category."
    })

# ==========================================
# SECTION 2: APP CONFIG & STATE
# ==========================================
st.set_page_config(page_title="FE Exam AI Tutor", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_id" not in st.session_state:
    st.session_state.active_id = 1

# ==========================================
# SECTION 3: SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("### 📚 FE Practice Problems")
    for prob in PROBLEM_BANK:
        if st.button(f"Problem {prob['id']}: {prob['category']}", key=f"btn_{prob['id']}"):
            st.session_state.active_id = prob['id']
            st.session_state.messages = [{"role": "assistant", "content": f"I'm ready to help with this {prob['category']} problem. What's your first step?"}]
            st.rerun()

# ==========================================
# SECTION 4: MAIN INTERFACE
# ==========================================
current_prob = PROBLEM_BANK[st.session_state.active_id - 1]

st.markdown(f"## {current_prob['category']} - Problem {current_prob['id']}")
st.subheader(current_prob['question'])

col1, col2 = st.columns([2, 1])

with col1:
    user_choice = st.radio("Select an option:", current_prob['options'], index=None)
    if user_choice:
        if user_choice == current_prob['correctAnswer']:
            st.success("Correct!")
            with st.expander("View Full Solution"):
                st.write(current_prob['explanation'])
        else:
            st.error("Incorrect. Use the chat for a hint!")

with col2:
    st.markdown("### 🧠 AI Tutor Chat")
    chat_container = st.container(height=450)
    for msg in st.session_state.messages:
        chat_container.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ask for a hint..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_container.chat_message("user").write(prompt)

        # GEMINI API CALL
        with chat_container.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("Thinking...")
            
            # Replace with your actual key
            API_KEY = "YOUR_GEMINI_API_KEY_HERE" 
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            
            sys_instr = f"Tutor rules: Never give the answer. Use first principles. Problem: {current_prob['question']}. Correct: {current_prob['correctAnswer']}."
            
            try:
                payload = {"contents": [{"parts": [{"text": f"{sys_instr}\nUser: {prompt}"}]}]}
                res = requests.post(url, json=payload, timeout=10)
                ai_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                placeholder.markdown(ai_text)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})
            except:
                placeholder.error("Connection error. Is the API Key valid?")
