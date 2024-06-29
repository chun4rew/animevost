#TODO
#   1. Сделать обрезку видео, например: с 5 минуты до 6 минуты
#   2. Добавить кроп видео
#   3. Добавить выбор серии

from moviepy.video.compositing.concatenate import concatenate_videoclips
import cv2
from moviepy.video.fx import resize
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, ImageClip
from bs4 import BeautifulSoup as bs
import requests
import re
import wget
import math
import urllib.parse
import subprocess
from datetime import timedelta
import os
import whisperx

'''
Необходимые зависимости
 - ffmpeg
 - opencv-python
'''

'''
Живые аниме обои
https://winzoro.net/wallpapers_all/zhivye-oboi-anime/

Линк для получения ссылки на скачивание
https://xn--80aeiluelyj.xn--p1ai/dw.php?file=

Линк для поиска
https://xn--80aeiluelyj.xn--p1ai/list.php?f= &s=0
'''

data = "com_cod=250&d=1&caps=MjUw"

headers = {
    "accept": "text/html",
    "Content-Type": "application/x-www-form-urlencoded"
}


def transcribe_video(input_video):
    batch_size = 32
    compute_type = "float32"
    device = "cpu"

    model = whisperx.load_model("large-v2", device=device, compute_type=compute_type)

    audio = whisperx.load_audio(input_video)
    result = model.transcribe(audio, batch_size=batch_size, language="en")

    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

    segments = result["segments"]


   # if srt file exists, delete it
    if os.path.exists("subtitles.srt"):
        os.remove("subtitles.srt")
    for index, segment in enumerate(segments):
        startTime = str(0)+str(timedelta(seconds=int(segment['start'])))+',000'
        endTime = str(0)+str(timedelta(seconds=int(segment['end'])))+',000'
        text = segment['text']
        print(text)
        segment = f"{index + 1}\n{startTime} --> {endTime}\n{text[1:] if text[0] == ' ' else text}\n\n"

        srtFilename = os.path.join(f"subtitles.srt")
        with open(srtFilename, 'a', encoding='utf-8') as srtFile:
            srtFile.write(segment)

    generator = lambda txt: TextClip(txt, font='Arial', fontsize=24, color='white')
    subs = SubtitlesClip('subtitles.srt', generator)
    subtitles = SubtitlesClip(subs, generator)

    video = VideoFileClip(input_video)
    result = CompositeVideoClip([video, subtitles.set_pos(('center', 'bottom'))])

    result.write_videofile("output_subs.mp4")

def decode_html_entities(page):
    def decode_html(match):
        byte_sequence = match.group(0).replace(r'\x', '')
        return bytes.fromhex(byte_sequence).decode('utf-8')

    pattern = r'(\\x[0-9a-fA-F]{2})+'
    decoded_content = re.sub(pattern, decode_html, page)

    return decoded_content


def encode_string(string):
    encoded_string = urllib.parse.quote(string, encoding='windows-1251')
    return encoded_string


def download_video(link):
    response = requests.post(f'https://xn--80aeiluelyj.xn--p1ai/dw.php',
                             headers=headers, data=data, params={"file": f'{link}'})

    decoded_content = decode_html_entities(response.text)
    soup = bs(decoded_content, 'lxml')

    href_download = soup.find('img', {'src': 'img/dw/download_720.png'}).find_parent('a').get('href')
    wget.download(href_download, 'video.mp4')


def search_anime(request):
    response = requests.get(f'https://xn--80aeiluelyj.xn--p1ai/list.php?f={encode_string(request)}&s=0',
                            headers=headers)
    decoded_content = decode_html_entities(response.text)
    return decoded_content


def process_video(input_video_path, output_video_path):
    # Загрузка видео и фона
    video = VideoFileClip(input_video_path)
    # img = cv2.imread('test.jpg')
    # cropped_img = img[1920:720, 1920:720]
    # cv2.imwrite('output.jpg', cropped_img)
    background = ImageClip('test.jpg')
    start_time = 5 * 60
    end_time = 6 * 60

    # Trim the video using start_time and end_time values
    trimmed_video = video.subclip(start_time, end_time)

    # Loop the background video to match the duration of the trimmed video
    # background_loop = concatenate_videoclips([background] * math.ceil(trimmed_video.duration / background.duration))
    background_loop = background.set_duration(trimmed_video.duration).resize((1080, 1920))


    # Resize the trimmed video to fit the full length of the background
    # Place the trimmed video in the center of the background
    trimmed_video = trimmed_video.set_position(('center', 'center'))

    # Наложение видео на фон
    final_video = CompositeVideoClip([
        background_loop,
        trimmed_video
    ])

    # Сохранение видео
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')


if __name__ == "__main__":
    #download_video('MzEzNiU3QzQrJUYxJUU1JUYwJUU4JUZGJTdDNjk0MjM2MzU0')

    # subprocess.call([
    #     "C:\\ffmpeg\\bin\\ffmpeg.exe",  # Укажите полный путь к ffmpeg.exe
    #     "-ss", "00:05:00",
    #     "-t", "00:01:00",
    #     "-i", "video.mp4",
    #     "-i", "bg.jpg",
    #     "-filter_complex", "[0:v]scale=1280:720[v];[1:v][v]overlay=80:1000",
    #     "-c:a", "copy",
    #     "-async", "1",
    #     "-af", "adelay=2500|2500",
    #     "output.mp4"
    # ])

    process_video('video.mp4', 'output.mp4')

# Загружаем на ютуб
# https://github.com/linouk23/youtube_uploader_selenium
# https://github.com/ContentAutomation/YouTubeUploader
# https://github.com/dquint54/YT-Shorts-AI
# https://github.com/NickFerd/Highlights
# def upload_to_youtube(self):
#     pass
