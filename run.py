from app import create_app
import logging
app = create_app()

if __name__ == '__main__':
    logging.basicConfig(
    level=logging.INFO,  # 设置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    handlers=[
        logging.FileHandler("app.log"),  # 输出到文件
        logging.StreamHandler()  # 输出到控制台
    ])
    logger = logging.getLogger(__name__)
    app.config["JSON_AS_ASCII"] = False
    app.run(debug=True)