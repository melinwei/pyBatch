from dataclasses import dataclass, field
from ftplib import FTP, FTP_TLS
from typing import List, Optional
import os
from pathlib import Path


@dataclass
class ModelFtpInfo:
    # サーバー情報
    ftp_server: str                    # FTPサーバーアドレス
    ftp_port: int = 21                 # FTPポート
    
    # 認証情報
    username: str = ''                 # FTPユーザー名
    password: str = ''                 # FTPパスワード
    
    # セキュリティ設定
    use_tls: bool = False              # FTPS暗号化を使用
    passive_mode: bool = True          # パッシブモード
    
    # 接続設定
    timeout: int = 30                  # 接続タイムアウト時間
    
    # 作業ディレクトリ
    remote_dir: str = '/'              # リモート作業ディレクトリ
    local_dir: str = './'              # ローカル作業ディレクトリ
    
    # 設定名
    config_name: str = ''              # 設定名、管理用


class FtpClient:
    def __init__(self, config: ModelFtpInfo):
        self.config = config
        self.ftp = None
    
    def connect(self) -> bool:
        """FTPサーバーに接続"""
        try:
            if self.config.use_tls:
                self.ftp = FTP_TLS()
            else:
                self.ftp = FTP()
            
            # タイムアウト設定
            self.ftp.timeout = self.config.timeout
            
            # サーバーに接続
            self.ftp.connect(self.config.ftp_server, self.config.ftp_port)
            
            # ログイン
            self.ftp.login(self.config.username, self.config.password)
            
            # TLS使用時、データ接続保護を設定
            if self.config.use_tls:
                self.ftp.prot_p()
            
            # パッシブモード設定
            self.ftp.set_pasv(self.config.passive_mode)
            
            # 作業ディレクトリに移動
            if self.config.remote_dir != '/':
                self.ftp.cwd(self.config.remote_dir)
            
            return True
            
        except Exception as e:
            print(f"接続失敗: {e}")
            return False
    
    def disconnect(self):
        """FTP接続を切断"""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                self.ftp.close()
            self.ftp = None
    
    def upload_file(self, local_path: str, remote_filename: Optional[str] = None) -> bool:
        """
        ファイルをアップロード
        
        Args:
            local_path: ローカルファイルパス
            remote_filename: リモートファイル名、指定しない場合はローカルファイル名を使用
        
        Returns:
            bool: アップロード成功かどうか
        """
        if not self.ftp:
            print("FTPサーバーに接続されていません")
            return False
        
        try:
            local_file = Path(local_path)
            if not local_file.exists():
                print(f"ローカルファイルが存在しません: {local_path}")
                return False
            
            # リモートファイル名を決定
            if remote_filename is None:
                remote_filename = local_file.name
            
            # ファイルをアップロード
            with open(local_path, 'rb') as file:
                self.ftp.storbinary(f'STOR {remote_filename}', file)
            
            print(f"アップロード成功: {local_path} -> {remote_filename}")
            return True
            
        except Exception as e:
            print(f"アップロード失敗: {e}")
            return False
    
    def upload_string(self, content: str, remote_filename: str, encoding: str = 'utf-8') -> bool:
        """
        文字列コンテンツを直接リモートファイルにアップロード
        
        Args:
            content: アップロードする文字列コンテンツ
            remote_filename: リモートファイル名
            encoding: ファイルエンコーディング、デフォルトはutf-8
        
        Returns:
            bool: アップロード成功かどうか
        """
        if not self.ftp:
            print("FTPサーバーに接続されていません")
            return False
        
        try:
            from io import BytesIO
            
            # 文字列をバイトにエンコードしてメモリバッファを作成
            content_bytes = content.encode(encoding)
            buffer = BytesIO(content_bytes)
            
            # コンテンツをアップロード
            self.ftp.storbinary(f'STOR {remote_filename}', buffer)
            
            print(f"文字列アップロード成功: {remote_filename} (サイズ: {len(content_bytes)} バイト)")
            return True
            
        except Exception as e:
            print(f"文字列アップロード失敗: {e}")
            return False
    
    def download_file(self, remote_filename: str, local_path: Optional[str] = None) -> bool:
        """
        ファイルをダウンロード
        
        Args:
            remote_filename: リモートファイル名
            local_path: ローカル保存パス、指定しない場合はローカル作業ディレクトリに保存
        
        Returns:
            bool: ダウンロード成功かどうか
        """
        if not self.ftp:
            print("FTPサーバーに接続されていません")
            return False
        
        try:
            # ローカル保存パスを決定
            if local_path is None:
                local_path = os.path.join(self.config.local_dir, remote_filename)
            
            # ローカルディレクトリが存在することを確認
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # ファイルをダウンロード
            with open(local_path, 'wb') as file:
                self.ftp.retrbinary(f'RETR {remote_filename}', file.write)
            
            print(f"ダウンロード成功: {remote_filename} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"ダウンロード失敗: {e}")
            return False
    
    def delete_file(self, remote_filename: str) -> bool:
        """
        リモートファイルを削除
        
        Args:
            remote_filename: 削除するリモートファイル名
        
        Returns:
            bool: 削除成功かどうか
        """
        if not self.ftp:
            print("FTPサーバーに接続されていません")
            return False
        
        try:
            self.ftp.delete(remote_filename)
            print(f"削除成功: {remote_filename}")
            return True
            
        except Exception as e:
            print(f"削除失敗: {e}")
            return False
    
    def read_file(self, remote_filename: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        リモートファイルの内容を直接読み取って文字列を返す
        
        Args:
            remote_filename: リモートファイル名
            encoding: ファイルエンコーディング、デフォルトはutf-8
        
        Returns:
            Optional[str]: ファイル内容文字列、失敗時はNone
        """
        if not self.ftp:
            print("FTPサーバーに接続されていません")
            return None
        
        try:
            from io import BytesIO
            
            # メモリバッファを作成
            buffer = BytesIO()
            
            # ファイル内容をバッファに読み取り
            self.ftp.retrbinary(f'RETR {remote_filename}', buffer.write)
            
            # バッファ内容を取得して文字列にデコード
            buffer.seek(0)
            content = buffer.read().decode(encoding)
            
            print(f"ファイル読み取り成功: {remote_filename}")
            return content
            
        except Exception as e:
            print(f"ファイル読み取り失敗: {e}")
            return None
    
    def get_file_list(self, path: str = '.') -> List[str]:
        """
        ファイルリストを取得
        
        Args:
            path: リスト表示するディレクトリパス、デフォルトは現在のディレクトリ
        
        Returns:
            List[str]: ファイル名リスト
        """
        if not self.ftp:
            print("FTPサーバーに接続されていません")
            return []
        
        try:
            file_list = []
            self.ftp.retrlines(f'NLST {path}', file_list.append)
            return file_list
            
        except Exception as e:
            print(f"ファイルリスト取得失敗: {e}")
            return []
    
    def get_detailed_list(self, path: str = '.') -> List[str]:
        """
        詳細ファイルリストを取得（権限、サイズ、日付などの情報を含む）
        
        Args:
            path: リスト表示するディレクトリパス、デフォルトは現在のディレクトリ
        
        Returns:
            List[str]: 詳細ファイル情報リスト
        """
        if not self.ftp:
            print("FTPサーバーに接続されていません")
            return []
        
        try:
            detailed_list = []
            self.ftp.retrlines(f'LIST {path}', detailed_list.append)
            return detailed_list
            
        except Exception as e:
            print(f"詳細ファイルリスト取得失敗: {e}")
            return []
    
    def change_dir(self, path: str) -> bool:
        """
        リモートディレクトリを変更
        
        Args:
            path: ターゲットディレクトリパス
        
        Returns:
            bool: 変更成功かどうか
        """
        if not self.ftp:
            print("FTPサーバーに接続されていません")
            return False
        
        try:
            self.ftp.cwd(path)
            return True
            
        except (OSError, EOFError) as e:
            print(f"ディレクトリ変更失敗: {e}")
            return False
    
    def get_current_dir(self) -> str:
        """
        現在のリモートディレクトリを取得
        
        Returns:
            str: 現在のディレクトリパス
        """
        if not self.ftp:
            return ""
        
        try:
            return self.ftp.pwd()
        except (OSError, EOFError) as e:
            print(f"現在のディレクトリ取得失敗: {e}")
            return ""
    
    def __enter__(self):
        """with文のコンテキストマネージャーをサポート"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """with文のコンテキストマネージャーをサポート"""
        self.disconnect()


# 使用例
if __name__ == "__main__":
    # FTP設定を作成
    ftp_config = ModelFtpInfo(
        ftp_server="ftp.example.com",
        ftp_port=21,
        username="your_username",
        password="your_password",
        use_tls=False,
        remote_dir="/upload",
        local_dir="./downloads",
        config_name="サンプルFTP設定"
    )
    
    # 使用方法1：手動で接続管理
    client = FtpClient(ftp_config)
    if client.connect():
        # ファイルリストを取得
        files = client.get_file_list()
        print("ファイルリスト:", files)
        
        # ファイルをアップロード
        # client.upload_file("local_file.txt")
        
        # ファイルをダウンロード
        # client.download_file("remote_file.txt")
        
        # ファイル内容を読み取り
        # content = client.read_file("remote_file.txt")
        # print("ファイル内容:", content)
        
        client.disconnect()
    
    # 使用方法2：with文を使用（推奨）
    with FtpClient(ftp_config) as client:
        files = client.get_file_list()
        print("ファイルリスト:", files)
        
        # CSV文字列を直接アップロード
        # csv_data = "姓名,年龄,城市\n张三,25,北京\n李四,30,上海\n王五,28,广州"
        # client.upload_string(csv_data, "employees.csv", encoding="utf-8")
        
        # ファイル内容を直接読み取り
        # content = client.read_file("config.txt", encoding="utf-8")
        # if content:
        #     print("ファイル内容:", content)