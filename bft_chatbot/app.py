import streamlit as st
from chatbot import init_chat, Talker  # Importer depuis le fichier chatbot.py
from PIL import Image

# Initialisation du chatbot
conversation = init_chat()

# Stockage des conversations multiples
if 'all_conversations' not in st.session_state:
    st.session_state.all_conversations = {}

# Stockage de l'historique des questions et réponses pour la conversation active
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = "Conversation 1"
    st.session_state.history = []

# Sidebar (à gauche) pour gérer les conversations
with st.sidebar:
    st.title("Historique des conversations")
    
    # Afficher toutes les conversations avec option de suppression
    for conv in list(st.session_state.all_conversations.keys()):
        col1, col2 = st.columns([3, 1])  # Créer deux colonnes pour les boutons
        with col1:
            if st.button(conv):
                st.session_state.current_conversation = conv
                st.session_state.history = st.session_state.all_conversations[conv]
        
        with col2:
            if st.button("Supprimer", key=f"delete_{conv}"):
                del st.session_state.all_conversations[conv]
                if st.session_state.current_conversation == conv:
                    st.session_state.current_conversation = "Conversation 1"
                    st.session_state.history = st.session_state.all_conversations.get("Conversation 1", [])
    
    # Ajouter un bouton pour créer une nouvelle conversation
    if st.button("Nouvelle conversation"):
        new_conv = f"Conversation {len(st.session_state.all_conversations) + 1}"
        st.session_state.all_conversations[new_conv] = []
        st.session_state.current_conversation = new_conv
        st.session_state.history = []

# Titre principal en haut de la page
st.title("Chatbot BFT")
# Option pour afficher le logo dans la barre latérale
logo = Image.open("logo_bft.png")  # Remplacez par le chemin vers votre logo
st.image(logo, use_column_width=True)
# Entrée utilisateur en bas de la page
user_input = st.text_input("Posez votre question :", "")

# Bouton d'envoi
if st.button("Envoyer"):
    if user_input:
        with st.spinner("Réponse en cours..."):
            response = Talker(user_input, conversation)
            
            # Ajouter la question et la réponse à l'historique
            st.session_state.history.append({"question": user_input, "response": response})
            
            # Sauvegarder la conversation actuelle dans l'historique général
            st.session_state.all_conversations[st.session_state.current_conversation] = st.session_state.history
    else:
        st.warning("Veuillez entrer une question.")

# Affichage de l'historique des questions et réponses
if st.session_state.history:
    st.subheader(f"Historique de {st.session_state.current_conversation}")
    for item in reversed(st.session_state.history):  # Inverser l'ordre d'affichage
        # Créer un conteneur pour la question et la réponse
        with st.container():
            # Question
            st.markdown(f'<div style="background-color: #4CAF50; padding: 10px; border-radius: 5px; color: white; width: 100%;">'
                        f'👤 {item["question"]}</div>', unsafe_allow_html=True)
            
            # Réponse
            st.markdown(f'<div style="background-color: white; padding: 10px; border-radius: 5px; border: 1px solid #e0e0e0; color: black; width: 100%;">'
                        f'🤖 {item["response"]}</div>', unsafe_allow_html=True)
            st.markdown("---")  # Ligne de séparation

# Optionnel : ajout de styles CSS pour personnaliser davantage
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #4CAF50;  /* Couleur verte */
        color: white; /* Texte blanc */
        font-weight: bold;
    }
    .stTextInput>div>input {
        font-size: 18px;
    }
    .stMarkdown {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)
