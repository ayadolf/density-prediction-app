import numpy as np
import paho.mqtt.client as mqtt
import json
import time

def on_connect(client, userdata, flags, rc):
    print(f"Connecté avec le code : {rc}")

# Connexion au broker Mosquitto local
client = mqtt.Client()
client.on_connect = on_connect
client.connect("localhost", 1883, 60)

# Plages réalistes basées sur vos données
np.random.seed(42)
while True:
    data = {
        'Débit_Acide_m3h': np.random.uniform(29.5, 30.5),
        'Débit_Vapeur_kgh': np.random.uniform(3500, 3600),
        'Température_Évaporateur_C': np.random.uniform(92.0, 92.5),
        'Vide_Bouilleur_torr': np.random.uniform(58.5, 59.5)
    }
    payload = json.dumps(data)
    client.publish("emaphos/sensors", payload)
    print(f"Données envoyées : {payload}")
    time.sleep(1)