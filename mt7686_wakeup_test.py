#!/usr/bin/env python3
import os, sys
import time, datetime
import asyncio
import websockets
import json
import socket

from mqtt_client import *
from mt7686_uart import *

file_count = 0
pcm_window = 20*32000

def save_pcm_file(_buffer):
	global file_count

	if None == _buffer:
		return

	str_file = 'received_%d.pcm' % (file_count)

	with open(str_file, 'wb') as f:
		f.write(_buffer)

	print("xxxxxxxxxxxxxx %s xxxxxxxxxxxx" %str_file)

	file_count += 1

@asyncio.coroutine
def websocket_handler(websocket, path):
	global pcm_window
	write_buffer = None

	try:
		while True:
			datas = yield from websocket.recv()

			if None == write_buffer:
				try:
					datas = json.loads(datas)

					if datas['audio']['audioType'] in ['ogg', 'wav', 'adpcm']:
						write_buffer = b''
				except:
					print(datas)

			elif len(datas) == 0:
				save_pcm_file(write_buffer)
				write_buffer = None
			else:
				write_buffer += datas
				length = len(write_buffer)

				if length > pcm_window:
					remove_len = length - pcm_window
					remove_len = (remove_len >>2) <<2
					write_buffer = write_buffer[remove_len:]

	except Exception as e:
		save_pcm_file(write_buffer)
		write_buffer = None
		print(e)

def test_main(deviceid, ipaddress, port, uart):
	if 'auto' == ipaddress:
		ipaddress = socket.gethostbyname(socket.gethostname())

	if 'auto' == uart:
		uart = [i[0] for i in serial.tools.list_ports.comports()]

		if 0 == len(uart): err += 1
		else: uart = uart[0]

	mqtt = MyMqtt(deviceid, 'gh_b47c524e9c3a')
	mqtt.start()

	mqtt.recorderBypassEnable(mqtt.devId, VOICE_FILE_TYPE_DUI, ipaddress, port, True)

	comm = CommSrvProcessor(uart)
	comm.Start()

	while True:
		if True == comm.WaitResp('player_path: ImHere.mp3', False, 10):
			mqtt.recorderBypassDisable(mqtt.devId)
			mqtt.recorderBypassEnable(mqtt.devId, VOICE_FILE_TYPE_DUI, ipaddress, port, True)
	

if __name__ == "__main__":
	deviceid	= sys.argv[1] if len(sys.argv) > 1 else '00000000400120181120704f08002657'
	ipaddress 	= sys.argv[2] if len(sys.argv) > 2 else 'auto'
	port        = sys.argv[3] if len(sys.argv) > 3 else '8003'
	uart     	= sys.argv[4] if len(sys.argv) > 4 else 'auto'
	
	port = int(port)

	ws_thread = threading.Thread(target=test_main, args=(deviceid, ipaddress, port, uart,))
	ws_thread.setDaemon(True)
	ws_thread.start()

	start_server = websockets.serve(websocket_handler, '0.0.0.0', port)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(start_server)
	loop.run_forever()
	#time.sleep(10000)