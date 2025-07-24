# Importation de la bibliothèque paho.mqtt.client pour gérer les communications MQTT
import paho.mqtt.client as mqtt
import json
# Importation de la bibliothèque requests pour effectuer des requêtes HTTP vers l'API
import requests

# Définition de l'URL de l'API Flask pour les prédictions
API_URL = "http://127.0.0.1:5000/predict"

# Définition de l'adresse du broker MQTT (local)
MQTT_BROKER = "localhost"

# Définition du port du broker MQTT (port standard pour MQTT)
MQTT_PORT = 1883

# Définition du topic MQTT où les prédictions seront publiées
PREDICTION_TOPIC = "emaphos/predictions"

# Définition de la fonction de rappel exécutée lors de la connexion au broker MQTT
def on_connect(client, userdata, flags, rc):
    # Affichage du code de retour (rc) pour indiquer le statut de la connexion (0 = succès)
    print(f"Connecté au broker MQTT avec code {rc}")
    # Souscription au topic "emaphos/sensors" pour recevoir les données des capteurs
    client.subscribe("emaphos/sensors")

# Définition de la fonction de rappel exécutée lors de la réception d'un message MQTT
def on_message(client, userdata, msg):
    # Décodage et conversion du message MQTT reçu (payload) en dictionnaire JSON
    data = json.loads(msg.payload.decode('utf-8'))
    # Affichage des données reçues pour le suivi
    print(f"Données reçues via MQTT : {data}")

    try:
        # Envoi des données reçues à l'API Flask via une requête POST
        response = requests.post(API_URL, json=data)
        # Extraction de la réponse JSON de l'API
        result = response.json()
        # Affichage de la prédiction reçue pour le suivi
        print(f"Prédiction reçue de l'API : {result}")

        # Conversion de la prédiction en chaîne JSON pour publication
        prediction_payload = json.dumps(result)
        # Publication de la prédiction sur le topic MQTT "emaphos/predictions"
        client.publish(PREDICTION_TOPIC, prediction_payload)
        # Affichage pour confirmer la publication
        print(f"Prédiction publiée sur MQTT topic '{PREDICTION_TOPIC}'")

    except Exception as e:
        # Gestion des erreurs : affichage de l'erreur en cas de problème avec l'appel API
        print(f"Erreur lors de l'appel API : {e}")

# Création d'une instance du client MQTT
client = mqtt.Client()

# Assignation des fonctions de rappel pour la connexion et la réception des messages
client.on_connect = on_connect
client.on_message = on_message

# Connexion au broker MQTT avec l'adresse, le port et un timeout de 60 secondes
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Lancement de la boucle infinie pour maintenir la connexion MQTT et traiter les messages
client.loop_forever()