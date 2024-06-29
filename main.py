#TODO
#   1. С̶д̶е̶л̶а̶т̶ь̶ ̶о̶б̶р̶е̶з̶к̶у̶ ̶в̶и̶д̶е̶о̶,̶ ̶н̶а̶п̶р̶и̶м̶е̶р̶:̶ ̶с̶ ̶5̶ ̶м̶и̶н̶у̶т̶ы̶ ̶д̶о̶ ̶6̶ ̶м̶и̶н̶у̶т̶ы̶
#   2. Д̶о̶б̶а̶в̶и̶т̶ь̶ ̶к̶р̶о̶п̶ ̶в̶и̶д̶е̶о̶
#   3. Добавить выбор серии

from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx import resize
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, TextClip
from bs4 import BeautifulSoup as bs
import requests
import re
import wget
import urllib.parse
import os
import textwrap
import whisper
import logging
import moviepy.config as conf
import numpy as np
from tqdm import tqdm

conf.change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

'''
Необходимые зависимости
 - ffmpeg
 - opencv-python
 - BeautifulSoup4
 - moviepy
 - whisper
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


def decode_html_entities(page):
    logging.info('PHP Decode')

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
    logging.info('Download video')
    response = requests.post(f'https://xn--80aeiluelyj.xn--p1ai/dw.php',
                             headers=headers, data=data, params={"file": f'{link}'})

    decoded_content = decode_html_entities(response.text)
    soup = bs(decoded_content, 'lxml')

    href_download = soup.find('img', {'src': 'img/dw/download_720.png'}).find_parent('a').get('href')
    wget.download(href_download, 'video.mp4')


def search_anime(request):
    logging.info('Anime search')
    response = requests.get(f'https://xn--80aeiluelyj.xn--p1ai/list.php?f={encode_string(request)}&s=0',
                            headers=headers)
    decoded_content = decode_html_entities(response.text)
    return decoded_content


def video_to_text_with_timestamps(video_input):
    logging.info('Started video to text func')

    # Проверяем, является ли вход путем к файлу или объектом VideoFileClip
    if isinstance(video_input, str):
        video = VideoFileClip(video_input)
        audio = video.audio
    elif isinstance(video_input, VideoFileClip):
        video = video_input
        audio = video.audio
    else:
        raise ValueError("Input must be either a file path or a VideoFileClip object")

    # Извлечение аудио
    audio.write_audiofile("temp_audio.wav")

    # Загрузка модели whisper
    model = whisper.load_model("large-v2")

    # Создание progress bar
    pbar = tqdm(total=100, desc="Распознавание речи", unit="%")

    # Распознавание речи
    result = model.transcribe("temp_audio.wav", language="ru")

    # Обновление progress bar после завершения
    pbar.update(100)
    pbar.close()

    logging.info('Removing temp_audio.wav')

    # Удаление временного аудиофайла
    os.remove("temp_audio.wav")

    return result["segments"]


def create_subtitle_clip(text, video_width, font_size=40, max_lines=3):
    # Оборачивание текста
    wrapper = textwrap.TextWrapper(width=int(video_width / (font_size / 2)), max_lines=max_lines)
    text_lines = wrapper.wrap(text)
    text = '\n'.join(text_lines)

    # Создание текстового клипа
    txt_clip = TextClip(text, fontsize=font_size, color='white', font='Arial-Bold',
                        method='label', align='center', size=(video_width, None))

    # Создание обводки
    stroke_color = 'black'
    stroke_width = 5

    def make_stroke(txt):
        """ Создает 'обводку' вокруг текста """
        return TextClip(txt, fontsize=font_size, color=stroke_color, font='Arial-Bold',
                        method='label', align='center', size=(video_width, None))

    strokes = [
        make_stroke(text).set_position((x, y))
        for x in range(-stroke_width, stroke_width+1, stroke_width)
        for y in range(-stroke_width, stroke_width+1, stroke_width)
        if (x, y) != (0, 0)
    ]

    # Объединение обводки и текста
    final_txt_clip = CompositeVideoClip([*strokes, txt_clip])
    final_txt_clip = final_txt_clip.set_position(('center', 'bottom'))

    return final_txt_clip


def create_subtitle_clips(segments, video_width, subtitle_y_position, video_duration):
    logging.info('Create subtitle clips')

    subtitle_clips = []
    for segment in segments:
        start = segment['start']
        end = min(segment['end'], video_duration)  # Ограничиваем конец длительностью видео
        text = segment['text']
        subtitle_clip = create_subtitle_clip(text, video_width)
        subtitle_clip = subtitle_clip.set_start(start).set_end(end).set_position(('center', subtitle_y_position))
        subtitle_clips.append(subtitle_clip)

    # Добавляем пустой клип в конец, чтобы субтитры длились до конца видео
    empty_clip = TextClip(" ", fontsize=1, color='white', size=(video_width, 1))
    empty_clip = empty_clip.set_duration(video_duration - subtitle_clips[-1].end).set_start(subtitle_clips[-1].end)
    subtitle_clips.append(empty_clip)

    return subtitle_clips


def process_video(input_video_path, output_video_path):
    logging.info('Started composite video')

    # Загрузка видео и фона
    video = VideoFileClip(input_video_path)
    background = ImageClip('test.jpg')
    start_time = 5 * 60
    end_time = 6 * 60

    # Обрезка видео
    trimmed_video = video.subclip(start_time, end_time)

    # Определение размеров финального видео (вертикальный формат 9:16)
    final_width = 1080
    final_height = 1920

    # Изменение размера фона с сохранением пропорций
    background_resized = background.resize(height=final_height)

    if background_resized.w > final_width:
        background_resized = background_resized.crop(x_center=background_resized.w / 2, width=final_width)

    background_loop = background_resized.set_duration(trimmed_video.duration)

    # Размещение видео в центре
    video_pos = ('center', 'center')

    # Изменение размера видео с сохранением пропорций
    video_aspect_ratio = trimmed_video.w / trimmed_video.h
    if video_aspect_ratio > (final_width / final_height):
        new_video_width = final_width
        new_video_height = int(final_width / video_aspect_ratio)
    else:
        new_video_height = int(final_height * 0.6)  # Видео занимает 60% высоты
        new_video_width = int(new_video_height * video_aspect_ratio)

    resized_video = trimmed_video.resize((new_video_width, new_video_height))

    # Вычисление позиции для субтитров
    video_bottom = (final_height - new_video_height) // 2 + new_video_height

    # Получение субтитров с временными метками
    segments = video_to_text_with_timestamps(trimmed_video)

    subtitle_y_position = video_bottom + 20  # 20 пикселей под видео
    subtitle_clips = create_subtitle_clips(segments, final_width, subtitle_y_position, trimmed_video.duration)

    # Создание финального видео
    final_video = CompositeVideoClip([
     background_loop,
     resized_video.set_position(video_pos)
    ] + subtitle_clips, size=(final_width, final_height))

    # Установка длительности финального видео
    final_video = final_video.set_duration(trimmed_video.duration)

    # Сохранение видео
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')


if __name__ == "__main__":
    download_video('MzUwOSU3QzUrJUYxJUU1JUYwJUU4JUZGJTdDMjUwMDAxMjU4')
    process_video('video.mp4', 'output.mp4')
