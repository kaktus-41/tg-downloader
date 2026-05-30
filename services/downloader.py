import os
import glob
import yt_dlp

def get_playlist_info(url):
    ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "playlistend": 20}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get("entries", [])
        return info.get("title", "Плейлист"), len(entries), entries

def download_video(url, output_dir, quality):
    fmt = {
        "360": "bestvideo[height<=360]+bestaudio/best",
        "720": "bestvideo[height<=720]+bestaudio/best"
    }.get(quality, "bestvideo+bestaudio/best")
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": fmt,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            filename = filename.rsplit(".", 1)[0] + ".mp4"
        return filename, info.get("title", "video")

def download_audio(url, output_dir):
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        "quiet": True,
        "no_warnings": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "audio")
    mp3_files = glob.glob(os.path.join(output_dir, "*.mp3"))
    if not mp3_files:
        raise Exception("MP3 файл не найден")
    return mp3_files[0], title
