import streamlit as st
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
from google.api_core import exceptions
import time

# --- ENVIRONMENT SETUP ---
load_dotenv()

# api_key = os.getenv("GEMINI_API_KEY")

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

# --- REFINED CHEF INSTRUCTIONS ---
instructions = """
You are ChefPro AI, a friendly Personal Chef & Meal Planner. You are fun, energetic, and a total foodie!

1. Kitchen Memory
- ALWAYS check chat history first.
- If the history is empty and user asks about past dishes, say politely: "Sorry! I forgot our previous recipes, but let's make something amazing today!" 

2. Contextual Feedback
- If history exists, ask about the last dish the user tried.

3. Recipe Steps
- Give recipes in simple, numbered steps.
- End EVERY recipe with one **Secret Pro-Tip** (keep it hidden in chat).

4. Style & Language
- Use very simple English.
- Switch to Urdu/Roman Urdu if user does.
- Refuse non-food questions in a funny, friendly way.

5. Formatting
- Give clear, easy-to-read responses.
"""

FILE_NAME = "chat_memory.json"

def load_data():
    if os.path.exists(FILE_NAME):
        if os.path.getsize(FILE_NAME) > 0:
            with open(FILE_NAME, "r") as f:
                return json.load(f)
    return []

def save_data(chat_history):
    new_memory = []
    for message in chat_history:
        # Gemini history object handles parts differently, so we extract text carefully
        message_text = message.parts[0].text
        role = "model" if message.role == "model" else "user"
        new_memory.append({"role": role, "parts": [{"text": message_text}]}) 
    with open(FILE_NAME, "w") as diary:
        json.dump(new_memory, diary, indent=4)

# --- UI SETUP ---
st.set_page_config(page_title="ChefPro AI 👩‍🍳", page_icon="🥘", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&family=Playfair+Display:wght@700&display=swap');
    .stApp { background: linear-gradient(to bottom, #ffffff, #fdf2f2); font-family: 'Poppins', sans-serif; }
    .main-header { font-family: 'Playfair Display', serif; font-size: 55px; background: -webkit-linear-gradient(#E63946, #D62828); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-top: -40px; font-weight: 800; }
    .subtitle { text-align: center; color: #457B9D; font-size: 18px; margin-top: -10px; margin-bottom: 30px; }
    [data-testid="stChatMessage"] { background-color: white !important; border-radius: 20px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #f1f1f1; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 📟 Chief Command")
    st.image("https://cdn-icons-png.flaticon.com/512/3448/3448099.png", width=100)
    st.divider()
    if st.button("🗑️ Clear Kitchen Memory"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
        st.session_state.chat_history = []
        if "greeted" in st.session_state:
            del st.session_state.greeted
        st.success("History Reset! 🧼")
        st.rerun()

st.markdown('<h1 class="main-header">ChefPro AI 🥘</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Where every recipe tells a story... ✨</p>', unsafe_allow_html=True)

# --- CHAT INITIALIZATION ---
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite', # Updated to a valid available model name
    system_instruction=instructions
)

if "chat_history" not in st.session_state:
    raw_data = load_data()
    st.session_state.chat_history = []
    for msg in raw_data:
        # Loading for st.session_state display
        st.session_state.chat_history.append({"role": msg['role'], "parts": [msg['parts'][0]['text']]})

# Always start chat with the current session state history
chat = model.start_chat(history=st.session_state.chat_history)

# --- SMART FEEDBACK TRIGGER (Only if history exists) ---
if len(st.session_state.chat_history) > 0 and "greeted" not in st.session_state:
    with st.chat_message("assistant", avatar="👩‍🍳"):
        status_box = st.empty()
        status_box.markdown("*(Thinking... 🍳)*")
        try:
            response = chat.send_message("I'm back! Check history, find the last dish, and ask how it was. No placeholders!")
            final_text = response.text
            status_box.markdown(final_text)
            
            # Sync session state and save
            st.session_state.chat_history.append({"role": "model", "parts": [final_text]})
            st.session_state.greeted = True
            save_data(chat.history)
        except:
            status_box.empty()

# --- DISPLAY ALL CHAT BUBBLES ---
for message in st.session_state.chat_history:
    role = "assistant" if message['role'] in ["model", "assistant"] else "user"
    avatar = "👩‍🍳" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        # Extract text correctly from parts
        part_text = message['parts'][0] if isinstance(message['parts'][0], str) else message['parts'][0]['text']
        st.markdown(part_text)

# --- CHAT INPUT AREA ---
if user_input := st.chat_input("What’s on the menu today, Chief? 🍔"):
    # 1. Add User message to UI and State
    st.session_state.chat_history.append({"role": "user", "parts": [user_input]})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    
    # 2. Generate and display assistant response
    with st.chat_message("assistant", avatar="👩‍🍳"):
        response_container = st.empty()
        response_container.markdown("*(Thinking... 🍳)*")
        
        try:
            response = chat.send_message(user_input)
            final_text = response.text
            
            # Typing effect
            displayed_text = ""
            for char in final_text:
                displayed_text += char
                response_container.markdown(displayed_text + "▌")
                time.sleep(0.01)
            response_container.markdown(final_text)
            
            # 3. Add Model message to State and save to JSON
            st.session_state.chat_history.append({"role": "model", "parts": [final_text]})
            save_data(chat.history)
            
        except exceptions.ResourceExhausted:
            response_container.error("🚨 Quota Reached!")
        except Exception as e:
            response_container.error(f"Chef's a bit busy! {str(e)}")