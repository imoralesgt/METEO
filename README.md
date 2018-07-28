# METEO
## TFM MSEEI Universidad de Malaga
## Iván René Morales Argueta - 2018

===========================================================


# ToDo List
## Meteo
- [x] Connect to MQTT Broker in object constructor
	* [x] Subscribe to each ```Settings``` sub-topic ```Settings/#```
	* [ ] \(Optional) _Show performance and broker info by subscribing to special $SYS topics (https://www.hivemq.com/blog/mqtt-essentials-part-5-mqtt-topics-best-practices)_
- [x] Sample each sensor using separate threads
	* [x] Create a generic sampling method (one-shot), which receives the sensor name as parameter
		- [x] ```sampleSensor (sensorName)```
		- [x] Front-end interface variables (i.e. Air Quality, instead of Humidity+Gas_Resistance)
	- [x] Create a thread/method to periodically launch the one-shot sampling method
	* [x] Generate as many threads running this method as required
	* [ ] ~~Kill sampling threads during object destruction~~ Destructor not compatible with threaded implementation
	* [X] Implement a mutual-exclusion mechanism to avoid access violations
- [x] Send sensors' data via MQTT using topics to distribute data into different channels
- [x] Each "METEO" station MUST have a vaild (integer type) identifier, starting from 0
- [x] Topics should accomplish with the following template:
	* [x] ```METEO/<stationNumber>/Data/<sensor>```
	* [x] Valid ```<stationNumber>``` (identifiers) are integers from 0 to N-1
	* [x] Valid ```<sensor>``` values are:
		- [x] Temperature (Environmental temperature) [temp]
		- [x] Humidity (Relative humidity) [hum]
		- [x] Pressure (Local atmospheric pressure) [pres]
		- [x] Light (Incident light measurement) [light]
		- [x] AirQuality (Air quality as pollution measurement) [airQ]
		- [ ] ~~PPM (Raw particle count) [ppm]~~ PPM is irrelevant. Instead, PPM field used to transmit raw gas resistance value
- [x] A special topic may be used to set/get the sampling period dymanically
	* [x] ```METEO/<stationNumber>/Settings/SamplingRate/<sensor>```
	* [x] ```<sensor>``` field (sub-topic) is the same as described before
	* [x] Sampling rate value must be validated to remain between a valid range
		- [x] Min sampling rate 1 minute
		- [x] Max sampling rate 120 minutes
		- [x] If a sampling rate (SR) out of these limits is set, a default value will be chosen if a prior valid SR wasn't set yet; otherwise, the last valid SR will remain active
- [ ] \(Optional) _A special topic may be used to remotely reboot the device if no Alive beacons have been received_
	- [ ] _```METEO/<stationNumber>/Setiings/Reboot```_
	- [ ] _A unique key must be sent as password (through ```Reboot``` topic) to force a reboot_
	- [ ] _Key will be ```stationNumber```-dependent and time-dependent (unix format) hash_
	- [ ] _Hash must be computed by UI_
- [x] A special topic may be used to announce "I'm Alive" messages from stations to broker
	* [x] Invoke it via a separate thread as it may behave as a locking method
	* [x] ```METEO/Alive```
	* [x] Each station should publish a message containing only its ```<stationNumber>``` periodically (ie. every 1 minute)
		
## BME680_METEO
- [x] Compute Air Quality (%) using Humidity and Gas measurements
- [ ] ~~Compute PPM using Gas Baseline and Gas measurements~~ Not a requirement. Discarded from further releases.

## User Interaction
- [x] Add an LED status indicator to show whether the server is running or not (using RPI-GPIO)
- [x] Add a push-button input to hard-reset the server via a separate thread if anything fails (using RPI-GPIO)


## Data management
- [ ] Grab sensors' data from MQTT broker and process it to deliver filtered information 
- [ ] Store the processed data into a database (CSV files?)

## Reliability
- [x] Run meteo.py as a standalone application
	- [x] Set flag to meteo.py
		- [x] ```chmod +x meteo.py```
- [x] Autorun on boot
	- [x] ```sudo crontab -e```
	- [x] ```@reboot /home/pi/METEO/meteo.py &```
- [x] Software WDT
	- [x] Run a parallel process (subscribed to ```ALIVE``` topic) to check whether METEO is running or not
	- [x] Restart METEO process after 3 consecutive ```ALIVE``` periods with no answer
	- [x] Start WDT timer after the first ```ALIVE``` message

# User interface
- [ ] Node-red User Interface
