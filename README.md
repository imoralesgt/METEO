# METEO
## TFM MSEEI Universidad de Malaga - METEO

===========================================================


# ToDo List
## Meteo
- [ ] Connect to MQTT Broker in object constructor
	* [ ] Subscribe to every single 'settings' topic
	* [ ] \(Optional) _Show performance and broker info by subscribing to special $SYS topics (https://www.hivemq.com/blog/mqtt-essentials-part-5-mqtt-topics-best-practices)_
- [ ] Set sampling rates by reading this value from a specific MQTT Topic (which we must be suscribed to)
- [ ] Sample each sensor using separate threads
	* [x] Create a generic sampling method (one-shot), which receives the sensor name as parameter
		- [x] ```sampleSensor (sensorName)```
		- [x] Front-end interface variables (i.e. Air Quality, instead of Humidity+Gas_Resistance)
	- [ ] Create a thread/method to periodically launch the one-shot sampling method
	* [ ] Generate as many threads running this method as required
	* [ ] Kill sampling threads during object destruction
	* [X] Implement a mutual-exclusion mechanism to avoid access violations
- [ ] Send sensors' data via MQTT using topics to distribute data into different channels
- [ ] Each "METEO" station MUST have a vaild (integer type) identifier, starting from 0
- [ ] Topics should follow the following template:
	* [ ] ```METEO/<stationNumber>/<sensor>```
	* [ ] Valid ```<stationNumber>``` (identifiers) are integers from 0 to N-1
	* [ ] Valid ```<sensor>``` values are:
		- [ ] Temperature (Environmental temperature) [temp]
		- [ ] Humidity (Relative humidity) [hum]
		- [ ] Pressure (Local atmospheric pressure) [pres]
		- [ ] Light (Incident light measurement) [light]
		- [ ] AirQuality (Air quality as pollution measurement) [airQ]
		- [ ] PPM (Raw particle count) [ppm]
- [ ] A special topic may be used to set/get the sampling period dymanically
	* [ ] ```METEO/Settings/SamplingRate/<sensor>```
	* [ ] ```<sensor>``` field (sub-topic) is the same as described before
	* [x] Sampling rate value must be validated to remain between a valid range
		- [x] Min sampling rate 1 minute
		- [x] Max sampling rate 120 minutes
		- [x] If a sampling rate (SR) out of these limits is set, a default value will be chosen if a prior valid SR wasn't set yet; otherwise, the last valid SR will remain active
		
## BME680_METEO
- [ ] Compute Air Quality (%) using Humidity and Gas measurements
- [ ] Compute PPM using Gas Baseline and Gas measurements
