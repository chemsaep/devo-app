import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import streamlit_authenticator as stauth

# --- 1. CONFIGURATION ET SÉCURITÉ ---
st.set_page_config(page_title="Devo Pro", layout="wide", page_icon="🥐")

# Données utilisateurs
names = ['Administrateur']
usernames = ['admin']
passwords = ['1234']

# Méthode de hachage la plus compatible
hashed_passwords = stauth.Hasher(passwords).generate()

# Configuration directe sans passer par une variable externe
authenticator = stauth.Authenticate(
    {'usernames': {
        usernames[0]: {'name': names[0], 'password': hashed_passwords[0]}
    }},
    'devo_cookie',
    'signature_key',
    cookie_expiry_days=30
)

# Formulaire de connexion
# Note : Sur certaines versions, c'est login('Connexion', 'main') 
# ou authenticator.login() tout court.
try:
    name, authentication_status, username = authenticator.login('main')
except:
    name, authentication_status, username = authenticator.login('Connexion', 'main')

if authentication_status:
    st.sidebar.title(f"✨ Bienvenue {name}")
    authenticator.logout('Déconnexion', 'sidebar')
    
    # --- ICI TU GARDES TOUT TON RESTE DE CODE (Sidebar, PDF, Analyse) ---
    # (Veille à ce que le reste du code soit bien indenté sous ce "if")
    st.title("🥐 Devo : Wassah Event")
    
    # ... la suite de ton code ...

elif authentication_status == False:
    st.error('Identifiant ou mot de passe incorrect')
elif authentication_status == None:
    st.warning('Veuillez entrer vos identifiants.')

