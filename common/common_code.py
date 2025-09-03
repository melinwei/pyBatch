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
                raise FileNotFoundError(f"❌ 設定ファイル {cls._config_file} が存在しません")

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
        ロガーを初期化し、ログファイルを日付で命名されたフォルダに保存する
        
        Args:
            log_file: ログファイル名、デフォルト 'applog.log'
            level: ログレベル、デフォルト logging.INFO
            backup_count: バックアップファイル数、デフォルト 7
            base_log_dir: 基本ログディレクトリ、デフォルト 'log'
        """
        logger = logging.getLogger("CommonLogger")
        logger.setLevel(level)
    
        if not logger.handlers:
            # 現在の日付をフォルダ名として取得
            today = datetime.now().strftime('%Y%m%d')
            log_dir = os.path.join(base_log_dir, today)
            
            # 日付フォルダを作成（存在しない場合）
            os.makedirs(log_dir, exist_ok=True)
            
            # 完全なログファイルパス
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
    
   