# rpirelaymqtt
Simple python tool to drive relays connected to raspberry pi GPIO pins using mqtt.

It uses json config file to describe relays and mqtt topics related to them. 
Example config json in examples directory.

Example execution:
```
$ RELAY_CONFIG=example.json 
$ MQTT_USERNAME=<username> 
$ MQTT_PASSWORD=<password> 
$ MQTT_HOST=localhost 
$ rpirelaymqtt
```
