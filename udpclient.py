import socket
import threading
import struct
import cv2
import time
import pickle
import pyaudio
import os
import numpy

class MultiChatClient(threading.Thread):

    def __init__(self,address,audioclient,videoclient):
        threading.Thread.__init__(self)
        self.address = address
        self.audioclient = audioclient
        self.videoclient = videoclient
        self.connect = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        while True:
            audiodata = self.audioclient.collectordata()
            videodata = self.videoclient.collectordata()
            totaldata = audiodata + videodata
            totaldatalen = len(totaldata)
            audiodatalen = len(audiodata)
            print (audiodatalen)
            print(totaldatalen)
            if totaldatalen > 60000:
                flag = "BOF".encode('utf-8')
                for i in range(0, totaldatalen, 60000):
                    j = i + 60000
                    totaldataslicing = totaldata[i:j]
                    self.connect.sendto(struct.pack('3sII', flag, audiodatalen, totaldatalen) + totaldataslicing,
                                    self.address)
            else:
                flag ='NOF'.encode('utf-8')
                self.connect.sendto(struct.pack('3sII', flag, audiodatalen, totaldatalen) + totaldata, self.address)

class VideoClient():
    def __init__(self):
        self.resolution = (800, 600)
        self.img_quality = 100
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]
        self.camera = cv2.VideoCapture(0)

    def collectordata(self):
        time.sleep(0)  # 每秒采样次数
        (ret, frame) = self.camera.read()
        cv2.imshow('client', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            cv2.destroyWindow('client')
        frame = cv2.resize(frame, self.resolution)
        result, imgencode = cv2.imencode('.jpg', frame, self.encode_param)
        imgdata = pickle.dumps(imgencode)
        return imgdata

class AudioClient():
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.RECORD_SECONDS = 0.16
        self.audio =pyaudio.PyAudio()
        self.stream = None
        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True,
                                      frames_per_buffer=self.CHUNK)

    def collectordata(self):
        frames = []
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = self.stream.read(self.CHUNK)
            frames.append(data)
        audiodata = pickle.dumps(frames)
        return audiodata

def main():
    address = ('127.0.0.1', 31500)
    audioclient = AudioClient()
    videoclient = VideoClient()
    chatclient = MultiChatClient(address,audioclient,videoclient)
    chatclient.start()

if __name__ == "__main__":
    main()