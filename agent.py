import streamlit as st
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv

# --- YOUR ORIGINAL CODE (UNCHANGED) ---
load_dotenv()

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

instructions = """
Role: You are my Personal Master-Chef & Meal Planner. You know every recipe, snack, and drink in the world.

Instruction 1: The Warm Welcome & Setup

Greeting: Start with a high-energy, fun, and short greeting.

Discovery: Ask about my preferences (Cuisines, Spice level, Allergies, Dislikes) in a few quick bullet points.

Instruction 2: Short & Elegant Language (Strict)

Keep it Short: Do NOT give long answers. Keep every response concise and to the point.

Simple English: Use easy, everyday words. No complex vocabulary.

Format: Use bullet points and bold text so I can read everything at a glance.

Instruction 3: Global Recipes & "The Weird Recipe" Reaction

Everything: Recipes for meals, snacks, tea, coffee, and desserts are all allowed.

The Weird Reaction: If I ask for something gross (like Tea with Salt), react with a funny/shocked emoji, tell me why it’s a bad idea, and suggest a better alternative—keep it brief!

Weekly Plan: Provide a clean 7-day table or list.

Flexibility: If I dislike a dish, give 3 short alternatives.

Secret Twist: One-line "Pro-Tip" for each main dish.

Instruction 4: The "Kitchen Focus" Guardrail

Strictly Food: Politely refuse non-food questions (weather, coding, etc.).

Short Refusal: "Sorry! My brain is only marinating in recipes. I can't help with that. Let's get back to the food!"

Vibe: Professional, witty, fast-paced, and organized.
"""

FILE_NAME = "chat_memory.json"

def load_data():
    if os.path.exists(FILE_NAME):
        if os.path.getsize(FILE_NAME) > 0:
            with open(FILE_NAME, "r") as f:
                return json.load(f)
    return []

def save_data(chat_history):
     new_memory=[]
     for message in chat_history:
          # Handling the format for your specific save_data logic
          message_text = message.parts[0].text if hasattr(message, 'parts') else message['content']
          role = message.role if hasattr(message, 'role') else ("model" if message['role'] == "assistant" else "user")
          
          new_memory.append({
               "role": role,
               "parts": [{"text": message_text}]
          }) 
     with open(FILE_NAME, "w") as diary:
          json.dump(new_memory, diary, indent=4)

# --- STREAMLIT UI SETUP ---
st.set_page_config(page_title="ChefPro AI", page_icon="👩‍🍳", layout="centered")

# Elegant Custom Fonts & Styles
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Poppins:wght@300;400&display=swap');
    
    .main-header {
        font-family: 'Playfair Display', serif;
        font-size: 42px;
        color: #E63946;
        text-align: center;
        margin-top: -50px;
    }
    .quote-text {
        font-family: 'Poppins', sans-serif;
        font-size: 14px;
        color: #457B9D;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar with Memory
with st.sidebar:
    st.title("📟 Agent Memory")
    if st.button("Clear History"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
        st.session_state.chat_history = []
        st.rerun()

# Top Header
st.markdown('<h1 class="main-header">ChefPro AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="quote-text">"Good food is the foundation of genuine happiness."</p>', unsafe_allow_html=True)

# Model Initialization using YOUR exact settings
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite',
    system_instruction=instructions
)

# Load History into Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_data()

# Start Chat
chat = model.start_chat(history=st.session_state.chat_history)

# Display Chat History
for message in chat.history:
    role = "assistant" if message.role == "model" else "user"
    avatar = "👨‍🍳" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.parts[0].text)

# Input Field
if user_input := st.chat_input("What's on the menu today?"):
    # Show user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    
    # Get Response
    response = chat.send_message(user_input)
    
    # Show Agent message
    with st.chat_message("assistant", avatar="👨‍🍳"):
        st.markdown(response.text)
    
    # Save automatically
    save_data(chat.history)