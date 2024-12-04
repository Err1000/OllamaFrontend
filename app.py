import streamlit as st
import requests
import json

# Konstanten für Ollama API
OLLAMA_API_BASE = "http://localhost:11434"

# Seitenkonfiguration
st.set_page_config(
    page_title="Ollama Chat",
    page_icon="🤖",
    layout="wide"
)

# Funktion zum Abrufen verfügbarer Modelle
def get_available_models():
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/api/tags")
        if response.status_code == 200:
            models = response.json()["models"]
            return [model["name"] for model in models]
        return []
    except:
        return []

# Funktion zum Überprüfen des Modellstatus
def is_model_ready(model_name):
    try:
        response = requests.post(
            f"{OLLAMA_API_BASE}/api/generate",
            json={"model": model_name, "prompt": "Hi", "stream": False}
        )
        return response.status_code == 200
    except:
        return False

# Chat-Funktion
def chat_with_model(model_name, prompt):
    try:
        response = requests.post(
            f"{OLLAMA_API_BASE}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False}
        )
        if response.status_code == 200:
            return response.json()["response"]
        return "Fehler bei der Kommunikation mit dem Modell."
    except:
        return "Fehler bei der API-Anfrage."

# Erweiterte Session State Initialisierung
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Liste der gespeicherten Chats
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = 0

# Seitenaufbau - Statusleiste kommt vor dem Titel
status_container = st.container()
with status_container:
    st.markdown("""
    <div style='
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background-color: rgba(240, 242, 246, 0.95);
        padding: 10px;
        z-index: 1000;
        text-align: center;
        border-bottom: 1px solid rgba(49, 51, 63, 0.2);
    '>
    """, unsafe_allow_html=True)
    
    if st.session_state.selected_model and st.session_state.selected_model != "Keine Modelle gefunden":
        model_status = is_model_ready(st.session_state.selected_model)
        st.write(f"📌 Aktives Modell: **{st.session_state.selected_model}** | Status: {'🟢 Aktiv' if model_status else '🔴 Nicht verfügbar'}")
    else:
        st.write("⚠️ Kein Modell ausgewählt")
        
    st.markdown("</div>", unsafe_allow_html=True)

# Haupttitel mit etwas Abstand von der Statusleiste
st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
st.title("🤖 Ollama Chat")

# Sidebar mit Chat-Historie
with st.sidebar:
    st.header("Modelleinstellungen")
    available_models = get_available_models()
    st.session_state.selected_model = st.selectbox(
        "Wähle ein Modell",
        available_models if available_models else ["Keine Modelle gefunden"],
        key="model_selector"
    )
    
    # Trennlinie
    st.markdown("---")
    
    # Neuer Chat mit Namenseingabe
    new_chat_name = st.text_input("Chat-Name (optional)", key="new_chat_name", placeholder="z.B. Python Hilfe")
    if st.button("📝 Neuer Chat", use_container_width=True):
        # Aktuellen Chat in Historie speichern, falls Nachrichten vorhanden
        if st.session_state.messages:
            # Verwende benutzerdefinierten Namen oder Standardnamen
            chat_title = new_chat_name if new_chat_name else f"Chat {len(st.session_state.chat_history) + 1}"
            st.session_state.chat_history.append({
                "id": st.session_state.current_chat_id,
                "title": chat_title,
                "messages": st.session_state.messages.copy(),
                "model": st.session_state.selected_model
            })
        # Neuen Chat starten
        st.session_state.messages = []
        st.session_state.current_chat_id += 1
        # Das Textfeld wird beim nächsten Render automatisch geleert
        st.rerun()
    
    # Trennlinie
    st.markdown("---")
    
    # Chat-Historie anzeigen
    st.header("Chat-Historie")
    for idx, chat in enumerate(reversed(st.session_state.chat_history)):
        col1, col2 = st.columns([4, 1])
        
        # Chat-Button mit aktuellem Titel
        with col1:
            if st.button(
                f"💬 {chat['title']} ({chat['model']})",
                key=f"chat_{chat['id']}",
                use_container_width=True
            ):
                st.session_state.messages = chat['messages'].copy()
                st.rerun()
        
        # Bearbeiten-Button für den Chat-Namen
        with col2:
            if st.button("✏️", key=f"edit_{chat['id']}", help="Chat umbenennen"):
                st.session_state[f"edit_mode_{chat['id']}"] = True
                st.rerun()
        
        # Eingabefeld für neue Bezeichnung wenn im Bearbeitungsmodus
        if st.session_state.get(f"edit_mode_{chat['id']}", False):
            new_title = st.text_input(
                "Neuer Name:",
                value=chat['title'],
                key=f"new_title_{chat['id']}"
            )
            col3, col4 = st.columns([1, 1])
            with col3:
                if st.button("Speichern", key=f"save_{chat['id']}", use_container_width=True):
                    st.session_state.chat_history[-(idx+1)]['title'] = new_title
                    del st.session_state[f"edit_mode_{chat['id']}"]
                    st.rerun()
            with col4:
                if st.button("Abbrechen", key=f"cancel_{chat['id']}", use_container_width=True):
                    del st.session_state[f"edit_mode_{chat['id']}"]
                    st.rerun()
        
        st.markdown("---")

# Chat-Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat-Eingabe
if prompt := st.chat_input("Schreibe eine Nachricht..."):
    if st.session_state.selected_model and st.session_state.selected_model != "Keine Modelle gefunden":
        # Benutzernachricht anzeigen
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Modellantwort generieren
        with st.chat_message("assistant"):
            with st.spinner("Denke nach..."):
                response = chat_with_model(st.session_state.selected_model, prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.error("Bitte wähle zuerst ein verfügbares Modell aus.")

# Aktualisiertes CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stChatMessage {
        background-color: rgba(240, 242, 246, 0.5);
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .stChatInput {
        border-radius: 20px;
    }
    /* Sidebar immer sichtbar machen */
    section[data-testid="stSidebar"] {
        width: 250px !important;
        min-width: 250px !important;
    }
    /* Anpassungen für die Statusleiste */
    [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
        align-items: center;
    }
</style>
""", unsafe_allow_html=True) 