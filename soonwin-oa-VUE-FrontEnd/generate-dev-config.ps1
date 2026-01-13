# PowerShell 脚本：手动设置开发环境配置
# 在大多数情况下，Vite配置会自动检测本机IP
# 只有在自动检测失败时才需要使用此脚本
# 使用方法: .\generate-dev-config.ps1 [IP地址]

param(
    [string]$IP = ""
)

# 如果没有提供IP参数，则尝试自动获取
if (-not $IP) {
    $IP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*","*Local*","*Connection*" -ErrorAction SilentlyContinue | 
            Where-Object { $_.IPAddress -notlike "169.254.*" -and $_.IPAddress -notlike "127.*" } |
            Select-Object -First 1).IPAddress
}

# 如果仍然无法自动获取IP，则使用默认值
if (-not $IP) {
    $IP = "192.168.1.24"
}

# 生成 .env.development 文件
$content = @"
# 开发环境配置 - 手动设置
# 后端API目标地址（用于Vite代理配置）
VITE_API_TARGET=http://$IP:5000

# 开发环境接口基础路径（配合代理）
VITE_API_BASE_URL=

# 项目标题
VITE_APP_TITLE=SoonWin OA系统
"@

# 写入文件
Set-Content -Path ".env.development" -Value $content

Write-Host "已生成 .env.development 文件，后端地址设置为: http://$IP:5000"
Write-Host "注意：通常无需使用此脚本，Vite配置会自动检测本机IP"