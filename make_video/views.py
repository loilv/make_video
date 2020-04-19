import json
import os
import random
import subprocess
from datetime import datetime
from gtts import gTTS
from wsgiref.util import FileWrapper

import requests
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

base_dir = os.path.dirname(os.path.realpath(__file__))


def index(request):
    return render(request, 'make-video.html')


def create_video(request):
    text = request.POST['t-text']
    voice = request.POST['s-voice']
    speed = request.POST['i-speed']
    output_type = request.POST['i-type']
    volume = request.POST['i-volume']
    audio = _handle_make_audio(text=text, voice=voice, speed=speed, output_type=output_type)
    # audio = _handle_text_to_speech(mytext=text, language='vi', voice=voice)
    sub = _generate_sub(audio)
    if request.POST['submit'] == 'audio':
        if 'i-bg-music' in request.FILES:
            audio_bg = _handle_create_bg_music(request.FILES['i-bg-music'], audio, volume)

    if request.POST['submit'] == 'video':
        audio_bg = None
        if 'i-bg-music' in request.FILES:
            audio_bg = _handle_create_bg_music(request.FILES['i-bg-music'], audio, volume)
        if 'i-intro' in request.FILES:
            _handle_upload_file(request.FILES['i-intro'], 'i-intro', 'video')
        if 'i-outro' in request.FILES:
            _handle_upload_file(request.FILES['i-outro'], 'i-outro', 'video')
        if 'i-images' in request.POST:
            images = request.POST['i-images']
            list_images = images.split(',')
            i = 0
            for img in list_images:
                i += 1
                try:
                    _get_image_from_url(img, 'images-{}'.format(i), 'images')
                except Exception as e:
                    print(e)
                    continue
        video = _handle_create_video()
        video_prod = _handle_create_video_loop(video=video, audio=audio_bg)
        file_complete = _merge_video_sub(video_prod, sub)
        file = FileWrapper(open(file_complete, 'rb'))
        response = HttpResponse(file, content_type="video/mp4")

        response['Content-Disposition'] = 'attachment; filename="complete.mp4"'
        return response


def _handle_make_audio(text, voice, speed, output_type):
    try:
        key = [
            'SNxGGJ1CHZjBr3op9TL5X4ldZhc7RDVAcQ6PnvVHjj0GLZYnrgmagaOErArToIMM',
            'w1SqUDVyFPYXHhpUV8HiRfUQiUCuBK-ttAJe4N2T0gpOTBMZybhhWqDcm18jKJwS',
            'iPMb3fudkMakf7hqXYORU6-40KASGstUNVXPtfEFXZq-MbIBbP4YwuEpyHVRONaW'
        ]

        url = 'https://viettelgroup.ai/voice/api/tts/v1/rest/syn'
        headers = {
            'Content-Type': 'application/json',
            'token': random.choice(key)
        }

        data = dict(
            text=text,
            voice=voice,
            id='voice-{}'.format(datetime.now()),
            speed=float(speed),
            tts_return_option=output_type
        )

        response = requests.post(url, data=json.dumps(data), headers=headers)
        print(response.headers)
        print(response.status_code)

        if int(output_type) == 2:
            o_t = '.mp3'
        else:
            o_t = '.wav'

        data = response.content
        name_of_file = '{}-{}'.format(voice, datetime.now().strftime('%d-%m-%Y'))
        save_path = os.path.dirname(os.path.realpath(__file__)) + '/media/audio/'
        completeName = os.path.join(save_path, name_of_file + o_t)
        f = open(completeName, 'wb')
        f.write(data)
        f.close()

        return completeName
    except Exception as e:
        print(e)
        return False


def _handle_upload_file(file, name, path):
    name_of_file = '{}-{}.png'.format(name, datetime.now().strftime('%d-%m-%Y-%H-%m-%s'))
    save_path = base_dir + '/media/' + path + '/'
    completeName = os.path.join(save_path, name_of_file)
    with open(completeName, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return completeName


def _get_image_from_url(url, name, path, chunk=2048):
    name_of_file = '{}.jpg'.format(name)
    save_path = base_dir + '/media/' + path + '/'
    completeName = os.path.join(save_path, name_of_file)
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(completeName, 'wb') as f:
            for chunk in res.iter_content(chunk):
                f.write(chunk)
            f.close()
    return completeName


def _handle_process_ffmpeg(code):
    print(code)
    try:
        subprocess.call(code, shell=True)
    except Exception as e:
        return False


def _handle_text_to_speech(mytext, language, voice):
    myVoice = gTTS(text=mytext, lang=language, slow=False)
    completeName = base_dir + '/media/audio/{}-{}.mp3' \
        .format(voice, datetime.now().strftime('%d-%m-%Y'))
    with open(completeName, 'wb+') as f:
        myVoice.write_to_fp(f)

    return completeName


def _handle_create_bg_music(music, audio, volume):
    if music:
        bg_audio = _handle_upload_file(music, 'bg-music', 'music')
        save_path = base_dir + '/media/audio/'
        code = 'ffmpeg -y -i ' + audio + ' -i ' \
               + bg_audio + \
               ' -filter_complex "[0]volume=10[s];' \
               '[1]volume={}[t];' \
               '[s][t]amix=duration=shortest" {}audio-bg{}.mp3'.format(
                   volume, save_path, datetime.now().strftime('%d-%m-%Y'))
        _handle_process_ffmpeg(code)
        return '{}audio-bg{}.mp3'.format(save_path, datetime.now().strftime('%d-%m-%Y'))


def _handle_create_video():
    source_path = base_dir + '/media/images/'
    save_path = base_dir + '/media/video/'
    list_file = os.listdir(source_path)
    number_files = len(list_file)
    WIDTH = 1280
    HEIGHT = 720
    FPS = 30
    TRANSITION_DURATION = 1
    IMAGE_DURATION = 10
    SCREEN_MODE = 4  # 1=CENTER, 2=CROP, 3=SCALE, 4=BLUR
    BACKGROUND_COLOR = "black"

    # INTERNAL VARIABLES
    TRANSITION_FRAME_COUNT = TRANSITION_DURATION * FPS
    IMAGE_FRAME_COUNT = IMAGE_DURATION * FPS
    TOTAL_DURATION = IMAGE_DURATION + TRANSITION_DURATION * number_files - TRANSITION_DURATION
    TOTAL_FRAME_COUNT = TOTAL_DURATION * FPS

    # 1. START COMMAND
    FULL_SCRIPT = "ffmpeg -y "
    for i in list_file:
        FULL_SCRIPT += ' -loop 1 -i {} '.format(source_path + i)

    # 3. START FILTER COMPLEX
    FULL_SCRIPT += "-filter_complex \""

    # 4. PREPARE INPUTS
    for i in range(number_files):
        if SCREEN_MODE == 1:
            FULL_SCRIPT += "[{i}:v]setpts=PTS-STARTPTS," \
                           "scale=w='if(gte(iw/ih,{width}/{height})," \
                           "min(iw,{width}),-1)':h='if(gte(iw/ih,{width}/{height}),-1," \
                           "min(ih,{height}))'," \
                           "scale=trunc(iw/2)*2:trunc(ih/2)*2," \
                           "setsar=sar=1/1," \
                           "fps={fps}," \
                           "format=rgba," \
                           "split=2[stream{i1}out1][stream{i1}out2];". \
                format(i=i, i1=i + 1, width=WIDTH, height=HEIGHT, fps=FPS)
        elif SCREEN_MODE == 2:
            FULL_SCRIPT += "[{i}:v]setpts=PTS-STARTPTS," \
                           "scale=w='if(gte(iw/ih,{width}/{height}),-1,{width})':h='if(gte(iw/ih,{width}/{height}),{height},-1)'," \
                           "crop={width}:{height}," \
                           "setsar=sar=1/1,fps={fps}," \
                           "format=rgba,split=2[stream{i1}out1][stream{i1}out2];" \
                .format(i=i, i1=i + 1, width=WIDTH, height=HEIGHT, fps=FPS)
        elif SCREEN_MODE == 3:
            FULL_SCRIPT += "[{i}:v]setpts=PTS-STARTPTS," \
                           "scale={width}:{height},setsar=sar=1/1," \
                           "fps={fps},format=rgba," \
                           "split=2[stream{i1}out1][stream{i1}out2];" \
                .format(i=i, i1=i + 1, width=WIDTH, height=HEIGHT, fps=FPS)
        elif SCREEN_MODE == 4:
            FULL_SCRIPT += "[{i}:v]scale={width}x{height}," \
                           "setsar=sar=1/1," \
                           "fps={fps}," \
                           "format=rgba," \
                           "boxblur=100," \
                           "setsar=sar=1/1[stream{i}blurred];".format(i=i, i1=i + 1, width=WIDTH, height=HEIGHT, fps=FPS)
            FULL_SCRIPT += "[{i}:v]scale=w='if(gte(iw/ih,{width}/{height})," \
                           "min(iw,{width}),-1)':h='if(gte(iw/ih,{width}/{height}),-1," \
                           "min(ih,{height}))',scale=trunc(iw/2)*2:trunc(ih/2)*2," \
                           "setsar=sar=1/1," \
                           "fps={fps}," \
                           "format=rgba[stream{i}raw];".format(i=i, i1=i + 1, width=WIDTH, height=HEIGHT, fps=FPS)
            FULL_SCRIPT += "[stream{i}blurred][stream{i}raw]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:format=rgb," \
                           "setpts=PTS-STARTPTS," \
                           "split=2[stream{i1}out1][stream{i1}out2];" \
                .format(i=i, i1=i + 1, width=WIDTH, height=HEIGHT, fps=FPS)

    # 5. APPLY PADDING
    for i in range(number_files):
        i += 1
        FULL_SCRIPT += "[stream{i}out1]pad=width={width}:height={height}:x=({width}-iw)/2:y=({height}-ih)/2:color={bg_color}," \
                       "trim=duration={img_duration}," \
                       "select=lte(n\,{img_frame_count})[stream{i}overlaid];" \
            .format(i=i, width=WIDTH, height=HEIGHT,
                    bg_color=BACKGROUND_COLOR, img_duration=IMAGE_DURATION, img_frame_count=IMAGE_FRAME_COUNT)
        if i == 1:
            FULL_SCRIPT += "[stream{i}out2]pad=width={width}:height={height}:x=({width}-iw)/2:y=({height}-ih)/2:color={bg_color}," \
                           "trim=duration={trans_duration}," \
                           "select=lte(n\,{trans_frame_count})," \
                           "fade=t=out:s=0:n={trans_frame_count}[stream{i}fadeout];" \
                .format(i=i, width=WIDTH, height=HEIGHT,
                        bg_color=BACKGROUND_COLOR,
                        trans_duration=TRANSITION_DURATION,
                        trans_frame_count=TRANSITION_FRAME_COUNT)
        elif i < number_files:
            FULL_SCRIPT += "[stream{i}out2]pad=width={width}:height={height}:x=({width}-iw)/2:y=({height}-ih)/2:color={bg_color}," \
                           "trim=duration={trans_duration}," \
                           "select=lte(n\,{trans_frame_count})," \
                           "split=2[stream{i}starting][stream{i}ending];" \
                .format(i=i, width=WIDTH, height=HEIGHT,
                        bg_color=BACKGROUND_COLOR,
                        trans_duration=TRANSITION_DURATION,
                        trans_frame_count=TRANSITION_FRAME_COUNT)
        elif i == number_files:
            FULL_SCRIPT += "[stream{i}out2]pad=width={width}:height={height}:x=({width}-iw)/2:y=({height}-ih)/2:color={bg_color}," \
                           "trim=duration={trans_duration}," \
                           "select=lte(n\,{trans_frame_count})," \
                           "fade=t=in:s=0:n={trans_frame_count}[stream{i}fadein];" \
                .format(i=i, width=WIDTH, height=HEIGHT,
                        bg_color=BACKGROUND_COLOR,
                        trans_duration=TRANSITION_DURATION,
                        trans_frame_count=TRANSITION_FRAME_COUNT)

        if i != 1 and i != number_files:
            FULL_SCRIPT += "[stream{i}starting]fade=t=in:s=0:n={trans_frame_count}[stream{i}fadein];" \
                .format(i=i, trans_frame_count=TRANSITION_FRAME_COUNT)
            FULL_SCRIPT += "[stream{i}ending]fade=t=out:s=0:n={trans_frame_count}[stream{i}fadeout];" \
                .format(i=i, trans_frame_count=TRANSITION_FRAME_COUNT)

    # 6. CREATE TRANSITION FRAMES
    for i in range(1, number_files):
        FULL_SCRIPT += "[stream{i1}fadein][stream{i}fadeout]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2," \
                       "trim=duration={trans_duration}," \
                       "select=lte(n\,{trans_frame_count})[stream{i1}blended];" \
            .format(i1=i + 1, i=i, trans_duration=TRANSITION_DURATION, trans_frame_count=TRANSITION_FRAME_COUNT)

    # 7. BEGIN CONCAT
    for i in range(1, number_files):
        FULL_SCRIPT += "[stream{i}overlaid][stream{i1}blended]".format(i=i, i1=i + 1)

    # 8. END CONCAT
    FULL_SCRIPT += "[stream{img_count}overlaid]concat=n={img_count21}:v=1:a=0,format=yuv420p[video]\"" \
        .format(img_count=number_files, img_count21=2*number_files-1)

    # 9. END
    FULL_SCRIPT += " -map [video] -vsync 2 -async 1 -rc-lookahead 0 -g 0 " \
                   "-profile:v main -level 42 -c:v libx264 -r {fps} {output}video.mp4" \
        .format(fps=FPS, output=save_path)
    _handle_process_ffmpeg(FULL_SCRIPT)
    return '{}video.mp4'.format(save_path)


def _handle_create_video_loop(video=None, audio=None):
    save_path = base_dir + '/media/prods/'
    code = 'ffmpeg -y -i {audio} -filter_complex movie={video}:loop=0,setpts=N/FRAME_RATE/TB -shortest {save}prod.mp4'.format(video=video, audio=audio, save=save_path)
    _handle_process_ffmpeg(code)
    return '{}prod.mp4'.format(save_path)


def _generate_sub(path_file):
    save_path = base_dir + '/media/prods/sub_video.srt'
    code = 'autosub -o {save} -S vi -F srt -D vi {path}'.format(path=path_file, save=save_path)
    _handle_process_ffmpeg(code)
    return save_path


def _merge_video_sub(video, sub):
    save_path = base_dir + '/media/prods/'
    code = 'ffmpeg -y -i {video} -vf subtitles={sub} {save}complete.mp4'.format(video=video, sub=sub, save=save_path)
    _handle_process_ffmpeg(code)
    return '{}complete.mp4'.format(save_path)