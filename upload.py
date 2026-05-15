import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

def upload_video(video_path: str):
    file_size = os.path.getsize(video_path)

    print(f"Размер файла: {file_size} байт")
    print("Инициализация загрузки...")

    response = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "post_info": {
                "title": "Моё первое видео через API",
                "privacy_level": "SELF_ONLY",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            },
            "post_mode": "MEDIA_UPLOAD"
        }
    )
    init_data = response.json()
    print(init_data)

    if "data" not in init_data:
        print("Ошибка инициализации!")
        return

    upload_url = init_data["data"]["upload_url"]
    publish_id = init_data["data"]["publish_id"]

    print("Загрузка видео...")
    with open(video_path, "rb") as f:
        upload_response = requests.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{file_size-1}/{file_size}"
            },
            data=f
        )
    print(f"Статус: {upload_response.status_code}")
    print(f"Готово! Publish ID: {publish_id}")

upload_video("video.mp4")