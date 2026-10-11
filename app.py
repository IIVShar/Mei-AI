import os
import requests
import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------
# 1. Page Configuration & Environment Setup
# ---------------------------------------------------------
load_dotenv()

st.set_page_config(
    page_title="Mei AI", 
    page_icon="🤖", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Inject custom CSS to match your Gemini dark theme colors and clean layouts
st.markdown("""
    <style>
        .stApp { background-color: #131314 !important; color: #f3f4f6 !important; }
        section[data-testid="stSidebar"] { background-color: #1e1e20 !important; border-right: 1px solid #1f2937 !important; }
        div[data-testid="stSidebarNav"] { background-color: transparent !important; }
        .stButton>button {
            background-color: #282a2c !important; color: #e5e7eb !important;
            border-radius: 9999px !important; border: 1px solid #374151 !important;
        }
        .stButton>button:hover { background-color: #333538 !important; border-color: #4b5563 !important; }
        div[data-testid="stChatMessage"] { background-color: #131314 !important; padding: 1rem !important; border-radius: 0.75rem !important; }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatar"] img) { background-color: #2b2d30 !important; }
        pre { background-color: #0d1117 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; border-radius: 0.5rem !important; }
        code { color: #f472b6 !important; background-color: #2d333b !important; padding: 0.125rem 0.25rem !important; border-radius: 0.25rem !important; }
    </style>
""", unsafe_allowed_html=True)

# ---------------------------------------------------------
# 2. Session State Tracking (Chat History Management)
# ---------------------------------------------------------
if "chats" not in st.session_state:
    st.session_state.chats = {
        "Chat 1": [{"role": "assistant", "content": "Hello! I am Mei AI. Enter your API key in the sidebar to get started."}]
    }
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

def start_new_chat():
    new_chat_id = f"Chat {len(st.session_state.chats) + 1}"
    st.session_state.chats[new_chat_id] = [
        {"role": "assistant", "content": "Started a new conversation thread. Ask me anything!"}
    ]
    st.session_state.current_chat = new_chat_id

# ---------------------------------------------------------
# 3. Sidebar UI (Key Input, Custom Persona, Exports)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#a8c7fa; font-size:1.5rem; margin-bottom:0.5rem;'>Mei AI</h2>", unsafe_allowed_html=True)
    
    # API Key Input Block
    default_key = os.getenv("OPENROUTER_API_KEY", "")
    st.markdown("<div style='font-size:0.75rem; font-weight:600; color:#9ca3af; margin-top: 0.5rem;'>OpenRouter API Key</div>", unsafe_allowed_html=True)
    user_api_key = st.text_input(
        label="OpenRouter API Key",
        value=default_key,
        type="password",
        placeholder="sk-or-v1-...",
        label_visibility="collapsed"
    )
    
    # System Prompt Customization
    st.markdown("<div style='font-size:0.75rem; font-weight:600; color:#9ca3af; margin-top: 0.75rem;'>AI Personality / System Instructions</div>", unsafe_allowed_html=True)
    system_instruction = st.text_area(
        label="System Instructions",
        value="You are Mei AI, a helpful, precise, and polite AI assistant.",
        placeholder="e.g. Speak like a pirate / Be a senior software engineer...",
        label_visibility="collapsed",
        key="system_prompt_input"
    )

    st.markdown("<br>", unsafe_allowed_html=True)
    
    if st.button("➕ New Chat", use_container_width=True):
        start_new_chat()
        st.rerun()
        
    st.markdown("<div style='font-size:0.75rem; font-weight:600; color:#9ca3af; margin: 1rem 0 0.5rem 0.5rem;'>Recent Conversations</div>", unsafe_allowed_html=True)
    
    # Chat thread navigation
    for chat_title in list(st.session_state.chats.keys()):
        is_active = "⏳ " if chat_title == st.session_state.current_chat else "💬 "
        if st.button(f"{is_active}{chat_title}", key=f"nav_{chat_title}", use_container_width=True):
            st.session_state.current_chat = chat_title
            st.rerun()

    st.markdown("<br><hr style='border-color:#374151;'>", unsafe_allowed_html=True)
    
    # --- CHAT HISTORY DOWNLOAD LINK ---
    active_chat_title = st.session_state.current_chat
    chat_log_raw = ""
    for msg in st.session_state.chats[active_chat_title]:
        chat_log_raw += f"[{msg['role'].upper()}]:\n{msg['content']}\n\n"
        
    st.download_button(
        label="📥 Download History (.txt)",
        data=chat_log_raw,
        file_name=f"{active_chat_title.lower().replace(' ', '_')}_history.txt",
        mime="text/plain",
        use_container_width=True
    )

# ---------------------------------------------------------
# 4. Main Window Viewport & API Request Processing
# ---------------------------------------------------------
active_messages = st.session_state.chats[active_chat_title]

st.markdown(f"<h3 style='color:#e2e8f0;'>Current Thread: {active_chat_title}</h3>", unsafe_allowed_html=True)

# Loop and systematically render full conversation history log
for message in active_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User prompt field parsing logic loop
if user_input := st.chat_input("Ask Mei AI a question..."):
    if not user_api_key:
        st.error("🔑 Please enter your OpenRouter API Key in the sidebar before sending messages.")
    else:
        # Render and persist user prompt
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chats[active_chat_title].append({"role": "user", "content": user_input})

        # Injecting system context parameters alongside historical data index
        payload_messages = []
        if system_instruction.strip():
            payload_messages.append({"role": "system", "content": system_instruction})
            
        for msg in st.session_state.chats[active_chat_title]:
            payload_messages.append({"role": msg["role"], "content": msg["content"]})

        # Request stream handling targeting OpenRouter endpoint safely
        with st.chat_message("assistant"):
            with st.spinner("Mei AI is processing..."):
                try:
                    response = requests.post(
                        url="https://openrouter.ai",
                        headers={
                            "Authorization": f"Bearer {user_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "meta-llama/llama-3-8b-instruct:free",
                            "messages": payload_messages
                        }
                    )
                    
                    if response.status_code == 200:
                        json_payload = response.json()
                        ai_response = json_payload["choices"]["message"]["content"]
                        st.markdown(ai_response)
                        st.session_state.chats[active_chat_title].append({"role": "assistant", "content": ai_response})
                        st.rerun() # Forces layout sync refresh to update download logs tracking state
                    else:
                        st.error(f"API Error ({response.status_code}): Check if your entered key is valid.")
                        st.caption(response.text)
                except Exception as e:
                    st.error(f"Failed handling request payload execution routine: {e}")
