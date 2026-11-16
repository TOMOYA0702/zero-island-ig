# ZERO ISLAND Instagram 自動投稿

`posts/YYYY-MM-DD/` に `1.jpg`〜`10.jpg` と `caption.txt` を置くと、その日の19:00ごろ @reijima_toji に自動投稿されます。
投稿が済むと同じフォルダに `posted.json` ができ、二重投稿はしません。

- 秘密情報：Settings → Secrets → Actions に `IG_ACCESS_TOKEN`（必須）、`IG_USER_ID`（任意）
- 手動で今すぐ流す：Actions → 「Instagram 自動投稿」→ Run workflow
