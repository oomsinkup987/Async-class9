import time
import random
import json
import asyncio
import aiomqtt
import os
import sys
from enum import Enum

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
S_STOP      = 'STOP'

# Function
S_DOORCLOSED            = 'DOORCLOSE'
S_FULLLEVELDETECTED     = 'FULLLEVELDETECTED'
S_TEMPERATUREREACHED    = 'TEMPERATUREREACHED'
S_FUNCTIONCOMPLETED     = 'FUNCTIONCOMPLETED'
S_TIMEOUT               = 'TIMEOUT'
S_MOTORFAILURE          = 'MOTORFAILURE'
S_FAULTCLEARED          = 'FAULTCLEARED'

async def publish_message(serial, client, app, action, name, value):
    await asyncio.sleep(2)
    payload = {
                "action"    : "get",
                "project"   : student_id,
                "model"     : "model-01",
                "serial"    : serial,
                "name"      : name,
                "value"     : value
            }
    print(f"{time.ctime()} - PUB topic: v1cdti/{app}/{action}/{student_id}/model-01/{serial} payload: {name}:{value}")
    await client.publish(f"v1cdti/{app}/{action}/{student_id}/model-01/{serial}"
                        , payload=json.dumps(payload))
    
async def app_monitor(client):
    while True:
        await asyncio.sleep(20)
        payload = {
                    "action"    : "get",
                    "project"   : student_id,
                    "model"     : "model-01",

                }
        print(f"{time.ctime()} - GET MACHINE STATUS")
        await client.publish(f"v1cdti/app/get/{student_id}/model-01/"
                            , payload=json.dumps(payload))

async def listen(client):
    async with client.messages() as messages:
        print(f'{time.ctime()}  subscribe for topic v1cdti/hw/get/{student_id}/model-01/')
        print(f"{time.ctime()} -  SUB topic: v1cdti/hw/get/{student_id}/model-01/")
        await client.subscribe(f"v1cdti/hw/get/{student_id}/model-01/+")

        async for message in messages:
            m_decode = json.loads(message.payload)
            if message.topic.matches(f"v1cdti/hw/get/{student_id}/model-01/+"):
                print(f"{time.ctime()} - MQTT [{m_decode['serial']}:{m_decode['name']} => {m_decode['value']}]")
                
                if (m_decode['name']=="STATUS" and m_decode['value']==S_READY):
                    await publish_message(m_decode['serial'],client, "hw", "set", "STATUS",S_READY)
                
                if (m_decode['name']=="STATUS" and m_decode['value']==S_FILLWATER):
                    await publish_message(m_decode['serial'],client, "hw", "set", "STATUS",S_FULLLEVELDETECTED)

                if (m_decode['name']=="STATUS" and m_decode['value']==S_HEATWATER):
                    await asyncio.sleep(2)
                    await publish_message(m_decode['serial'],client, "hw", "set", "STATUS",S_TEMPERATUREREACHED)
               
                if (m_decode['name']=="STATUS" and m_decode['value']==S_TEMPERATUREREACHED):
                    await asyncio.sleep(2)
                    await publish_message(m_decode['serial'],client, "hw", "set", "STATUS",S_WASH)

                if (m_decode['name']=="STATUS" and m_decode['value']==S_STOP):
                    await publish_message(m_decode['serial'],client, "hw", "set", "STATUS",S_OFF)


async def main():
    async with aiomqtt.Client("broker.hivemq.com") as client:
        await asyncio.gather(listen(client), app_monitor(client))

if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

asyncio.run(main())