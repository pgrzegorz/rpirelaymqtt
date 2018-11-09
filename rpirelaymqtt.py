#!/usr/bin/env python 

import paho.mqtt.client as mqtt
import json
import logging
import os
import signal
import sys
import RPi.GPIO as GPIO

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
        self.maxlen = 0
        with open(filename, "r") as read_file:
            self.config = json.load(read_file)
        GPIO.setmode(GPIO.BCM)
        for name in self.config:
            GPIO.setup(int(self.config[name]["pin"]), GPIO.OUT)
            if len(name) > self.maxlen:
                self.maxlen = len(name)
        self.act()

    def set_logger(self, logger):
        self.logger = logger

    
    def process(self, node, state):
        """
        Setup state for one node and dependencies. Break if circular/doubled dependencies.
        """
        def visit(todo,path):
            p =[]
            p = p + path
            for i in todo:
                if i:
                    if i in p:
                        if self.logger:
                            self.logger.warning("Circular or doubled dependency for %s, something may not work as expected"%i)    
                        return
                    p.append(i)
                    self.config[i]["state"]=state
                    visit(self.config[i]["demands"],p)
        visit([node],path=[])


    def get_name_from_mqtt(self, mqtt_topic):
        for name in self.config:
            if self.config[name]["mqtt_topic"]==mqtt_topic:
                return(name)
   
    def act(self):
        """
        Calculate states for all relays and set I/O states for specified pins.
        """
        for name in self.config:
            if self.config[name]["state"]:
                self.process(name,1)
        if self.logger:
            for name in self.config:
                state = int(self.config[name]["state"]) and True or False
                self.logger.info("[ %s ] state %d for pin %02d" % (name.ljust(self.maxlen),state,int(self.config[name]["pin"])))
                GPIO.output(int(self.config[name]["pin"]), state)


def on_connect(client, userdata, flags, rc):
    if rc==0:
        client._easy_log(mqtt.MQTT_LOG_INFO,  "Connected with result code: %s"%str(rc))
    else:
        client._easy_log(mqtt.MQTT_LOG_ERROR, "Connection error code: %s"%str(rc)) 
    client.subscribe(topic="#",qos=2)

def on_message(client, userdata, msg):
    name = userdata.get_name_from_mqtt(msg.topic)
    userdata.process(name, int(msg.payload))
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

