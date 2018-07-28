def meteoTestBench():
	try:
		myMeteo = Meteo(True) # IRM Enable Debugging
		#myMeteo = Meteo(False) # IRM Debugging disabled
	except KeyboardInterrupt:
		print 'Killing Meteo!'
		del myMeteo

	# IRM Playing out with sampling rate values
	print myMeteo.getSensorNames()
	print myMeteo.getSRvalues()

	print myMeteo.setSR('temp', 500)
	print myMeteo.setSR('Temp', 600) # IRM Wrong value, should return an error code
	print myMeteo.setSR('airQ', 5*60)

	print myMeteo.getSRvalues()

	print myMeteo.sampleSensor(TEMP)
	print myMeteo.sampleSensor(LIGHT)
	print myMeteo.sampleSensor(PPM)
	print myMeteo.sampleSensor(AIR_Q)
	print myMeteo.sampleSensor(HUM)



def mutexTestBench(): # IRM Simple mutex tests without threads

	myMeteo = Meteo(DEBUG = True)

	bme180Mutex = Mutex()

	print 'MUTEX running on AutoExec Mode'

	temp = bme180Mutex.lock(myMeteo.sampleSensor, [TEMP])
	if temp[0]:
		print 'Temperature: ' + str(temp[1][0]) + ' Celsius'
	else:
		print '*Invalid temp: ERROR ' + str(temp[1][0])

	hum  = bme180Mutex.lock(myMeteo.sampleSensor, [HUM])
	if hum[0]:
		print 'Humidity: ' + str(hum[1][0]) + '%'	
	else:
		print '*Invalid hum:  ERROR ' + str(temp[1][0])

	airQ = bme180Mutex.lock(myMeteo.sampleSensor, [AIR_Q])
	if airQ[0]:
		print 'Air Quality: ' + str(airQ[1][0]) + '%'
	else:
		print '*Invalid AirQ:  ERROR ' + str(airQ[1][0])


	print 'MUTEX running without AutoExec Mode'

	bme180NoAutoExecMutex = Mutex(autoExec = False)
	while(bme180NoAutoExecMutex.isMutexLocked()): # IRM Wait until mutex (and shared resource) is available
		print 'Mutex Locked waiting until released'

	bme180NoAutoExecMutex.lock()
	temp = myMeteo.sampleSensor(TEMP)
	if temp[0]:
		print 'Temperature: ' + str(temp[1][0]) + ' Celsius'
	else:
		print '*Invalid temp: ERROR ' + str(temp[1][0])


tempSensor    = Meteo()
tempMutex     = Mutex(autoExec = False)
tempMutexAuto = Mutex(autoExec = True)
	
def sampleTempTest(mutex = True, threadNumber = 0):
	if mutex:
		while tempMutex.isMutexLocked():
			pass
		tempMutex.lock()
		print 'Mutex Owned! Thread # ' + str(threadNumber)

	temp = tempSensor.sampleSensor(TEMP)

	if mutex:
		tempMutex.unlock()
		print 'Mutex Released! Thread # ' + str(threadNumber)

	print 'Thread ' + str(threadNumber) + ' --- ',
	if temp[0]:
		print temp[1][0]
	else:
		print False

def sampleTempTestWithAutoExec(mutex = True, threadNumber = 0):
	if mutex:
		temp = tempMutexAuto.lock(tempSensor.sampleSensor, [TEMP])
		print 'Mutex Owned! Thread # ' + str(threadNumber)

	print 'Thread ' + str(threadNumber) + ' --- ',
	if temp[0]:
		print temp[1][0]
	else:
		print False	


# IRM Using Threading native mutex mechanism (lock/unlock)
tTempMutex = threading.Lock()
def sampleTempTestThreadingLock(mutex = True, threadNumber = 0):
	if mutex:
		tTempMutex.acquire()
		print 'Mutex Owned! Thread # ' + str(threadNumber)

	temp = tempSensor.sampleSensor(TEMP)

	if mutex:
		tTempMutex.release()
		print 'Mutex Released! Thread # ' + str(threadNumber)

	print 'Thread ' + str(threadNumber) + ' --- ',
	if temp[0]:
		print temp[1][0]
	else:
		print False	


def mutexAndThreadsTestBench():
	MAX_TASKS = 20 # IRM Max simultaneous threads to run Temperature Measurement
	MUTEX_ENABLED = True # IRM Enable/Disable to check Mutex functionality

	for i in range(MAX_TASKS):
		#tempMutexThread = threading.Thread(target = sampleTempTest, args = [True, i], name = 'Temp Sensor ' + str(i), )
		tempMutexThread = threading.Thread(target = sampleTempTestWithAutoExec, args = [True, i], name = 'Temp Sensor ' + str(i), )
		#tempMutexThread = threading.Thread(target = sampleTempTestThreadingLock, args = [True, i], name = 'Temp Sensor ' + str(i), )
		#tempMutexThread.setDaemon(True)
		tempMutexThread.start()


