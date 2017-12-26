import socket
import threading
import struct
import cv2
import time
import pickle
import pyaudio
import queue
import time
import os
import numpy

class MultiChatClient(threading.Thread):

    def __init__(self,address,audiodataque,videodataque):
        threading.Thread.__init__(self)
        self.address = address
        self.connect = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audiodataque = audiodataque
        self.videodataque = videodataque

    def run(self):
        while True:
            audiodata = self.audiodataque.get()
            while self.audiodataque.empty() is not True:
                audiodata += self.audiodataque.get()
            videodata = self.videodataque.get()
            while self.videodataque.empty() is not True:
                videodata += self.videodataque.get()
            numpydata = pickle.loads(videodata)
            image = cv2.imdecode(numpydata, 1)
            cv2.imshow('client', image)
            if cv2.waitKey(1) & 0xFF == 27:
                cv2.destroyWindow('client')
            totaldata = audiodata + videodata
            totaldatalen = len(totaldata)
            audiodatalen = len(audiodata)
            print ('发送一次UDP数据包')
            print ('音频数据长度: '+str(audiodatalen))
            print ("视频数据长度: "+str(len(videodata)))
            print ("音视频总数据长度: " +str(totaldatalen))
            if totaldatalen > 60000:
                flag = "BOF".encode('utf-8')
                for i in range(0, totaldatalen, 60000):
                    j = i + 60000
                    totaldataslicing = totaldata[i:j]
                    self.connect.sendto(struct.pack('3sII', flag, audiodatalen, totaldatalen) + totaldataslicing,
                                    self.address)
                    print ('发送数据包分片长度: '+ str(len(totaldataslicing)))
            else:
                flag ='NOF'.encode('utf-8')
                self.connect.sendto(struct.pack('3sII', flag, audiodatalen, totaldatalen) + totaldata, self.address)

class VideoClient(threading.Thread):
    def __init__(self,videodataque):
        threading.Thread.__init__(self)
        self.resolution = (800, 600)
        self.img_quality = 80
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]
        self.videodataque = videodataque
        self.camera = cv2.VideoCapture(0)
    def run(self):
        self.collectordata()
    def collectordata(self):
        while True:
            time.sleep(0)  # 视频每秒采样次数
            (ret, frame) = self.camera.read()
            frame = cv2.resize(frame, self.resolution)
            result, imgencode = cv2.imencode('.jpg', frame, self.encode_param)
            imgdata = pickle.dumps(imgencode)
            #return imgdata
            self.videodataque.put(imgdata)
            print('视频数据进入队列')

class AudioClient(threading.Thread):
    def __init__(self,audiodataque):
        threading.Thread.__init__(self)
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.RECORD_SECONDS = 0.3
        self.audio =pyaudio.PyAudio()
        self.stream = None
        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True,
                                      frames_per_buffer=self.CHUNK)
        self.audiodataque = audiodataque
    def run(self):
        while True:
            self.collectordata()

    def collectordata(self):
        frames = []
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = self.stream.read(self.CHUNK)
            frames.append(data)
        audiodata = pickle.dumps(frames)
        #return audiodata
        self.audiodataque.put(audiodata)
        print('语音数据进入队列')

def main():
    videodataque = queue.Queue()
    audiodataque = queue.Queue()

    address = ('127.0.0.1', 31500)
    audioclient = AudioClient(audiodataque)
    videoclient = VideoClient(videodataque)
    audioclient.start()
    videoclient.start()
    chatclient = MultiChatClient(address, audiodataque,videodataque)
    chatclient.start()


if __name__ == "__main__":
    main()