
from dataclasses import dataclass, field



@dataclass
class ModelEmailInfo:
     # サーバー情報
    smtp_server: str                   # SMTPサーバーアドレス
    smtp_port: int = 587               # SMTPポート
    
    # 認証情報
    username: str = ''                 # メールユーザー名
    password: str = ''                 # メールパスワードまたはアプリパスワード
    
    # セキュリティ設定
    use_tls: bool = True              # TLS暗号化を使用
    use_ssl: bool = False             # SSL暗号化を使用
    
    # 接続設定
    timeout: int = 30                 # 接続タイムアウト時間
    
    # 送信者情報
    sender_email: str = ''            # 送信者メールアドレス
    sender_name: str = ''             # 送信者表示名   

    
    # 設定名
    config_name: str = ''             # 設定名、管理用