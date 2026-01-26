#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OA系统启动/维护脚本 - Python版本
替代传统BAT脚本，支持后端/前端/Nginx一站式管理，新增Nginx配置强制覆盖生成功能
"""
import os
import sys
import subprocess
import socket
import time
import signal
import platform
import traceback
from pathlib import Path

# ====================== 基础配置（请根据实际环境修改） ======================
# Nginx相关配置
NGINX_INSTALL_PATH = Path(__file__).parent.parent / "nginx-1.28.1"  # Nginx安装目录
NGINX_CONF = NGINX_INSTALL_PATH / "conf" / "oa_nginx.conf"          # 生成的配置文件路径
NGINX_PORT = 5183                                                  # Nginx监听端口
NGINX_PID_DIR = Path(os.environ.get("TEMP", "./")) / "nginx_pid"    # Nginx PID存储目录（低权限路径）

# 后端配置
BACKEND_DIR = Path(__file__).parent.parent / "soonwin-os-Python-Server"  # 后端项目目录
BACKEND_VENV_DIR = BACKEND_DIR / "venv" / "Scripts"                     # 虚拟环境目录
BACKEND_STABLE_PORT = 5000                                              # 稳定版端口
BACKEND_DEV_PORT = 5001                                                 # 开发版端口

# 前端配置
FRONTEND_DIR = Path(__file__).parent.parent / "soonwin-oa-VUE-FrontEnd"  # 前端项目目录
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"                               # 前端构建目录
FRONTEND_DEV_PORT = 5173                                                # 前端开发端口

# 系统配置
SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
ENCODING = "gbk" if IS_WINDOWS else "utf-8"

# ====================== 核心管理类 ======================
class OAServerManager:
    def __init__(self):
        # 初始化路径（兼容字符串/Path对象）
        self.nginx_exe = NGINX_INSTALL_PATH / "nginx.exe" if IS_WINDOWS else NGINX_INSTALL_PATH / "sbin" / "nginx"
        self.nginx_conf = Path(NGINX_CONF)
        self.nginx_port = NGINX_PORT
        self.nginx_pid_dir = Path(NGINX_PID_DIR)

        self.backend_dir = Path(BACKEND_DIR)
        self.backend_venv_python = self.backend_dir / "venv" / ("Scripts/python.exe" if IS_WINDOWS else "bin/python3")
        self.backend_stable_port = BACKEND_STABLE_PORT
        self.backend_dev_port = BACKEND_DEV_PORT

        self.frontend_dir = Path(FRONTEND_DIR)
        self.frontend_dist_dir = Path(FRONTEND_DIST_DIR)
        self.frontend_dev_port = FRONTEND_DEV_PORT

        # 进程管理
        self.running_processes = []
        self._setup_signal_handler()

    def _setup_signal_handler(self):
        """设置信号处理（优雅退出）"""
        if not IS_WINDOWS:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """信号处理函数"""
        print("\n[!] 接收到退出信号，正在停止所有服务...")
        self._stop_all_processes()
        self.run_nginx("stop")
        sys.exit(0)

    def _wait_for_input(self):
        """等待用户输入（兼容Windows/Linux）"""
        input("\n按回车键继续...")

    def check_paths(self):
        """检查核心路径是否存在"""
        print("[v] 开始路径检查...")
        check_result = True

        # 检查Nginx可执行文件
        if not self.nginx_exe.exists():
            print(f"[!] Nginx可执行文件不存在: {self.nginx_exe}")
            check_result = False
        else:
            print(f"[v] Nginx路径: {self.nginx_exe}")

        # 检查后端目录
        if not self.backend_dir.exists():
            print(f"[!] 后端项目目录不存在: {self.backend_dir}")
            check_result = False
        else:
            print(f"[v] 后端目录: {self.backend_dir}")

            # 检查后端虚拟环境
            if not self.backend_venv_python.exists():
                print(f"[!] 后端虚拟环境Python不存在: {self.backend_venv_python}")
                check_result = False
            else:
                print(f"[v] 后端虚拟环境: {self.backend_venv_python}")

            # 检查WSGI文件
            wsgi_file = self.backend_dir / "wsgi.py"
            if not wsgi_file.exists():
                print(f"[!] 后端WSGI文件不存在: {wsgi_file}")
                check_result = False

        # 检查前端目录
        if not self.frontend_dir.exists():
            print(f"[!] 前端项目目录不存在: {self.frontend_dir}")
            check_result = False
        else:
            print(f"[v] 前端目录: {self.frontend_dir}")

            # 检查前端dist目录（非必须，开发模式不需要）
            if not self.frontend_dist_dir.exists():
                print(f"[!] 前端构建目录不存在: {self.frontend_dist_dir}（开发模式可忽略）")

        # 自动生成Nginx配置（首次运行）
        if not self.nginx_conf.exists():
            print(f"[v] Nginx配置文件不存在，自动生成: {self.nginx_conf}")
            self.generate_nginx_config()

        print(f"[v] 路径检查完成: {'通过' if check_result else '存在错误'}")
        return check_result

    def check_port(self, port):
        """检查端口是否被占用（基础版）"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0  # True=端口被占用
        except Exception as e:
            print(f"[!] 检查端口{port}失败: {e}")
            return True

    def check_port_with_netstat(self, port):
        """检查端口占用（精准版，基于netstat）"""
        try:
            if IS_WINDOWS:
                cmd = f"netstat -ano | findstr :{port}"
            else:
                cmd = f"netstat -tulpn | grep :{port}"

            result = subprocess.run(
                cmd, shell=True, capture_output=True, encoding=ENCODING
            )
            return len(result.stdout.strip()) > 0
        except Exception as e:
            print(f"[!] 精准检查端口{port}失败: {e}")
            return self.check_port(port)

    def kill_port_process(self, port):
        """强制释放指定端口"""
        print(f"[v] 开始释放端口{port}...")
        try:
            if IS_WINDOWS:
                # Windows: 查找PID并终止
                cmd_find = f"netstat -ano | findstr :{port}"
                result = subprocess.run(
                    cmd_find, shell=True, capture_output=True, encoding=ENCODING
                )

                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                # 终止进程
                                subprocess.run(
                                    f"taskkill /F /PID {pid}",
                                    shell=True, capture_output=True
                                )
                                print(f"[v] 已终止占用端口{port}的进程(PID: {pid})")
                            except Exception as e:
                                print(f"[!] 终止PID{pid}失败: {e}")
                else:
                    print(f"[v] 端口{port}未被占用")
            else:
                # Linux: 使用fuser
                subprocess.run(
                    f"fuser -k {port}/tcp",
                    shell=True, capture_output=True
                )
                print(f"[v] 已释放Linux端口{port}")

            # 兜底：终止相关进程
            self._kill_related_processes()

            # 等待端口释放
            time.sleep(2)
            if self.check_port(port):
                print(f"[!] 端口{port}释放失败，仍被占用")
                return False
            else:
                print(f"[v] 端口{port}释放成功")
                return True

        except Exception as e:
            print(f"[!] 释放端口{port}失败: {e}")
            traceback.print_exc()
            return False

    def _kill_related_processes(self):
        """终止相关进程（兜底）"""
        try:
            if IS_WINDOWS:
                # 终止nginx和python进程
                subprocess.run("taskkill /F /IM nginx.exe 2>nul", shell=True)
                subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq OA*\" 2>nul", shell=True)
            else:
                subprocess.run("pkill -f nginx", shell=True)
                subprocess.run("pkill -f waitress-serve", shell=True)
        except:
            pass

    def generate_nginx_config(self, force_overwrite: bool = False):
        """
        生成Nginx配置文件
        :param force_overwrite: 是否强制覆盖已有配置文件
        """
        try:
            # 检查文件是否已存在，非强制模式下提示
            if self.nginx_conf.exists() and not force_overwrite:
                print(f"[!] Nginx配置文件 {self.nginx_conf} 已存在，跳过生成（如需覆盖请使用重新生成功能）")
                return False

            # 创建配置文件目录
            self.nginx_conf.parent.mkdir(parents=True, exist_ok=True)

            # 创建PID目录
            self.nginx_pid_dir.mkdir(parents=True, exist_ok=True)

            # 路径转换（Windows反斜杠转正斜杠）
            frontend_dist = str(self.frontend_dist_dir).replace("\\", "/")
            nginx_pid = str(self.nginx_pid_dir / "nginx.pid").replace("\\", "/")
            nginx_logs = str(self.nginx_pid_dir).replace("\\", "/")

            # Nginx配置内容
            nginx_config = f"""
# OA系统Nginx配置文件（自动生成）
# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
worker_processes  1;

error_log  {nginx_logs}/nginx_error.log  warn;
pid        {nginx_pid};

events {{
    worker_connections  1024;
}}

http {{
    include       mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  {nginx_logs}/nginx_access.log  main;

    sendfile        on;
    keepalive_timeout  65;
    client_max_body_size 100M;

    # 跨域配置
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS';
    add_header Access-Control-Allow-Headers 'DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';

    # 前端静态文件
    server {{
        listen       {self.nginx_port};
        server_name  localhost;

        # 前端静态资源
        location / {{
            root   {frontend_dist};
            index  index.html index.htm;
            try_files $uri $uri/ /index.html;  # 支持Vue路由History模式
        }}

        # 后端API代理
        location /api {{
            proxy_pass http://127.0.0.1:{self.backend_stable_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}

        # 处理OPTIONS预检请求
        location /api/ {{
            if ($request_method = 'OPTIONS') {{
                add_header Access-Control-Allow-Origin *;
                add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS';
                add_header Access-Control-Allow-Headers 'DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';
                return 204;
            }}
        }}

        # 后端静态文件代理
        location /static {{
            proxy_pass http://127.0.0.1:{self.backend_stable_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }}
    }}
}}
"""
            # 写入配置文件
            with open(self.nginx_conf, 'w', encoding='utf-8') as f:
                f.write(nginx_config.strip())

            print(f"[v] Nginx配置文件已{'强制' if force_overwrite else ''}生成: {self.nginx_conf}")
            return True

        except Exception as e:
            print(f"[!] 生成Nginx配置文件失败: {e}")
            traceback.print_exc()
            return False

    def regenerate_nginx_config(self):
        """重新生成Nginx配置文件（强制覆盖）"""
        print("=" * 55)
        print("                重新生成Nginx配置文件")
        print("=" * 55)

        # 二次确认，防止误操作
        try:
            confirm = input(f"确认要覆盖已有Nginx配置文件 \n{self.nginx_conf}\n 吗？(y/N): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
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

    def run_nginx(self, command):
        """执行Nginx命令"""
        try:
            if not self.nginx_exe.exists():
                print(f"[!] Nginx可执行文件不存在: {self.nginx_exe}")
                return False

            # 构建命令
            cmd = [
                str(self.nginx_exe),
                f"-c {str(self.nginx_conf)}" if command not in ["-t"] else "",
                f"-s {command}" if command in ["stop", "reload", "restart"] else command
            ]
            # 清理空参数
            cmd = [c for c in cmd if c.strip()]
            cmd_str = " ".join(cmd)

            print(f"[v] 执行Nginx命令: {cmd_str}")

            # 执行命令
            result = subprocess.run(
                cmd_str, shell=True, capture_output=True, encoding=ENCODING
            )

            if result.returncode == 0:
                print(f"[v] Nginx {command} 成功")
                if result.stdout:
                    print(f"[输出] {result.stdout}")
                return True
            else:
                print(f"[!] Nginx {command} 失败 (返回码: {result.returncode})")
                if result.stderr:
                    print(f"[错误] {result.stderr}")
                return False

        except Exception as e:
            print(f"[!] 执行Nginx命令失败: {e}")
            traceback.print_exc()
            return False

    def nginx_start(self):
        """启动Nginx"""
        print("[v] 启动Nginx服务...")
        # 检查端口
        if self.check_port(self.nginx_port):
            print(f"[!] Nginx端口{self.nginx_port}已被占用，尝试释放...")
            self.kill_port_process(self.nginx_port)

        # 启动Nginx
        success = self.run_nginx("start")
        if success:
            print(f"[v] Nginx启动成功，访问地址: http://localhost:{self.nginx_port}")
        else:
            print("[!] Nginx启动失败")
        self._wait_for_input()

    def nginx_stop(self):
        """停止Nginx"""
        print("[v] 停止Nginx服务...")
        success = self.run_nginx("stop")
        if not success:
            # 兜底终止
            self._kill_related_processes()
            print("[v] 已强制终止Nginx进程")
        self._wait_for_input()

    def nginx_restart(self):
        """重启Nginx"""
        print("[v] 重启Nginx服务...")
        self.nginx_stop()
        time.sleep(2)
        self.nginx_start()

    def start_process(self, cmd, cwd, title="OA Service"):
        """启动子进程"""
        try:
            if IS_WINDOWS:
                # Windows: 新建CMD窗口
                cmd = f"start \"{title}\" cmd /k {cmd}"
            else:
                # Linux: 后台运行
                cmd = f"nohup {cmd} > {title}.log 2>&1 &"

            print(f"[v] 启动进程: {cmd} (工作目录: {cwd})")
            proc = subprocess.Popen(
                cmd, cwd=str(cwd), shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.running_processes.append(proc)
            return proc
        except Exception as e:
            print(f"[!] 启动进程失败: {e}")
            traceback.print_exc()
            return None

    def start_backend(self, port):
        """启动后端服务"""
        print(f"[v] 启动后端服务（端口{port}）...")

        # 检查并释放端口
        if self.check_port(port):
            print(f"[!] 后端端口{port}已被占用，尝试释放...")
            self.kill_port_process(port)

        # 后端启动命令
        cwd = self.backend_dir
        if port == self.backend_stable_port:
            # 稳定版：waitress-serve
            cmd = f'"{self.backend_venv_python}" -m waitress --port {port} wsgi:app'
        else:
            # 开发版：flask run
            cmd = f'"{self.backend_venv_python}" -m flask run --host 0.0.0.0 --port {port} --debug'

        # 启动后端
        proc = self.start_process(cmd, cwd, f"OA_Backend_{port}")
        if proc:
            # 等待服务启动
            time.sleep(3)
            if not self.check_port(port):
                print(f"[!] 后端服务启动失败，端口{port}未监听")
            else:
                print(f"[v] 后端服务启动成功: http://localhost:{port}")
        return proc

    def start_frontend_dev(self):
        """启动前端开发服务"""
        print("[v] 启动前端开发服务（yarn dev）...")

        # 检查并释放端口
        if self.check_port(self.frontend_dev_port):
            print(f"[!] 前端端口{self.frontend_dev_port}已被占用，尝试释放...")
            self.kill_port_process(self.frontend_dev_port)

        # 前端启动命令
        cwd = self.frontend_dir
        if IS_WINDOWS:
            cmd = "yarn dev"
        else:
            cmd = "npm run dev"

        # 启动前端
        proc = self.start_process(cmd, cwd, "OA_Frontend_Dev")
        if proc:
            print(f"[v] 前端开发服务启动成功: http://localhost:{self.frontend_dev_port}")
        return proc

    def start_stable_version(self):
        """稳定版：启动后端5000 + Nginx"""
        print("=" * 55)
        print("                启动稳定版（后端5000 + Nginx）")
        print("=" * 55)

        # 前置检查
        if not self.check_paths():
            self._wait_for_input()
            return

        # 启动后端
        self.start_backend(self.backend_stable_port)

        # 启动Nginx
        self.nginx_start()

        print(f"[v] 稳定版启动完成！访问地址: http://localhost:{self.nginx_port}")
        self._wait_for_input()

    def start_dev_version(self):
        """开发版：启动后端5001 + 前端yarn dev"""
        print("=" * 55)
        print("                启动开发版（后端5001 + 前端5173）")
        print("=" * 55)

        # 前置检查
        if not self.check_paths():
            self._wait_for_input()
            return

        # 启动后端开发版
        self.start_backend(self.backend_dev_port)

        # 启动前端开发版
        self.start_frontend_dev()

        print(f"[v] 开发版启动完成！")
        print(f"[v] 后端地址: http://localhost:{self.backend_dev_port}")
        print(f"[v] 前端地址: http://localhost:{self.frontend_dev_port}")
        self._wait_for_input()

    def _stop_all_processes(self):
        """停止所有运行的子进程"""
        print("[v] 停止所有服务进程...")
        for proc in self.running_processes:
            try:
                if proc.poll() is None:  # 进程仍在运行
                    proc.terminate()
                    proc.wait(timeout=5)
                    print(f"[v] 已终止进程: {proc.pid}")
            except Exception as e:
                print(f"[!] 终止进程失败: {e}")

        # 兜底：终止waitress/flask进程
        if IS_WINDOWS:
            subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq OA*\" 2>nul", shell=True)
        else:
            subprocess.run("pkill -f waitress-serve", shell=True)
            subprocess.run("pkill -f 'flask run'", shell=True)

        self.running_processes.clear()
        print("[v] 所有进程已停止")

    def show_menu(self):
        """显示主菜单"""
        # 初始检查
        self.check_paths()

        while True:
            os.system('cls' if IS_WINDOWS else 'clear')
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
                choice = input("请输入数字：0-6：").strip()

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
                elif choice == "6":
                    self.regenerate_nginx_config()
                elif choice == "0":
                    self._stop_all_processes()
                    self.run_nginx("stop")
                    print("[v] 系统退出，所有服务已停止")
                    break
                else:
                    print("[!] 输入错误，只能输入0-6之间的数字")
                    self._wait_for_input()

            except KeyboardInterrupt:
                print("\n[!] 用户中断操作")
                self._stop_all_processes()
                self.run_nginx("stop")
                break
            except Exception as e:
                print(f"[!] 菜单操作失败: {e}")
                traceback.print_exc()
                self._wait_for_input()

# ====================== 主函数 ======================
def main():
    """主函数"""
    print("=" * 55)
    print("                OA系统启动/维护脚本")
    print("=" * 55)

    # 创建管理器实例
    manager = OAServerManager()

    # 显示菜单
    manager.show_menu()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[!] 脚本执行异常: {e}")
        traceback.print_exc()
        input("\n按回车键退出...")