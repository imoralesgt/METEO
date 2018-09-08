'''
IRM General/Global project definitions
'''



'''
============================================================
Modify these values to setup your METEO client
Don't modify any parameter if you don't know what it means
'''
STATION_NUMBER = 0 # METEO Station Number. If this is the main station, default value is 0

#Network-related settings
MQTT_BROKER = '127.0.0.1' #MQTT broker address. If this is the main station, default value is 'localhost' or '127.0.0.1'
MQTT_PORT   = 1883 # IRM MQTT borker port. Default value is 1883


#Sensors sampling rate limits
MIN_SAMPLING_RATE     = 1   * 60 # 1 minute
MAX_SAMPLING_RATE     = 120 * 60 # 2 hours
DEFAULT_SAMPLING_RATE = MIN_SAMPLING_RATE * 5 # 5 minutes


'''
Don't modify anything else below this line
============================================================
'''




# IRM Software-level sensor names
TEMP  = 'temp'
HUM   = 'hum'
PRES  = 'pres'
LIGHT = 'light'
AIR_Q = 'airQ'
PPM   = 'ppm'

SENSOR_BME680 = 'BME680'
SENSOR_BH1750 = 'BH1750'

# IRM List of available sensors
AVAILABLE_SENSORS = [TEMP, HUM, PRES, LIGHT, AIR_Q, PPM]

# IRM Mapping measured variables to corresponding hardware sensors
SENSORS_VAR_MAP   = {TEMP : SENSOR_BME680, HUM : SENSOR_BME680,
					PRES : SENSOR_BME680, LIGHT : SENSOR_BH1750,
					AIR_Q : SENSOR_BME680, PPM : SENSOR_BME680}

'''
IRM MQTT Client-related definitions
'''
# IRM MQTT Topics/Sub-topics
ROOT_TOPIC       = 'METEO'
SENSOR_TOPICS    = {TEMP : 'Temperature', HUM : 'Humidity', PRES : 'Pressure', 
					LIGHT : 'Light', AIR_Q : 'AirQuality', PPM : 'PPM'}
SENSOR_TOPICS_R  = {'Temperature' : TEMP, 'Humidity' : HUM, 'Pressure' : PRES,
					'Light' : LIGHT, 'AirQuality' : AIR_Q, 'PPM' : PPM}
SENSOR_TOPICS_LST = (
					SENSOR_TOPICS[TEMP],
					SENSOR_TOPICS[HUM],
					SENSOR_TOPICS[PRES],
					SENSOR_TOPICS[LIGHT],
					SENSOR_TOPICS[AIR_Q]
					)

DATA_TOPIC       = 'Data'
SETTINGS_TOPIC   = 'Settings'
SR_TOPIC         = 'SamplingRate'
KEEP_ALIVE_TOPIC = 'Alive'

MQTT_SINGLE_LEVEL = '+'
MQTT_MULTI_LEVEL  = '#'

# IRM MQTT-related clients' settings
IDENTIFIER_TOPIC_TYPE = int
MAX_CLIENTS = 256




# IRM other MQTT-related defines
KEEP_ALIVE_BEACON_PERIOD = 60 # IRM Send beacon every minute
MQTT_RX_QUEUE_SUPERVISE_PERIOD = 0.1 # IRM Check input queue every 100 ms

'''
IRM Other METEO settings
'''


'''
IRM Errors list
'''
INVALID_SAMPLING_RATE  = 'INVALID_SAMPLING_RATE'
INVALID_SENSOR_NAME    = 'INVALID_SENSOR_NAME'
INVALID_STATION_NUMBER = 'INVALID_STATION_NUMBER'
INVALID_LIGHT_VALUE    = 'INVALID_LIGHT_VALUE'
INVALID_TEMP_VALUE     = 'INVALID_TEMP_VALUE'
INVALID_HUM_VALUE      = 'INVALID_HUM_VALUE'
INVALID_PRES_VALUE     = 'INVALID_PRES_VALUE'
INVALID_AIR_Q_VALUE    = 'INVALID_AIR_Q_VALUE'
INVALID_PPM_VALUE      = 'INVALID_PPM_VALUE'

ERRORS = {
		 INVALID_SAMPLING_RATE  : -1, INVALID_SENSOR_NAME : -2,
		 INVALID_STATION_NUMBER : -3, INVALID_LIGHT_VALUE : -4,
		 INVALID_TEMP_VALUE     : -5, INVALID_HUM_VALUE   : -6,
		 INVALID_PRES_VALUE     : -7, INVALID_AIR_Q_VALUE : -8, 
		 INVALID_PPM_VALUE      : -9
		 }

'''
IRM Data storage settings
'''
METEO_DATA_FOLDER   = 'data'
METEO_FILENAME_ROOT = 'METEO_'
METEO_FILE_FORMAT   = '.csv'
CSV_HEADER          = 'Date, Time, METEO_ID, Temperature, Humidity, Pressure, Luminosity, Air Quality,'
DB_FILE_NAME		= 'meteo.db'
DB_TABLE_NAME	    = 'meteo'
DB_TABLE_FIELDS     = ('Date', 'Time', 'Node', SENSOR_TOPICS[TEMP], SENSOR_TOPICS[HUM],
						 SENSOR_TOPICS[PRES], SENSOR_TOPICS[LIGHT], SENSOR_TOPICS[AIR_Q] )
