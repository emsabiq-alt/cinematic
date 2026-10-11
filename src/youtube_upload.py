"""youtube_upload.py — Upload film ke YouTube Data API v3.

Port Python dari repo emsabiq-alt/yt-longform (src/youtube-publisher.js):
  1. Tukar refresh token -> access token (oauth2.googleapis.com/token).
  2. Buat sesi resumable upload, PUT file MP4 -> videoId.
  3. Upload thumbnail kustom (<=2MB, retry, non-fatal).
  4. Upload caption SRT (retry, non-fatal).
  5. Set defaultLanguage/defaultAudioLanguage = id.
  6. Jadwal publish: upload sebagai private + publishAt (YouTube yang
     mempublikasikan otomatis), atau langsung public/unlisted/private.

Kredensial lewat environment (disarankan GitHub Secrets):
  YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN

Contoh:
  python3 src/youtube_upload.py --video export/..._MASTER.mp4 \\
      --title "SUPERVOLCANO EROPA" --description-file input/youtube_meta.json \\
      --thumbnail thumb.jpg --srt subtitles.srt --privacy scheduled
"""
import argparse
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TOKEN_URL = "https://oauth2.googleapis.com/token"
VIDEO_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
VIDEO_API_URL = "https://www.googleapis.com/youtube/v3/videos"
THUMBNAIL_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
CAPTION_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/captions"
MAX_THUMBNAIL_BYTES = 2 * 1024 * 1024


class UploadError(RuntimeError):
    pass


def _req(url, method="GET", headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            detail = json.loads(body).get("error", {}).get("message") or body
        except Exception:
            detail = body
        raise UploadError(f"{detail} [HTTP {e.code}]")


def _json(status_body):
    _s, body = status_body
    return json.loads(body.decode("utf-8") or "{}")


def get_access_token(client_id, client_secret, refresh_token):
    body = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    data = _json(_req(TOKEN_URL, "POST",
                      {"Content-Type": "application/x-www-form-urlencoded"}, body))
    token = data.get("access_token")
    if not token:
        raise UploadError("Google tidak mengembalikan access token.")
    return token


def next_publish_at(time_str="19:00", tz_name="Asia/Jakarta", lead_minutes=15):
    """Waktu prime-time berikutnya (ISO 8601) di zona target."""
    h, m = time_str.split(":")
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    minimum = now + timedelta(minutes=lead_minutes)
    for offset in range(3):
        day = (minimum + timedelta(days=offset)).date()
        cand = datetime(day.year, day.month, day.day, int(h), int(m), tzinfo=tz)
        if cand > minimum:
            return cand.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    raise UploadError("Gagal menentukan jadwal publikasi.")


def resumable_upload(video_path, metadata, access_token):
    size = video_path.stat().st_size
    url = VIDEO_UPLOAD_URL + "?" + urllib.parse.urlencode(
        {"uploadType": "resumable", "part": "snippet,status"})
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Length": str(size),
        "X-Upload-Content-Type": "video/mp4",
    }
    req = urllib.request.Request(url, data=json.dumps(metadata).encode(),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            session_url = r.headers.get("Location")
    except urllib.error.HTTPError as e:
        raise UploadError(f"Sesi upload gagal: {e.read().decode()[:300]} [HTTP {e.code}]")
    if not session_url:
        raise UploadError("YouTube tidak mengembalikan URL sesi upload.")

    # PUT file (single request, seperti yt-longform)
    req2 = urllib.request.Request(session_url, method="PUT",
                                  headers={"Content-Type": "video/mp4",
                                           "Content-Length": str(size)})
    last = {}
    try:
        with open(video_path, "rb") as f, \
                urllib.request.urlopen(req2, data=f, timeout=3600) as r2:
            last = json.loads(r2.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        raise UploadError(f"Upload video gagal: {e.read().decode()[:300]} [HTTP {e.code}]")
    video_id = (last.get("id") or "").strip()
    if not video_id:
        raise UploadError("Upload selesai tetapi video id kosong.")
    return video_id


def set_thumbnail(video_id, thumb_path, access_token, attempts=3):
    if not thumb_path or not Path(thumb_path).exists():
        return {"ok": False, "skipped": True, "error": ""}
    size = Path(thumb_path).stat().st_size
    if not size:
        return {"ok": False, "error": "Thumbnail kosong."}
    if size > MAX_THUMBNAIL_BYTES:
        return {"ok": False, "error": f"Thumbnail melebihi 2MB ({size} bytes)."}
    data = Path(thumb_path).read_bytes()
    url = THUMBNAIL_UPLOAD_URL + "?" + urllib.parse.urlencode(
        {"videoId": video_id, "uploadType": "media"})
    err = ""
    for attempt in range(1, attempts + 1):
        try:
            _req(url, "POST", {"Authorization": f"Bearer {access_token}",
                               "Content-Type": "image/jpeg",
                               "Content-Length": str(size)}, data)
            return {"ok": True, "error": ""}
        except UploadError as e:
            err = str(e)
            time.sleep(attempt * 3)
    return {"ok": False, "error": err}


def upload_caption(video_id, srt_path, access_token, language="id", attempts=3):
    if not srt_path or not Path(srt_path).exists():
        return {"ok": False, "skipped": True, "error": ""}
    body = Path(srt_path).read_text(encoding="utf-8")
    if not body.strip():
        return {"ok": False, "skipped": True, "error": ""}
    metadata = {"snippet": {"videoId": video_id, "language": language,
                            "name": "", "isDraft": False}}
    boundary = f"caption-{int(time.time() * 1000)}"
    parts = [
        f"--{boundary}", "Content-Type: application/json; charset=UTF-8", "",
        json.dumps(metadata),
        f"--{boundary}", "Content-Type: application/octet-stream", "",
        body,
        f"--{boundary}--", "",
    ]
    payload = "\r\n".join(parts).encode("utf-8")
    url = CAPTION_UPLOAD_URL + "?" + urllib.parse.urlencode({"part": "snippet"})
    err = ""
    for attempt in range(1, attempts + 1):
        try:
            _req(url, "POST", {"Authorization": f"Bearer {access_token}",
                               "Content-Type": f"multipart/related; boundary={boundary}"},
                 payload)
            return {"ok": True, "error": ""}
        except UploadError as e:
            err = str(e)
            time.sleep(attempt * 5)
    return {"ok": False, "error": err}


def set_language(video_id, access_token, title, description, category_id="27"):
    """Set defaultLanguage/defaultAudioLanguage = id (tanpa localizations)."""
    url = VIDEO_API_URL + "?" + urllib.parse.urlencode({"part": "snippet"})
    body = {"id": video_id,
            "snippet": {"title": title[:100], "description": description[:5000],
                        "categoryId": category_id,
                        "defaultLanguage": "id", "defaultAudioLanguage": "id"}}
    try:
        _req(url, "PUT", {"Authorization": f"Bearer {access_token}",
                          "Content-Type": "application/json; charset=UTF-8"},
             json.dumps(body).encode())
        return {"ok": True, "error": ""}
    except UploadError as e:
        return {"ok": False, "error": str(e)}


def publish(video_path, title, description, tags, thumbnail, srt, privacy,
            schedule_time, schedule_tz, category_id="27"):
    cid = os.environ.get("YOUTUBE_CLIENT_ID", "")
    csec = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    rtok = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
    missing = [n for n, v in [("YOUTUBE_CLIENT_ID", cid),
                              ("YOUTUBE_CLIENT_SECRET", csec),
                              ("YOUTUBE_REFRESH_TOKEN", rtok)] if not v]
    if missing:
        raise UploadError(f"Kredensial belum lengkap: {', '.join(missing)}")

    token = get_access_token(cid, csec, rtok)
    print("✓ Access token didapat", flush=True)

    if privacy == "scheduled":
        status = {"privacyStatus": "private",
                  "publishAt": next_publish_at(schedule_time, schedule_tz),
                  "selfDeclaredMadeForKids": False}
    else:
        status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}

    metadata = {"snippet": {"title": title[:100],
                            "description": description[:5000],
                            "categoryId": category_id,
                            "tags": list(dict.fromkeys(tags))[:30],
                            "defaultLanguage": "id",
                            "defaultAudioLanguage": "id"},
                "status": status}

    video_id = resumable_upload(Path(video_path), metadata, token)
    print(f"✓ Video terupload: https://www.youtube.com/watch?v={video_id}", flush=True)

    thumb = set_thumbnail(video_id, thumbnail, token)
    print(("✓ Thumbnail ok" if thumb["ok"] else
           f"○ Thumbnail dilewati/gagal: {thumb.get('error', '')}"), flush=True)

    cap = upload_caption(video_id, srt, token)
    print(("✓ Caption ok" if cap["ok"] else
           f"○ Caption dilewati/gagal: {cap.get('error', '')}"), flush=True)

    lang = set_language(video_id, token, title, description, category_id)
    print(("✓ Bahasa id ok" if lang["ok"] else
           f"○ Set bahasa gagal: {lang['error']}"), flush=True)

    return {"videoId": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "privacyStatus": status["privacyStatus"],
            "scheduledPublishAt": status.get("publishAt", "")}


def main():
    ap = argparse.ArgumentParser(description="Upload film ke YouTube Data API v3")
    ap.add_argument("--video", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--description-file", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--thumbnail", default="")
    ap.add_argument("--srt", default="")
    ap.add_argument("--privacy", default="scheduled",
                    choices=["scheduled", "public", "unlisted", "private"])
    ap.add_argument("--schedule-time", default="19:00")
    ap.add_argument("--schedule-tz", default="Asia/Jakarta")
    ap.add_argument("--category-id", default="27")
    args = ap.parse_args()

    desc = args.description
    if args.description_file and Path(args.description_file).exists():
        raw = Path(args.description_file).read_text(encoding="utf-8")
        try:
            desc = json.loads(raw).get("description", raw)
        except Exception:
            desc = raw
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    try:
        out = publish(args.video, args.title, desc, tags, args.thumbnail or None,
                      args.srt or None, args.privacy, args.schedule_time,
                      args.schedule_tz, args.category_id)
    except UploadError as e:
        print(f"GAGAL: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"video_id={out['videoId']}\nurl={out['url']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
