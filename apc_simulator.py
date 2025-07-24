import time
import paho.mqtt.client as mqtt
import json

# Définition du topic MQTT où les prédictions sont reçues
MQTT_TOPIC = "emaphos/predictions"

# Définition de l'adresse du broker MQTT (local)
MQTT_BROKER = "localhost"
# Définition du port du broker MQTT (port standard pour MQTT)
MQTT_PORT = 1883

# Variable globale pour stocker la dernière prédiction reçue
last_prediction = None

# Définition de la fonction pour ajuster les paramètres du procédé en fonction de la prédiction
def ajuster_parametres(prediction):
    # Affichage de la prédiction pour indiquer que l'ajustement des paramètres est en cours
    print(f">>> Ajustement des paramètres du procédé avec la prédiction : {prediction}")

# Définition de la fonction de rappel exécutée lors de la connexion au broker MQTT
def on_connect(client, userdata, flags, rc):
    # Affichage du code de retour (rc) pour indiquer le statut de la connexion (0 = succès)
    print(f"[APC Simulator] Connecté au broker MQTT avec code {rc}")
    # Souscription au topic "emaphos/predictions" pour recevoir les prédictions
    client.subscribe(MQTT_TOPIC)

# Définition de la fonction de rappel exécutée lors de la réception d'un message MQTT
def on_message(client, userdata, msg):
    # Accès à la variable globale last_prediction pour la mettre à jour
    global last_prediction
    try:
        # Décodage du message MQTT reçu (payload) en chaîne UTF-8
        payload = msg.payload.decode('utf-8')
        # Conversion de la chaîne en dictionnaire JSON
        data = json.loads(payload)
        # Vérification si la clé 'Densité_Sortie' est présente dans les données
        if 'Densité_Sortie' in data:
            # Mise à jour de la variable globale avec la valeur de la prédiction
            last_prediction = data['Densité_Sortie']
            # Affichage de la prédiction reçue pour le suivi
            print(f"[APC Simulator] Prédiction reçue via MQTT : {last_prediction}")
    except Exception as e:
        # Gestion des erreurs : affichage de l'erreur en cas de problème avec le message
        print(f"[APC Simulator] Erreur traitement message MQTT : {e}")

# Définition de la fonction principale du programme
def main():
    # Accès à la variable globale last_prediction
    global last_prediction

    # Création d'une instance du client MQTT
    client = mqtt.Client()
    # Assignation des fonctions de rappel pour la connexion et la réception des messages
    client.on_connect = on_connect
    client.on_message = on_message

    # Connexion au broker MQTT avec l'adresse, le port et un timeout de 60 secondes
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Lancement de la boucle MQTT en arrière-plan pour traiter les messages de manière asynchrone
    client.loop_start()

    # Affichage pour indiquer le démarrage de la simulation
    print("[APC Simulator] Démarrage de la simulation d'ajustement...")

    # Boucle infinie pour vérifier périodiquement la dernière prédiction
    while True:
        # Vérification si une prédiction a été reçue
        if last_prediction is not None:
            # Appel de la fonction pour ajuster les paramètres avec la dernière prédiction
            ajuster_parametres(last_prediction)
        else:
            # Affichage d'un message si aucune prédiction n'a encore été reçue
            print("[APC Simulator] En attente de la première prédiction...")
        # Pause de 5 secondes avant la prochaine vérification
        time.sleep(5)

# Vérification que le script est exécuté directement (et non importé comme module)
if __name__ == "__main__":
    # Appel de la fonction principale pour démarrer le programme
    main()