
'''
=======================================================
IRM BME680 Defines
=======================================================
'''
GAS_HEATER_TEMPERATURE = 320 #IRM BME680's gas heater operating temperature
GAS_HEATER_DURATION    = 150 #IRM BME680's gas heater startup duration (microseconds)
GAS_HEATER_PROFILE     = 0   #IRM BME680's chosen gas heating profile


GAS_BURN_IN_TIME = 300 #IRM Burn-in time (seconds) before gas sensor is operative (default: 5 minutes)
GAS_BASELINE_MEASUREMENTS = 50 #IRM How many gas sensor measurements should be used for average GAS_BASELINE_MEASUREMENT

HUM_BASELINE = 40 #IRM Optimal indoor relative humidity percentage (default: 40%)


IAQ_MAX_GAS = 250000 # IRM Max gas resistance measurement
IAQ_MIN_GAS = 50    # IRM Min gas resistance measurement
IAQ_MIN_HUM = 0     # IRM Min relative humidity
IAQ_MAX_HUM = 100   # IRM Max relative humidity

GAS_OPTIMAL = IAQ_MAX_GAS

IAQ_HUM_CONTRIBUTION = 0.25 # IRM Humidity contribution to Index of Air Quality
IAQ_GAS_CONTRIBUTION = 1 - IAQ_HUM_CONTRIBUTION # IRM Gas contribution to Index of Air Quality

'''
=======================================================
IRM BH1750 Defines
=======================================================
'''
DEFAULT_LIGHT_SENSITIVITY = 69
DEFAULT_LIGHT_I2C_ADDRESS = 0x23
