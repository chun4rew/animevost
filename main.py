#TODO
#   1. Сделать обрезку видео, например: с 5 минуты до 6 минуты
#   2. Добавить кроп видео
#   3. Добавить выбор серии

from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from bs4 import BeautifulSoup as bs
import requests
import re
import wget
import urllib.parse
import subprocess

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


def process_video(input_video_path, output_video_path, background_image_path):
    # Загрузка видео и фона
    video = VideoFileClip(input_video_path)
    background = VideoFileClip(background_image_path)
    start_time = 5 * 60
    end_time = (6 * 60) - 10

    # Trim the video using start_time and end_time values
    trimmed_video = video.subclip(start_time, end_time)

    # # Наложение видео на фон
    # trimmed_video = CompositeVideoClip([
    #     background.set_duration(trimmed_video.duration),  # Устанавливаем продолжительность фона равной видео
    #     video.set_position(('center', 'center'))
    # ])

    # Сохранение видео
    trimmed_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')


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

    process_video('video.mp4', 'output.mp4', 'image.jpg')

# Загружаем на ютуб
# https://github.com/linouk23/youtube_uploader_selenium
# https://github.com/ContentAutomation/YouTubeUploader
# https://github.com/dquint54/YT-Shorts-AI
# https://github.com/NickFerd/Highlights
# def upload_to_youtube(self):
#     pass
