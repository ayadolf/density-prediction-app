import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import json
import pandas as pd
from threading import Thread
import tkinter.ttk as ttk
from tkinter import messagebox
from datetime import datetime
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import io
import numpy as np
import os

# Données
data_store = []
last_sensor_data = {}  # Pour stocker les dernières données des capteurs

def on_connect(client, userdata, flags, rc):
    print(f"Connecté avec le code : {rc}")
    client.subscribe("emaphos/sensors")
    client.subscribe("emaphos/predictions")

def on_message(client, userdata, msg):
    global last_sensor_data
    data = json.loads(msg.payload.decode('utf-8'))
    data['topic'] = msg.topic
    data['timestamp'] = pd.Timestamp.now()
    
    if data['topic'] == 'emaphos/sensors':
        last_sensor_data = data.copy()
        data_store.append(data)
        print(f"Données capteurs reçues à {data['timestamp']} : {data}")
    
    elif data['topic'] == 'emaphos/predictions':
        if 'Densité_Sortie' in data and not pd.isna(data['Densité_Sortie']):
            combined_data = last_sensor_data.copy()
            combined_data.update(data)
            data_store.append(combined_data)
            print(f"Prédiction valide reçue à {combined_data['timestamp']} : {combined_data}")
        else:
            print(f"Prédiction ignorée à {data['timestamp']} : valeurs nulles détectées")

# Connexion MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

# Interface Tkinter
root = tk.Tk()
root.title("Tableau de bord EMAPHOS")

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8, 6))
ax1.set_title("Données des Capteurs")
ax2.set_title("Prédictions de Densité")
ax1.set_ylabel("Valeurs")
ax2.set_ylabel("Densité Sortie")
ax1.grid(True)
ax2.grid(True)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Label pour afficher les dernières valeurs
label_frame = tk.Frame(root)
label_frame.pack(pady=10)
labels = {
    'Débit_Acide_m3h': tk.Label(label_frame, text="Débit_Acide_m3h: N/A"),
    'Débit_Vapeur_kgh': tk.Label(label_frame, text="Débit_Vapeur_kgh: N/A"),
    'Température_Évaporateur_C': tk.Label(label_frame, text="Température_Évaporateur_C: N/A"),
    'Vide_Bouilleur_torr': tk.Label(label_frame, text="Vide_Bouilleur_torr: N/A"),
    'Densité_Sortie': tk.Label(label_frame, text="Densité_Sortie: N/A")
}
for i, (key, label) in enumerate(labels.items()):
    label.grid(row=i, column=0, padx=5, pady=2)

def update_plot():
    df = pd.DataFrame(data_store[-100:])
    df_sensors = df[df['topic'] == 'emaphos/sensors']
    df_predictions = df[df['topic'] == 'emaphos/predictions']

    ax1.clear()
    ax2.clear()
    if not df_sensors.empty:
        for col in ['Débit_Acide_m3h', 'Débit_Vapeur_kgh', 'Température_Évaporateur_C', 'Vide_Bouilleur_torr']:
            if col in df_sensors.columns and not df_sensors[col].isna().all():
                ax1.plot(df_sensors['timestamp'], df_sensors[col], label=col)
        ax1.legend()
    if not df_predictions.empty:
        ax2.plot(df_predictions['timestamp'], df_predictions['Densité_Sortie'], label='Densité Sortie')
        ax2.legend()

    latest_prediction = df_predictions.iloc[-1].to_dict() if not df_predictions.empty else {}
    for key, label in labels.items():
        value = latest_prediction.get(key, 'N/A')
        label.config(text=f"{key}: {value if value != 'N/A' else 'N/A'}")

    ax1.set_title("Données des Capteurs")
    ax2.set_title("Prédictions de Densité")
    ax1.set_ylabel("Valeurs")
    ax2.set_ylabel("Densité Sortie")
    ax1.grid(True)
    ax2.grid(True)
    canvas.draw()
    root.after(1000, update_plot)

# Fonction pour ouvrir la fenêtre d'export
def open_export_window():
    export_window = tk.Toplevel(root)
    export_window.title("Exporter l'historique")
    export_window.geometry("300x200")

    tk.Label(export_window, text="Choisir la période :").pack(pady=5)
    tk.Label(export_window, text="Date de début (YYYY-MM-DD HH:MM:SS) :").pack()
    start_date_entry = tk.Entry(export_window)
    start_date_entry.pack()
    tk.Label(export_window, text="Date de fin (YYYY-MM-DD HH:MM:SS) :").pack()
    end_date_entry = tk.Entry(export_window)
    end_date_entry.pack()

    def export_data():
        df = pd.DataFrame(data_store)
        if df.empty:
            messagebox.showerror("Erreur", "Aucune donnée à exporter.")
            return

        start_date_str = start_date_entry.get().strip()
        end_date_str = end_date_entry.get().strip()

        try:
            start_date = pd.Timestamp(start_date_str)
            end_date = pd.Timestamp(end_date_str)
            if start_date > end_date:
                messagebox.showerror("Erreur", "La date de début doit être antérieure à la date de fin.")
                return
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide. Utilisez YYYY-MM-DD HH:MM:SS.")
            return

        # Filtrer uniquement les prédictions
        df = df[df['topic'] == 'emaphos/predictions']
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

        if df.empty:
            messagebox.showerror("Erreur", "Aucune prédiction dans la période sélectionnée.")
            return

        # Supprimer la colonne 'topic'
        df = df.drop(columns=['topic'])

        # Formater le timestamp au format 'YYYY-MM-DD HH:MM:SS'
        df['timestamp'] = df['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))

        # Créer le nom du fichier avec date_debut_date_fin
        file_prefix = f"{start_date_str.replace(':', '-')}_{end_date_str.replace(':', '-')}"
        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        excel_path = os.path.join(export_dir, f"historique_predictions_{file_prefix}.xlsx")
        pdf_path = os.path.join(export_dir, f"historique_predictions_{file_prefix}.pdf")

        # Export Excel
        try:
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            with open(excel_path, "wb") as f:
                f.write(excel_buffer.getvalue())
            messagebox.showinfo("Succès", f"Export Excel terminé : {excel_path}")
            if messagebox.askyesno("Ouvrir dossier", "Voulez-vous ouvrir le dossier contenant les fichiers ?"):
                os.startfile(export_dir)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'export Excel : {e}")

        # Export PDF
        try:
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
            elements = []
            table_data = [df.columns.tolist()] + df.values.tolist()[:100]
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
            doc.build(elements)
            pdf_buffer.seek(0)
            with open(pdf_path, "wb") as f:
                f.write(pdf_buffer.getvalue())
            messagebox.showinfo("Succès", f"Export PDF terminé : {pdf_path}")
            if messagebox.askyesno("Ouvrir dossier", "Voulez-vous ouvrir le dossier contenant les fichiers ?"):
                os.startfile(export_dir)
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'export PDF : {e}")

    tk.Button(export_window, text="Exporter", command=export_data).pack(pady=10)

# Bouton pour ouvrir la fenêtre d'export
export_button = tk.Button(root, text="Exporter l'historique", command=open_export_window)
export_button.pack(pady=10)

root.after(1000, update_plot)
root.mainloop()

# Arrêt propre du client MQTT
def on_closing():
    client.loop_stop()
    client.disconnect()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)