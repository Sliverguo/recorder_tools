#!/usr/bin/env python3
import time,queue,threading
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json

AUDIO_SRC_FLAG_LOCAL       = 1
AUDIO_SRC_FLAG_PROMPT      = 2
AUDIO_SRC_FLAG_HTTP_URL    = 3
AUDIO_SRC_FLAG_TTS         = 4

AUDIO_PLAYER_SRC_WEB       = 0
AUDIO_PLAYER_SRC_FLASH     = 1
AUDIO_PLAYER_SRC_SD_CARD   = 2

AUDIO_PLAYER_TYPE_RESOURCE = 0
AUDIO_PLAYER_TYPE_PROMPT   = 1

VOICE_FILE_TYPE_SD_CARD    = 0
VOICE_FILE_TYPE_DUI        = 1

class MyMqtt(object):
	#publish.single("lettuce", "payload", hostname=HOST, port=61613, auth={'username': "admin", 'password':"password"})
	def __init__(self, devId='00000000200120180404704f08000298', weChat='gh_11950ee43a0c'):
		self.client = mqtt.Client()
		self.client.username_pw_set("admin", "password")
		self.client.on_connect = self.on_connect
		self.client.on_message = self.on_message

		self.RecvProcRunning = False
		self.recvQueue = queue.Queue()
		self.devId = devId
		self.weChat = weChat

		#self.HOST = "172.16.153.212"
		self.HOST = "mqtt.iot.aispeech.com" #"120.24.75.220"
		self.PORT = 1883 #61613

	def __del__(self):
		self.close()

	def reopen(self):
		self.close()
		self.client.connect(self.HOST, self.PORT, 60)

	def close(self):
		self.RecvProcRunning = False
		self.recvQueue.queue.clear()
		self.client.disconnect()

	def start(self):
		self.reopen()
		self.thread = threading.Thread(target=self.RecvProc)
		self.thread.setDaemon(True)
		self.thread.start()

	def RecvProc(self):
		self.RecvProcRunning = True
		while self.RecvProcRunning:
			self.client.loop_forever()

	def on_connect(self, client, userdata, flags, rc):
		#print("Connected with result code "+str(rc))
		self.client.subscribe(self.weChat)
		self.client.subscribe("web_" + self.devId)
		self.client.subscribe(self.devId)

	def on_message(self, client, userdata, msg):
		recv = msg.payload.decode()
		try:
			recv = json.loads(recv)
		except:
			print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")
			print(recv)
			print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")

		ignore = False
		if 'deviceid' in recv and recv['deviceid'] != self.devId:
			ignore = True

		if False == ignore:
			if 'device_test'==recv['do']:
				self.recvQueue.put(recv)

			print(recv)

	def transfer_inner(self, do, devId, sendJson, timeout=2):
		sendJson['do'] = do
		sendJson = json.dumps(sendJson)

		self.recvQueue.queue.clear()
		self.client.publish(devId, sendJson)

		while timeout > 0:
			begTime = time.time()
			try:
				recvJson = self.recvQueue.get(True, timeout)

				if recvJson['deviceid']==devId:
					return recvJson
			except:
				pass

			timeout -= time.time() - begTime

		return None

	def transfer(self, devId, sendJson, timeout=2):
		return self.transfer_inner('device_test', devId, sendJson, timeout)

	def deviceUnread(self,devId,num):             				return self.transfer_inner('device_unread', devId, {'name':'toy', 'data':{'num':num}})
	def deviceUpgrade(self,devId,url,version):             		return self.transfer_inner('device_upgrade', devId, {'name':'toy','data':{'url':url,'publish_id':1,'version':version}})
	def devicePlay(self,devId,url):             				return self.transfer_inner('device_play', devId, {'name':'toy','data':{'url':url}})
	def devicePause(self,devId):             					return self.transfer_inner('device_pause', devId, {'name':'toy','data':{}})
	def deviceResume(self,devId):             					return self.transfer_inner('device_resume', devId, {'name':'toy','data':{}})
	def deviceSeekProgress(self,devId,progress):             	return self.transfer_inner('device_seek_progress', devId, {'name':'toy','data':{'progress':progress}})
	def deviceEnableProgress(self,devId,enable):             	return self.transfer_inner('device_enable_progress', devId, {'name':'toy', 'data':{'enable':enable}})
	def deviceIsPlaying(self,devId):							return self.transfer_inner('device_is_playing', devId, {'name':'toy', 'data':{}})
	def deviceSetScreen(self,devId,state):             			return self.transfer_inner('device_set_screen', devId, {'name':'toy', 'data':{'state':state}})
	def devicePlayWechat(self,devId,url,remainCount=0):      	return self.transfer_inner('device_play_wechat', devId, {'name':'toy', 'data':{'url':url, 'remainCount':remainCount}})
	def deviceSpeechNone(self,devId):							return self.transfer_inner('device_speech_none', devId, {'name':'toy', 'data':{}})
	def deviceMessageIn(self,devId):							return self.transfer_inner('device_message_in', devId, {'name':'toy', 'data':{}})
	def deviceSetWechatPrompt(self,devId,index):				return self.transfer_inner('device_set_wechat_prompt', devId, {'name':'toy', 'data':{'index':index}})
	def deviceSetLpPrompt(self,devId,index):					return self.transfer_inner('device_set_lp_prompt', devId, {'name':'toy', 'data':{'index':index}})
	def deviceLikeNull(self,devId):								return self.transfer_inner('device_like_null', devId, {'name':'toy', 'data':{}})
	def deviceWelcomeNote(self,devId,url):						return self.transfer_inner('device_welcome_note', devId, {'name':'toy', 'data':{'url':url}})
	def devicePowerOff(self,devId):             				return self.transfer_inner('device_poweroff', devId, {'name':'toy','data':{'duration':0,'poweroff':1}})
	def deviceLock(self,devId):             					return self.transfer_inner('device_lock', devId, {'name':'toy','data':{}})
	def deviceUnlock(self,devId):             					return self.transfer_inner('device_unlock', devId, {'name':'toy','data':{}})
	def deviceCleanLock(self,devId):             				return self.transfer_inner('device_clean_lock', devId, {'name':'toy','data':{}})
	def deviceSetBrightness(self,devId,brightness):				return self.transfer_inner('device_set_brightness', devId, {'name':'toy', 'data':{'brightness':brightness}})
	def deviceSound(self,devId,volume):							return self.transfer_inner('device_sound', devId, {'name':'toy', 'data':{'volume':volume}})
	def deviceTrigerIntent(self,devId,intent,slots):			return self.transfer_inner('device_triger_intent', devId, {'name':'toy', 'data':{'intent':intent,'slots':slots}})

	def testPlayStart(self,devId,url,src_flag):              	return self.transfer(devId, {'action':'play_start','url':url,'src_flag':src_flag})
	def testPlayStop(self,devId):                            	return self.transfer(devId, {'action':'play_stop'})
	def testPlayPause(self,devId):                           	return self.transfer(devId, {'action':'play_pause'})
	def testPlayResume(self,devId):                          	return self.transfer(devId, {'action':'play_resume'})
	def testPlaySeek(self,devId,progress):                   	return self.transfer(devId, {'action':'play_seek', 'progress':progress})
	def dumpAllTaskStatus(self,devId):                       	return self.transfer(devId, {'action':'dump_all_task_status'})
	def showCpu(self,devId,meausre_time=5000):               	return self.transfer(devId, {'action':'show_cpu', 'meausre_time':str(meausre_time)})
	def testGroup(self,devId,group):                         	return self.transfer(devId, {'action':'test_group','group':group})
	def testHttpDownloadStart(self,devId,url,range=True):    	return self.transfer(devId, {'action':'http_download_start','url':url,'range_enable':1 if range else 0})
	def testHttpDownloadStop(self,devId):                    	return self.transfer(devId, {'action':'http_download_stop'})
	def testHttpDownloadPause(self,devId):                   	return self.transfer(devId, {'action':'http_download_pause'})
	def testHttpDownloadResume(self,devId):                  	return self.transfer(devId, {'action':'http_download_resume'})
	def testPcmRecorderStart(self,devId,path,sample,chann):  	return self.transfer(devId, {'action':'pcm_recorder_start','path':path,'sample_rate':sample,'channels':chann})
	def testPcmRecorderStop(self,devId):                     	return self.transfer(devId, {'action':'pcm_recorder_stop'})
	def testPcmPlayerStart(self,devId,path,sample,chann):    	return self.transfer(devId, {'action':'pcm_player_start','path':path,'sample_rate':sample,'channels':chann})
	def testPcmPlayerStop(self,devId):                       	return self.transfer(devId, {'action':'pcm_player_stop'})
	def memTraceStart(self,devId):               				return self.transfer(devId, {'action':'mem_trace_start'})
	def memTraceStop(self,devId):               				return self.transfer(devId, {'action':'mem_trace_stop'})
	def recorderBypassEnable(self,devId,_tp,host,port,preproc): return self.transfer(devId, {'action':'com_recorder_bypass_enable','type':_tp,'host':host,'port':port,'preproc':preproc})
	def recorderBypassDisable(self,devId):    					return self.transfer(devId, {'action':'com_recorder_bypass_disable'})

if __name__=="__main__":
	#mqtt = MyMqtt('00000000400120181120704f080000b0', 'gh_5e9c85479d21')
	#mqtt = MyMqtt('00000000400120181120704f080015df', 'gh_5e9c85479d21')
	#mqtt = MyMqtt('00000000400120181120704f080000b0', 'gh_b47c524e9c3a')
	mqtt = MyMqtt('00000000400120181120704f08001ccc', 'gh_5e9c85479d21')
	mqtt.start()
	devId = mqtt.devId
	
	#mqtt.testPlayStop(devId)
	#mqtt.devicePlay(devId, 'http://47.98.36.22/432506345.mp3')
	#mqtt.devicePlay(devId, 'http://47.98.36.22/186154.mp3')
	mqtt.devicePlay(devId, 'http://47.98.36.22/22472149.mp3')
	#mqtt.devicePlay(devId, 'http://47.98.45.59/28508590.mp3')
	#mqtt.devicePlay(devId, 'http://192.168.60.7:8000/music/mp3_test/1khz.mp3')
	#mqtt.devicePlay(devId, 'http://image.kaolafm.net/mz/mp3_32/201803/a4cf6694-dc1e-4514-8beb-4a39ee9652f8.mp3')
	#mqtt.deviceSeekProgress(devId, 50)
	#mqtt.deviceEnableProgress(devId, 0)
	#mqtt.deviceSetBrightness(devId, 30)
	#mqtt.deviceLock(devId)
	#mqtt.deviceUnlock(devId)

	#mqtt.testPlayStart(devId, 'CountDown.mp3', AUDIO_SRC_FLAG_PROMPT)
	#mqtt.testPlayStart(devId, 'SD:/CountDown.mp3', AUDIO_SRC_FLAG_LOCAL)
	#mqtt.deviceUpgrade(devId, 'http://192.168.60.7:8000/0004_001_v011_V0.1.1.bin', 'V1.1.1')
	mqtt.showCpu(devId)
	#mqtt.devicePowerOff(devId)

	#mqtt.testPcmRecorderStart(devId, "SD:/orginal.pcm", 32000, 2)
	#mqtt.testPcmRecorderStop(devId)
	#mqtt.memTraceStart(devId)
	#mqtt.memTraceStop(devId)
	#mqtt.recorderBypassEnable(devId, VOICE_FILE_TYPE_DUI, "192.168.60.7", 8003, True)
	time.sleep(1)
	#mqtt.recorderBypassDisable(devId)
	#time.sleep(100000)