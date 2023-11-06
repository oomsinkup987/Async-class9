import time
import random
import json
import asyncio
import aiomqtt
from enum import Enum
import os
import sys
student_id = "6300001"

class MachineStatus(Enum):
    pressure = round(random.uniform(2000,3000), 2)
    temperature = round(random.uniform(25.0,40.0), 2)

class MachineMaintStatus(Enum):
    filter = random.choice(["clear", "clogged"])
    noise = random.choice(["quiet", "noisy"])

class WashingMachine:
    def __init__(self, serial):
        self.MACHINE_STATUS = 'OFF'
        self.SERIAL = serial


    # wash 10 seconds, if out of balance detected then fault

    # rinse 10 seconds, if motor failure detect then fault

    # spin 10 seconds, if motor failure detect then fault
    async def waiting(self):
        try:
            print(f'{time.ctime()} - Start waiting')
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            print(f'{time.ctime()} - Waiting function is canceled!')
            raise

        print(f'{time.ctime()} - Waiting 10 second already! -> TIMEOUT!')
        self.MACHINE_STATUS = 'FAULT'
        self.FAULT_TYPE = 'TIMEOUT'
        print(
            f'{time.ctime()} - [{self.SERIAL}] STATUS: {self.MACHINE_STATUS}')

    async def waiting_task(self):
        self.task = asyncio.create_task(self.waiting())
        return self.task

    async def cancel_waiting(self):
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            print(f'{time.ctime()} - Get message before timeout!')


async def publish_message(w, client, app, action, name, value):
    print(f"{time.ctime()} - [{w.SERIAL}] {name}:{value}")
    await asyncio.sleep(2)
    payload = {
                "action"    : "get",
                "project"   : student_id,
                "model"     : "model-01",
                "serial"    : w.SERIAL,
                "name"      : name,
                "value"     : value
            }
    print(f"{time.ctime()} - PUBLISH - [{w.SERIAL}] - {payload['name']} > {payload['value']}")
    await client.publish(f"v1cdti/{app}/{action}/{student_id}/model-01/{w.SERIAL}"
                        , payload=json.dumps(payload))

async def CoroWashingMachine(w, client):
    while True:
        wait_next = round(10*random.random(),2)
        print(f"{time.ctime()} - [{w.SERIAL}-{w.MACHINE_STATUS}] Waiting to start... {wait_next} seconds.")
        await asyncio.sleep(wait_next)
        if w.MACHINE_STATUS == 'OFF':
            continue
        if w.MACHINE_STATUS == 'READY':
            print(f"{time.ctime()} - [{w.SERIAL}-{w.MACHINE_STATUS}]")


            await publish_message(w, client, "app", "get", "STATUS", "READY")
            # door close

            await publish_message(w, client, 'hw', 'get', 'DOOR', 'CLOSE')
            # fill water untill full level detected within 10 seconds if not full then timeout 
            w.MACHINE_STATUS = 'FILLING'
            await publish_message(w, client, 'hw', 'get', 'STATUS', 'FILLING')
            task = w.waiting_task()
            await task
            # When washing is in FAULT state, wait until get FAULTCLEARED
            if w.MACHINE_STATUS == 'FAULT':
                await publish_message(w, client, 'hw', 'get', 'FAULT', w.FAULT_TYPE)
                
            while w.MACHINE_STATUS == 'FAULT':
                print(
                    f"{time.ctime()} - [{w.SERIAL}] Waiting to clear fault...")
                await asyncio.sleep(1)
            # heat water until temperature reach 30 celcius within 10 seconds if not reach 30 celcius then timeout
            if w.MACHINE_STATUS == 'HEATING':
                task = w.waiting_task()
            await task
            while w.MACHINE_STATUS == 'HEATING':
                await asyncio.sleep(2)

            if w.MACHINE_STATUS == 'WASHING':
                continue

            

async def listen(w, w_sensor, client):
    async with client.messages() as messages:
        await client.subscribe(f"v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}")
        async for message in messages:
            mgs_decode = json.loads(message.payload)
            if message.topic.matches(f"v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}"):
                print(
                    f"FROM MQTT: [{mgs_decode['serial']} {mgs_decode['name']} {mgs_decode['value']}]")

                if mgs_decode['name'] == "STATUS":
                    w.MACHINE_STATUS = mgs_decode['value']

                if w.MACHINE_STATUS == 'FILLING':
                    if mgs_decode['name'] == "WATERLEVEL":
                        w_sensor.fulldetect = mgs_decode['value']
                        if w_sensor.fulldetect == 'FULL':
                            w.MACHINE_STATUS = 'HEATING'
                            print(
                                f'{time.ctime()} - [{w.SERIAL}] STATUS: {w.MACHINE_STATUS}')
                            await publish_message(w, client, 'hw', 'get', 'STATUS', w.MACHINE_STATUS)

                        await w.cancel_waiting()

                if w.MACHINE_STATUS == 'HEATING':
                    if mgs_decode['name'] == "TEMPERATURE":
                        w_sensor.heatreach = mgs_decode['value']
                        if w_sensor.heatreach == 'REACH':
                            w.MACHINE_STATUS = 'WASH'
                            print(
                                f'{time.ctime()} - [{w.SERIAL}] STATUS: {w.MACHINE_STATUS}')
                            await publish_message(w, client, 'hw', 'get', 'STATUS', w.MACHINE_STATUS)

                        await w.cancel_waiting()
                if mgs_decode['name'] == "FAULT":
                    if mgs_decode['value'] == 'CLEAR':
                        w.MACHINE_STATUS = 'OFF'
                        await publish_message(w, client, 'hw', 'get', 'STATUS', w.MACHINE_STATUS)


async def main():
    w1 = WashingMachine(serial='SN-001')
    async with aiomqtt.Client("broker.hivemq.com") as client:
        await asyncio.gather(listen(w1, client) , CoroWashingMachine(w1, client)
                             )
if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

asyncio.run(main())
