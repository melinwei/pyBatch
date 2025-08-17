
from dataclasses import dataclass, field



@dataclass
class ModelEmailInfo:
     # 服务器信息
    smtp_server: str                    # SMTP服务器地址
    smtp_port: int = 587               # SMTP端口
    
    # 认证信息
    username: str = ''                 # 邮箱用户名
    password: str = ''                 # 邮箱密码或应用密码
    
    # 安全设置
    use_tls: bool = True              # 使用TLS加密
    use_ssl: bool = False             # 使用SSL加密
    
    # 连接设置
    timeout: int = 30                 # 连接超时时间
    
    # 发送者信息
    sender_email: str = ''            # 发送者邮箱
    sender_name: str = ''             # 发送者显示名称
    
    # 服务器类型
    server_type: MailServerType = MailServerType.CUSTOM
    
    # 配置名称
    config_name: str = ''             # 配置名称，便于管理
    description: str = ''             # 配置描述