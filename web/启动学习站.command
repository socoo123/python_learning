#!/bin/zsh
# 双击启动本地学习站。web/ 根目录就是站点,不需要 Vite。
# 直接双击 index.html 也能看(file://)。这个脚本走 http,方便刷新。
cd "$(dirname "$0")" || exit 1

PORT=5188
if lsof -i :"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  open "http://localhost:$PORT/"
  exit 0
fi

( sleep 0.8; open "http://localhost:$PORT/" ) &
echo "学习站运行中:http://localhost:$PORT/"
echo "关闭本窗口(或 Ctrl-C)即停止服务。"
python3 -m http.server "$PORT" --directory .
