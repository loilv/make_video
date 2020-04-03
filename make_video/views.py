import json
import os
import random
import subprocess
from datetime import datetime
from gtts import gTTS

import requests
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse


def index(request):
    return render(request, 'make-video.html')


def create_video(request):
    if request.POST['submit'] == 'audio':
        text = request.POST['t-text']
        voice = request.POST['s-voice']
        speed = request.POST['i-speed']
        output_type = request.POST['i-type']
        # audio = _handle_make_audio(text=text, voice=voice, speed=speed, output_type=output_type)
        audio = _handle_text_to_speech(mytext=text, language='vi', voice=voice)
        if request.FILES['i-bg-music']:
            bg_audio = _handle_upload_file(request.FILES['i-bg-music'], 'bg-music', 'music')
            save_path = os.path.dirname(os.path.realpath(__file__)) + '/media/audio/'
            code = 'ffmpeg -i ' + audio + ' -i ' + bg_audio + ' -filter_complex "[0]volume=1[s];[1]volume=0.5[t];[s][t]amix=duration=shortest" {}audio-bg{}.mp3'.format(
                save_path, datetime.now().strftime('%d-%m-%Y'))
            _handle_process_ffmpeg(code)

    if request.POST['submit'] == 'video':
        # if 'i-bg-music' in request.FILES['i-bg-music']:
        #     _handle_upload_file(request.FILES['i-bg-music'], 'bg-music', 'music')
        if 'i-intro' in request.FILES['i-intro']:
            _handle_upload_file(request.FILES['i-intro'], 'i-intro', 'video')
        if 'i-outro' in request.FILES['i-outro']:
            _handle_upload_file(request.FILES['i-outro'], 'i-outro', 'video')
        if 'images' in request.FILES.getlist('images'):
            for file in request.FILES.getlist('images'):
                _handle_upload_file(file, 'images', 'images')

    return redirect('create-video')


def _handle_make_audio(text, voice, speed, output_type):
    try:
        key = [
            'jEMLimROBIzzj5JuWsu57-dsNE7oM3bLv3T3aQe-hGoYC-Ek9vS8126AallW5eLg',
            'IhPBlnrop4OtYm8qIl-dhEn-iSLlzyKdZgRlM-HN2yE7uAiQyNiaj93S-fwl37x4',
            'v8s228l7EdSzvAZE-YoTOKaiEoRPh9MxXbwLJx64cC1ASfbmwJtsSpiA8HwJEzFR',
            '-vJc-bAEfQNtrUKoMFV4ZZX5sLnhARLEKBo9a4K1DKlWK1FRy3JP-fg-fsj62HDR',
            '6WUWwDkRFQRLvvVq4Q-OZ3XbOZrRRG0ASDtocwMXcO10o-bas3ZQsz9PkPRbrH-q',
            '5Y03AmoSJ9ljf1WuRg7rc9XrOq5c9Cc7CbDBZ0LhlNGy15YyoDFB3gwe0rEb8K2a'
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
    name_of_file = '{}-{}'.format(name, datetime.now().strftime('%d-%m-%Y'))
    save_path = os.path.dirname(os.path.realpath(__file__)) + '/media/' + path + '/'
    completeName = os.path.join(save_path, name_of_file)
    with open(completeName, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return completeName


def _handle_process_ffmpeg(code):
    try:
        subprocess.call(code, shell=True)
    except Exception as e:
        return False


def _handle_text_to_speech(mytext, language, voice):
    myVoice = gTTS(text=mytext, lang=language, slow=False)
    completeName = os.path.dirname(os.path.realpath(__file__)) + '/media/audio/{}-{}.mp3'.format(voice, datetime.now().strftime('%d-%m-%Y'))
    with open(completeName, 'wb+') as f:
        myVoice.write_to_fp(f)

    return completeName
