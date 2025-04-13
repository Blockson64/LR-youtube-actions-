import yt_dlp
from datetime import datetime, timedelta
import time

log_file = "log.txt"

# Extra UI state for tracking last check, check count, and videos found
extra_ui_state = {
    "last_check": None,
    "check_count": 0,
    "videos_found": 0
}

def normalize_string(s):
    return s.lower().strip()

def search_youtube(term, max_results=20):
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    search_term_with_date = f"\"{term}\" after:{yesterday}"
    search_url = f"ytsearchdate{max_results}:{search_term_with_date}"

    flat_opts = {
        "quiet": True,
        "extract_flat": True,
        "dump_single_json": True,
    }

    with yt_dlp.YoutubeDL(flat_opts) as ydl:
        result = ydl.extract_info(search_url, download=False)

    entries = result.get("entries", [])
    full_entries = []
    full_opts = {"quiet": True}

    with yt_dlp.YoutubeDL(full_opts) as ydl:
        for entry in entries:
            url = entry.get("url") or entry.get("webpage_url")
            try:
                full_info = ydl.extract_info(url, download=False)
                full_entries.append(full_info)
            except yt_dlp.utils.DownloadError:
                continue

    print(f"\nSearch URL: https://www.youtube.com/results?search_query={search_term_with_date}\n")
    return full_entries

def is_uploaded_today(entry):
    upload_date = entry.get("upload_date")
    if upload_date:
        upload_date_obj = datetime.strptime(str(upload_date), "%Y%m%d")
        return upload_date_obj.date() == datetime.today().date()
    return False

def load_seen_videos():
    try:
        with open(log_file, "r") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

def save_seen_video(str):
    with open(log_file, "a") as file:
        file.write(f"{str}\n")

def run_check():
    search_term = "line rider"
    normalized_search_term = normalize_string(search_term)

    print(f"\nSearching for: {search_term}")
    results = search_youtube(search_term)
    if not results:
        print("No search results found.")
        return

    seen_videos = load_seen_videos()
    found = False

    skipped = 0

    for entry in results:
        title = entry.get("title")
        url = entry.get("url") or entry.get("webpage_url")
        uploader = entry.get('uploader', 'Unknown author')
        upload_date = entry.get("upload_date", "Unknown")
        video_id = entry.get("id")
        short_url = f"https://youtu.be/{video_id}"
        video_str = title + " | " + uploader + " | " + short_url

        name = title + " | " + uploader
        normalized_title = normalize_string(title)

        if normalized_search_term not in normalized_title:
            skipped += 1
            continue

        print(f"\n Checking: {title} by {uploader}")
        print(f"   URL: {short_url}")
        print(f"   Upload Date: {upload_date}")
        print(f"   Already seen: {'✅' if video_str in seen_videos else '❌'}")

        if video_str not in seen_videos:
            print(f"\n Title: {title}")
            print(f" Link: {url}")
            print(f" Uploaded: {datetime.strptime(str(entry['upload_date']), '%Y%m%d')}")
            found = True
            save_seen_video(video_str)
            seen_videos.add(name)
            extra_ui_state["videos_found"] += 1

    # Update UI state
    print(f"\nskipped: {skipped}")
    extra_ui_state["check_count"] += 1

def main():
    run_check()

if __name__ == "__main__":
    main()
