from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def make_format_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 360p", callback_data="video_360"),
         InlineKeyboardButton(text="🎬 720p", callback_data="video_720")],
        [InlineKeyboardButton(text="🎬 1080p", callback_data="video_1080"),
         InlineKeyboardButton(text="🎵 MP3", callback_data="audio_mp3")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])
    return kb

def make_playlist_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Все видео 720p", callback_data="playlist_video"),
         InlineKeyboardButton(text="🎵 Все MP3", callback_data="playlist_audio")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])
    return kb
