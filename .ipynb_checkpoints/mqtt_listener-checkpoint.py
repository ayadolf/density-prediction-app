import paho.mqtt.client as mqtt
import json
import requests

API_URL = "http://127.0.0.1:5000/predict"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
PREDICTION_TOPIC = "emaphos/predictions"

def on_connect(client, userdata, flags, rc):
    print(f"Connecté au broker MQTT avec code {rc}")
    client.subscribe("emaphos/sensors")

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode('utf-8'))
    print(f"Données reçues via MQTT : {data}")

    try:
        # Appel API pour prédiction
        response = requests.post(API_URL, json=data)
        result = response.json()
        print(f"Prédiction reçue de l'API : {result}")

        # Publier la prédiction sur le topic MQTT pour APC Simulator
        prediction_payload = json.dumps(result)
        client.publish(PREDICTION_TOPIC, prediction_payload)
        print(f"Prédiction publiée sur MQTT topic '{PREDICTION_TOPIC}'")

    except Exception as e:
        print(f"Erreur lors de l'appel API : {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
