import socket
import threading
import struct
import cv2
import time
import os
import pickle
import numpy
import pyaudio
import queue

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
        while True:
            data, addr = self.connect.recvfrom(204800)
            isflag, adatalen, datalen = struct.unpack('3sII', data[:12])
            print(datalen)
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

class AudioVideoOutput(threading.Thread):
    def __init__(self,dataque):
        threading.Thread.__init__(self)
        self.dataque = dataque
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.RECORD_SECONDS = 0.3
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, output=True,
                                      frames_per_buffer=self.CHUNK)


    def run(self):
        while True:
            datatemp = self.dataque.get()
            adatalen = struct.unpack("I",datatemp[:4])[0]
            print (adatalen)
            data = datatemp[4:]
            adata = data[:adatalen]
            vdata = data[adatalen:]

            numpydata = pickle.loads(vdata)
            image = cv2.imdecode(numpydata, 1)
            cv2.imshow('server', image)
            if cv2.waitKey(1) & 0xFF == 27:
                cv2.destroyWindow('server')
                break

            frames = pickle.loads(adata)
            for frame in frames:
                self.stream.write(frame, self.CHUNK)

def main():
    address = ('127.0.0.1', 31500)
    dataque = queue.Queue()
    multichatserver = MultiChatServer(address,dataque)
    multichatserver.start()
    audiovideooutput = AudioVideoOutput(dataque)
    audiovideooutput.start()

if __name__ == "__main__":
    main()
