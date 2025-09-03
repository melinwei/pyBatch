import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Optional, Union
import mimetypes
import logging
from dataclasses import dataclass


@dataclass
class ModelEmailInfo:
    # サーバー情報
    smtp_server: str                  # SMTPサーバーアドレス
    smtp_port: int = 587              # SMTPポート
    
    # 認証情報
    username: str = ''                # メールユーザー名
    password: str = ''                # メールパスワードまたはアプリパスワード
    
    # セキュリティ設定
    use_tls: bool = True              # TLS暗号化を使用
    use_ssl: bool = False             # SSL暗号化を使用
    
    # 接続設定
    timeout: int = 30                 # 接続タイムアウト時間
    
    # 送信者情報
    sender_email: str = ''            # 送信者メールアドレス
    sender_name: str = ''             # 送信者表示名
    
    # 設定名
    config_name: str = ''             # 設定名、管理しやすくするため


class EmailSender:
    """メール送信器クラス、テキスト、HTMLメールと添付ファイル送信をサポート"""
    
    def __init__(self, email_config: ModelEmailInfo):
        """
        メール送信器を初期化
        
        Args:
            email_config: メール設定情報
        """
        self.config = email_config
        self.logger = logging.getLogger(__name__)
        
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """SMTP接続を作成"""
        try:
            if self.config.use_ssl:
                # SSL接続を使用
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.config.smtp_server, 
                    self.config.smtp_port,
                    timeout=self.config.timeout,
                    context=context
                )
            else:
                # 通常接続を使用
                server = smtplib.SMTP(
                    self.config.smtp_server, 
                    self.config.smtp_port,
                    timeout=self.config.timeout
                )
                
                if self.config.use_tls:
                    # TLS暗号化を有効化
                    server.starttls()
            
            # メールボックスにログイン
            if self.config.username and self.config.password:
                server.login(self.config.username, self.config.password)
                
            return server
            
        except Exception as e:
            self.logger.error(f"SMTP接続作成失敗: {e}")
            raise
    
    def _get_mime_type_and_subtype(self, file_path: str) -> tuple:
        """ファイルのMIMEタイプとサブタイプを取得"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            return 'application', 'octet-stream'
        
        main_type, sub_type = mime_type.split('/', 1)
        return main_type, sub_type
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str, filename: Optional[str] = None):
        """メールに添付ファイルを追加"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"添付ファイルが存在しません: {file_path}")
            
            # カスタムファイル名または元のファイル名を使用
            attach_filename = filename or path.name
            main_type, sub_type = self._get_mime_type_and_subtype(file_path)
            
            with open(file_path, 'rb') as fp:
                file_data = fp.read()
            
            if main_type == 'text':
                # テキストファイル
                attachment = MIMEText(file_data.decode('utf-8'), sub_type)
            elif main_type == 'image':
                # 画像ファイル
                attachment = MIMEImage(file_data, sub_type)
            elif main_type == 'audio':
                # 音声ファイル
                attachment = MIMEAudio(file_data, sub_type)
            else:
                # その他のタイプのファイル
                attachment = MIMEApplication(file_data, sub_type)
            
            # 添付ファイルヘッダー情報を設定
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=attach_filename
            )
            
            msg.attach(attachment)
            self.logger.info(f"添付ファイル追加成功: {attach_filename}")
            
        except Exception as e:
            self.logger.error(f"添付ファイル追加失敗 {file_path}: {e}")
            raise
    
    def send_email(self, 
                   to_emails: Union[str, List[str]],
                   subject: str,
                   body: str = '',
                   html_body: str = '',
                   cc_emails: Optional[Union[str, List[str]]] = None,
                   bcc_emails: Optional[Union[str, List[str]]] = None,
                   attachments: Optional[List[Union[str, tuple]]] = None,
                   reply_to: Optional[str] = None) -> bool:
        """
        メールを送信
        
        Args:
            to_emails: 受信者メールアドレス（文字列またはリスト）
            subject: メール件名
            body: プレーンテキストメール内容
            html_body: HTML形式メール内容
            cc_emails: CCメールアドレス
            bcc_emails: BCCメールアドレス
            attachments: 添付ファイルリスト、ファイルパス文字列または(ファイルパス, 表示名)タプル
            reply_to: 返信メールアドレス
            
        Returns:
            bool: 送信が成功したかどうか
        """
        try:
            # メールオブジェクトを作成
            msg = MIMEMultipart('alternative')
            
            # メールヘッダー情報を設定
            sender_info = f"{self.config.sender_name} <{self.config.sender_email}>" if self.config.sender_name else self.config.sender_email
            msg['From'] = sender_info
            msg['Subject'] = subject
            
            # 受信者を処理
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            msg['To'] = ', '.join(to_emails)
            
            # CCを処理
            if cc_emails:
                if isinstance(cc_emails, str):
                    cc_emails = [cc_emails]
                msg['Cc'] = ', '.join(cc_emails)
                to_emails.extend(cc_emails)
            
            # BCCを処理
            if bcc_emails:
                if isinstance(bcc_emails, str):
                    bcc_emails = [bcc_emails]
                to_emails.extend(bcc_emails)
            
            # 返信アドレスを設定
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # メール内容を追加
            if body:
                text_part = MIMEText(body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # プレーンテキストもHTML内容もない場合、デフォルト内容を追加
            if not body and not html_body:
                default_text = MIMEText('', 'plain', 'utf-8')
                msg.attach(default_text)
            
            # 添付ファイルを追加
            if attachments:
                for attachment in attachments:
                    if isinstance(attachment, tuple):
                        # (ファイルパス, 表示名)
                        file_path, display_name = attachment
                        self._add_attachment(msg, file_path, display_name)
                    else:
                        # ファイルパス文字列
                        self._add_attachment(msg, attachment)
            
            # メールを送信
            with self._create_smtp_connection() as server:
                text = msg.as_string()
                server.sendmail(self.config.sender_email, to_emails, text)
                self.logger.info(f"メール送信成功: {subject} -> {', '.join(to_emails)}")
                return True
                
        except Exception as e:
            self.logger.error(f"メール送信失敗: {e}")
            return False
    
    def send_simple_email(self, 
                         to_email: str, 
                         subject: str, 
                         body: str) -> bool:
        """
        シンプルなプレーンテキストメールを送信
        
        Args:
            to_email: 受信者メールアドレス
            subject: メール件名
            body: メール内容
            
        Returns:
            bool: 送信が成功したかどうか
        """
        return self.send_email(to_email, subject, body)
    
    def test_connection(self) -> bool:
        """SMTP接続をテスト"""
        try:
            with self._create_smtp_connection() as server:
                self.logger.info("SMTP接続テスト成功")
                return True
        except Exception as e:
            self.logger.error(f"SMTP接続テスト失敗: {e}")
            return False


# 使用例
if __name__ == "__main__":
    # ログを設定
    logging.basicConfig(level=logging.INFO)
    
    # メール設定を作成（例設定）
    email_config = ModelEmailInfo(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="your_email@gmail.com",
        password="your_password",
        use_tls=True,
        sender_email="your_email@gmail.com",
        sender_name="送信者名",
        config_name="Gmail設定"
    )
    
    # メール送信器を作成
    sender = EmailSender(email_config)
    
    # 接続をテスト
    if sender.test_connection():
        print("接続テスト成功！")
        
        # 添付ファイル付きメールを送信
        success = sender.send_email(
            to_emails=["recipient@example.com"],
            subject="テストメール",
            body="これはプレーンテキスト内容です",
            html_body="<h1>これはHTML内容です</h1><p>HTML形式をサポート</p>",
            attachments=[
                "document.pdf",  # シンプルファイルパス
                ("image.jpg", "私の画像.jpg"),  # カスタム表示名
            ]
        )
        
        if success:
            print("メール送信成功！")
        else:
            print("メール送信失敗！")
    else:
        print("接続テスト失敗！")