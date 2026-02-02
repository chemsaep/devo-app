import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import streamlit_authenticator as stauth

# --- 1. CONFIGURATION ET SÉCURITÉ ---
st.set_page_config(page_title="Devo Pro", layout="wide", page_icon="🥐")

# Identifiants par défaut
names = ['Administrateur']
usernames = ['admin']
passwords = ['1234'] # À changer plus tard

# Hachage compatible (évite le bug Hasher ligne 16)
hashed_passwords = stauth.Hasher(passwords).generate()

config = {
    'credentials': {
        'usernames': {
            usernames[0]: {'name': names[0], 'password': hashed_passwords[0]}
        }
    },
    'cookie': {'expiry_days': 30, 'key': 'devo_key', 'name': 'devo_cookie'}
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login : gestion flexible des versions de la bibliothèque
try:
    name, authentication_status, username = authenticator.login(location='main')
except:
    name, authentication_status, username = authenticator.login('Connexion', 'main')

if authentication_status:
    # --- 2. BARRE LATÉRALE DE PERSONNALISATION ---
    st.sidebar.title(f"✨ Espace de {name}")
    authenticator.logout('Déconnexion', 'sidebar')
    
    st.sidebar.markdown("---")
    uploaded_bg = st.sidebar.file_uploader("1. Ton Fond (PNG/JPG)", type=["png", "jpg"])
    fond_final = uploaded_bg if uploaded_bg else "fond_devis.png"

    nom_pro = st.sidebar.text_input("2. Nom entreprise", "Wassah Event")
    contact_pro = st.sidebar.text_input("3. Contact", "Ward - 06.65.62.00.92")
    insta_pro = st.sidebar.text_input("4. Instagram", "@wassah.event")
    lieu_pro = st.sidebar.text_input("5. Zone/Ville", "94")

    st.sidebar.subheader("6. Tes Tarifs")
    try:
        df_catalogue = pd.read_csv("catalogue.csv")
    except:
        df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])
    
    df_catalogue = st.sidebar.data_editor(df_catalogue, num_rows="dynamic", use_container_width=True)

    # --- 3. LOGIQUE PDF ---
    class PDF(FPDF):
        def header(self):
            try:
                self.image(fond_final, x=0, y=0, w=210, h=297)
            except:
                pass
            
            self.set_y(55) 
            self.set_font('Arial', 'I', 10)
            self.set_text_color(139, 115, 85)
            self.cell(0, 10, f"Des événements sur-mesure - {nom_pro}", 0, 1, 'C')
            
            self.set_y(80); self.set_x(25) 
            self.set_font('Arial', '', 9); self.set_text_color(0, 0, 0)
            self.cell(0, 5, f"Contact : {contact_pro}", 0, 1, 'L')
            self.set_x(25); self.cell(0, 5, f"Insta : {insta_pro}", 0, 1, 'L')
            self.set_x(25); self.cell(0, 5, f"Lieu : {lieu_pro}", 0, 1, 'L')

    def generer_pdf(client_info, df_panier, total_ttc):
        pdf = PDF(); pdf.add_page()
        pdf.set_y(80); pdf.set_right_margin(25); pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 5, f"Devis {nom_pro} pour :", 0, 1, 'R')
        pdf.set_font("Arial", size=10)
        for ligne in client_info:
            pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
        
        pdf.set_y(135); pdf.set_font("Arial", 'B', 13); pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
        pdf.set_font("Arial", size=11)
        for _, row in df_panier.iterrows():
            pdf.set_x(40); pdf.cell(0, 8, f"- {row['Désignation']} (x{int(row['Qté'])})", 0, 1, 'L')

        pdf.set_y(220); pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR", 0, 1, 'R')
        return pdf.output(dest='S').encode('latin-1', 'replace')

    # --- 4. INTERFACE ---
    st.title(f"🥐 Devo : {nom_pro}")
    
    # Logique d'analyse de texte
    def analyser_texte(texte, df_cat):
        lignes = texte.split('\n')
        client, panier = [], []
        for l in lignes:
            l = l.strip()
            if not l: continue
            match = re.search(r'(\d+)', l)
            if match and ("-" in l or any(p in l.lower() for p in ["box", "westaf", "brick"])):
                qte = int(match.group(1))
                nom = re.sub(r'[-\d+]', '', l).strip().lower()
                prix = 0.0
                for _, row in df_cat.iterrows():
                    if nom in str(row['Produit']).lower():
                        nom, prix = row['Produit'], float(row['Prix']); break
                panier.append({"Désignation": nom, "Prix Unit.": prix, "Qté": qte})
            else: client.append(l)
        return client, panier

    if 'panier_df' not in st.session_state:
        st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
    if 'client_info' not in st.session_state:
        st.session_state['client_info'] = []

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Message Client")
        txt = st.text_area("Colle la demande ici :", height=200)
        if st.button("✨ Analyser"):
            client, panier = analyser_texte(txt, df_catalogue)
            st.session_state['client_info'], st.session_state['panier_df'] = client, pd.DataFrame(panier)
            st.rerun()

    with c2:
        st.subheader("2. Finalisation")
        if not st.session_state['panier_df'].empty:
            ed_df = st.data_editor(st.session_state['panier_df'], use_container_width=True)
            total = (ed_df["Prix Unit."] * ed_df["Qté"]).sum()
            pdf_b = generer_pdf(st.session_state['client_info'], ed_df, total)
            st.download_button("📩 Télécharger le PDF", pdf_b, "devis.pdf")

elif authentication_status == False:
    st.error('Identifiant ou mot de passe incorrect')
elif authentication_status == None:
    st.warning('Veuillez entrer vos identifiants.')
