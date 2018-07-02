'''
IRM General/Global project definitions
'''
# IRM Software-level sensor names
TEMP  = 'temp'
HUM   = 'hum'
PRES  = 'pres'
LIGHT = 'light'
AIR_Q = 'airQ'
PPM   = 'ppm'

# IRM List of available sensors
AVAILABLE_SENSORS = [TEMP, HUM, PRES, LIGHT, AIR_Q, PPM]

'''
IRM MQTT Client-related definitions
'''
# IRM MQTT Topics/Sub-topics
ROOT_TOPIC     = 'METEO'
SENSOR_TOPICS  = {TEMP : 'Temperature', HUM : 'Humidity', PRES : 'Pressure', 
				 LIGHT : 'Light', AIR_Q : 'AirQuality', PPM : 'PPM'}
SETTINGS_TOPIC = 'Settings'
SR_TOPIC       = 'SamplingRate'

MQTT_SINGLE_LEVEL = '+'
MQTT_MULTI_LEVEL  = '#'

# IRM MQTT-related clients' settings
IDENTIFIER_TOPIC_TYPE = int
MAX_CLIENTS = 256

# IRM Network-related settings
MQTT_BROKER = '127.0.0.1' # IRM MQTT broker will always be running on localhost (at least for this version)
MQTT_PORT   = 1883 # IRM MQTT borker port

'''
IRM Other METEO settings
'''
MIN_SAMPLING_RATE     = 1   * 60 # IRM 1 minute
MAX_SAMPLING_RATE     = 120 * 60 # IRM 2 hours
DEFAULT_SAMPLING_RATE = 15  * 60 # IRM 15 minutes

'''
IRM Errors list
'''
INVALID_SAMPLING_RATE = 'INVALID_SAMPLING_RATE'
INVALID_SENSOR_NAME   = 'INVALID_SENSOR_NAME'


ERRORS = {INVALID_SAMPLING_RATE : -1, INVALID_SENSOR_NAME : -2}
