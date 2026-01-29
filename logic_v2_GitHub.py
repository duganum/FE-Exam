import streamlit as st
import google.generativeai as genai
import json
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_gemini_model(system_instruction):
    """Initializes and returns the Gemini model."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        # Using 1.5 Flash for high speed and reliability in tutor apps
        return genai.GenerativeModel(
            model_name='models/gemini-1.5-flash', 
            system_instruction=system_instruction
        )
    except Exception as e:
        st.error(f"Gemini Initialization Failed: {e}")
        return None

def load_problems():
    """Loads the FE Exam problems from your JSON repository."""
    try:
        # Ensure this filename matches your 100-problem JSON file exactly
        with open('fe_problems_100.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Problem bank load error: {e}")
        return []

def check_numeric_match(user_val, correct_val, tolerance=0.05):
    """Checks for a 5% error margin, essential for engineering precision."""
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
    """Evaluates student mastery based on NCEES FE Mechanical standards."""
    eval_instruction = (
        "You are an Engineering Professor at TAMUCC evaluating FE Exam readiness. "
        "Score the student (0-10) based on their logic and first principles.\n\n"
        "SCORING RUBRIC:\n"
        "0-3: Non-technical or guessed answers.\n"
        "4-6: Understands basic concepts but lacks reference to the FE Handbook.\n"
        "7-8: Solid technical logic. Correctly uses LaTeX for formulas.\n"
        "9-10: Perfect engineering reasoning and unit consistency.\n\n"
        "RULES:\n"
        "1. Prioritize 'First Principles' thinking.\n"
        "2. Award points for LaTeX formatting ($\sigma, \Delta T, \sum F$).\n"
        "3. Output ONLY the integer."
    )
    
    model = get_gemini_model(eval_instruction)
    if not model: return 0
    try:
        response = model.generate_content(f"Chat history to evaluate:\n{chat_history}")
        score_match = re.search(r"\d+", response.text)
        return int(score_match.group()) if score_match else 0
    except: return 0

def analyze_and_send_report(user_name, topic_title, chat_history):
    """Sends a professional FE Mastery report to Dr. Dugan Um."""
    score = evaluate_understanding_score(chat_history)
    
    report_instruction = (
        f"Generate an academic report for Dr. Dugan Um regarding {user_name}'s FE prep.\n"
        "Include: Mastery Score, Conceptual Strengths, and Handbook usage proficiency."
    )
    
    model = get_gemini_model(report_instruction)
    if not model: return "Analysis Unavailable"

    prompt = (f"Student: {user_name}\nTopic: {topic_title}\nScore: {score}/10\n\nDATA:\n{chat_history}")
    
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
    msg['Subject'] = f"FE-Exam Tutor ({user_name}): {topic_title} [Score: {score}/10]"
    msg.attach(MIMEText(report_text, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"SMTP Error: {e}")
    
    return report_text
