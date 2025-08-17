import os
import logging
import configparser
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler



class CommonCode:
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
    def init_logger(cls, log_file='applog.log', level=logging.INFO, backup_count=7):
        logger = logging.getLogger("CommonLogger")
        logger.setLevel(level)
        if not logger.handlers:
            handler = TimedRotatingFileHandler(
                filename=log_file,
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
    
   