"""
Local MQTT Test Client

Publishes random data to device topics and periodically requests data
for a given date and device. Subscribes to response topics and prints
results to stdout for local testing.
"""

import os
import json
import time
import random
import argparse
from datetime import datetime, date
import logging
import paho.mqtt.client as mqtt

import config

# Logging setup
logging.basicConfig(
    level=getattr(logging, os.getenv('TEST_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_client')


class TestMQTTClient:
    def __init__(self, broker_host, broker_port, target_client_id, client_id,
                 temp_device_id, power_device_id, fingerprint_device_id,
                 request_date):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.target_client_id = target_client_id  # The server/client we are testing
        self.client_id = client_id                # This test client's ID
        self.temp_device_id = temp_device_id
        self.power_device_id = power_device_id
        self.fingerprint_device_id = fingerprint_device_id
        self.request_date = request_date

        self.client = mqtt.Client(client_id=self.client_id)
        if config.MQTT_USERNAME and config.MQTT_PASSWORD:
            self.client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info('Test client connected to broker')
            # Subscribe to response topics for the target server client
            topics = [
                f"{config.TEMP_DATA_TOPIC_PREFIX}/{self.target_client_id}",
                f"{config.POWER_DATA_TOPIC_PREFIX}/{self.target_client_id}",
                f"{config.FINGERPRINT_DATA_TOPIC_PREFIX}/{self.target_client_id}",
            ]
            for t in topics:
                client.subscribe(t, qos=1)
                logger.info(f"Subscribed to response topic: {t}")
        else:
            logger.error(f"Connect failed with rc={rc}")

    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected with rc={rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            logger.info(f"Response on {msg.topic}: {payload}")
        except Exception as e:
            logger.error(f"Error decoding response: {e}")

    def connect(self):
        self.client.connect(self.broker_host, self.broker_port, keepalive=config.MQTT_KEEPALIVE)
        self.client.loop_start()
        logger.info(f"Connecting to {self.broker_host}:{self.broker_port}")

    def shutdown(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Test client disconnected")

    # --- Publishers ---
    def publish_temperature(self):
        payload = {
            'device_id': self.temp_device_id,
            'temperature': round(random.uniform(18.0, 30.0), 2),
            'humidity': round(random.uniform(30.0, 70.0), 2),
            'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        }
        self.client.publish(config.TEMPERATURE_DEVICE_TOPIC, json.dumps(payload), qos=1)
        logger.debug(f"Published temperature: {payload}")

    def publish_power(self):
        ebstatus = random.choice(['ON', 'OFF'])
        dgstatus = random.choice(['ON', 'OFF'])
        payload = {
            'device_id': self.power_device_id,
            'ebstatus': ebstatus,
            'dgstatus': dgstatus,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        }
        self.client.publish(config.POWER_DEVICE_TOPIC, json.dumps(payload), qos=1)
        logger.debug(f"Published power: {payload}")

    def publish_fingerprint(self):
        user_id = f"user_{random.randint(100, 999)}"
        auth_status = random.choice(['PASS', 'FAIL'])
        payload = {
            'device_id': self.fingerprint_device_id,
            'user_id': user_id,
            'auth_status': auth_status,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        }
        self.client.publish(config.FINGERPRINT_DEVICE_TOPIC, json.dumps(payload), qos=1)
        logger.debug(f"Published fingerprint: {payload}")

    # --- Requesters ---
    def request_temperature(self):
        topic = f"{config.TEMP_REQUEST_TOPIC_PREFIX}/{self.target_client_id}"
        payload = {
            'device_id': self.temp_device_id,
            'date': self.request_date
        }
        self.client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"Requested temperature data on {topic}: {payload}")

    def request_power(self):
        topic = f"{config.POWER_REQUEST_TOPIC_PREFIX}/{self.target_client_id}"
        payload = {
            'device_id': self.power_device_id,
            'date': self.request_date
        }
        self.client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"Requested power data on {topic}: {payload}")

    def request_fingerprint(self):
        topic = f"{config.FINGERPRINT_REQUEST_TOPIC_PREFIX}/{self.target_client_id}"
        payload = {
            'device_id': self.fingerprint_device_id,
            'date': self.request_date
        }
        self.client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"Requested fingerprint data on {topic}: {payload}")

    def run(self):
        try:
            self.connect()
            temp_interval = int(os.getenv('TEMP_INTERVAL', '5'))
            power_interval = int(os.getenv('POWER_INTERVAL', '15'))
            fingerprint_interval = int(os.getenv('FINGERPRINT_INTERVAL', '20'))
            request_interval = int(os.getenv('REQUEST_INTERVAL', '300'))

            last_temp = last_power = last_fp = last_req = 0

            while True:
                now = time.time()
                if now - last_temp >= temp_interval:
                    self.publish_temperature()
                    last_temp = now
                if now - last_power >= power_interval:
                    self.publish_power()
                    last_power = now
                if now - last_fp >= fingerprint_interval:
                    self.publish_fingerprint()
                    last_fp = now
                if now - last_req >= request_interval:
                    # Request all three types for the same date
                    self.request_temperature()
                    self.request_power()
                    self.request_fingerprint()
                    last_req = now
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.shutdown()


def parse_args():
    parser = argparse.ArgumentParser(description='Local MQTT Test Client')
    parser.add_argument('--broker-host', default=os.getenv('MQTT_BROKER_HOST', config.MQTT_BROKER_HOST), help='MQTT broker host')
    parser.add_argument('--broker-port', type=int, default=int(os.getenv('MQTT_BROKER_PORT', config.MQTT_BROKER_PORT)), help='MQTT broker port')
    parser.add_argument('--target-client-id', default=os.getenv('TARGET_CLIENT_ID', config.MQTT_CLIENT_ID), help='Target server client ID to request from')
    parser.add_argument('--client-id', default=os.getenv('TEST_CLIENT_ID', 'mqtt_tester_1'), help='This test client ID')
    parser.add_argument('--temp-device-id', default=os.getenv('TEMP_DEVICE_ID', 'temp_sensor_01'))
    parser.add_argument('--power-device-id', default=os.getenv('POWER_DEVICE_ID', 'power_switch_01'))
    parser.add_argument('--fingerprint-device-id', default=os.getenv('FP_DEVICE_ID', 'fingerprint_01'))
    parser.add_argument('--date', default=os.getenv('REQUEST_DATE', date.today().strftime('%Y-%m-%d')), help='Date (YYYY-MM-DD) to request')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    tester = TestMQTTClient(
        broker_host=args.broker_host,
        broker_port=args.broker_port,
        target_client_id=args.target_client_id,
        client_id=args.client_id,
        temp_device_id=args.temp_device_id,
        power_device_id=args.power_device_id,
        fingerprint_device_id=args.fingerprint_device_id,
        request_date=args.date,
    )
    tester.run()
