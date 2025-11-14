import logging
import os

from dotenv import load_dotenv

from app import create_app


load_dotenv()
app = create_app()


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,  # 设置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
        handlers=[
            logging.FileHandler("app.log"),  # 输出到文件
            logging.StreamHandler()  # 输出到控制台
        ])


if __name__ == '__main__':
    configure_logging()
    logger = logging.getLogger(__name__)
    # Ensure JSON responses use unicode characters
    app.config["JSON_AS_ASCII"] = False

    # Host/port can be configured via environment variables for flexibility
    host ="0.0.0.0"#os.environ.get('HOST', os.environ.get('FLASK_RUN_HOST', '0.0.0.0'))
    port = int(os.environ.get('PORT', os.environ.get('FLASK_RUN_PORT', 9001)))
    debug = os.environ.get('FLASK_DEBUG', '1') in ('1', 'true', 'True')

    logger.info(f"Starting app on {host}:{port} (debug={debug})")
    # Bind to 0.0.0.0 so the app is reachable from other devices on the same network
    app.run(host=host, port=port, debug=debug)