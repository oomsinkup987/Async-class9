import time
import random
import json
import asyncio
import aiomqtt
from enum import Enum
import os
import sys
student_id = "6310301025"

# State 
S_OFF       = 'OFF'
S_READY     = 'READY'
S_FAULT     = 'FAULT'
S_FILLWATER = 'FILLWATER'
S_HEATWATER = 'HEATWATER'
S_WASH      = 'WASH'
S_RINSE     = 'RINSE'
S_SPIN      = 'SPIN'

# Function
S_DOORCLOSED            = 'DOORCLOSE'
S_FULLLEVELDETECTED     = 'FULLLEVELDETECTED'
S_TEMPERATUREREACHED    = 'TEMPERATUREREACHED'
S_FUNCTIONCOMPLETED     = 'FUNCTIONCOMPLETED'
S_TIMEOUT               = 'TIMEOUT'
S_OUTOFBALANCE          = 'OUTOFBALANCE'
S_MOTORFAILURE          = 'MOTORFAILURE'
S_FAULTCLEARED          = 'FAULTCLEARED'

async def publish_message(w, client, app, action, name, value):
    await asyncio.sleep(1)
    payload = {
                "action"    : "get",
                "project"   : student_id,
                "model"     : "model-01",
                "serial"    : w.SERIAL,
                "name"      : name,
                "value"     : value
            }
    print(f"{time.ctime()} - PUB topic: v1cdti/{app}/{action}/{student_id}/model-01/{w.SERIAL} payload: {name}:{value}")
    await client.publish(f"v1cdti/{app}/{action}/{student_id}/model-01/{w.SERIAL}"
                        , payload=json.dumps(payload))

async def door(w, doortime=10):
    print(f"{time.ctime()} - [{w.SERIAL}] Waiting for door close")
    await asyncio.sleep(doortime)


async def fillwater(w, filltime=10):
    print(f"{time.ctime()} - [{w.SERIAL}] Waiting for fill water maxinum {filltime} seconds")
    await asyncio.sleep(filltime)

async def waterheater(w, heatertime=10):
    print(f"{time.ctime()}- [{w.SERIAL}] Water Heater detect {heatertime} seconds")
    await asyncio.sleep(heatertime)

async def wash_rinse_spine(w, washtime=10):
    print(f"{time.ctime()}- [{w.SERIAL}] Failure detect {washtime} seconds")
    await asyncio.sleep(washtime)

class MachineStatus(Enum):
    pressure = round(random.uniform(2000,3000), 2)
    temperature = round(random.uniform(25.0,40.0), 2)

class MachineMaintStatus(Enum):
    filter = random.choice(["clear", "clogged"])
    noise = random.choice(["quiet", "noisy"])

class WashingMachine:
    def __init__(self, serial):
        self.SERIAL = serial
        self.STATE = 'OFF'
        self.Task = None
        self.event = asyncio.Event()

async def CoroWashingMachine(w, client,event):

    while True:
        
        
        if w.STATE == S_OFF:
            print(f"{time.ctime()} - [{w.SERIAL}-{w.STATE}] Waiting to start... ")
            await event.wait()
            event.clear()
            continue

        if w.STATE == S_FAULT:
            print(f"{time.ctime()} - [{w.SERIAL}-{w.STATE}] Waiting to clear fault... ")
            await event.wait()
            event.clear()
            continue

        if w.STATE == S_READY:
            print(f"{time.ctime()} - [{w.SERIAL}-{w.STATE}]")

            await publish_message(w, client, "hw", "get", "STATUS", "READY")

            # door closes
            await publish_message(w, client, "hw", "get", "LID", "CLOSE")
            w.STATE = 'FILLWATER'
                    

            # fill water untill full level detected within 10 seconds if not full then timeout 
            await publish_message(w, client, "hw", "get", "STATUS", "FILLWATER")
            try:
                async with asyncio.timeout(10):
                    await fillwater(w)
            except TimeoutError:
                if w.STATE == 'FULLLEVELDETECTED' :
                    print(f"{time.ctime()} - Water level full")
                    await publish_message(w, client, "app", "get", "STATUS", "WATERHEATER")

                else:
                    print(f"{time.ctime()} - Water level fault")
                    await publish_message(w, client, "app", "get", "STATUS", "FAULT")
                    w.STATE = 'FAULT'
                    continue

            #Water Heater 
            await publish_message(w, client, "app", "get", "STATUS", "HEATWATER_ON")
            try:
                async with asyncio.timeout(10):
                    await waterheater(w)
            except TimeoutError:
                if w.STATE == 'TEMPERATUREREACHED' : 
                    print(f"{time.ctime()} - Water heater reached ")
                    await publish_message(w, client, "app", "get", "STATUS", "WASH")
                    
                else:
                    print(f"{time.ctime()} - Water heater fault")
                    await publish_message(w, client, "app", "get", "STATUS", "FAULT")
                    w.STATE = 'FAULT'
                    continue

        # wash 10 seconds, if out of balance detected then fault
        
            try:
                async with asyncio.timeout(10):
                    await wash_rinse_spine(w)
            except TimeoutError:
                if w.STATE == 'OUTOFBALANCE':
                    await publish_message(w, client, "app", "get", "STATUS", "OUTOFBALANCE")
                    w.STATE = 'FAULT'
                    continue
                else:
                    await publish_message(w, client, "app", "get", "STATUS", "RINSE")



        # rinse 10 seconds, if motor failure detect then fault
            try:
                async with asyncio.timeout(10):
                    await wash_rinse_spine(w)
            except TimeoutError:
                if w.STATE == 'MOTORFAILURE':
                    await publish_message(w, client, "app", "get", "STATUS", "MOTORFAILURE")
                    w.STATE = 'FAULT'
                    continue
                else:
                    await publish_message(w, client, "app", "get", "STATUS", "SPIN")
                    


        # spin 10 seconds, if motor failure detect then fault
            try:
                async with asyncio.timeout(10):
                    await wash_rinse_spine(w)
            except TimeoutError:
                if w.STATE == 'MOTORFAILURE':
                    await publish_message(w, client, "app", "get", "STATUS", "MOTORFAILURE")
                    w.STATE = 'FAULT'
                    continue
                else:
                    await publish_message(w, client, "app", "get", "STATUS", "OFF")
                    
                    
        # When washing is in FAULT state, wait until get FAULTCLEARED

       
            

async def listen(w, client,event):
    async with client.messages() as messages:
        print(f"{time.ctime()} - SUB topic: v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}")
        await client.subscribe(f"v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}")
        async for message in messages:
            m_decode = json.loads(message.payload)
            if message.topic.matches(f"v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}"):
                # set washing machine status
                print(f"{time.ctime()} - MQTT [{m_decode['serial']}]:{m_decode['name']} => {m_decode['value']}")
                if (m_decode['name']=="STATUS" and m_decode['value']==S_READY):
                    w.STATE = S_READY
                    event.set()
                elif (m_decode['name']=="STATUS" and m_decode['value']==S_FULLLEVELDETECTED):
                    w.STATE = S_FULLLEVELDETECTED
                elif (m_decode['name']=="STATUS" and m_decode['value']==S_FILLWATER):
                    w.STATE = S_FILLWATER
                elif (m_decode['name']=="STATUS" and m_decode['value']==S_TEMPERATUREREACHED):
                    w.STATE = S_TEMPERATUREREACHED
                elif (m_decode['name']=="STATUS" and m_decode['value']==S_MOTORFAILURE):
                    w.STATE = S_MOTORFAILURE
                elif (m_decode['name']=="STATUS" and m_decode['value']==S_OUTOFBALANCE):
                    w.STATE = S_OUTOFBALANCE
                elif (m_decode['name']=="STATUS" and m_decode['value']==S_FAULT):
                    w.STATE = S_FAULT
                elif (m_decode['name']=="STATUS" and m_decode['value']==S_FAULTCLEARED):
                    w.STATE = S_READY
                    event.set()
                elif (m_decode['name']=="STATUS" and m_decode['value']==S_OFF):
                    w.STATE = "OFF"
                else:
                    print(f"{time.ctime()} - ERROR MQTT [{m_decode['serial']}]:{m_decode['name']} => {m_decode['value']}")

async def main():
    # event = asyncio.Event()
    # w = WashingMachine(serial='SN-001')
    # async with aiomqtt.Client("broker.hivemq.com") as client:
    #     await asyncio.gather(listen(w, client, event) , CoroWashingMachine(w, client,event)
    #                          )
    n = 5
    W = [WashingMachine(serial= f'SN-0{i+1}') for i in range(n)]
    Event = [asyncio.Event() for i in range(n)]
    async with aiomqtt.Client("broker.hivemq.com") as client:
        listenTask = []
        CoroTask = []
        for w, event in zip(W, Event):
            listenTask.append(listen(w, client, event))
            CoroTask.append(CoroWashingMachine(w, client, event))
        await asyncio.gather(*listenTask, *CoroTask)
    
if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        

asyncio.run(main())


# Tue Sep 19 13:39:55 2023 - SUB topic: v1cdti/hw/set/6310301025/model-01/SN-01
# Tue Sep 19 13:39:55 2023 - SUB topic: v1cdti/hw/set/6310301025/model-01/SN-02
# Tue Sep 19 13:39:55 2023 - SUB topic: v1cdti/hw/set/6310301025/model-01/SN-03
# Tue Sep 19 13:39:55 2023 - SUB topic: v1cdti/hw/set/6310301025/model-01/SN-04
# Tue Sep 19 13:39:55 2023 - SUB topic: v1cdti/hw/set/6310301025/model-01/SN-05
# Tue Sep 19 13:39:55 2023 - [SN-01-OFF] Waiting to start...
# Tue Sep 19 13:39:55 2023 - [SN-02-OFF] Waiting to start...
# Tue Sep 19 13:39:55 2023 - [SN-03-OFF] Waiting to start...
# Tue Sep 19 13:39:55 2023 - [SN-04-OFF] Waiting to start...
# Tue Sep 19 13:39:55 2023 - [SN-05-OFF] Waiting to start...
# Tue Sep 19 13:40:25 2023 - MQTT [SN-00]:STATUS => READY
# Tue Sep 19 13:40:25 2023 - [SN-05-READY]
# Tue Sep 19 13:40:26 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-05 payload: STATUS:READY
# Tue Sep 19 13:40:27 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-05 payload: LID:CLOSE
# Tue Sep 19 13:40:28 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-05 payload: STATUS:FILLWATER
# Tue Sep 19 13:40:28 2023 - [SN-05] Waiting for fill water maxinum 10 seconds
# Tue Sep 19 13:40:32 2023 - MQTT [SN-00]:STATUS => READY
# Tue Sep 19 13:40:32 2023 - [SN-03-READY]
# Tue Sep 19 13:40:33 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: STATUS:READY
# Tue Sep 19 13:40:34 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: LID:CLOSE
# Tue Sep 19 13:40:35 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: STATUS:FILLWATER
# Tue Sep 19 13:40:35 2023 - [SN-03] Waiting for fill water maxinum 10 seconds
# Tue Sep 19 13:40:38 2023 - Water level fault
# Tue Sep 19 13:40:39 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-05 payload: STATUS:FAULTTue Sep 19 13:40:39 2023 - [SN-05-FAULT] Waiting to clear fault...
# Tue Sep 19 13:40:45 2023 - Water level fault
# Tue Sep 19 13:40:46 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-03 payload: STATUS:FAULTTue Sep 19 13:40:46 2023 - [SN-03-FAULT] Waiting to clear fault...
# Tue Sep 19 13:41:28 2023 - MQTT [SN-03]:STATUS => READY
# Tue Sep 19 13:41:28 2023 - [SN-03-READY]
# Tue Sep 19 13:41:29 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: STATUS:READY
# Tue Sep 19 13:41:30 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: LID:CLOSE
# Tue Sep 19 13:41:31 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: STATUS:FILLWATER
# Tue Sep 19 13:41:31 2023 - [SN-03] Waiting for fill water maxinum 10 seconds
# Tue Sep 19 13:41:41 2023 - Water level fault
# Tue Sep 19 13:41:42 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-03 payload: STATUS:FAULTTue Sep 19 13:41:42 2023 - [SN-03-FAULT] Waiting to clear fault...
# Tue Sep 19 13:42:03 2023 - MQTT [SN-03]:STATUS => READY
# Tue Sep 19 13:42:03 2023 - [SN-03-READY]
# Tue Sep 19 13:42:04 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: STATUS:READY
# Tue Sep 19 13:42:05 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: LID:CLOSE
# Tue Sep 19 13:42:06 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-03 payload: STATUS:FILLWATER
# Tue Sep 19 13:42:06 2023 - [SN-03] Waiting for fill water maxinum 10 seconds
# Tue Sep 19 13:42:16 2023 - Water level fault
# Tue Sep 19 13:42:17 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-03 payload: STATUS:FAULT
# Tue Sep 19 13:42:17 2023 - [SN-03-FAULT] Waiting to clear fault...
# Tue Sep 19 13:42:49 2023 - MQTT [SN-02]:STATUS => READY
# Tue Sep 19 13:42:49 2023 - [SN-02-READY]
# Tue Sep 19 13:42:50 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: STATUS:READY
# Tue Sep 19 13:42:51 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: LID:CLOSE
# Tue Sep 19 13:42:52 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: STATUS:FILLWATER
# Tue Sep 19 13:42:52 2023 - [SN-02] Waiting for fill water maxinum 10 seconds
# Tue Sep 19 13:43:02 2023 - Water level fault
# Tue Sep 19 13:43:03 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-02 payload: STATUS:FAULT
# Tue Sep 19 13:43:03 2023 - [SN-02-FAULT] Waiting to clear fault...
# Tue Sep 19 13:44:22 2023 - MQTT [SN-02]:STATUS => FAULTCLEARED
# Tue Sep 19 13:44:22 2023 - [SN-02-READY]
# Tue Sep 19 13:44:23 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: STATUS:READY
# Tue Sep 19 13:44:24 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: LID:CLOSE
# Tue Sep 19 13:44:25 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: STATUS:FILLWATER
# Tue Sep 19 13:44:25 2023 - [SN-02] Waiting for fill water maxinum 10 seconds
# Tue Sep 19 13:44:35 2023 - Water level fault
# Tue Sep 19 13:44:36 2023 - MQTT [SN-02]:STATUS => FAULTCLEARED
# Tue Sep 19 13:44:36 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-02 payload: STATUS:FAULT
# Tue Sep 19 13:44:36 2023 - [SN-02-FAULT] Waiting to clear fault... 
# Tue Sep 19 13:44:36 2023 - [SN-02-FAULT] Waiting to clear fault... 
# Tue Sep 19 13:44:51 2023 - MQTT [SN-02]:STATUS => FAULTCLEARED
# Tue Sep 19 13:44:51 2023 - [SN-02-READY]
# Tue Sep 19 13:44:52 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: STATUS:READY
# Tue Sep 19 13:44:53 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: LID:CLOSE
# Tue Sep 19 13:44:54 2023 - PUB topic: v1cdti/hw/get/6310301025/model-01/SN-02 payload: STATUS:FILLWATER
# Tue Sep 19 13:44:54 2023 - [SN-02] Waiting for fill water maxinum 10 seconds
# Tue Sep 19 13:44:59 2023 - MQTT [SN-02]:STATUS => FULLLEVELDETECTED
# Tue Sep 19 13:45:04 2023 - Water level full
# Tue Sep 19 13:45:05 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-02 payload: STATUS:WATERHEATER
# Tue Sep 19 13:45:06 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-02 payload: STATUS:HEATWATER_ON
# Tue Sep 19 13:45:06 2023- [SN-02] Water Heater detect 10 seconds
# Tue Sep 19 13:45:08 2023 - MQTT [SN-02]:STATUS => TEMPERATUREREACHED
# Tue Sep 19 13:45:16 2023 - Water heater reached 
# Tue Sep 19 13:45:17 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-02 payload: STATUS:WASH
# Tue Sep 19 13:45:17 2023- [SN-02] Failure detect 10 seconds
# Tue Sep 19 13:45:28 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-02 payload: STATUS:RINSE
# Tue Sep 19 13:45:28 2023- [SN-02] Failure detect 10 seconds
# Tue Sep 19 13:45:39 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-02 payload: STATUS:SPIN
# Tue Sep 19 13:45:39 2023- [SN-02] Failure detect 10 seconds
# Tue Sep 19 13:45:50 2023 - PUB topic: v1cdti/app/get/6310301025/model-01/SN-02 payload: STATUS:OFF