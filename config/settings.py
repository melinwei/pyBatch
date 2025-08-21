import os
import logging
import configparser
import toml
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from utils.ftpclient import ModelFtpInfo





class Settings:

    # App情報
    APP_NAME: str = "YorkIY Batch With Python"
    APP_VERSION: str = "1.0.1"

    # 基本フォルダ設定
    BASE_DIR = Path(__file__).resolve().parent.parent
    PROJECT_ROOT = BASE_DIR
    config = toml.load("config.toml")
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
    @classmethod
    def get_Ftp_Info_01(cls):
        ftp_info = ModelFtpInfo(
        ftp_server=cls.config['ftpinfo01']['ftp_server'],
        ftp_port=cls.config['ftpinfo01']['ftp_port'],
        username=cls.config['ftpinfo01']['username'],
        password=cls.config['ftpinfo01']['password'],
        use_tls=cls.config['ftpinfo01']['use_tls'],
        passive_mode=cls.config['ftpinfo01']['passive_mode'],
        remote_dir=cls.config['ftpinfo01']['remote_dir'],
        timeout=60,
        config_name="テストFTP情報"
        )
        return ftp_info

    _logger = None
    @classmethod
    def init_logger(cls, log_file='appLog.log', level=logging.INFO, backup_count=7, base_log_dir='logs'):
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
