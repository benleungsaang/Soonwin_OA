#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OA系统启动/维护脚本 - Python版本
用于替代原有的BAT脚本，提供相同功能但更好的跨平台兼容性

配置说明：以下路径请根据实际部署环境修改
"""
import os
import sys
import subprocess
import socket
import time
import signal
import platform


# ====================== 基础配置，请根据实际环境修改 ======================

# 确保 nginx 目录存在
# NGINX_FILES = os.path.join(os.getcwd(),  "nginx")
# os.makedirs(NGINX_FILES, exist_ok=True)
NGINX_INSTALL_PATH = os.path.join(os.getcwd(),  "nginx-1.28.1")
NGINX_TEMP_FILES = os.path.join(NGINX_INSTALL_PATH, 'temp', "personal_temp_files")
os.makedirs(NGINX_TEMP_FILES, exist_ok=True)
NGINX_EXE = os.path.join(NGINX_INSTALL_PATH, "nginx.exe") # nginx.exe
MIME_TYPES_PATH = os.path.join(NGINX_INSTALL_PATH, "conf", "mime.types") # nginx 自带的 mime.types
NGINX_CONF = os.path.join(NGINX_INSTALL_PATH, 'conf', "nginx.conf") # 自生成的 nginx.conf 文件路径
NGINX_PID_PATH = os.path.join(NGINX_INSTALL_PATH, 'logs', "nginx.pid") # 开启nginx后会生成一个PID文件，方便停止程序时使用，实际经常用不上
NGINX_PORT = 5183

if os.path.exists("soonwin-os-Python-Server"):
    # 后端项目路径
    BACKEND_DIR = os.path.join(os.getcwd(), "soonwin-os-Python-Server")
    # 前端项目路径
    FRONTEND_DIR = os.path.join(os.getcwd(), "soonwin-oa-VUE-FrontEnd")
else:
    # 后端项目路径
    BACKEND_DIR = os.path.join(os.getcwd(), "SoonwinOA_Backend")
    # 前端项目路径
    FRONTEND_DIR = os.path.join(os.getcwd(), "SoonwinOA_Frontend")


# 前端构建输出路径 (Nginx静态文件目录)
FRONTEND_DIST_DIR = os.path.join(FRONTEND_DIR, "dist")


# 生成时间
generate_time = time.strftime('%Y-%m-%d %H:%M:%S')


class OAServerManager:
    def __init__(self):
        # 基础配置
        self.nginx_exe = NGINX_EXE
        self.nginx_conf = NGINX_CONF
        self.mime_path = MIME_TYPES_PATH
        self.nginx_pid_path = NGINX_PID_PATH
        self.nginx_temp_files = NGINX_TEMP_FILES
        self.nginx_port = NGINX_PORT
        self.backend_dir = BACKEND_DIR
        self.frontend_dir = FRONTEND_DIR

        # 存储运行的进程
        self.running_processes = []

        # 优雅关闭信号处理
        if platform.system().lower() != "windows":
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    def generate_nginx_config(self, force_overwrite: bool = False):
        """生成Nginx配置文件"""
        try:
            # 检查文件是否已存在，非强制模式下提示
            if os.path.exists(self.nginx_conf) and not force_overwrite:
                print(f"[!] Nginx配置文件 {self.nginx_conf} 已存在，跳过生成（如需覆盖请使用重新生成功能）")
                return False

            # 修复5：PID路径转成Nginx兼容的正斜杠，且不加多余转义
            pid_path_nginx = self.nginx_pid_path.replace('\\', '/')

            # 统一路径处理
            mime_types_path = self.mime_path.replace('\\', '/')
            frontend_dist = FRONTEND_DIST_DIR.replace('\\', '/')
            nginx_temp_files = self.nginx_temp_files.replace('\\', '/')

            config_content = """# oa_frontend.conf 完整配置（由Python脚本自动生成）
worker_processes  1;  # 内网自用，1个进程足够
pid        "{}";  # 修复：Nginx兼容的正斜杠路径，加引号

events {{
    worker_connections  1024;
}}

http {{
    include       "{}";
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout  65;

    upstream backend_server {{
        server 127.0.0.1:5000;
        keepalive 64;
    }}

    server {{
        listen       {};
        # server_name  localhost 192.168.110.13;
        # 修改：server_name 改为 _（匹配所有IP/域名），适配192.168.30.xx网段
        server_name  _;
        root         {};
        index        index.html;
        # 核心：允许200MB的请求体（必须≥你的最大上传文件大小）
        client_max_body_size 200M;

        # 请求体缓冲区大小（Windows下建议适度增大）
        # 默认16K太小，大文件会频繁写临时文件，调整为128K
        client_body_buffer_size 128K;

        # 指定请求体临时文件存储路径（Windows下需确保目录存在）
        # 避免系统临时目录权限问题，建议自定义
        client_body_temp_path "{}";

        # 代理缓冲区（针对/api/转发的请求，避免后端接收不完整）
        proxy_buffering on;
        proxy_buffer_size 64K;
        proxy_buffers 4 64K;

        location /api/ {{
            proxy_pass http://backend_server;  # 无末尾/，保留/api
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 60s;
            # 新增：跨域头（避免移动端跨域报错）
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS';
            add_header Access-Control-Allow-Headers 'Content-Type, Authorization';

            # 新增：处理OPTIONS预检请求（避免跨域报错）
            if ($request_method = 'OPTIONS') {{
                return 204;
            }}
        }}

        location / {{
            try_files $uri $uri/ /index.html;
        }}

        # 修复6：正则表达式转义正确（Nginx需要的是 /\\.）
        location ~ /\\\\. {{
            deny all;
        }}
    }}
}}
""".format(
    pid_path_nginx,
    mime_types_path,
    self.nginx_port,
    frontend_dist,
    nginx_temp_files
)

            with open(self.nginx_conf, 'w', encoding='utf-8') as f:
                f.write(config_content)

            # 额外：验证PID目录是否真的存在
            if not os.path.exists(os.path.dirname(self.nginx_pid_path)):
                os.makedirs(os.path.dirname(self.nginx_pid_path), exist_ok=True)

            print(f"[v] Nginx配置文件已{'强制' if force_overwrite else ''}生成: {self.nginx_conf}")
            return True
        except Exception as e:
            print(f"[!] 生成Nginx配置文件失败: {e}")
            import traceback
            traceback.print_exc()  # 新增：打印详细错误栈
            return False

    def regenerate_nginx_config(self):
        """重新生成Nginx配置文件（强制覆盖）"""
        print("=" * 55)
        print("                重新生成Nginx配置文件")
        print("=" * 55)

        # 二次确认，防止误操作
        try:
            confirm = input(f"确认要覆盖已有Nginx配置文件 {self.nginx_conf} 吗？(y/N): ").strip().lower()
            if confirm not in ['y', 'yes', '是', '']:
                print("[v] 用户取消覆盖操作")
                self._wait_for_input()
                return
        except:
            print("[!] 输入异常，取消操作")
            self._wait_for_input()
            return

        # 强制生成并覆盖
        success = self.generate_nginx_config(force_overwrite=True)

        if success:
            # 额外校验配置文件语法
            print("[v] 正在校验新生成的Nginx配置语法...")
            syntax_ok = self.run_nginx("-t")
            if syntax_ok:
                print("[v] ✅ 配置文件生成成功且语法校验通过")
            else:
                print("[!] ⚠️ 配置文件生成成功，但语法校验失败，请检查！")
        else:
            print("[!] ❌ 配置文件生成失败")

        self._wait_for_input()

    def check_paths(self):
        """检查所有配置路径是否存在"""
        print("=" * 60)
        print("                检查配置路径...")
        print("=" * 60)

        paths_to_check = [
            ("Nginx可执行文件", self.nginx_exe),
            ("后端项目目录", self.backend_dir),
            ("前端项目目录", self.frontend_dir),
            ("前端构建目录", FRONTEND_DIST_DIR),
            ("mime.types文件", self.mime_path)  # 新增：检查mime.types是否存在
        ]

        all_paths_exist = True

        for name, path in paths_to_check:
            exists = os.path.exists(path)
            status = "[v] 存在" if exists else "[!] 不存在"
            print(f"{name}: {path} {status}")
            if not exists:
                all_paths_exist = False

        # 特别检查后端虚拟环境
        venv_path = os.path.join(self.backend_dir, "venv", "Scripts", "activate.bat")
        venv_exists = os.path.exists(venv_path)
        status = "[v] 存在" if venv_exists else "[!] 不存在"
        print(f"后端虚拟环境: {venv_path} {status}")
        if not venv_exists:
            all_paths_exist = False

        # 新增：检查后端wsgi.py文件是否存在
        wsgi_path = os.path.join(self.backend_dir, "wsgi.py")
        wsgi_exists = os.path.exists(wsgi_path)
        status = "[v] 存在" if wsgi_exists else "[!] 不存在"
        print(f"后端WSGI文件: {wsgi_path} {status}")
        if not wsgi_exists:
            all_paths_exist = False

        # 特别检查前端配置文件
        frontend_config = os.path.join(self.frontend_dir, "package.json")
        frontend_config_exists = os.path.exists(frontend_config)
        status = "[v] 存在" if frontend_config_exists else "[!] 不存在"
        print(f"前端配置文件: {frontend_config} {status}")
        if not frontend_config_exists:
            all_paths_exist = False

        # 检查Nginx配置文件
        nginx_conf_exists = os.path.exists(self.nginx_conf)
        status = "[v] 存在" if nginx_conf_exists else "[!] 不存在"
        print(f"Nginx配置文件: {self.nginx_conf} {status}")

        print("=" * 60)

        if all_paths_exist and nginx_conf_exists:
            print("[v] 所有路径检查通过，可以正常启动服务")
        elif all_paths_exist and not nginx_conf_exists:
            print("[!] Nginx配置文件不存在，将自动生成")
            self.generate_nginx_config()
            print("[v] Nginx配置文件已生成")
        else:
            print("[!] 部分路径不存在，请检查配置并确认文件/目录已正确部署")

        print("=" * 60)

        return all_paths_exist

    def _signal_handler(self, signum, frame):
        """处理关闭信号，清理运行的进程"""
        print("\n[v] 正在停止所有运行的服务...")
        self._stop_all_processes()
        print("[v] 所有服务已停止，系统退出")
        sys.exit(0)

    def _stop_all_processes(self):
        """停止所有运行的子进程"""
        for proc in self.running_processes[:]:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"[v] 进程 {proc.pid} 已停止")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"[v] 进程 {proc.pid} 已强制终止")
            except Exception as e:
                print(f"[!] 停止进程 {proc.pid} 时出错: {e}")

        self.running_processes.clear()

        # 额外：终止所有waitress-serve进程（兜底）
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq OA System - *后端*'],
                          capture_output=True)
            print("[v] 已终止所有后端waitress-serve进程")
        except:
            pass

    def check_port(self, port: int) -> bool:
        """
        检查端口是否被占用
        :param port: 要检查的端口号
        :return: True if port is free, False if in use
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                return result != 0  # 连接失败=端口空闲
        except Exception:
            return False

    def check_port_with_netstat(self, port: int) -> bool:
        """
        使用netstat命令检查端口是否被占用
        :param port: 要检查的端口号
        :return: True if port is free, False if in use
        """
        try:
            result = subprocess.run(
                ['netstat', '-an'],
                capture_output=True,
                text=True,
                check=True,
                encoding='gbk'  # 修复：Windows下netstat输出为gbk编码
            )
            lines = result.stdout.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if f':{port}' in line_stripped and ('LISTENING' in line_stripped or 'LISTEN' in line_stripped):
                    print(f"[!] 端口{port}被占用，占用状态行：{line_stripped}")
                    return False  # 端口被占用，返回False
            return True  # 端口空闲，返回True
        except subprocess.CalledProcessError:
            # 如果netstat命令失败，回退到socket方法
            return self.check_port(port)

    def kill_port_process(self, port: int):
        """
        强制杀死占用指定端口的所有进程（Windows增强版）
        :param port: 要释放的端口号
        """
        try:
            # 步骤1：查找所有占用该端口的PID
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'tcp'],
                capture_output=True,
                text=True,
                encoding='gbk'
            )
            lines = result.stdout.split('\n')
            pids = set()  # 用集合去重，避免重复杀进程

            for line in lines:
                line_stripped = line.strip()
                if f':{port}' in line_stripped and 'LISTENING' in line_stripped:
                    try:
                        pid = line_stripped.split()[-1]
                        if pid.isdigit():
                            pids.add(pid)
                    except:
                        continue

            if not pids:
                print(f"[v] {port}端口未被占用，nginx 启动成功！")
                return

            # 步骤2：终止所有关联PID（包括子进程）
            for pid in pids:
                # 先尝试正常终止
                try:
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True, check=True)
                    print(f"[v] 已强制终止PID {pid}（占用{port}端口）")
                except subprocess.CalledProcessError:
                    # 若正常终止失败，尝试终止进程树
                    try:
                        subprocess.run(['taskkill', '/F', '/T', '/PID', pid], capture_output=True)
                        print(f"[v] 已强制终止PID {pid}及其子进程（占用{port}端口）")
                    except:
                        print(f"[!] 终止PID {pid}失败，请手动结束进程")

            # 步骤3：额外终止所有nginx.exe和python.exe进程（兜底）
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'nginx.exe'], capture_output=True)
                print(f"[v] 已终止所有nginx.exe进程（兜底）")
            except:
                pass

            try:
                subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq OA System - *后端*'],
                              capture_output=True)
                print(f"[v] 已终止所有后端Python进程（兜底）")
            except:
                pass

            # 步骤4：等待端口释放（关键：给Windows足够时间清理端口）
            print(f"[v] 等待5秒，让{port}端口完全释放...")
            time.sleep(5)

            # 步骤5：再次检查端口状态
            if self.check_port_with_netstat(port):
                print(f"[v] {port}端口已成功释放")
            else:
                print(f"[!] {port}端口仍显示被占用，可能是Windows网络栈延迟，建议等待10秒后重试")

        except Exception as e:
            print(f"[!] 释放{port}端口失败: {e}")
            import traceback
            traceback.print_exc()

    def start_process(self, command: str, cwd: str = None, name: str = "Process"):
        """
        启动一个进程
        :param command: 要执行的命令
        :param cwd: 工作目录
        :param name: 进程名称
        """
        try:
            if platform.system().lower() == "windows":
                # 根据命令类型判断是否需要激活后端虚拟环境
                # 后端命令包含"waitress-serve"，前端命令包含"yarn"或"npm"
                if "waitress-serve" in command:
                    # 后端命令需要激活Python虚拟环境
                    activate_cmd = "call venv\\Scripts\\activate.bat && " if os.path.exists(os.path.join(self.backend_dir, "venv", "Scripts", "activate.bat")) else ""
                else:
                    # 前端命令不需要激活Python虚拟环境
                    activate_cmd = ""

                # 修复：路径含空格时用引号包裹cwd
                full_cwd = f'"{cwd}"' if ' ' in cwd else cwd
                full_command = f"cd /d {full_cwd} && {activate_cmd}{command}"

                # 在Windows下使用start命令启动新窗口
                # 使用PowerShell的Start-Process来更好地处理路径和引号
                startup_cmd = f'start "OA System - {name}" cmd /k "{full_command}"'

                proc = subprocess.Popen(
                    startup_cmd,
                    shell=True,
                    cwd=cwd  # 明确指定工作目录
                )
                self.running_processes.append(proc)
                print(f"[v] {name} 已在新窗口中启动 (PID: {proc.pid})")
                return proc
            else:
                activate_cmd = f"source {self.backend_dir}/venv/bin/activate && " if os.path.exists(os.path.join(self.backend_dir, "venv", "bin", "activate")) else ""
                full_command = f"gnome-terminal -e 'bash -c \"{activate_cmd}{command}; exec bash\"' || xterm -e 'bash -c \"{activate_cmd}{command}; exec bash\"'"
                proc = subprocess.Popen(full_command, shell=True)
                self.running_processes.append(proc)
                print(f"[v] {name} 已在新终端中启动")
                return proc
        except Exception as e:
            print(f"[!] 启动 {name} 失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_nginx(self, cmd: str = ""):
        """
        执行Nginx命令 - 微调参数拼接逻辑，补充PID目录检查
        :param cmd: Nginx命令参数 (start, stop, reload等)
        """
        try:
            # 补充：检查PID目录是否存在，避免Nginx创建PID失败
            pid_dir = os.path.dirname(self.nginx_pid_path)
            if not os.path.exists(pid_dir):
                os.makedirs(pid_dir, exist_ok=True)

            nginx_dir = os.path.dirname(self.nginx_exe)
            # 修复7：处理配置文件路径的引号（避免空格问题）
            nginx_conf_quoted = f'"{self.nginx_conf}"' if ' ' in self.nginx_conf else self.nginx_conf

            # 构造Nginx命令
            nginx_cmd = [self.nginx_exe]
            if cmd.strip() == "stop":
                nginx_cmd.extend(["-s", "stop", "-c", nginx_conf_quoted])
            elif cmd.strip() == "quit":
                nginx_cmd.extend(["-s", "quit", "-c", nginx_conf_quoted])
            elif cmd.strip() == "reload":
                nginx_cmd.extend(["-s", "reload", "-c", nginx_conf_quoted])
            elif cmd.strip() == "-t":
                nginx_cmd.extend(["-t", "-c", nginx_conf_quoted])
            else:
                # 核心微调：仅当cmd为空时加-c（启动Nginx的核心场景）
                # 避免传入冗余参数导致配置加载异常
                if not cmd:
                    nginx_cmd.extend(['-c', nginx_conf_quoted])
                else:
                    # 若有自定义cmd（如带参数的启动命令），先拆分再处理
                    cmd_parts = cmd.split()
                    # 确保-c参数优先（覆盖默认配置）
                    if "-c" not in cmd_parts:
                        nginx_cmd.extend(['-c', nginx_conf_quoted])
                        nginx_cmd.extend(cmd_parts)
                    else:
                        nginx_cmd.extend(cmd_parts)

            # 打印最终执行的命令（便于调试）
            print(f"[v] 执行Nginx命令: {' '.join(nginx_cmd)}")

            # 执行命令并捕获输出
            result = subprocess.run(
                nginx_cmd,
                cwd=nginx_dir,
                capture_output=True,
                text=True,
                encoding='gbk'  # Windows下Nginx输出为gbk
            )

            if result.returncode == 0:
                if result.stdout:
                    print(f"[v] Nginx命令执行成功: {result.stdout.strip()}")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                # 因为后续会强制 kill 5183端口相关的程序，所以这里的使用 pid错误跟 stop错误都不作提醒
                if all(keyword not in error_msg for keyword in ['nginx.pid', 'stop']):
                    print(f"[!] Nginx错误信息: {error_msg}")
                if "-t" in cmd and error_msg:
                    print(f"[!] Nginx配置文件语法错误，请检查：{self.nginx_conf}")
                return False
        except FileNotFoundError as e:
            print(f"[!] 未找到Nginx可执行文件: {self.nginx_exe}")
            print(f"[!] 请检查NGINX_INSTALL_PATH配置是否正确")
            print(f"[!] 错误详情: {e}")
            return False
        except Exception as e:
            print(f"[!] 执行Nginx命令出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start_stable_version(self):
        """启动稳定版服务 (后端5000 + Nginx动态代理)"""
        print("=" * 55)
        print("                启动稳定版服务...")
        print("=" * 55)

        # 检查虚拟环境
        venv_path = os.path.join(self.backend_dir, "venv", "Scripts", "activate.bat")
        if not os.path.exists(venv_path):
            print(f"[!] 后端未找到Python虚拟环境！")
            print(f"路径：{venv_path}")
            self._wait_for_input()
            return

        # 检查wsgi.py文件
        wsgi_path = os.path.join(self.backend_dir, "wsgi.py")
        if not os.path.exists(wsgi_path):
            print(f"[!] 未找到后端WSGI文件！")
            print(f"路径：{wsgi_path}")
            self._wait_for_input()
            return

        # 启动后端 (端口5000)
        print("[1/2] 启动稳定版后端，5000端口...")
        backend_port = 5000
        if not self.check_port_with_netstat(backend_port):
            print(f"[!] 端口{backend_port}已被占用，尝试强制释放...")
            self.kill_port_process(backend_port)
            # 再次检查，仍占用则退出
            if not self.check_port_with_netstat(backend_port):
                print(f"[!] 端口{backend_port}释放失败，启动服务失败")
                self._wait_for_input()
                return

        # 修改：使用waitress-serve启动后端
        backend_cmd = f"waitress-serve --host=0.0.0.0 --port={backend_port} wsgi:application"
        self.start_process(backend_cmd, cwd=self.backend_dir, name="稳定版后端(5000)")
        time.sleep(2)

        # 启动Nginx
        print("[2/2] 启动Nginx服务...")
        self.run_nginx("stop")  # 先停止可能运行的nginx
        time.sleep(2)  # 修复：等待端口释放
        # 强制释放Nginx端口
        self.kill_port_process(self.nginx_port)
        # 启动nginx
        success = self.run_nginx()

        if not success:
            print(f"[!] Nginx启动失败，请检查配置文件")
        else:
            time.sleep(2)
            if self.check_port_with_netstat(self.nginx_port):
                print(f"[!] Nginx启动后端口{self.nginx_port}未监听，启动失败")
            else:
                print()
                print("=" * 55)
                print("[v] 稳定版启动完毕！")
                print(f"[?]  后端：http://localhost:{backend_port}")
                print(f"[?] 前端：http://localhost:{self.nginx_port}")
                print("=" * 55)

        self._wait_for_input()

    def start_dev_version(self):
        """启动开发版服务 (后端5001 + 前端5173)"""
        print("=" * 55)
        print("                启动开发版服务...")
        print("=" * 55)

        # 检查虚拟环境
        venv_path = os.path.join(self.backend_dir, "venv", "Scripts", "activate.bat")
        if not os.path.exists(venv_path):
            print(f"[!] 后端未找到Python虚拟环境！")
            self._wait_for_input()
            return

        # 检查wsgi.py文件
        # wsgi_path = os.path.join(self.backend_dir, "wsgi.py")
        # if not os.path.exists(wsgi_path):
        #     print(f"[!] 未找到后端WSGI文件！")
        #     print(f"路径：{wsgi_path}")
        #     self._wait_for_input()
        #     return

        # 检查前端项目
        frontend_config = os.path.join(self.frontend_dir, "package.json")
        if not os.path.exists(frontend_config):
            print(f"[!] 未找到前端项目文件！")
            self._wait_for_input()
            return

        # 启动后端 (端口5001)
        print("[1/2] 启动开发版后端，5001端口...")
        backend_port = 5001
        if not self.check_port_with_netstat(backend_port):
            print(f"[!] 端口{backend_port}已被占用，尝试强制释放...")
            self.kill_port_process(backend_port)
            if not self.check_port_with_netstat(backend_port):
                print(f"[!] 端口{backend_port}释放失败，启动服务失败")
                self._wait_for_input()
                return

        # 开发时使用普通方式启动服务
        backend_cmd = r"python .\run.py --port 5001"
        self.start_process(backend_cmd, cwd=self.backend_dir, name="开发版后端(5001)")
        time.sleep(2)

        # 启动前端 (端口5173)
        print("[2/2] 启动开发版前端，5173端口...")
        frontend_port = 5173
        if not self.check_port_with_netstat(frontend_port):
            print(f"[!] 端口{frontend_port}已被占用，尝试强制释放...")
            self.kill_port_process(frontend_port)
            if not self.check_port_with_netstat(frontend_port):
                print(f"[!] 端口{frontend_port}释放失败，启动服务失败")
                self._wait_for_input()
                return

        frontend_cmd = f"yarn dev --port {frontend_port} --host 0.0.0.0"
        self.start_process(frontend_cmd, cwd=self.frontend_dir, name="开发版前端(5173)")
        time.sleep(2)

        print()
        print("=" * 55)
        print("[v] 开发版启动完毕！")
        print(f"[?]  后端：http://localhost:{backend_port}")
        print(f"[?]  前端：http://localhost:{frontend_port}")
        print("=" * 55)
        self._wait_for_input()

    def nginx_start(self):
        """启动Nginx服务 - 简化调用逻辑"""
        print("=" * 55)
        print("                启动Nginx...")
        print("=" * 55)

        if not os.path.exists(self.nginx_conf):
            print("[!] 未找到Nginx配置文件，自动生成...")
            if not self.generate_nginx_config():
                print("[!] Nginx配置文件生成失败，启动终止")
                self._wait_for_input()
                return

        # 先停止nginx并释放端口（自动带-c参数）
        self.run_nginx("stop")
        time.sleep(2)
        self.kill_port_process(self.nginx_port)

        # 检查端口是否空闲
        if not self.check_port_with_netstat(self.nginx_port):
            print(f"[!] 端口{self.nginx_port}仍被占用，启动失败")
            self._wait_for_input()
            return

        # 核心：直接调用run_nginx()，会自动添加-c参数加载自定义配置
        success = self.run_nginx()

        if success:
            time.sleep(3)
            # 校验端口监听状态（False=端口被占用=启动成功）
            if self.check_port_with_netstat(self.nginx_port):
                print(f"[!] Nginx启动后端口{self.nginx_port}未监听，启动失败")
                self.kill_port_process(self.nginx_port)
            else:
                print(f"[v] Nginx启动完毕，地址：http://localhost:{self.nginx_port}")
                print(f"[v] Nginx PID文件路径：{self.nginx_pid_path}")
        else:
            print("[!] Nginx启动失败！请检查配置文件或端口状态")
            # 语法检查（自动带-c参数）
            print("[!] 正在检查Nginx配置文件语法...")
            self.run_nginx("-t")

        self._wait_for_input()

    def nginx_stop(self):
        """停止Nginx服务（增强版：多维度终止）"""
        print("=" * 55)
        print("                停止Nginx...")
        print("=" * 55)

        # 第一步：尝试通过Nginx命令正常停止（忽略PID文件错误）
        print("[1/4] 尝试正常停止Nginx...")
        result = self.run_nginx("stop")
        time.sleep(3)  # 延长等待时间

        # 第二步：强制终止所有nginx.exe进程（不管端口）
        print("[2/4] 强制终止所有nginx.exe进程...")
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'nginx.exe'], capture_output=True)
            print(f"[v] 已发送终止命令给所有nginx.exe进程")
        except:
            pass
        time.sleep(2)

        # 第三步：强制释放Nginx端口
        print(f"[3/4] 强制释放{self.nginx_port}端口...")
        self.kill_port_process(self.nginx_port)

        # 第四步：最终校验端口状态
        print("[4/4] 校验端口释放状态...")
        if self.check_port_with_netstat(self.nginx_port):
            print(f"[v] Nginx停止成功，端口{self.nginx_port}已释放")
        else:
            print(f"[!] Nginx停止后端口{self.nginx_port}仍显示被占用：")
            # 打印当前端口占用详情
            result = subprocess.run(['netstat', '-ano', '-p', 'tcp'], capture_output=True, text=True, encoding='gbk')
            for line in result.stdout.split('\n'):
                if f':{self.nginx_port}' in line and 'LISTENING' in line:
                    print(f"    {line.strip()}")
            print("[!] 解决方案：等待10秒后重试，或手动在任务管理器结束nginx.exe进程")

        self._wait_for_input()

    def nginx_restart(self):
        """重启Nginx服务"""
        print("=" * 55)
        print("                重启Nginx...")
        print("=" * 55)

        # 第一步：停止Nginx
        self.nginx_stop()
        # 校验停止状态
        if not self.check_port_with_netstat(self.nginx_port):
            print(f"[!] Nginx停止不彻底，重启终止")
            self._wait_for_input()
            return

        time.sleep(1)
        self.nginx_start()

        # 第三步：校验重启结果
        if not self.check_port_with_netstat(self.nginx_port):
            print("[v] Nginx重启成功！")
        else:
            print("[!] Nginx重启失败，请检查配置或端口")

        self._wait_for_input()

    def show_menu(self):
        """显示主菜单"""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 55)
            print("                OA系统启动/维护菜单")
            print("=" * 55)
            print("[1] 稳定版 - 启动5000 + Nginx动态代理")
            print("[2] 开发版 - 启动5001 + yarn dev(5173)")
            print("[3] Nginx - 启动服务")
            print("[4] Nginx - 停止服务")
            print("[5] Nginx - 重启服务")
            print("[6] Nginx - 重新生成配置文件（覆盖）")  # 新增选项
            print("[0] 退出")
            print("=" * 55)

            try:
                choice = input("请输入数字：0-5：").strip()

                if choice == "1":
                    self.start_stable_version()
                elif choice == "2":
                    self.start_dev_version()
                elif choice == "3":
                    self.nginx_start()
                elif choice == "4":
                    self.nginx_stop()
                elif choice == "5":
                    self.nginx_restart()
                elif choice == "6":  # 新增分支
                    self.regenerate_nginx_config()
                elif choice == "0":
                    self._stop_all_processes()
                    self.run_nginx("stop")  # 退出时停止nginx
                    print("[v] 系统退出，所有服务已停止")
                    break
                else:
                    print("[!] 输入错误，只能输入0-5之间的数字")
                    self._wait_for_input()

            except KeyboardInterrupt:
                print("\n\n[v] 正在退出系统...")
                self._stop_all_processes()
                self.run_nginx("stop")
                break
            except Exception as e:
                print(f"[!] 发生错误: {e}")
                import traceback
                traceback.print_exc()
                self._wait_for_input()

    def _wait_for_input(self):
        """通用的等待用户输入函数"""
        try:
            input("按回车键继续...")
        except:
            time.sleep(2)


def main():
    """主函数"""
    # 检查是否为Windows系统
    if platform.system().lower() != "windows":
        print("[!] 该脚本仅支持Windows系统运行")
        return

    print("正在启动OA系统管理脚本...")

    # 创建服务器管理器实例
    manager = OAServerManager()

    # 首先检查所有路径
    if not manager.check_paths():
        print("\n[!] 路径检查未通过，是否继续？(y/N): ", end="")
        try:
            response = input().strip().lower()
            if response not in ['y', 'yes', '是', '']:
                print("用户选择退出。")
                return
        except:
            print("\n输入错误，退出程序。")
            return

    print("\n按回车键继续...")
    try:
        input()
    except:
        time.sleep(2)

    # 显示菜单
    manager.show_menu()


if __name__ == "__main__":
    # 以管理员身份运行检查（可选）
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        print("[!] 警告：未以管理员身份运行，可能导致Nginx(80/443端口)启动失败！")
        input("按回车键继续（建议以管理员身份重新运行）...")

    main()