import http.server
import socketserver
import subprocess
import os
import sys
import time
import socket

PORT = 8080

def get_local_ip():
    """获取本机的局域网 IP 地址"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 不需要真的连接上，只是为了获取出口 IP
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class AutoSyncHandler(http.server.SimpleHTTPRequestHandler):
    last_sync_time = 0
    sync_cooldown = 60  # 60 秒同步冷却时间，避免过于频繁拉取触发飞书限流

    def do_GET(self):
        # 拦截对主页或数据文件的请求，触发异步同步
        if self.path in ['/', '/index.html', '/scripts/data.js']:
            self.check_and_sync()
        return super().do_GET()

    def check_and_sync(self):
        current_time = time.time()
        # 判定是否需要同步
        if current_time - AutoSyncHandler.last_sync_time > AutoSyncHandler.sync_cooldown:
            AutoSyncHandler.last_sync_time = current_time
            print("⏳ 触发数据同步，正在后台拉取飞书最新数据...")
            
            # 使用 Popen 进行非阻塞异步调用，防止主页加载被卡死
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch_data.py")
            subprocess.Popen([sys.executable, script_path])

def run_server():
    # 切换到项目根目录，以便正确服务 index.html
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    
    local_ip = get_local_ip()
    
    handler = AutoSyncHandler
    # 允许多线程处理，提升内嵌网页加载体验
    class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        pass

    # 允许端口复用，避免频繁重启服务提示 Address already in use
    socketserver.TCPServer.allow_reuse_address = True
    
    with ThreadingHTTPServer(("", PORT), handler) as httpd:
        print("=========================================================")
        print("🚀 飞书看板内嵌 Web 服务器已启动！")
        print("=========================================================")
        print(f"🔗 本地访问地址: http://localhost:{PORT}")
        print(f"🔗 局域网访问地址: http://{local_ip}:{PORT}")
        print("=========================================================")
        print("👉 请在飞书多维表格中依次操作:")
        print("   1. 点击顶部 '+' 号，选择 '新建仪表盘'")
        print("   2. 在右侧组件库中拖入一个 '网页' 组件")
        print("   3. 在网页配置中，填入上面的【局域网访问地址】或【本地访问地址】")
        print("   4. 搞定！你和同事就可以直接在飞书里看到经过排版优化的看板了！")
        print("=========================================================")
        print("ℹ️ 提示: 每当在飞书里刷新该网页组件，后台都会自动同步最新数据。")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 服务器已关闭。")

if __name__ == "__main__":
    run_server()
