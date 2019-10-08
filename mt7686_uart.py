#!/usr/bin/env python3
import os,sys
import time
import serial
import serial.tools.list_ports
import queue
import threading

class CommSrvProcessor(object):
	def __init__(self, strPort=''):
		self.ser = serial.Serial(port=strPort, baudrate=115200)
		self.RecvProcRunning = False
		self.RecvProcPause = False
		self.recvQueue = queue.Queue()

		#for strPort in serial.tools.list_ports.comports():
		#	print(strPort[0])

	def __del__(self):
		self.Close()

	def Reopen(self):
		self.Close()
		self.ser.open()
		self.ser.reset_input_buffer()
		self.ser.reset_output_buffer()

	def Close(self):
		self.RecvProcRunning = False
		self.RecvProcPause = False
		self.recvQueue.queue.clear()
		self.ser.close()

	# 启动通讯侦听
	def Start(self):
		self.Reopen()
		self.thread = threading.Thread(target=self.RecvProc)
		self.thread.setDaemon(True)
		self.thread.start()

	# 数据接收线程
	def RecvProc(self):
		self.RecvProcRunning = True
		while self.RecvProcRunning:
			if False==self.RecvProcPause:
				try:
					_buffer = self.ser.readline().decode()
					_buffer = _buffer.replace('\r','').replace('\n','')
					self.RecvHandler(_buffer)
					self.recvQueue.put(_buffer)
				except: 
					_buffer = ''
			else:
				time.sleep(0.1)
				continue

			if False==self.RecvProcRunning:
				break

	def MatchInfo(self, _buffer, key_list):
		for _key in key_list:
			pos = _buffer.find(_key)

			if pos >= 0:
				#print(_buffer[pos:])
				break

	def RecvHandler(self, _buffer):
		#self.MatchInfo(_buffer, ['Platform:MT7686', 'AIspeech Platform: ', 'Firmware: ', 'Compile : '])
		self.MatchInfo(_buffer, ['[Device ID]: '])

	def WaitResp(self,strExpect=None,whole=True,timeout=1):
		beg_time = time.time()

		if None == strExpect:
			try: return self.recvQueue.get(True, timeout)
			except: return None

		while strExpect:
			remain = timeout - (time.time() - beg_time)
			if remain <= 0:
				break

			try: tmp = self.recvQueue.get(True, remain)
			except: tmp = None

			if tmp:
				if False == whole and tmp.find(strExpect) >= 0:
					return True
				if True == whole and tmp == strExpect:
					return True

		return False

	def Send(self,str,strCompare=None,whole=True,timeout=1):
		for try_cnt in range(0,2):
			self.ser.reset_input_buffer()
			self.recvQueue.queue.clear()
			self.ser.write('\n\r'.encode())
			time.sleep(0.1)
			self.ser.write((str+'\n\r').encode())

			if True == self.WaitResp(strCompare, whole, timeout):
				print("[%s] \n%s\n" %(str, strCompare))
				return True

		return False

	def MacAddr(self, mac_addr):	return self.Send('MacAddr '+mac_addr, 'RX_MACADDR_OK ^_^')
	def Engineer(self, _mode):		return self.Send('Engineer '+_mode, 'open normal-mode ok')
	def WaitEngineeringMode(self):	return self.WaitResp('Enter engineering mode', False, 8)
	def Reboot(self):				return self.Send('reboot', '[Device ID]: ', False, 3)

if __name__ == "__main__":
	comm = CommSrvProcessor('/dev/ttyUSB0')
	comm.Start()

	while True:
		if True == comm.WaitResp('player_path: ImHere.mp3', False, 10):
			print("wake up")
	
	comm.Close()
