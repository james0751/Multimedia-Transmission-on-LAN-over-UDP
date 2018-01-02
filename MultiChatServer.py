import socket
import threading
import struct
import cv2
import time
import pickle
import pyaudio
import queue
import os

class MultiChatServer(threading.Thread):
    def __init__(self,address,dataque):
        threading.Thread.__init__(self)
        self.address = address
        self.connect = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connect.bind(self.address)
        self.databuf = b''
        self.datalenbuf = 0
        self.dataque = dataque

    def run(self):
        print ('server on ...')
        while True:
            begin = time.time()
            data, addr = self.connect.recvfrom(204800)
            isflag, adatalen, datalen = struct.unpack('3sII', data[:12])
            adatalenstruct = struct.pack("I",adatalen)
            try:
                flag = isflag.decode('utf-8')
            except:
                flag = ''
                pass
            if flag == 'BOF':
                tempbuf = data[12:]
                self.databuf += tempbuf
                if len(self.databuf) != datalen:
                    if self.datalenbuf == 0 or self.datalenbuf == datalen:
                        self.datalenbuf = datalen
                        continue
                    else:
                        self.databuf = b''
                        self.databuf += tempbuf
                        self.datalenbuf = datalen
                        continue
                data = self.databuf
                self.databuf = b''
                datatemp = adatalenstruct + data
                self.dataque.put(datatemp)
            elif flag == 'NOF':
                self.dataque.put(adatalenstruct + data[12:])
            end = time.time()

class AudioVideoSplit(threading.Thread):

    def __init__(self,dataque,audiodataque,videodataque):
        threading.Thread.__init__(self)
        self.dataque = dataque
        self.audiodataque = audiodataque
        self.videodataque = videodataque

    def run(self):
        while True:
            datatemp = self.dataque.get()
            adatalen = struct.unpack("I",datatemp[:4])[0]
            data = datatemp[4:]
            if data[:2] != b'\x80\x03':
                continue
            adata = data[:adatalen]
            vdata = data[adatalen:]
            if  vdata[4:6] != b'\x80\x03':
                logfile = open("log.txt", 'a+')
                print("%s  VideoFlowError: VideoFlowHead is: %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), str(vdata[4:6])),file=logfile)
                logfile.close()
                continue
            self.audiodataque.put(adata)
            self.videodataque.put(vdata)

class AudioPlayer(threading.Thread):

    def __init__(self,audiodataque):
        threading.Thread.__init__(self)
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.RECORD_SECONDS = 2
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, output=True,
                                      frames_per_buffer=self.CHUNK)
        self.audiodataque = audiodataque

    def run(self):
        while True:
            audiopickledata = self.audiodataque.get()
            audioframes = pickle.loads(audiopickledata)
            for frame in audioframes:
                self.stream.write(frame, self.CHUNK)

class VideoPlayer(threading.Thread):

    def __init__(self,videodataque):
        threading.Thread.__init__(self)
        self.videodataque = videodataque
        self.playbackrate = 0

    def run(self):
        while True:
            videodataquesize = self.videodataque.qsize()
            if videodataquesize > 1:
                self.playbackrate = 0
            videoframesdata = self.videodataque.get()
            videoframestimespace = round(struct.unpack('f', videoframesdata[:4])[0],3)
            videoframes = pickle.loads(videoframesdata[4:])
            videoframeslen = len(videoframes)
            begin = time.time()
            for videoframe in videoframes:
                try:
                    image = cv2.imdecode(videoframe, 1)
                    cv2.imshow('client', image)
                    time.sleep(self.playbackrate)
                    if cv2.waitKey(1) & 0xFF == 27:
                        cv2.destroyWindow('client')
                        break
                except Exception as e:
                    logfile = open("log.txt", 'a+')
                    print("%s  Output_Error: %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), e),
                          file=logfile)
                    cv2.destroyWindow('server')
                    logfile.close()
                    continue
            end = time.time()
            runtimelength = round(end - begin,3)
            if self.playbackrate == 0:
                self.playbackrate = (videoframestimespace - runtimelength) / videoframeslen
                self.playbackrate = round(self.playbackrate,3)
            if videodataquesize <= 1 and self.playbackrate != 0 and videoframestimespace +0.015< runtimelength:
                self.playbackrate -= 0.003
            if videodataquesize <= 1 and self.playbackrate != 0 and videoframestimespace - runtimelength >= 0.03:
                if (videoframestimespace - runtimelength) >= videoframestimespace / 4:
                    self.playbackrate = (videoframestimespace - runtimelength) / videoframeslen
                    self.playbackrate = round(self.playbackrate, 3)
                else:
                    self.playbackrate += 0.001

def main():
    address = ('127.0.0.1', 52100)
    dataque = queue.Queue()
    audiodataque = queue.Queue()
    videodataque = queue.Queue()

    multichatserver = MultiChatServer(address,dataque)
    multichatserver.start()

    audiovideosplit = AudioVideoSplit(dataque,audiodataque,videodataque)
    audiovideosplit.start()

    audioplayer = AudioPlayer(audiodataque)
    audioplayer.start()
    videoplayer = VideoPlayer(videodataque)
    videoplayer.start()

if __name__ == "__main__":
    main()
