import json
import os

STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {"total_downloads": 0, "total_users": [], "video_downloads": 0, "audio_downloads": 0, "errors": 0}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

async def log_download(user_id, download_type, status="success"):
    stats = load_stats()
    if status == "success":
        stats["total_downloads"] += 1
        if str(user_id) not in stats["total_users"]:
            stats["total_users"].append(str(user_id))
        if download_type == "video":
            stats["video_downloads"] += 1
        elif download_type == "audio":
            stats["audio_downloads"] += 1
    else:
        stats["errors"] += 1
    save_stats(stats)
