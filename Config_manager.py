import configparser
import os

class ConfigManager:
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