#!/usr/bin/env python
#-*- coding: UTF-8-*-

import websockets
import asyncio

async def hello():
	async with websockets.connect('ws://localhost:8004') as websocket:
		name = input("what's your name? ")
		await websocket.send(name)
		print(f"send server:{name}")
		greeting = await websocket.recv()
		print(f"receive from server:{greeting}")
		print()


if __name__ == '__main__':
	while True:
		asyncio.get_event_loop().run_until_complete(hello())