import subprocess
import time
import sys

def get_all_services():
    """
    获取所有Windows服务列表
    """
    try:
        # 使用GBK编码处理Windows命令输出
        result = subprocess.run(['sc', 'query', 'state=all'], capture_output=True, text=True, encoding='gbk')
        return result.stdout
    except Exception as e:
        print(f"获取服务列表时出错: {e}")
        try:
            # 如果GBK编码失败，尝试使用系统默认编码
            result = subprocess.run(['sc', 'query', 'state=all'], capture_output=True, text=True)
            return result.stdout
        except Exception as e2:
            print(f"获取服务列表时再次出错: {e2}")
            return None

def find_service_by_name(partial_name):
    """
    根据部分名称查找Windows服务
    """
    try:
        services_output = get_all_services()
        if not services_output:
            return None

        lines = services_output.splitlines()

        for i in range(len(lines)):
            if 'SERVICE_NAME:' in lines[i]:
                service_name = lines[i].split('SERVICE_NAME:')[1].strip()
                if partial_name.lower() in service_name.lower():
                    return service_name
        return None
    except Exception as e:
        print(f"查找服务时出错: {e}")
        return None

def list_services_with_keyword(keyword):
    """
    列出包含特定关键词的所有服务
    """
    try:
        services_output = get_all_services()
        if not services_output:
            print("无法获取服务列表")
            return []

        lines = services_output.splitlines()
        matching_services = []

        for i in range(len(lines)):
            if 'SERVICE_NAME:' in lines[i]:
                service_name = lines[i].split('SERVICE_NAME:')[1].strip()
                if keyword.lower() in service_name.lower():
                    # 获取服务状态
                    status = "Unknown"
                    # 在接下来的几行中查找状态
                    for j in range(i+1, min(i+5, len(lines))):
                        if 'STATE' in lines[j]:
                            status = lines[j].split('STATE')[1].strip().split()[0]  # 获取状态的第一部分
                            break
                    matching_services.append((service_name, status))
        return matching_services
    except Exception as e:
        print(f"列出服务时出错: {e}")
        return []

def restart_service(service_name):
    """
    重启指定的服务
    """
    try:
        print(f"正在停止服务: {service_name}")
        result = subprocess.run(['sc', 'stop', service_name], capture_output=True, text=True, encoding='gbk')
        if result.returncode == 0 or "cannot be stopped" in result.stdout.lower():
            # 检查停止命令的输出
            if "cannot be stopped" in result.stdout.lower():
                print(f"服务 {service_name} 可能已经在停止状态或无法停止")
            else:
                print(f"服务 {service_name} 停止命令已发送")
        else:
            print(f"停止服务 {service_name} 时出错: {result.stdout} {result.stderr}")

        # 等待服务完全停止
        time.sleep(5)

        print(f"正在启动服务: {service_name}")
        result = subprocess.run(['sc', 'start', service_name], capture_output=True, text=True, encoding='gbk')
        if result.returncode == 0:
            print(f"服务 {service_name} 启动命令已发送")
        else:
            print(f"启动服务 {service_name} 时出错: {result.stdout} {result.stderr}")

    except Exception as e:
        print(f"操作服务 {service_name} 时出错: {e}")

def get_all_running_services():
    """
    获取所有正在运行的Windows服务列表
    """
    try:
        services_output = get_all_services()
        if not services_output:
            return []
            
        lines = services_output.splitlines()
        running_services = []
        
        for i in range(len(lines)):
            if 'SERVICE_NAME:' in lines[i]:
                service_name = lines[i].split('SERVICE_NAME:')[1].strip()
                # 在接下来的几行中查找状态
                status = "Unknown"
                for j in range(i+1, min(i+10, len(lines))):  # 检查接下来的10行
                    if j < len(lines) and 'STATE' in lines[j]:
                        if 'RUNNING' in lines[j]:
                            status = "RUNNING"
                        elif 'STOPPED' in lines[j]:
                            status = "STOPPED"
                        else:
                            status = lines[j].split('STATE')[1].strip().split()[0]  # 获取状态的第一部分
                        break
                running_services.append((service_name, status))
        return running_services
    except Exception as e:
        print(f"获取运行服务列表时出错: {e}")
        return []

def select_service_interactively(keyword):
    """
    交互式选择服务
    """
    print(f"\n正在搜索包含关键词 '{keyword}' 的服务...")
    matching_services = list_services_with_keyword(keyword)
    
    if matching_services:
        print(f"找到 {len(matching_services)} 个包含'{keyword}'的服务:")
        for i, (service_name, status) in enumerate(matching_services):
            print(f"  {i+1}. {service_name} (状态: {status})")
        
        # 让用户选择重启哪个服务
        if len(matching_services) == 1:
            selected_service = matching_services[0][0]
            print(f"\n自动选择服务: {selected_service}")
            return selected_service
        else:
            try:
                choice = int(input(f"\n请选择要重启的服务 (1-{len(matching_services)}, 0 跳过): ")) - 1
                if 0 <= choice < len(matching_services):
                    selected_service = matching_services[choice][0]
                    print(f"选择服务: {selected_service}")
                    return selected_service
                else:
                    print("跳过服务重启")
                    return None
            except ValueError:
                print("无效输入，跳过服务重启")
                return None
    else:
        # 如果没有找到匹配关键词的服务，显示所有运行中的服务供用户选择
        print(f"未找到包含关键词 '{keyword}' 的服务")
        show_all_services = input("是否显示所有服务供选择? (y/n): ").lower().strip()
        
        if show_all_services in ['y', 'yes', '是']:
            all_services = get_all_running_services()
            if all_services:
                running_count = sum(1 for _, status in all_services if status == "RUNNING")
                print(f"\n找到 {len(all_services)} 个服务，其中 {running_count} 个正在运行:")
                for i, (service_name, status) in enumerate(all_services):
                    marker = " [运行中]" if status == "RUNNING" else f" [{status}]"
                    print(f"  {i+1}. {service_name}{marker}")
                
                try:
                    choice = int(input(f"\n请选择要重启的服务 (1-{len(all_services)}, 0 跳过): ")) - 1
                    if 0 <= choice < len(all_services):
                        selected_service = all_services[choice][0]
                        status = all_services[choice][1]
                        if status != "RUNNING":
                            confirm = input(f"服务 {selected_service} 当前处于 {status} 状态，确定要重启吗? (y/n): ").lower().strip()
                            if confirm not in ['y', 'yes', '是']:
                                print("取消重启")
                                return None
                        print(f"选择服务: {selected_service}")
                        return selected_service
                    else:
                        print("跳过服务重启")
                        return None
                except ValueError:
                    print("无效输入，跳过服务重启")
                    return None
            else:
                print("无法获取服务列表")
                return None
        else:
            print("跳过服务重启")
            return None

def main():
    print("开始重启nginx和waitress服务...")
    
    # 交互式选择并重启nginx服务
    nginx_service = select_service_interactively('nginx')
    if nginx_service:
        print(f"\n正在重启nginx相关服务: {nginx_service}")
        restart_service(nginx_service)
    else:
        print("\n跳过nginx服务重启")
    
    # 交互式选择并重启waitress服务
    waitress_service = select_service_interactively('waitress')
    if waitress_service:
        print(f"\n正在重启waitress相关服务: {waitress_service}")
        restart_service(waitress_service)
    else:
        print("\n跳过waitress服务重启")
    
    print("\n服务重启操作完成!")

if __name__ == "__main__":
    main()