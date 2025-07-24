from flask import Flask, request, jsonify
import joblib
import pandas as pd

# Initialisation de l'application Flask
app = Flask(__name__)

# Chargement du modèle
model = joblib.load('modele_final.pkl')
print("✅ Modèle chargé avec succès.")

# Lecture de la moyenne enregistrée (y_mean)
with open('y_mean.txt', 'r') as f:
    y_mean = float(f.read())
print(f"✅ Moyenne y_mean chargée : {y_mean}")

# Définition de la route de prédiction
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        print(f"📥 Données reçues : {data}")
        input_data = pd.DataFrame([data])
        prediction = model.predict(input_data) + y_mean
        print(f"📤 Prédiction retournée : {prediction[0]}")
        return jsonify({'Densité_Sortie': prediction[0]})
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return jsonify({'error': str(e)}), 500

# Démarrage du serveur Flask
if __name__ == '__main__':
    print("🚀 Lancement du serveur Flask sur http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)
