import socket
import threading
import struct
import cv2
import time
import pickle
import pyaudio
import queue
import os

class MultiChatClient(threading.Thread):

    def __init__(self,address,audiodataque,videodataque):
        threading.Thread.__init__(self)
        self.address = address
        self.connect = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audiodataque = audiodataque
        self.videodataque = videodataque

    def run(self):
        print('client on ...')
        while True:
            videodata = self.videodataque.get()
            audiodata = self.audiodataque.get()
            totaldata = audiodata + videodata
            totaldatalen = len(totaldata)
            audiodatalen = len(audiodata)
            if totaldatalen > 60000:
                flag = "BOF".encode('utf-8')
                for i in range(0, totaldatalen, 60000):
                    j = i + 60000
                    totaldataslicing = totaldata[i:j]
                    self.connect.sendto(struct.pack('3sII', flag, audiodatalen, totaldatalen) + totaldataslicing,
                                            self.address)
            else:
                flag = 'NOF'.encode('utf-8')
                self.connect.sendto(struct.pack('3sII', flag, audiodatalen, totaldatalen) + totaldata, self.address)


class VideoCollector(threading.Thread):

    def __init__(self,imgquality,resolution,videoframerate,videodataque,judgeque):
        threading.Thread.__init__(self)
        self.resolution = resolution
        self.img_quality = imgquality
        self.videoframerate = videoframerate
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]
        self.videodataque = videodataque
        self.judgeque = judgeque
        self.camera = cv2.VideoCapture(0)

    def run(self):
        self.collectordata()

    def collectordata(self):
        while True:
            videoframes = []
            starttime = time.time()
            timespace = starttime + 0.2 
            while True:
                time.sleep(self.videoframerate) 
                (ret, frame) = self.camera.read()
                frame = cv2.resize(frame, self.resolution)
                result, imgencode = cv2.imencode('.jpg', frame, self.encode_param)
                videoframes.append(imgencode)
                endtime = time.time()
                if endtime >= timespace:
                    runtime = endtime - starttime
                    videodatapacket = pickle.dumps(videoframes)
                    self.videodataque.put(struct.pack('f',runtime) + videodatapacket)
                    self.judgeque.put(True)
                    break

class AudioCollector(threading.Thread):
    def __init__(self,audiodataque,judgeque):
        threading.Thread.__init__(self)
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.RECORD_SECONDS = 2 
        self.audio =pyaudio.PyAudio()
        self.stream = None
        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True,
                                      frames_per_buffer=self.CHUNK)
        self.judgeque = judgeque
        self.audiodataque = audiodataque

    def run(self):
        while True:
            self.collectordata()

    def collectordata(self):
        frames = []
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = self.stream.read(self.CHUNK)
            frames.append(data)
            try:
                flag = self.judgeque.get(block=False)
            except:
                flag = False
                pass
            if flag == True:
                break
        audiodatapacket = pickle.dumps(frames)
        self.audiodataque.put(audiodatapacket)

def main():
    address = ('127.0.0.1', 52100)
    imgquality = 50
    resolution = (640,480)
    videoframerate = 0.04
    judgeque = queue.Queue(maxsize=1)
    audiodataque = queue.Queue(maxsize=1)
    videodataque = queue.Queue(maxsize=1)
    audiocollector = AudioCollector(audiodataque,judgeque)
    videocollector = VideoCollector(imgquality,resolution,videoframerate,videodataque,judgeque)
    chatclient = MultiChatClient(address, audiodataque,videodataque)
    audiocollector.start()
    videocollector.start()
    chatclient.start()

if __name__ == "__main__":
    main()
