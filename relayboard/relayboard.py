import json
import logging
import RPi.GPIO as GPIO

class RelayBoard():
    def __init__(self, filename):
        self.filename = filename
        self.config = {}
        self.logger = None
        self.maxlen = 0
        with open(filename, "r") as read_file:
            self.config = json.load(read_file)
        GPIO.setmode(GPIO.BCM)
        for name in self.config:
            GPIO.setup(int(self.config[name]["gpio"]), GPIO.OUT)
            if len(name) > self.maxlen:
                self.maxlen = len(name)
        self.act()

    def set_logger(self, logger):
        self.logger = logger

    def process(self, node, state):
        """
        Setup state for one node and dependencies. Break if circular/doubled dependencies.
        """
        def visit(todo, path):
            ret = True
            p = []
            p = p + path
            for i in todo:
                if i:
                    if i in p:
                        if self.logger:
                            self.logger.warning("Circular or doubled dependency for %s, " % i +
                                                "something may not work as expected")
                        return False
                    p.append(i)
                    self.config[i]["state"] = state
                    ret = visit(self.config[i]["depends"], p)
            return ret
        return visit([node], path=[])

    def get_name_from_mqtt(self, mqtt_topic):
        for name in self.config:
            if self.config[name]["mqtt_topic"] == mqtt_topic:
                return(name)

    def act(self):
        """
        Calculate states for all relays and set I/O states for specified pins.
        """
        for name in self.config:
            if self.config[name]["state"]:
                self.process(name, 1)
        for name in self.config:
            state = int(self.config[name]["state"]) and True or False
            state = not state
            GPIO.output(int(self.config[name]["gpio"]), state)
            if self.logger:
                self.logger.info("[ %s ] state %d for gpio %02d" %\
                    (name.ljust(self.maxlen), state, int(self.config[name]["gpio"])))
