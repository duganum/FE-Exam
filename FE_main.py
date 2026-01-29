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

# Add placeholders for the remaining problems to match your 30-problem count
for i in range(4, 31):
    cat = ["Mathematics", "Engineering Econ", "Ethics", "Statics", "Fluid Mechanics"][i % 5]
    PROBLEM_BANK.append({
        "id": i,
        "category": cat,
        "question": f"FE Practice Problem #{i}: Given the parameters for this {cat} system, solve for the primary unknown.",
        "options": ["Correct Option", "Incorrect B", "Incorrect C", "Incorrect D"],
        "correctAnswer": "Correct Option",
        "explanation": "Use the FE Reference Handbook formulas for this category to solve."
    })

# ==========================================
# SECTION 2: APP CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="FE Exam AI Tutor", layout="wide")

# Custom CSS to mimic your React UI
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; font-weight: bold; }
    .tamu-header { background-color: white; padding: 1.5rem; border-bottom: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# SECTION 3: SESSION STATE
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_id" not in st.session_state:
    st.session_state.active_id = 1

# ==========================================
# SECTION 4: SIDEBAR & NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("### 📚 30 Practice Problems")
    for prob in PROBLEM_BANK:
        if st.button(f"Problem {prob['id']}: {prob['category']}", key=f"btn_{prob['id']}"):
            st.session_state.active_id = prob['id']
            st.session_state.messages = [{"role": "assistant", "content": f"Ready for this {prob['category']} challenge? Ask me for a hint!"}]
            st.rerun()

# ==========================================
# SECTION 5: MAIN INTERFACE
# ==========================================
current_prob = PROBLEM_BANK[st.session_state.active_id - 1]

# Header
st.markdown(f"""
    <div class="tamu-header">
        <h1 style='margin:0; color:#1e40af;'>FE Exam AI Tutor</h1>
        <p style='margin:0; color:#64748b; font-weight:bold; font-size:12px;'>TAMU-CC ENGINEERING | DR. DUGAN UM</p>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"**Category:** `{current_prob['category']}`")
    st.subheader(current_prob['question'])
    
    # Quiz logic
    user_choice = st.radio("Select an option:", current_prob['options'], index=None)
    
    if user_choice:
        if user_choice == current_prob['correctAnswer']:
            st.success("Correct!")
            with st.expander("See Explanation"):
                st.write(current_prob['explanation'])
        else:
            st.error("Not quite. Check your calculations or ask the tutor for a hint.")

with col2:
    st.markdown("### 🧠 AI Engineering Tutor")
    
    # Chat Container
    chat_container = st.container(height=400)
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask for a hint..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)

        # AI Logic (Gemini API Integration)
        # Note: You'll need to add your API Key in Streamlit Secrets
        with chat_container.chat_message("assistant"):
            response_placeholder = st.empty()
            response_placeholder.markdown("Thinking...")
            
            # This is where your API call logic goes. For now, a placeholder:
            time.sleep(1)
            response = f"To solve this {current_prob['category']} problem, remember to check the FE Reference Handbook section on {current_prob['category']}. Look for the primary variables provided in the prompt."
            
            response_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("---")
st.caption("NCEES FE Mechanical Standard | Instinct Economy AI Lab")
