from flask import Flask, request, jsonify
# Importation de Flask pour créer une application web, request pour gérer les requêtes HTTP, et jsonify pour retourner des réponses JSON
import joblib
import pandas as pd
# Initialisation de l'application Flask avec le nom du module courant
app = Flask(__name__)

model = joblib.load('modele_final.pkl')
print("✅ Modèle chargé avec succès.")
# Lecture de la moyenne enregistrée (y_mean) à partir du fichier 'y_mean.txt'
with open('y_mean.txt', 'r') as f:
    y_mean = float(f.read())
# Affichage de la valeur de y_mean pour confirmer son chargement
print(f"✅ Moyenne y_mean chargée : {y_mean}")

# Définition d'une route '/predict' qui accepte les requêtes POST pour effectuer des prédictions
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Récupération des données JSON envoyées dans la requête POST
        data = request.get_json()
        # Affichage des données reçues pour le suivi
        print(f"📥 Données reçues : {data}")
        # Conversion des données JSON en DataFrame pandas pour compatibilité avec le modèle
        input_data = pd.DataFrame([data])
        # Utilisation du modèle pour prédire et ajout de la moyenne y_mean à la prédiction
        prediction = model.predict(input_data) + y_mean
        # Affichage de la prédiction pour le suivi
        print(f"📤 Prédiction retournée : {prediction[0]}")
        # Retour de la prédiction sous forme de JSON avec la clé 'Densité_Sortie'
        return jsonify({'Densité_Sortie': prediction[0]})
    except Exception as e:
        # Gestion des erreurs : affichage de l'erreur pour le suivi
        print(f"❌ Erreur : {e}")
        # Retour d'une réponse JSON avec le message d'erreur et un code d'erreur HTTP 500
        return jsonify({'error': str(e)}), 500

# Vérification que le script est exécuté directement (et non importé comme module)
if __name__ == '__main__':
    # Affichage d'un message pour indiquer le démarrage du serveur Flask
    print("🚀 Lancement du serveur Flask sur http://127.0.0.1:5000 ...")
    # Démarrage du serveur Flask sur l'hôte '0.0.0.0' (accessible depuis l'extérieur) et le port 5000 avec le mode debug activé
    app.run(host='0.0.0.0', port=5000, debug=True)