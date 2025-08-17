import os
import logging
import configparser
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class Settings:

    # 基础路径设置
    BASE_DIR = Path(__file__).resolve().parent.parent
    PROJECT_ROOT = BASE_DIR

    # 应用信息
    APP_NAME: str = "YorkIY Batch With Python"
    APP_VERSION: str = "1.0.1"
    

     # 邮件配置
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS: bool = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "noreply@example.com")

    # 文件上传配置
    UPLOAD_FOLDER: str = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: set = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


    _config_file = "config.ini"
    _config = None
    @classmethod
    def load_config(cls):
        if cls._config is None:
            if os.path.exists(cls._config_file):
                cls._config = configparser.ConfigParser()
                cls._config.read(cls._config_file, encoding='utf-8')
            else:
                raise FileNotFoundError(f"❌ 配置文件 {cls._config_file} 不存在")
            
    @classmethod
    def get_connection_string(cls):
        cls.load_config()
        db_config = cls._config['database']
        return (
            f"DRIVER={db_config['driver']};"
            f"SERVER={db_config['server']},{db_config['port']};"
            f"DATABASE={db_config['database']};"
            f"UID={db_config['username']};"
            f"PWD={db_config['password']};"
            f"TrustServerCertificate={db_config['trust_certificate']};"
            f"Connection Timeout={db_config['connection_timeout']};"
        )        

    _logger = None
    @classmethod
    def init_logger(cls, log_file='appLog.log', level=logging.INFO, backup_count=7, base_log_dir='log'):
        """
        初始化日志器，将日志文件保存到按日期命名的文件夹中
        
        Args:
            log_file: 日志文件名，默认 'applog.log'
            level: 日志级别，默认 logging.INFO
            backup_count: 备份文件数量，默认 7
            base_log_dir: 基础日志目录，默认 'log'
        """
        logger = logging.getLogger("CommonLogger")
        logger.setLevel(level)
    
        if not logger.handlers:
            # 获取当前日期作为文件夹名
            today = datetime.now().strftime('%Y%m%d')
            log_dir = os.path.join(base_log_dir, today)
            
            # 创建日期文件夹（如果不存在）
            os.makedirs(log_dir, exist_ok=True)
            
            # 完整的日志文件路径
            log_path = os.path.join(log_dir, log_file)
            
            handler = TimedRotatingFileHandler(
                filename=log_path,
                when='D',
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            
            formatter = logging.Formatter(
                '%(asctime)s [%(threadName)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        cls._logger = logger
        return logger

    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            cls.init_logger()
        return cls._logger
