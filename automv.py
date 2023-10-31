import ffmpeg
import librosa
import random
import math
import os
from moviepy.editor import *
from hitfinder import *

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

def combineVideos3(videoFiles, audioFile, outputPath, batchSize = 200, bpm=130, beatsPerClip=4):
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
            randomVideoClip = VideoFileClip(randomVideoFile,target_resolution=(scaleHeight,scaleWidth))
            randomVideoClip = randomVideoClip.set_duration(videoDuration).set_position(("center","top"), relative=True)
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
    wholeClip = concatenate_videoclips(batchVideoFiles).set_duration(songDuration - 2)
    wholeClip.write_videofile(outputPath)
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

def addZoom(wholeVideoFile, onsetData, zoomAmount):
    print('')

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
testSongFile = '/home/eliot/Music/Downloads/Sewerslvt - Lexapro Delirium.mp3'
testSongFile = '/home/eliot/Music/Downloads/Folamour - When U Came into My Life.mp3'
testSongFile = '/home/eliot/Music/Downloads/Technotronic, Felly - Pump Up The Jam - Edit.mp3'
testOutputPath = '/home/eliot/Entertainment/nsfw/Edits/AutoMV/Technotronic, Felly - Pump Up The Jam - Edit2.mp4'
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


# testCombine(testVideo1, testVideo2, 'test_combine.mp4')

# combineVideos2(files, testSongFile, testOutputPath)

# hitData = prepareAudio(testSongFile)
# print('hitData: ', hitData)

combineVideos3(files, testSongFile, testOutputPath)