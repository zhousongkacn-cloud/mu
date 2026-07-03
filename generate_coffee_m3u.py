# -*- coding: utf-8 -*-
"""
咖啡直播 iPhone M3U 生成工具
作用：从 kafeizhibo.cc 抓取当前直播房间，解析线路，生成 iPhone/IPTV/VLC 可用的 coffee_live.m3u。
运行：python generate_coffee_m3u.py
可选：python generate_coffee_m3u.py --output coffee_live.m3u --serve
"""
import argparse
import json
import socket
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

HOST = "https://kafeizhibo.cc"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
TIMEOUT = 6

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Referer": HOST + "/live/all",
    "Origin": HOST,
}


def http_json(url, referer=None, timeout=TIMEOUT):
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    text = raw.decode("utf-8", errors="ignore")
    return json.loads(text)


def normalize_url(path):
    if not path:
        return ""
    path = str(path).strip()
    if path.startswith("http"):
        return path
    if path.startswith("//"):
        return "https:" + path
    return HOST + ("" if path.startswith("/") else "/") + path


def safe_text(value, default=""):
    if value is None:
        return default
    return str(value).strip() or default


def clean_title(text):
    text = safe_text(text, "咖啡直播")
    # M3U 标题尽量不要含有换行和逗号前的特殊控制字符
    return text.replace("\n", " ").replace("\r", " ").replace("$", " ").replace("#", " ").strip()


def fetch_live_rooms():
    """获取当前直播房间列表。"""
    data = http_json(HOST + "/api/v1/archor", referer=HOST + "/live/all")
    if str(data.get("code")) != "200":
        return []
    items = data.get("data") or []
    if not isinstance(items, list):
        return []
    return items


def fetch_room_detail(room_id):
    """获取单个房间线路。"""
    url = HOST + "/api/v1/room/" + quote(str(room_id))
    try:
        data = http_json(url, referer=HOST + "/room/" + quote(str(room_id)))
        if str(data.get("code")) != "200":
            return None
        return data.get("data") or {}
    except Exception:
        return None


def build_title(item, room_info=None, signal_name=None):
    room_info = room_info or {}
    home = safe_text(room_info.get("home_team") or item.get("home_team"))
    away = safe_text(room_info.get("away_team") or item.get("away_team"))
    league = safe_text(room_info.get("league") or item.get("league_name") or item.get("league"), "赛事")
    anchor = safe_text(item.get("name") or item.get("nickname") or item.get("title"))
    score_h = safe_text(room_info.get("home_score") or item.get("home_score"), "")
    score_a = safe_text(room_info.get("away_score") or item.get("away_score"), "")

    parts = []
    if league:
        parts.append(league)
    if home or away:
        parts.append((home + " vs " + away).strip())
    if score_h != "" and score_a != "":
        parts.append(score_h + "-" + score_a)
    if anchor:
        parts.append(anchor)
    if signal_name:
        parts.append(signal_name)
    return clean_title(" | ".join([p for p in parts if p]))


def extract_logo(item, detail=None):
    detail = detail or {}
    teams = detail.get("teams") or {}
    candidates = [
        item.get("screenshot"),
        item.get("cover"),
        item.get("home_team_logo"),
        (teams.get("home") or {}).get("logo"),
        (teams.get("away") or {}).get("logo"),
    ]
    for c in candidates:
        url = normalize_url(c)
        if url and "default" not in url:
            return url
    return ""


def generate_m3u(output_path):
    rooms = fetch_live_rooms()
    lines = ["#EXTM3U"]
    count = 0
    seen = set()

    for item in rooms:
        room_id = item.get("room_id") or item.get("id") or item.get("roomId")
        if not room_id:
            continue
        detail = fetch_room_detail(room_id) or {}
        signals = detail.get("signals") or []
        if not signals:
            archor = detail.get("archor") or {}
            if archor.get("stream_url"):
                signals = [archor]
            elif item.get("stream_url"):
                signals = [item]

        room_info = detail.get("room_info") or {}
        logo = extract_logo(item, detail)
        group = safe_text(room_info.get("league") or item.get("league_name") or "咖啡直播")

        for sig in signals:
            stream = safe_text(sig.get("stream_url") or sig.get("url") or sig.get("play_url") or sig.get("m3u8"))
            if not stream or stream in seen:
                continue
            seen.add(stream)
            signal_name = safe_text(sig.get("name") or sig.get("title"), "线路")
            title = build_title(item, room_info, signal_name)
            ext = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{title}'
            lines.append(ext)
            lines.append(stream)
            count += 1

    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return count, len(rooms)


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def serve_file(port):
    ip = get_lan_ip()
    print("\n已启动局域网服务。")
    print(f"iPhone 和电脑/安卓设备连接同一个 Wi‑Fi 后，在播放器里导入：")
    print(f"http://{ip}:{port}/coffee_live.m3u")
    print("\n保持这个窗口不要关闭。按 Ctrl+C 停止。\n")
    httpd = ThreadingHTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="生成咖啡直播 iPhone M3U 直播列表")
    parser.add_argument("--output", "-o", default="coffee_live.m3u", help="输出 M3U 文件名")
    parser.add_argument("--serve", action="store_true", help="生成后启动局域网 HTTP 服务")
    parser.add_argument("--port", type=int, default=8099, help="HTTP 服务端口")
    args = parser.parse_args()

    try:
        count, rooms = generate_m3u(args.output)
        print(f"生成完成：{args.output}")
        print(f"直播房间：{rooms} 个，播放线路：{count} 条")
        if count == 0:
            print("提示：当前可能没有直播，或接口临时不可访问。稍后重新运行。")
        if args.serve:
            serve_file(args.port)
    except (HTTPError, URLError) as e:
        print("访问咖啡直播接口失败：", e)
        sys.exit(1)
    except Exception as e:
        print("生成失败：", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
