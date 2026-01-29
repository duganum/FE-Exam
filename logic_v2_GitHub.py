import streamlit as st
import google.generativeai as genai
import json
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    """Initializes and returns the Gemini 2.0 Flash model."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            model_name='models/gemini-2.0-flash', 
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"Gemini Initialization Failed: {e}")
        return None

def load_problems():
    """Loads the list of Statics problems from the JSON repository."""
    try:
        with open('problems_v2_GitHub.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Problem bank load error: {e}")
        return []

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    """Extracts numbers and checks if they are within a 5% error margin."""
    try:
        u_match = re.search(r"[-+]?\d*\.\d+|\d+", str(user_val))
        if not u_match: return False
        u = float(u_match.group())
        c = float(correct_val)
        if c == 0: return abs(u) < tolerance
        return abs(u - c) <= abs(tolerance * c)
    except (ValueError, TypeError, AttributeError):
        return False

def evaluate_understanding_score(chat_history):
    """
    Evaluates student understanding (0-10) based on Statics principles.
    Focuses on Free Body Diagrams (FBD) and Equilibrium equations.
    """
    eval_instruction = (
        "You are a strict Engineering Professor at Texas A&M University - Corpus Christi. "
        "Evaluate the student's mastery of Statics (0-10) based ONLY on the chat history.\n\n"
        "STRICT SCORING RUBRIC:\n"
        "0-3: Purely non-technical chat or complete misunderstanding of vectors.\n"
        "4-5: Good conceptual understanding but fails to state governing equilibrium equations.\n"
        "6-8: Correctly identifies and uses LaTeX for equilibrium equations (e.g., $\sum F_x = 0$, $\sum M_A = 0$).\n"
        "9-10: Flawless logic. Correctly resolves vectors, applies moment arms, and explains the physics logic perfectly.\n\n"
        "CRITICAL RULES:\n"
        "1. If the student does not explicitly state the GOVERNING EQUATIONS ($\sum F = 0$), do NOT exceed 5.\n"
        "2. If the student uses sloppy notation (like 'Sum Fx' or 'MA') instead of LaTeX ($\sum F_x$ or $M_A$), penalize the score.\n"
        "3. Output ONLY the integer."
    )
    
    model = get_gemini_model(eval_instruction)
    if not model: return 0

    try:
        response = model.generate_content(f"Chat history to evaluate:\n{chat_history}")
        score_match = re.search(r"\d+", response.text)
        if score_match:
            score = int(score_match.group())
            return min(max(score, 0), 10)
        return 0
    except Exception:
        return 0

def analyze_and_send_report(user_name, topic_title, chat_history):
    """Analyzes the Statics session and sends a professional email report to Dr. Um."""
    
    # Calculate score based on Statics rubric
    score = evaluate_understanding_score(chat_history)
    
    report_instruction = (
        "You are an academic evaluator analyzing a Statics session for Dr. Dugan Um.\n"
        "Your report must include:\n"
        "1. Session Overview\n"
        f"2. Numerical Understanding Score: {score}/10\n"
        "3. Mathematical Rigor: Did the student use $\sum F=0$ or $\sum M=0$ in LaTeX?\n"
        "4. FBD Logic: Did the student correctly identify force components?\n"
        "5. Engagement Level\n"
        "6. CRITICAL: Quote the section '--- STUDENT FEEDBACK ---' exactly."
    )
    
    model = get_gemini_model(report_instruction)
    if not model: return "AI Analysis Unavailable"

    prompt = (
        f"Student Name: {user_name}\n"
        f"Topic: {topic_title}\n"
        f"Assigned Score: {score}/10\n\n"
        f"DATA:\n{chat_history}\n\n"
        "Format for Dr. Dugan Um. Ensure all math/vectors in the report use LaTeX."
    )
    
    try:
        response = model.generate_content(prompt)
        report_text = response.text
    except Exception as e:
        report_text = f"Analysis failed: {str(e)}"

    # Email Logic
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"] 
    receiver = "dugan.um@gmail.com" 

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"Statics Tutor ({user_name}): {topic_title} [Score: {score}/10]"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"SMTP Error: {e}")
    
    return report_text
