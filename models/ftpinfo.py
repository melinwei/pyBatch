
from dataclasses import dataclass, field



@dataclass
class ModelFtpInfo:
    """FTP连接信息数据类"""
    
    # 基本连接信息
    host: str                           # FTP服务器地址
    username: str                       # FTP用户名
    password: str                       # FTP密码
    port: int = 21                     # FTP端口，默认21
    
    # 连接配置
    timeout: int = 30                  # 连接超时时间（秒）
    passive_mode: bool = True          # 被动模式，默认True
    encoding: str = 'utf-8'           # 文件名编码
    
    # SSL/TLS配置
    use_tls: bool = False             # 是否使用TLS加密
    implicit_tls: bool = False        # 是否使用隐式TLS（端口990）
    
    # 工作目录
    remote_directory: str = '/'       # 远程工作目录
    local_directory: str = './downloads'  # 本地下载目录
    
    # 连接信息
    connection_name: str = ''         # 连接名称（便于管理）
    description: str = ''             # 连接描述