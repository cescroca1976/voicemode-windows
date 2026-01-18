"""FFmpeg detection and installation helper."""
import shutil
import platform

def check_ffmpeg():
    path = shutil.which('ffmpeg')
    return path is not None, path

def check_ffprobe():
    path = shutil.which('ffprobe')
    return path is not None, path

def get_install_instructions():
    return "Please install ffmpeg"
