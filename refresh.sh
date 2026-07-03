#!/bin/bash
# 一键从飞书多维表格获取最新数据并刷新浏览器本地页面

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "==========================================="
echo "🔄 正在同步飞书数据..."
echo "==========================================="

# 执行数据抓取
python3 scripts/fetch_data.py

if [ $? -eq 0 ]; then
    echo "==========================================="
    echo "✅ 同步成功！正在打开看板主页面..."
    echo "==========================================="
    # 打开部署在 GitHub Pages 的公网地址
    open "https://gyzwang.github.io/KOL-Marketing-Kanban/"
else
    echo "❌ 同步失败，请检查网络连接及 lark-cli 登录状态。"
fi
