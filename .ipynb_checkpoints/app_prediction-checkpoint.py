import streamlit as st
import pandas as pd
import joblib
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import importlib.util
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import io
import os

# Vérification des dépendances requises
required = ['streamlit', 'pandas', 'joblib', 'numpy', 'plotly', 'matplotlib', 'reportlab']
optional = ['seaborn']
for pkg in required:
    if not importlib.util.find_spec(pkg):
        st.error(f"❌ Module '{pkg}' manquant. Installez-le avec 'pip install {pkg}'.")
        st.stop()
seaborn_available = importlib.util.find_spec('seaborn') is not None
if not seaborn_available:
    st.warning("⚠️ Module 'seaborn' non trouvé. Utilisation d'une heatmap simplifiée avec Plotly.")

# Configuration de la page avec un titre personnalisé et une mise en page large
st.set_page_config(page_title=" Density Prediction Dashboard", layout="wide")

# Chemin pour sauvegarder l'historique
HISTORY_FILE = "historique_predictions.csv"

# Fonction pour charger l'historique depuis un fichier
def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    else:
        return pd.DataFrame(columns=[
            'Timestamp', 'Débit_Acide_m3h', 'Débit_Vapeur_kgh', 
            'Température_Évaporateur_C', 'Vide_Bouilleur_torr', 'Densité_Predite_kgm3'
        ])

# Fonction pour sauvegarder l'historique dans un fichier
def save_history(df):
    df.to_csv(HISTORY_FILE, index=False)

# Initialisation de l'état de la session pour l'historique
if 'history' not in st.session_state:
    st.session_state.history = load_history()

# CSS pour le thème clair avec fond blanc
theme_css = """
    <style>
        .main { 
            background: #ffffff; 
            padding: 20px; 
            border-radius: 10px; 
        }
        .card { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
            margin-bottom: 20px; 
        }
        .title { 
            font-family: 'Arial', sans-serif; 
            color: #2c3e50; 
            text-align: center; 
            margin-bottom: 20px; 
        }
        .prediction { 
            font-size: 24px; 
            color: #2ecc71; 
            text-align: center; 
            font-weight: bold; 
        }
        .error { 
            color: #e74c3c; 
            text-align: center; 
        }
        .stButton>button { 
            background-color: #4CAF50; 
            color: white; 
            border-radius: 8px; 
            padding: 10px 20px; 
            font-size: 16px; 
            transition: all 0.3s ease; 
        }
        .stButton>button:hover { 
            background-color: #45a049; 
            transform: scale(1.05); 
        }
        .stNumberInput input { 
            border: 2px solid #007bff; 
            border-radius: 5px; 
            padding: 8px; 
            background-color: #fff; 
        }
        .error-message { 
            color: #e74c3c; 
            font-size: 12px; 
            margin-top: 5px; 
        }
        @media (max-width: 600px) {
            .stNumberInput { width: 100% !important; }
            .card { padding: 10px; }
        }
    </style>
    <script>
        function showToast(message, type) {
            const toast = document.createElement('div');
            toast.style.position = 'fixed';
            toast.style.top = '20px';
            toast.style.right = '20px';
            toast.style.padding = '10px 20px';
            toast.style.borderRadius = '5px';
            toast.style.color = 'white';
            toast.style.zIndex = '1000';
            toast.innerText = message;
            toast.style.backgroundColor = type === 'success' ? '#2ecc71' : '#e74c3c';
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
        function validateInputs() {
            const inputs = [
                {id: 'debit_acide', min: 0, max: 100, errorId: 'debit_acide_error', errorMsg: 'Débit d\\'acide doit être entre 0 et 100 m³/h'},
                {id: 'debit_vapeur', min: 0, max: 10000, errorId: 'debit_vapeur_error', errorMsg: 'Débit de vapeur doit être entre 0 et 10000 kg/h'},
                {id: 'temperature', min: 0, max: 200, errorId: 'temperature_error', errorMsg: 'Température doit être entre 0 et 200 °C'},
                {id: 'vide', min: 0, max: 760, errorId: 'vide_error', errorMsg: 'Vide bouilleur doit être entre 0 et 760 Torr'}
            ];
            let valid = true;
            inputs.forEach(input => {
                const el = document.querySelector(`input[key="${input.id}"]`);
                const errorEl = document.getElementById(input.errorId);
                if (!el || el.value === '' || isNaN(el.value) || el.value < input.min || el.value > input.max) {
                    if (el) el.style.borderColor = 'red';
                    if (errorEl) errorEl.innerText = input.errorMsg;
                    valid = false;
                } else {
                    el.style.borderColor = '#007bff';
                    if (errorEl) errorEl.innerText = '';
                }
            });
            document.querySelector('.stButton>button[key="predict_button"]').disabled = !valid;
        }
        document.addEventListener('DOMContentLoaded', () => {
            const inputs = document.querySelectorAll('input[type="number"]');
            inputs.forEach(input => input.addEventListener('input', validateInputs));
            validateInputs();
        });
    </script>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# Titre
st.markdown("<h1 class='title'>🔮 Density Prediction Dashboard</h1>", unsafe_allow_html=True)

# Chargement du modèle et de y_mean
try:
    model = joblib.load("modele_final.pkl")
except Exception as e:
    st.markdown(f"<p class='error'>❌ Erreur lors du chargement du modèle : {e}</p>", unsafe_allow_html=True)
    st.markdown("<script>showToast('Erreur lors du chargement du modèle', 'error');</script>", unsafe_allow_html=True)
    st.stop()

try:
    with open("y_mean.txt", "r") as f:
        y_mean = float(f.read())
except Exception as e:
    st.markdown(f"<p class='error'>❌ Erreur lors du chargement de y_mean.txt : {e}</p>", unsafe_allow_html=True)
    st.markdown("<script>showToast('Erreur lors du chargement de y_mean', 'error');</script>", unsafe_allow_html=True)
    st.stop()

# Mise en page avec barre latérale et contenu principal
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("<div class='card'><h3>Paramètres d'entrée</h3>", unsafe_allow_html=True)
    
    # Champs de saisie avec valeurs par défaut, formatage précis et placeholders pour messages d'erreur
    debit_acide = st.number_input(
        "Débit d'acide (m³/h)", 
        value=30.0011291504, 
        step=1e-7, 
        format="%.10f", 
        key="debit_acide"
    )
    st.markdown("<div id='debit_acide_error' class='error-message'></div>", unsafe_allow_html=True)
    
    debit_vapeur = st.number_input(
        "Débit de vapeur (Kg/h)", 
        value=3525.1234567890, 
        step=1e-6, 
        format="%.10f", 
        key="debit_vapeur"
    )
    st.markdown("<div id='debit_vapeur_error' class='error-message'></div>", unsafe_allow_html=True)
    
    temperature = st.number_input(
        "Température évaporateur (°C)", 
        value=92.3600000001, 
        step=1e-6, 
        format="%.10f", 
        key="temperature"
    )
    st.markdown("<div id='temperature_error' class='error-message'></div>", unsafe_allow_html=True)
    
    vide = st.number_input(
        "Vide bouilleur (Torr)", 
        value=59.123456, 
        step=1e-6, 
        format="%.10f", 
        key="vide"
    )
    st.markdown("<div id='vide_error' class='error-message'></div>", unsafe_allow_html=True)

    # Bouton de prédiction
    if st.button("🔮 Prédire", key="predict_button"):
        with st.spinner("Calcul de la prédiction..."):
            try:
                # Création du DataFrame pour la prédiction
                X = pd.DataFrame([{
                    'Débit_Acide_m3h': debit_acide,
                    'Débit_Vapeur_kgh': debit_vapeur,
                    'Température_Évaporateur_C': temperature,
                    'Vide_Bouilleur_torr': vide,
                }])

                # Vérification des entrées invalides
                if X.isna().any().any() or np.isinf(X).any().any():
                    st.markdown("<p class='error'>❌ Données d'entrée invalides (NaN ou infini).</p>", unsafe_allow_html=True)
                    st.markdown("<script>showToast('Données d\\'entrée invalides', 'error');</script>", unsafe_allow_html=True)
                else:
                    # Prédiction
                    y_pred = model.predict(X)[0] + y_mean
                    st.markdown(f"<p class='prediction'>✅ Densité prédite : {y_pred:.6f} kg/m³</p>", unsafe_allow_html=True)
                    st.markdown("<script>showToast('Prédiction réussie !', 'success');</script>", unsafe_allow_html=True)
                    
                    # Sauvegarde dans l'historique
                    new_entry = pd.DataFrame([{
                        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Débit_Acide_m3h': debit_acide,
                        'Débit_Vapeur_kgh': debit_vapeur,
                        'Température_Évaporateur_C': temperature,
                        'Vide_Bouilleur_torr': vide,
                        'Densité_Predite_kgm3': y_pred
                    }])
                    st.session_state.history = pd.concat([st.session_state.history, new_entry], ignore_index=True)
                    # Sauvegarder l'historique dans le fichier
                    save_history(st.session_state.history)
                    
            except Exception as e:
                st.markdown(f"<p class='error'>❌ Erreur lors de la prédiction : {e}</p>", unsafe_allow_html=True)
                st.markdown("<script>showToast('Erreur lors de la prédiction', 'error');</script>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card'><h3>Visualisations</h3>", unsafe_allow_html=True)
    
    # Jauge pour la densité prédite
    if 'y_pred' in locals():
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=y_pred,
            title={'text': "Densité Prédite (kg/m³)", 'font': {'color': '#2c3e50'}},
            gauge={
                'axis': {'range': [y_mean - 100, y_mean + 100]},
                'bar': {'color': "#2ecc71"},
                'steps': [
                    {'range': [y_mean - 100, y_mean - 50], 'color': "#e74c3c"},
                    {'range': [y_mean - 50, y_mean + 50], 'color': "#f1c40f"},
                    {'range': [y_mean + 50, y_mean + 100], 'color': "#2ecc71"}
                ],
                'bgcolor': "#ffffff",
                'bordercolor': "#2c3e50"
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Graphique linéaire de l'historique des prédictions
    if not st.session_state.history.empty:
        fig_history = px.line(
            st.session_state.history,
            x='Timestamp',
            y='Densité_Predite_kgm3',
            title="Historique des Prédictions",
            markers=True,
            color_discrete_sequence=["#2ecc71"]
        )
        st.plotly_chart(fig_history, use_container_width=True)

    # Affichage du tableau de l'historique des prédictions
    st.markdown("<h3>Historique des Prédictions</h3>", unsafe_allow_html=True)
    st.dataframe(st.session_state.history, use_container_width=True)

   

    # Téléchargement de l'historique en PDF
    st.markdown("<h3>Télécharger l'historique</h3>", unsafe_allow_html=True)
    if not st.session_state.history.empty:
        def generate_pdf():
            try:
                # Vérifier les données pour NaN ou valeurs invalides
                if st.session_state.history.isna().any().any():
                    st.markdown("<p class='error'>❌ Données historiques invalides (NaN détecté).</p>", unsafe_allow_html=True)
                    st.markdown("<script>showToast('Données historiques invalides', 'error');</script>", unsafe_allow_html=True)
                    return None
                
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
                elements = []
                
                # Limiter à 100 lignes pour éviter les problèmes avec les grands ensembles de données
                data = [[str(cell) for cell in row] for row in [st.session_state.history.columns.tolist()] + st.session_state.history.values.tolist()[:100]]
                
                # Définir des largeurs de colonnes proportionnelles
                col_widths = [100, 80, 80, 80, 80, 80]
                table = Table(data, colWidths=col_widths, splitByRow=True)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('WORDWRAP', (0, 0), (-1, -1), True),
                ]))
                elements.append(table)
                
                # Génération du PDF
                doc.build(elements)
                buffer.seek(0)
                
                # Sauvegarde locale pour débogage
                with open("test_historique_predictions.pdf", "wb") as f:
                    f.write(buffer.getvalue())
                
                return buffer
            except Exception as e:
                st.markdown(f"<p class='error'>❌ Erreur lors de la génération du PDF : {e}</p>", unsafe_allow_html=True)
                st.markdown("<script>showToast('Erreur lors de la génération du PDF', 'error');</script>", unsafe_allow_html=True)
                return None

        pdf_buffer = generate_pdf()
        if pdf_buffer:
            st.download_button(
                label="Télécharger l'historique (PDF)",
                data=pdf_buffer,
                file_name="historique_predictions.pdf",  # Nom de fichier sans espaces ni parenthèses
                mime="application/pdf",
                key="download_pdf_button"
            )
    else:
        st.markdown("<p class='error'>❌ Aucun historique disponible pour le téléchargement.</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)