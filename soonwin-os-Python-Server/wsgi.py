from app import create_app

# 为waitress创建一个应用实例，使用默认端口
application = create_app(port=5000)

if __name__ == "__main__":
    # 也可以直接运行进行调试
    application.run(host="0.0.0.0", port=5000, debug=True)