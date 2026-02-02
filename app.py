import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import streamlit_authenticator as stauth

# --- 1. CONFIGURATION ET SÉCURITÉ ---
st.set_page_config(page_title="Devo Pro", layout="wide", page_icon="🥐")

# Liste des utilisateurs
names = ['Administrateur']
usernames = ['admin']
passwords = ['1234']

# Hachage sécurisé des mots de passe
hashed_passwords = stauth.Hasher(passwords).generate()

# --- CRÉATION DE LA VARIABLE CONFIG (Indispensable) ---
config = {
    'credentials': {
        'usernames': {
            usernames[0]: {
                'name': names[0],
                'password': hashed_passwords[0]
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'signature_devo_key',
        'name': 'devo_cookie_auth'
    }
}

# Initialisation de l'authentification avec la variable config
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Formulaire de connexion
name, authentication_status, username = authenticator.login('Connexion', 'main')

if authentication_status:
    # --- TOUT LE RESTE DE TON CODE (Sidebar, Analyse, PDF) ---
    st.sidebar.title(f"✨ Espace de {name}")
    authenticator.logout('Déconnexion', 'sidebar')

    # ... (Copie-colle ici la suite de ton code habituel : Sidebar, Generer_pdf, etc.)
    st.title(f"🥐 Devo")
    st.info("Utilise la barre latérale pour configurer ton espace.")

elif authentication_status == False:
    st.error('Identifiant ou mot de passe incorrect')
elif authentication_status == None:
    st.warning('Veuillez entrer votre identifiant et votre mot de passe.')
