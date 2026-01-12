from app import create_app

# 创建Flask应用实例
app = create_app()

if __name__ == "__main__":
    # 启动服务（默认端口5000，允许局域网访问）
    app.run(host="0.0.0.0", port=5000, debug=True)