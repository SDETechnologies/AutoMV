import ffmpeg
import librosa
import random
import math
import os
from moviepy.editor import *
from hitfinder import *
from dotenv import load_dotenv
load_dotenv()

DOWNLOAD_FOLDER = r"C:\Entertainment\nsfw\webms"

def getVideoFiles(videoDir):
    fileList = []
    dirFiles = os.listdir(videoDir)
    for tempFile in dirFiles:
        if '.webm' in tempFile:
            fileList.append(os.path.join(videoDir,tempFile))
    
    return fileList

def getSecondsPerCut(bpm, beatsPerCut):
    bps = bpm / 60
    secondsPerCut = (1 / bps) * beatsPerCut
    return secondsPerCut

def getCutTimesFromBPM(bpm, beatsPerCut, songFile):
    cutTimes = []
    bps = bpm / 60
    secondsPerCut = (1 / bps) * beatsPerCut
    print('secondsPerCut: ', secondsPerCut)

    songDuration = librosa.get_duration(filename=songFile)
    print('songDuration: ', songDuration)

    numCuts = math.floor(songDuration / secondsPerCut)

    print('numCuts: ', numCuts)

    for i in range(0, numCuts):
        cutTime = (i + 1) * secondsPerCut
        cutTimes.append(cutTime)
    return cutTimes

def timeNumberToString(timeNumber):
    if len(str(timeNumber)) == 1:
        timeString = '0' + str(timeNumber)
    else:
        timeString = str(timeNumber)
    return timeString

def secondsToTimestamp(seconds):
    # print('secondsToTimestamp(seconds=',seconds,')')
    remainingSeconds = seconds
    # print('remainingSeconds: ', remainingSeconds)
    hours = math.floor(seconds / 60 / 60)
    remainingSeconds -= (hours * 60 * 60)
    # print('remainingSeconds: ', remainingSeconds)
    minutes = math.floor(remainingSeconds / 60)
    remainingSeconds -= (minutes * 60)
    # print('remainingSeconds: ', remainingSeconds)
    seconds = math.floor(remainingSeconds)
    remainingSeconds -= seconds
    # print('remainingSeconds: ', remainingSeconds)
    milliseconds = round(remainingSeconds,3)
    # print('hours: ', hours, ', minutes: ', minutes, ', seconds: ', seconds, ', milliseconds: ', milliseconds)
    hourString = str(hours)
    minuteString = str(minutes)
    
    timestamp = timeNumberToString(hours) + ':' + timeNumberToString(minutes) + ':' + timeNumberToString(seconds) + '.' + str(milliseconds).replace('0.','')
    return timestamp

def getRandomVideoFile(videoFiles):
    return videoFiles[random.randint(0,len(videoFiles) - 1)]

def combineVideos(videoFiles, cutTimes, songFile, outputPath, bpm, beatsPerCut):
    videoInputList = []
    secondsPerCut = getSecondsPerCut(bpm, beatsPerCut)
    print('len(videoFiles): ', len(videoFiles), ', len(cutTimes): ', len(cutTimes))
    songDuration = librosa.get_duration(filename=songFile)
    for i in range(0, len(cutTimes)):
        randomVideoFile = getRandomVideoFile(videoFiles)
        if i == 0:
            startTimestamp = secondsToTimestamp(0)
        else:
            startTimestamp = secondsToTimestamp(cutTimes[i])
        if i == len(cutTimes) - 1:
            endTimestamp = secondsToTimestamp(songDuration)
        else:
            endTimestamp = secondsToTimestamp(cutTimes[i + 1])
        # durationTimeStamp = secondsToTimestamp()
        # videoInput = ffmpeg.input(randomVideoFile)
        # print('tempCutTime: ', tempCutTime, ', tempTimestamp', tempTimestamp)
        print(i, ' - startTimestamp: ', startTimestamp, ', endTimestamp: ', endTimestamp)
        videoInput = ffmpeg.input(randomVideoFile).trim(start=0,duration=secondsPerCut)
        videoInputList.append(videoInput)
    for i in range(0, len(videoInputList)):
        tempVideoInput = videoInputList[i]
        if i == 0:
            out = tempVideoInput.output(outputPath).run()
        else:
            outputStream = ffmpeg.input(outputPath)
            ffmpeg.concat(outputStream, tempVideoInput).output(outputPath).run()
    outputStream = ffmpeg.input(outputPath)
    audio = ffmpeg.input(songFile)
    ffmpeg.concat(out, audio).output(outputStream,audio).run()

def combineVideos2(videoFiles, audioFile, outputPath, bpm=130, beatsPerClip=4):
    cutTimes = prepareAudio(audioFile)['onset_data']['low']
    print('len(cutTimes): ', len(cutTimes))
    # cutTimes = getCutTimesFromBPM(bpm, beatsPerClip, audioFile)
    audioClip = AudioFileClip(audioFile)
    videoInputList = []
    for i in range(0, len(cutTimes) - 1):
        if i % 10 == 0:
            print('i: ', i)
        randomVideoFile = getRandomVideoFile(videoFiles)
        if i == 0:
            videoDuration = cutTimes[0]
        else:
            videoDuration = cutTimes[i + 1] - cutTimes[i]
        # randomVideoClip = VideoFileClip(randomVideoFile, target_resolution=(720,1280))
        randomVideoClip = VideoFileClip(randomVideoFile, target_resolution=(720,1280))
        w,h = randomVideoClip.size 
        # randomVideoClip = randomVideoClip.resize(w,h)
        
        randomVideoClip = randomVideoClip.set_duration(videoDuration)#.resize(1280,720)
        videoInputList.append(randomVideoClip)
    wholeVideo = concatenate_videoclips(videoInputList).set_audio(audioClip).set_duration(cutTimes[len(cutTimes) - 2])
    wholeVideo.write_videofile(outputPath)

startTime = 0

def z_t(t):
    referenceTime = t - startTime
    # print('t - startTime: ', referenceTime)
    if 0 < t - startTime < 0.1:
        z = 2.5 * (t - startTime) + 1
        print('zooming in. z(',t - startTime,') = ', z)
        return  z# Zoom-in.
    elif 0.1 <= t - startTime <= 0.2:
        z = (-1 *  (2.5 * (t - startTime))) + 1.5
        # z = 1
        print('zooming in. z(',t - startTime,') = ', z)
        return z  # Stay.
    else: # 6 < t
        z = 1
        # print('staying. z(',t-startTime,') = 1')
        return z  # Zoom-out.

def combineVideos3(videoFiles, audioFile, outputPath, batchSize = 100, bpm=130, beatsPerClip=4):
    cutTimes = prepareAudio(audioFile)['onset_data']['low']
    print('len(cutTimes): ', len(cutTimes))
    # cutTimes = getCutTimesFromBPM(bpm, beatsPerClip, audioFile)
    batchFileList = []
    numBatches = math.ceil(len(cutTimes) / batchSize)
    for j in range(1, numBatches + 1):
        print('batch ', str(j), ' starting')
        batchInputList = []
        startCutTime = batchSize * (j - 1)
        endCutTime = batchSize * (j)
        cutTimesLeft = len(cutTimes) - startCutTime
        if cutTimesLeft < batchSize:
            endCutTime = startCutTime + cutTimesLeft - 1
            print('new endCutTime: ', endCutTime)
        print('startCutTime: ', startCutTime, ', endCutTime: ', endCutTime)
        i = startCutTime
        while i <= endCutTime and i >= startCutTime and i < len(cutTimes) - 1:
            startTime = cutTimes[i]
            print('startTime: ', startTime)
            # print('i: ', i)
            if i % 10 == 0:
                print('batch ', j, ', cutTimeIndex: ', i)
            randomVideoFile = getRandomVideoFile(videoFiles)
            if i == 0:
                videoDuration = cutTimes[0]
            else:
                videoDuration = cutTimes[i + 1] - cutTimes[i]
            tempRandomVideoClip = VideoFileClip(randomVideoFile)
            w,h = tempRandomVideoClip.size
            scaleDimensions = scaleToFull(w,h)
            # print('scaleDimensions: ', scaleDimensions)
            scaleWidth = scaleDimensions['width']
            scaleHeight = scaleDimensions['height']
            # randomVideoClip = VideoFileClip(randomVideoFile,target_resolution=(scaleHeight,scaleWidth))
            randomVideoClip = VideoFileClip(randomVideoFile,target_resolution=(1080,1920))
            randomClipDuration = randomVideoClip.duration
            randomStart = random.randint(0, round(randomClipDuration))
            print('random clip start: ', randomStart, ', randomClipDuration: ', randomClipDuration)
            z = lambda t : ((-t*t*2) + 2*t)

            # randomVideoClip = randomVideoClip.resize(z_t) temporarily

            randomVideoClip = randomVideoClip.set_start(randomStart)
            randomVideoClip = randomVideoClip.set_duration(videoDuration)#.set_position((0,0), relative=True)
            batchInputList.append(randomVideoClip)
            i += 1
        # print('batchInputList for batch ', str(j), ': ', batchInputList)

        audioClip = AudioFileClip(audioFile).subclip(cutTimes[startCutTime], cutTimes[endCutTime])
        batchVideoDuration = cutTimes[endCutTime] - cutTimes[startCutTime]
        batchClip = concatenate_videoclips(batchInputList).set_audio(audioClip).set_duration(batchVideoDuration)
        batchClipWholeFileName = os.path.basename(outputPath)
        print('batchClipWholeFileName: ', batchClipWholeFileName)
        # batchClipDir = outputPath.replace(batchClipWholeFileName,'')
        batchClipDir = os.path.dirname(outputPath)
        print('batchClipDir: ', batchClipDir)
        batchClipFileName = batchClipWholeFileName.split('.')[0]
        fileType = batchClipWholeFileName.split('.')[1]
        batchClipFilePath = os.path.join(batchClipDir, batchClipFileName + '_' + str(j) + '.' + fileType)
        print('batchClipFilePath: ', batchClipFilePath)
        batchClip.write_videofile(batchClipFilePath)
        batchFileInfo = {
            'path': batchClipFilePath,
            'duration': batchVideoDuration
        }
        batchFileList.append(batchFileInfo)

        for videoFile in batchInputList:
            videoFile.close()

    # if len(batchFileList)
    print('batchFileList: ', batchFileList)
    batchVideoFiles = []
    for batchFileInfo in batchFileList:
        print('batchFileInfo: ', batchFileInfo)
        batchFilePath = batchFileInfo['path']
        batchFileDuration = batchFileInfo['duration']
        batchVideoFile = VideoFileClip(batchFilePath)
        batchVideoFile = batchVideoFile.set_duration(batchFileDuration)
        batchVideoFiles.append(batchVideoFile)
    songDuration = librosa.get_duration(filename=audioFile)
    # print('songDuration: ', songDuration)
    try:
        wholeClip = concatenate_videoclips(batchVideoFiles).set_duration(songDuration - 2)
        wholeClip.write_videofile(outputPath)
    except IndexError:
        print('escaping index error')
    for batchFileInfo in batchFileList:
        batchFilePath = batchFileInfo['path']
        print('removing ', batchFilePath)
        # os.remove(batchFilePath)
            


    # for i in range(0, len(cutTimes) - 1):
    #     if i % 10 == 0:
    #         print('i: ', i)
    #     randomVideoFile = getRandomVideoFile(videoFiles)
    #     if i == 0:
    #         videoDuration = cutTimes[0]
    #     else:
    #         videoDuration = cutTimes[i + 1] - cutTimes[i]
    #     # randomVideoClip = VideoFileClip(randomVideoFile, target_resolution=(720,1280))
    #     randomVideoClip = VideoFileClip(randomVideoFile, target_resolution=(720,1280))
    #     w,h = randomVideoClip.size 
    #     # randomVideoClip = randomVideoClip.resize(w,h)
        
    #     randomVideoClip = randomVideoClip.set_duration(videoDuration)#.resize(1280,720)
    #     videoInputList.append(randomVideoClip)
    # wholeVideo = concatenate_videoclips(videoInputList).set_audio(audioClip).set_duration(cutTimes[len(cutTimes) - 2])
    # wholeVideo.write_videofile(outputPath)

def videoAlreadyDownloaded(videoSrc, downloadFolder):
    videoFileName = os.path.basename(videoSrc)
    downloadFolderFiles = os.listdir(downloadFolder)
    for downloadFolderFile in downloadFolderFiles:
        if '.webm' in downloadFolderFile:
            if videoFileName == downloadFolderFile:
                return True
    return False


def scaleToFull(width, height):
    if width > height:
        scale = 1920 / width
        return {
            'width': 1920,
            'height': int(height * scale)
        }
    else:
        scale = 1080 / height
        return {
            'width': int(width * scale),
            'height': 1080
        }

def addBounce(wholeVideoFile, audioFile, zoomAmount = 1.25):
    bounceTimes = prepareAudio(audioFile)['onset_data']['low']
    print('len(bounceTimes): ', len(bounceTimes))
    wholeClip = VideoFileClip(wholeVideoFile)
    wholeClipDuration = wholeClip.duration
    print('wholeClipDuration: ', wholeClipDuration)
    for i in range(0, len(bounceTimes)):
        if i % 10 == 0:
            print('current index: ', i)
        bounceTime = bounceTimes[i]
        if i != len(bounceTimes) - 1 and bounceTimes[i + 1] >= wholeClipDuration:
            break
        startTime = bounceTime
        wholeClip = wholeClip.resize(z_t)
    fileName = os.path.basename(wholeVideoFile)
    outputDir = wholeVideoFile.replace(fileName,'')
    baseFileName = fileName.split('.')[0]
    fileType =  fileName.split('.')[1]
    newFileName = baseFileName + '_withbounce' + '.' + fileType
    outputPath = os.path.join(outputDir, newFileName)
    wholeClip.write_videofile(outputPath)

def blurVideo():
    print('')

def testCombine(video1, video2, outputPath):
    # video1StartFrame = 0
    # video1EndFrame = video1['duration'] * fps
    # video2StartFrame = video1EndFrame
    # video2EndFrame = video2StartFrame + (video2['duration'] * fps)
    # videoInput1 = ffmpeg.input(video1['path']).trim(duration=3)
    # videoInput2 = ffmpeg.input(video2['path']).trim(duration=3)
    # audioInput1 = ffmpeg.input('Audio/Music/Sewerslvt - Lexapro Delirium.mp3').concat(videoInput1).output(outputPath).run()
    # # ffmpeg.concat(videoInput1, videoInput2).output(outputPath).run()
    # # ffmpeg.input(videoPath1).input(videoPath2).output(outputPath).run()
    # # ffmpeg.output(audioInput1.audio, videoInput1.video, outputPath).run()
    # ffmpeg.concat(videoInput2,videoInput1).output(outputPath).run()
    # # concatVideoAudio = ffmpeg.concat(concatVideo, audioInput1.audio).output(outputPath).run()
    # # # ffmpeg.output(outputPath).run()

    videoClip1 = VideoFileClip(video1['path'])
    videoClip2 = VideoFileClip(video2['path'])
    audioClip1 = AudioFileClip('Audio/Music/Sewerslvt - Lexapro Delirium.mp3').subclip(0,video1['duration'] + video2['duration'])
    final = concatenate_videoclips([videoClip1, videoClip2]).set_audio(audioClip1).set_fps(30)
    # final = CompositeVideoClip([videoClipsTogether, audioClip1])
    final.write_videofile(outputPath,fps=30)

testDir = '/home/eliot/Entertainment/nsfw/webms'
# testDir = 'C:/Entertainment/nsfw/webms'
testDir = '/home/eliot/ArchServer/HDD1/Entertainment/nsfw/webms'
testSongFile = '/home/eliot/Music/Downloads/Sewerslvt - Lexapro Delirium.mp3'
testSongFile = '/home/eliot/Music/Downloads/Folamour - When U Came into My Life.mp3'
testSongFile = '/home/eliot/Music/Downloads/Technotronic, Felly - Pump Up The Jam - Edit.mp3'
testSongFile = "/home/eliot/Music/Downloads/blood pup - Want me like!.mp3"
testOutputPath = '/home/eliot/Entertainment/nsfw/Edits/AutoMV/Technotronic, Felly - Pump Up The Jam - Edit2.mp4'
testOutputPath = "/home/eliot/Entertainment/nsfw/Edits/AutoMV/100 gecs - where’s my head at.mp4"
testOutputPath = "/home/eliot/ArchServer/HDD1/Entertainment/nsfw/Edits/AutoMV/wantmelike1.mp4"
testBPM = 130
files = getVideoFiles(testDir)
# for file in files:
#     print(file)
# cutTimes = getCutTimesFromBPM(testBPM, 4, testSongFile)
# print('cutTimes: ', cutTimes)

# timestamp = secondsToTimestamp(435.6923)
# print('timestamp in HH:MM:SS.xxx: ', timestamp)

# combineVideos(files, cutTimes, testSongFile, testOutputPath, testBPM, 4)

testVideoPath1 = os.path.join(testDir,'1697937585833611.webm')
testVideoPath2 = os.path.join(testDir,'1698416705000359.webm')

testVideo1 = {
    'path': os.path.join(testDir,'1697937585833611.webm'),
    'duration': 15
}

testVideo2 = {
    'path': os.path.join(testDir,'1698416705000359.webm'),
    'duration': 16
}

print(testVideoPath1, ', ', testVideoPath2)


# # testCombine(testVideo1, testVideo2, 'test_combine.mp4')

# # combineVideos2(files, testSongFile, testOutputPath)

# # hitData = prepareAudio(testSongFile)
# # print('hitData: ', hitData)

combineVideos3(files, testSongFile, testOutputPath, 50)

# # downloaded = videoAlreadyDownloaded('https://is2.4chan.org/gif/1698704730121802.webm',DOWNLOAD_FOLDER)
# # print(downloaded)

# wholeFile1 = 'C:/Entertainment/nsfw/Edits/Record Club - Morning Dance_1.mp4'
# addBounce(wholeFile1, testSongFile)
