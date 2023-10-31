import requests
import time
import os

from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import math
import librosa

import librosa.display
import librosa.util
import librosa.onset

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import numpy as np
from scipy.signal import butter,filtfilt
import openpyxl
import syllables
import json
import spotdl
import ffmpeg
import subprocess
from subprocess import Popen

import sys


def getFileName(filePath):
#    dashIndex = None
    i = len(filePath) - 1
    while i > 0:
        if filePath[i] == '/':
            return filePath[i+1:len(filePath)]
        i -= 1
    return None

def getBasePath(filePath):
#    dashIndex = None
    i = len(filePath) - 1
    while i > 0:
        if filePath[i] == '/':
            return filePath[0:i] + '/'
        i -= 1

def getSongPatterns(bpm, songSeconds, beatsPerPattern):
    songBeats = getSongBeats(bpm, songSeconds)
    # print('songBeats: ' + str(songBeats))
    songPatterns = math.floor(songBeats / beatsPerPattern)
    songPatterns = songBeats / beatsPerPattern
    return songPatterns

def getSongBeats(bpm, songSeconds):
    songMinutes = songSeconds / 60
    return bpm * songMinutes
    
    

    
    
def writeOnsetDataToFile(onsetData, fileName, sampleRate):
    with open(fileName, 'w') as f:
        for dataPoint in onsetData:
            f.write(str(dataPoint))
            f.write('\n')
    f.close()

def sortByTimeKey(val):
    return val[0]
    
def writeOnsetDataToFile2(onsetData, fileName, sampleRate):
    lowData = onsetData[0]
    midData = onsetData[1]
    combinedData = []
    for data in lowData:
        # combinedData.append(str(data) + ",low")
        # combinedData[0].append(float(data))
        # combinedData[1].append("low")
        combinedData.append((float(data), "low"))
    for data in midData:
        # combinedData.append(str(data) + ",mid")
        # combinedData[0].append(float(data))
        # combinedData[1].append("mid")
        combinedData.append((float(data), "mid"))
    combinedData.sort(key=sortByTimeKey)
    saveExtension = fileName[len(fileName) - 4:len(fileName)]
    baseFileName = fileName[0:len(fileName) - 4]
    lowFileName = baseFileName + "_low" + saveExtension
    midFileName = baseFileName + "_mid" + saveExtension
    combinedFileName = baseFileName + "_combined" + saveExtension
    print('baseFileName: ' + str(baseFileName))
    with open(lowFileName, 'w') as f:
        for dataPoint in lowData:
            f.write(str(dataPoint))
            f.write('\n')
    f.close()
    with open(midFileName, 'w') as f:
        for dataPoint in midData:
            f.write(str(dataPoint))
            f.write('\n')
    f.close()
    with open(combinedFileName, 'w') as f:
        for dataPoint in combinedData:
            f.write(str(dataPoint[0]) + "," + dataPoint[1])
            f.write('\n')
    f.close()
    return [lowFileName, midFileName, combinedFiledName]

    


def removeLowDataFromMid_(onsetData):
    lowData = onsetData[0]
    midData = onsetData[1]
    newMidData = []
    print(str(len(lowData)))
    print(str(len(midData)))
    for i in range(len(midData)):
        tempMidData = midData[i]
        inMidData = False
        # print('tempLowData: ' + str(tempLowData))
        # print('tempLowData2: ' + str(lowData[1]))
        for j in range(len(lowData)):
            tempLowData = lowData[j]
            
            # print('tempMidData: ' + str(tempMidData))
            if (tempMidData <= tempLowData + 0.75)  and (tempMidData >= tempLowData - 0.75):
                # print('removing ' + str(tempMidData) + ' from mid data')
                # midData.remove(j)
                # midData = np.delete(midData, tempMidData)
                # midData[0].remove(j)
                inMidData = True
                break
                # j -= 1
        if inMidData == False:
            newMidData.append(tempMidData)
    return [lowData, newMidData]

def getOnsetTimeValues(onsetData):
    newLowData = []
    newMidData = []
    combinedData = onsetData[0]
    oldLowData = combinedData[0]
    oldMidData = combinedData[1]
    for dataPoint in oldLowData:
        newLowData.append(dataPoint)
    for dataPoint in oldMidData:
        newMidData.append(dataPoint)
    return [newLowData, newMidData]
    
def removeLowDataFromMid(onsetData):
    timesData = onsetData[1]
    onsetData = onsetData[2]
    lowData = timesData[0][onsetData[0]]
    midData = timesData[1][onsetData[1]]
    newMidOnsetTimes = []
    for i in range(len(lowData)):
        tempLowData = lowData[i]
        print('tempLowData: ' + str(tempLowData))

def prepareAudio(songFilePath):
    fileName = getFileName(songFilePath)
    basePath = getBasePath(songFilePath)
    y, sr = librosa.load(songFilePath)
    y = librosa.to_mono(y)
    
    S_low = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmin=0, fmax=500)
    S_mid = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmin=200, fmax=3000)
    S_high = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmin=3000, fmax=10000)
    # S_voc = librosa.feature.melspectrogram(y=y_voc, sr=sr_voc, n_mels=128, fmin=0, fmax=5000)
    o_env_low = librosa.onset.onset_strength(y=y, sr=sr, detrend=True, S=S_low)
    o_env_mid = librosa.onset.onset_strength(y=y, sr=sr, detrend=True, S=S_mid)
    o_env_high = librosa.onset.onset_strength(y=y, sr=sr, detrend=True, S=S_high)
    # o_env_voc = librosa.onset.onset_strength(y=y_voc,sr=sr_voc, detrend=True)
    timesLow = librosa.times_like(o_env_low, sr=sr)
    timesMid = librosa.times_like(o_env_mid, sr=sr)
    timesHigh = librosa.times_like(o_env_high, sr=sr)
    # timesVoc = librosa.times_like(o_env_voc, sr=sr_voc)
    
    times = {
        'low': timesLow,
        'mid': timesMid,
        'high': timesHigh
    }
    
    onsetFramesLow = librosa.onset.onset_detect(y=y, onset_envelope=o_env_low, sr=sr, wait=sr*0.00005, delta = 0.15, backtrack=True)#, normalize=True)
    onsetFramesMid = librosa.onset.onset_detect(y=y, onset_envelope=o_env_mid, sr=sr, wait=sr*0.0005, delta = 0.15)
    onsetFramesHigh = librosa.onset.onset_detect(y=y, onset_envelope=o_env_mid, sr=sr, wait=sr*0.0005, delta = 0.15)
    # onsetFramesVoc = librosa.onset.onset_detect(y=y_voc, onset_envelope=o_env_voc, sr=sr_voc, wait=sr_voc*0.0000001, delta = 0.1, backtrack = True)
    onsetData = [timesLow[onsetFramesLow], timesMid[onsetFramesMid], timesHigh[onsetFramesHigh]]
    # onsetData = removeLowDataFromMid(onsetData)

    hitData = {
        'times': times,
        'onset_data': {
            'low': onsetData[0],
            'mid': onsetData[1],
            'high': onsetData[2]
        }
    }

    return hitData


