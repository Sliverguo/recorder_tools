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
pcm_window = 90000000*(32000+16000)
stop_flag_int = 0

def separation_mixing_file(file_name):
	file = open(file_name, "rb")
	file_org = open(r'D:\7686_record_audio\org_%d.pcm'%file_count, "wb")
	file_aec = open(r'D:\7686_record_audio\aec_%d.pcm'%file_count, "wb")
	tag1 = "pcm_str"
	tag2 = "aec_str"
	while True:
		try:
			head = file.read(7)
			x = file.read(4)
			len = x[0] + x[1] * 2 ** 8 + x[2] * 2 ** 16 + x[3] * 2 ** 24
			buffer = file.read(len)
			if tag1 == head.decode():
				file_org.write(buffer)
			elif tag2 == head.decode():
				file_aec.write(buffer)
			else:
				print(head.decode())
		except Exception as e:
			print(e)
			break

	file.close()
	file_org.close()
	file_aec.close()


def save_pcm_file(_buffer):
	global file_count
	receive_path = '7686_record_audio'

	if None == _buffer:
		return
	try:
		os.mkdir('D:\\%s'%receive_path)
	except Exception as e:
		print(e)

	str_file = "D:\%(dir)s\_received_%(count)d.pcm" % ({"dir": receive_path, "count": file_count})
	print(str_file)
	with open(str_file, 'wb') as f:
		f.write(_buffer)
	print("xxxxxxxxxxxxxx %s xxxxxxxxxxxx" %str_file)
	separation_mixing_file(str_file)
	file_count += 1

@asyncio.coroutine
def websocket_handler(websocket, path):
	global pcm_window
	write_buffer = None
	print("------------websocket_handler--------------")
	try:
		while True:
			datas = yield from websocket.recv()

			if None == write_buffer:
				try:
					datas = json.loads(datas)
					print('-receive-')
					print(datas)
					print('-receive-')
					if datas['audio']['audioType'] in ['ogg', 'wav', 'adpcm']:
						write_buffer = b''
				except Exception as e:
					print("==")
					print(e)
					print("==")
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

	mqtt = MyMqtt(deviceid, 'gh_5e9c85479d21')
	mqtt.start()

	mqtt.recorderBypassDisable(mqtt.devId)
	mqtt.recorderBypassEnable(mqtt.devId, VOICE_FILE_TYPE_DUI, ipaddress, port, True)

	while True:
		#time.sleep(0.5)
		stop_flag = input("请输入：")
		if 'stop' == stop_flag:
			mqtt.recorderBypassDisable(mqtt.devId)
		elif 'start' == stop_flag:
			mqtt.recorderBypassDisable(mqtt.devId)
			mqtt.recorderBypassEnable(mqtt.devId, VOICE_FILE_TYPE_DUI, ipaddress, port, True)

if __name__ == "__main__":
	deviceid	= sys.argv[1] if len(sys.argv) > 1 else '00000000400120181120704f08009235'
	ipaddress 	= sys.argv[2] if len(sys.argv) > 2 else '192.168.8.110'
	port        = sys.argv[3] if len(sys.argv) > 3 else '8005'
	uart     	= sys.argv[4] if len(sys.argv) > 4 else 'auto'
	port = int(port)
	#ipaddress = '192.168.8.102'
	ws_thread = threading.Thread(target=test_main, args=(deviceid, ipaddress, port, uart,))
	ws_thread.setDaemon(True)
	ws_thread.start()

	start_server = websockets.serve(websocket_handler, '0.0.0.0', port)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(start_server)
	loop.run_forever()
