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
import threading
import signal
import platform
from typing import Optional


# ====================== 基础配置，请根据实际环境修改 ======================
# Nginx配置 - 请在此处修改Nginx安装路径
NGINX_INSTALL_PATH = r"D:\\Program Files\\nginx-1.28.1"  # 您提供的Nginx静态路径
NGINX_CONF = r"E:\\Soonwin_OA\\nginx.conf"
NGINX_EXE = os.path.join(NGINX_INSTALL_PATH, "nginx.exe")  # 修复：统一Nginx可执行文件路径
NGINX_PORT = 5183

# 后端项目路径
BACKEND_DIR = r"E:\\Soonwin_OA\\soonwin-os-Python-Server"

# 前端项目路径
FRONTEND_DIR = r"E:\\Soonwin_OA\\soonwin-oa-VUE-FrontEnd"

# 前端构建输出路径 (Nginx静态文件目录)
FRONTEND_DIST_DIR = r"E:\\Soonwin_OA\\soonwin-oa-VUE-FrontEnd\\dist"

# mime.types
MIME_TYPES_PATH = r"D:\\Program Files\\nginx-1.28.1\\conf\\mime.types"

# 新增：低权限PID目录（避免Program Files权限问题）
NGINX_PID_DIR = r"D:\\nginx_temp"

# 确保PID目录存在
os.makedirs(NGINX_PID_DIR, exist_ok=True)
NGINX_PID_PATH = os.path.join(NGINX_PID_DIR, "nginx.pid").replace("\\", "/")

# Nginx配置模板
# 修复点1：给含空格的mime.types路径添加引号，并用统一的/分隔符
NGINX_CONFIG_TEMPLATE = f"""# oa_frontend.conf 完整配置（由Python脚本自动生成）
# 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
worker_processes  1;  # 内网自用，1个进程足够
pid        "{NGINX_PID_PATH}";  # 移到低权限目录，避免Program Files权限问题

events {{
    worker_connections  1024;
}}

http {{
    include       "{MIME_TYPES_PATH.replace('\\', '/')}";  # 引号包裹含空格路径，单斜杠
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout  65;

    # 后端服务代理配置（保留/api前缀转发）
    upstream backend_server {{
        server 127.0.0.1:5000;
        keepalive 64;
    }}

    server {{
        listen       {NGINX_PORT};
        server_name  localhost 192.168.110.13;  # 适配局域网访问

        # 前端静态文件目录
        root         {FRONTEND_DIST_DIR.replace('\\', '/')};
        index        index.html;

        # 反向代理：/api开头的请求转发到后端（保留/api前缀）
        location /api/ {{
            proxy_pass http://backend_server;  # 不带末尾/，保留/api前缀
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 60s;
        }}

        # Vue History模式兼容：刷新页面不404
        location / {{
            try_files $uri $uri/ /index.html;
        }}

        # 禁止访问隐藏文件
        location ~ /\. {{
            deny all;
        }}
    }}
}}
"""


class OAServerManager:
    def __init__(self):
        # 基础配置
        self.nginx_conf = NGINX_CONF
        self.nginx_exe = NGINX_EXE  # 使用统一的Nginx可执行文件路径
        self.nginx_port = NGINX_PORT
        self.backend_dir = BACKEND_DIR
        self.frontend_dir = FRONTEND_DIR
        self.mime_path = MIME_TYPES_PATH
        self.nginx_pid_path = NGINX_PID_PATH  # 新增：PID路径属性

        # 存储运行的进程
        self.running_processes = []

        # 优雅关闭信号处理
        if platform.system().lower() != "windows":
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    def generate_nginx_config(self):
        """生成Nginx配置文件 - 修复PID路径格式"""
        try:
            # 关键：将PID路径转为Windows风格的反斜杠，且确保目录存在
            pid_path = self.nginx_pid_path.replace('/', '\\')
            # 确保PID目录存在（避免Nginx创建PID文件失败）
            os.makedirs(os.path.dirname(pid_path), exist_ok=True)

            # 统一路径处理
            mime_types_path = self.mime_path.replace('\\', '/')
            frontend_dist = FRONTEND_DIST_DIR.replace('\\', '/')

            config_content = f"""# oa_frontend.conf 完整配置（由Python脚本自动生成）
    worker_processes  1;  # 内网自用，1个进程足够
    pid        "{pid_path}";  # 修复：Windows风格绝对路径，加引号

    events {{
        worker_connections  1024;
    }}

    http {{
        include       "{mime_types_path}";
        default_type  application/octet-stream;
        sendfile        on;
        keepalive_timeout  65;

        upstream backend_server {{
            server 127.0.0.1:5000;
            keepalive 64;
        }}

        server {{
            listen       {self.nginx_port};
            # server_name  localhost 192.168.110.13;
            # 修改：server_name 改为 _（匹配所有IP/域名），适配192.168.30.xx网段
            server_name  _;
            root         {frontend_dist};
            index        index.html;

            location /api/ {{
                proxy_pass http://backend_server/;  # 补充末尾的/，避免路径拼接错误
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
            }}

            location / {{
                try_files $uri $uri/ /index.html;
            }}

            location ~ /\\. {{
                deny all;
            }}
        }}
    }}
    """
            with open(self.nginx_conf, 'w', encoding='utf-8') as f:
                f.write(config_content)
            print(f"[v] Nginx配置文件已生成: {self.nginx_conf}")
            print(f"[v] 配置中PID路径: {pid_path}")
            return True
        except Exception as e:
            print(f"[!] 生成Nginx配置文件失败: {e}")
            return False

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
        强制杀死占用指定端口的进程（Windows）
        :param port: 要释放的端口号
        """
        try:
            # 查找占用端口的PID
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'tcp'],
                capture_output=True,
                text=True,
                encoding='gbk'
            )
            lines = result.stdout.split('\n')
            pid = None
            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    break

            if pid:
                # 终止进程
                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                print(f"[v] 已强制终止占用{port}端口的进程(PID: {pid})")
                time.sleep(2)  # 等待端口释放
            else:
                print(f"[v] {port}端口未被占用")
        except Exception as e:
            print(f"[!] 释放{port}端口失败: {e}")

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
                # 后端命令包含"python run.py"，前端命令包含"yarn"或"npm"
                if "python run.py" in command:
                    # 后端命令需要激活Python虚拟环境
                    activate_cmd = "call venv\\Scripts\\activate.bat && " if os.path.exists(f"{self.backend_dir}\\venv\\Scripts\\activate.bat") else ""
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
                activate_cmd = f"source {self.backend_dir}/venv/bin/activate && " if os.path.exists(f"{self.backend_dir}/venv/bin/activate") else ""
                full_command = f"gnome-terminal -e 'bash -c \"{activate_cmd}{command}; exec bash\"' || xterm -e 'bash -c \"{activate_cmd}{command}; exec bash\"'"
                proc = subprocess.Popen(full_command, shell=True)
                self.running_processes.append(proc)
                print(f"[v] {name} 已在新终端中启动")
                return proc
        except Exception as e:
            print(f"[!] 启动 {name} 失败: {e}")
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
                print(f"[v] 已创建Nginx PID目录: {pid_dir}")

            nginx_dir = os.path.dirname(self.nginx_exe)
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
                print(f"[!] Nginx错误信息: {error_msg}")
                # 补充：PID文件相关错误提示
                if "CreateFile() .*nginx.pid failed" in error_msg:
                    print(f"[!] 解决方案：检查PID目录权限 -> {pid_dir}")
                    print(f"[!] 或手动创建目录：mkdir {pid_dir}")
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
            return False

    def start_stable_version(self):
        """启动稳定版服务 (后端5000 + Nginx)"""
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

        backend_cmd = f"python run.py --port {backend_port} --debug=False"
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

        backend_cmd = f"python run.py --port {backend_port}"
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
        """停止Nginx服务"""
        print("=" * 55)
        print("                停止Nginx...")
        print("=" * 55)

        # 第一步：执行正常stop命令
        self.run_nginx("stop")
        time.sleep(3)  # 延长等待时间

        # 第二步：检查端口是否仍被占用，若占用则强制释放
        if not self.check_port_with_netstat(self.nginx_port):
            print(f"[!] Nginx正常停止失败，强制释放{self.nginx_port}端口...")
            self.kill_port_process(self.nginx_port)
            time.sleep(2)

        # 第三步：校验停止结果
        if self.check_port_with_netstat(self.nginx_port):
            print(f"[v] Nginx停止成功，端口{self.nginx_port}已释放")
        else:
            print(f"[!] Nginx停止失败，端口{self.nginx_port}仍被占用，请手动检查")

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
            if response not in ['y', 'yes', '是']:
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