
from dataclasses import dataclass, field


@dataclass
class ModelFtpInfo:
    """FTP接続情報データクラス"""
    
    # 基本接続情報
    host: str                             # FTPサーバーアドレス
    username: str                         # FTPユーザー名
    password: str                         # FTPパスワード
    port: int = 21                        # FTPポート、デフォルト21
    
    # 接続設定
    timeout: int = 30                     # 接続タイムアウト時間（秒）
    passive_mode: bool = True             # パッシブモード、デフォルトTrue
    encoding: str = 'utf-8'               # ファイル名エンコーディング
    
    # SSL/TLS設定
    use_tls: bool = False                 # TLS暗号化を使用するかどうか
    implicit_tls: bool = False            # 暗黙的TLSを使用するかどうか（ポート990）
    
    # 作業ディレクトリ
    remote_directory: str = '/'           # リモート作業ディレクトリ
    local_directory: str = './downloads'  # ローカルダウンロードディレクトリ
    
    # 接続情報
    connection_name: str = ''             # 接続名（管理用）
    description: str = ''                 # 接続説明