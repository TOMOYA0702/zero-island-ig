"""ZERO ISLAND Instagram 自動投稿
posts/YYYY-MM-DD/ に 1.jpg〜N.jpg と caption.txt を置くと、その日の実行で
@reijima_toji にカルーセル投稿する。投稿済みの日は posted.json が作られ、二重投稿しない。
"""
import json, os, sys, time, datetime, urllib.request, urllib.parse, pathlib

API = "https://graph.facebook.com/v21.0"
TOKEN = os.environ["IG_ACCESS_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]          # owner/repo
BRANCH = os.environ.get("BRANCH", "main")
JST = datetime.timezone(datetime.timedelta(hours=9))

def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{API}/{path}?{data.decode()}")
    else:
        req = urllib.request.Request(f"{API}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code} on {path}: {e.read().decode()}")

def ig_user_id():
    if os.environ.get("IG_USER_ID"):
        return os.environ["IG_USER_ID"]
    pages = call("GET", "me/accounts", fields="name,instagram_business_account{username}")
    for p in pages.get("data", []):
        acct = p.get("instagram_business_account")
        if acct and acct.get("username") == "reijima_toji":
            return acct["id"]
    sys.exit("reijima_toji が見つかりません: " + json.dumps(pages, ensure_ascii=False))

def wait_ready(cid):
    for _ in range(30):
        st = call("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st == "ERROR":
            sys.exit(f"container {cid} ERROR")
        time.sleep(5)
    sys.exit(f"container {cid} timeout")

def main():
    day = os.environ.get("POST_DATE") or datetime.datetime.now(JST).strftime("%Y-%m-%d")
    d = pathlib.Path("posts") / day
    if not d.is_dir():
        print(f"{day}: 投稿なし"); return
    if (d / "posted.json").exists():
        print(f"{day}: 投稿済み"); return
    imgs = sorted(p.name for p in d.glob("*.jpg"))
    caption = (d / "caption.txt").read_text(encoding="utf-8").strip()
    base = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/posts/{day}/"
    uid = ig_user_id()
    if os.environ.get("DRY_RUN") == "1":
        info = call("GET", uid, fields="username,media_count")
        for name in imgs:
            urllib.request.urlopen(base + name, timeout=30).read(10)
        print(f"確認OK: {info} / {day} 画像{len(imgs)}枚・キャプション{len(caption)}字（投稿はしていません）")
        return
    if len(imgs) == 1:
        cid = call("POST", f"{uid}/media", image_url=base + imgs[0], caption=caption)["id"]
    else:
        kids = []
        for name in imgs:
            k = call("POST", f"{uid}/media", image_url=base + name, is_carousel_item="true")["id"]
            wait_ready(k); kids.append(k)
        cid = call("POST", f"{uid}/media", media_type="CAROUSEL",
                   children=",".join(kids), caption=caption)["id"]
    wait_ready(cid)
    res = call("POST", f"{uid}/media_publish", creation_id=cid)
    (d / "posted.json").write_text(json.dumps(
        {"media_id": res.get("id"), "at": datetime.datetime.now(JST).isoformat()}, ensure_ascii=False))
    print(f"{day}: 投稿しました {res}")

if __name__ == "__main__":
    main()
