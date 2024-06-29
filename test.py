import whisper
import moviepy.editor as mp
from moviepy.video.tools.subtitles import SubtitlesClip
import os

import moviepy.config as conf
conf.change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})


def video_to_text_with_timestamps(video_path):
    # Извлечение аудио из видео
    video = mp.VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile("temp_audio.wav")

    # Загрузка модели whisper
    model = whisper.load_model('large-v2', device='gpu')

    # Распознавание речи
    result = model.transcribe("temp_audio.wav", language="ru")

    # Удаление временного аудиофайла
    os.remove("temp_audio.wav")

    return result["segments"]


def create_subtitle_clips(segments):
    subtitle_clips = []
    for segment in segments:
        start = segment['start']
        end = segment['end']
        text = segment['text']
        subtitle_clip = mp.TextClip(text, fontsize=24, color='white', size=(720, None))
        subtitle_clip = subtitle_clip.set_start(start).set_end(end).set_pos(('center', 'center'))
        subtitle_clips.append(subtitle_clip)
    return subtitle_clips


def create_subtitled_video(video_path, subtitle_clips):
    video = mp.VideoFileClip(video_path)
    final_clip = mp.CompositeVideoClip([video] + subtitle_clips)
    final_clip.write_videofile("output_video.mp4")


# Использование функций
video_path = "output.mp4"
segments = video_to_text_with_timestamps(video_path)
subtitle_clips = create_subtitle_clips(segments)
create_subtitled_video(video_path, subtitle_clips)