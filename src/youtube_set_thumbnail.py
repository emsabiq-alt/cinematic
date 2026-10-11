#!/usr/bin/env python3
"""Pasang thumbnail ke video YouTube yang sudah terupload.

Memakai ulang OAuth (refresh token) dari youtube_upload.py.
Contoh:
    python3 src/youtube_set_thumbnail.py --video-id ABC123 --thumbnail thumb.jpg
Kredensial via env: YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / YOUTUBE_REFRESH_TOKEN
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from youtube_upload import get_access_token, set_thumbnail, UploadError


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video-id", required=True)
    ap.add_argument("--thumbnail", required=True)
    args = ap.parse_args()

    cid = os.environ.get("YOUTUBE_CLIENT_ID", "")
    csec = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    rtok = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
    if not (cid and csec and rtok):
        print("Kredensial YouTube tidak lengkap.", file=sys.stderr)
        return 2
    try:
        token = get_access_token(cid, csec, rtok)
        res = set_thumbnail(args.video_id, args.thumbnail, token)
        if res.get("ok"):
            print(f"Thumbnail terpasang: {args.video_id}")
            return 0
        if res.get("skipped"):
            print("Thumbnail dilewati (file tidak ada).")
            return 0
        print(f"Gagal pasang thumbnail: {res.get('error')}", file=sys.stderr)
        return 1
    except UploadError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
