#!/bin/bash
# 自动检测本机IP并生成开发环境配置
# 使用方法: ./generate-dev-config.sh

# 获取本机IP地址
LOCAL_IP=$(hostname -I | awk '{print $1}')

# 如果无法自动获取IP，则使用默认值
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="192.168.1.24"
fi

echo "# 开发环境配置 - 自动生成" > .env.development
echo "# 后端API目标地址（用于Vite代理配置）" >> .env.development
echo "VITE_API_TARGET=http://$LOCAL_IP:5000" >> .env.development
echo "" >> .env.development
echo "# 开发环境接口基础路径（配合代理）" >> .env.development
echo "VITE_API_BASE_URL=" >> .env.development
echo "" >> .env.development
echo "# 项目标题" >> .env.development
echo "VITE_APP_TITLE=SoonWin OA系统" >> .env.development

echo "已生成 .env.development 文件，后端地址设置为: http://$LOCAL_IP:5001"