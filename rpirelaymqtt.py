#!/usr/bin/env python 

import paho.mqtt.client as mqtt
import json
import logging
import os
import signal
import sys


HOSTNAME = "127.0.0.1"
DEFAULT_IDENTITY = "heater"
USERNAME = ""
PASSWORD = ""
CONFIG_FILE = ""
LOG_FILE = ""

class RelayBoard():
    def __init__(self,filename):
        self.filename = filename
        self.config = {}
        self.logger = None
        with open(filename, "r") as read_file:
            self.config = json.load(read_file)
        self.act()

    def set_logger(self, logger):
        self.logger = logger

    
    def process_dependencies(self):
        circular = False
        for name in self.config:
            if name in self.config[name]["depends"]:
                circular = True
            for dep in self.config[name]["depends"]:
                if name in self.config[dep]["depends"]:
                    circular = True
        if circular:
            return False
        newstates = {}
        for name in self.config:
            for dep in self.config[name]["depends"]:
                if dep:
                    if not newstates.get(name):
                        newstates.update({name:0})
                    newstates[name]+=int(self.config[dep]["state"])
                

        for n in newstates:
            if n:
                self.config[n]["state"]=newstates[n]
        return True

    def setup_state_name(self, name, state):
        self.config[name]["state"] = state

    def setup_state_mqtt(self, mqtt_topic, state):
        for name in self.config:
            if self.config[name]["mqtt_topic"]==mqtt_topic:
                self.config[name]["state"]=state
    
    def act(self):
        if self.process_dependencies():
            if self.logger:
                for name in self.config:
                    state = int(self.config[name]["state"]) and 1 or 0
                    self.logger.info("%s realy is changing state to %d for pin %s (real state: %s)" % (name,state,self.config[name]["pin"],self.config[name]["state"]))
        else:
            if self.logger:
                self.logger.warning("Circular dependency")


def on_connect(client, userdata, flags, rc):
    if rc==0:
        client._easy_log(mqtt.MQTT_LOG_INFO,  "Connected with result code: %s"%str(rc))
    else:
        client._easy_log(mqtt.MQTT_LOG_ERROR, "Connection error code: %s"%str(rc)) 
    client.subscribe(topic="#",qos=2)

def on_message(client, userdata, msg):
    userdata.setup_state_mqtt(msg.topic, msg.payload)
    userdata.act()
    

if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    if "RELAY_CONFIG" in os.environ:
        CONFIG_FILE=os.environ["RELAY_CONFIG"]
    r = RelayBoard(CONFIG_FILE)

    r.set_logger(logger)

    client = mqtt.Client(DEFAULT_IDENTITY,clean_session=False, userdata=r)
    client.enable_logger(logger)
    client.on_connect = on_connect
    client.on_message = on_message
    def signal_handler(sig, frame):
        client.loop_stop()
        client.disconnect()

    if not USERNAME and not PASSWORD:
        if "MQTT_USERNAME" in os.environ and "MQTT_PASSWORD" in os.environ:
            USERNAME = os.environ["MQTT_USERNAME"]
            PASSWORD = os.environ["MQTT_PASSWORD"]
    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)
    if "MQTT_HOST" in os.environ:
        HOSTNAME=os.environ["MQTT_HOST"]
    client.connect(HOSTNAME)
    signal.signal(signal.SIGINT, signal_handler) 
    client.loop_forever()

