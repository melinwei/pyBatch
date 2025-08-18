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
    
    # 配置名称
    config_name: str = ''             # 配置名称，便于管理


class EmailSender:
    """邮件发送器类，支持文本、HTML邮件和附件发送"""
    
    def __init__(self, email_config: ModelEmailInfo):
        """
        初始化邮件发送器
        
        Args:
            email_config: 邮件配置信息
        """
        self.config = email_config
        self.logger = logging.getLogger(__name__)
        
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """创建SMTP连接"""
        try:
            if self.config.use_ssl:
                # 使用SSL连接
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.config.smtp_server, 
                    self.config.smtp_port,
                    timeout=self.config.timeout,
                    context=context
                )
            else:
                # 使用普通连接
                server = smtplib.SMTP(
                    self.config.smtp_server, 
                    self.config.smtp_port,
                    timeout=self.config.timeout
                )
                
                if self.config.use_tls:
                    # 启用TLS加密
                    server.starttls()
            
            # 登录邮箱
            if self.config.username and self.config.password:
                server.login(self.config.username, self.config.password)
                
            return server
            
        except Exception as e:
            self.logger.error(f"创建SMTP连接失败: {e}")
            raise
    
    def _get_mime_type_and_subtype(self, file_path: str) -> tuple:
        """获取文件的MIME类型和子类型"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            return 'application', 'octet-stream'
        
        main_type, sub_type = mime_type.split('/', 1)
        return main_type, sub_type
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str, filename: Optional[str] = None):
        """添加附件到邮件"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"附件文件不存在: {file_path}")
            
            # 使用自定义文件名或原文件名
            attach_filename = filename or path.name
            main_type, sub_type = self._get_mime_type_and_subtype(file_path)
            
            with open(file_path, 'rb') as fp:
                file_data = fp.read()
            
            if main_type == 'text':
                # 文本文件
                attachment = MIMEText(file_data.decode('utf-8'), sub_type)
            elif main_type == 'image':
                # 图片文件
                attachment = MIMEImage(file_data, sub_type)
            elif main_type == 'audio':
                # 音频文件
                attachment = MIMEAudio(file_data, sub_type)
            else:
                # 其他类型文件
                attachment = MIMEApplication(file_data, sub_type)
            
            # 设置附件头信息
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=attach_filename
            )
            
            msg.attach(attachment)
            self.logger.info(f"成功添加附件: {attach_filename}")
            
        except Exception as e:
            self.logger.error(f"添加附件失败 {file_path}: {e}")
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
        发送邮件
        
        Args:
            to_emails: 收件人邮箱地址（字符串或列表）
            subject: 邮件主题
            body: 纯文本邮件内容
            html_body: HTML格式邮件内容
            cc_emails: 抄送邮箱地址
            bcc_emails: 密送邮箱地址
            attachments: 附件列表，可以是文件路径字符串或(文件路径, 显示名称)元组
            reply_to: 回复邮箱地址
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            
            # 设置邮件头信息
            sender_info = f"{self.config.sender_name} <{self.config.sender_email}>" if self.config.sender_name else self.config.sender_email
            msg['From'] = sender_info
            msg['Subject'] = subject
            
            # 处理收件人
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            msg['To'] = ', '.join(to_emails)
            
            # 处理抄送
            if cc_emails:
                if isinstance(cc_emails, str):
                    cc_emails = [cc_emails]
                msg['Cc'] = ', '.join(cc_emails)
                to_emails.extend(cc_emails)
            
            # 处理密送
            if bcc_emails:
                if isinstance(bcc_emails, str):
                    bcc_emails = [bcc_emails]
                to_emails.extend(bcc_emails)
            
            # 设置回复地址
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # 添加邮件内容
            if body:
                text_part = MIMEText(body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 如果既没有纯文本也没有HTML内容，添加默认内容
            if not body and not html_body:
                default_text = MIMEText('', 'plain', 'utf-8')
                msg.attach(default_text)
            
            # 添加附件
            if attachments:
                for attachment in attachments:
                    if isinstance(attachment, tuple):
                        # (文件路径, 显示名称)
                        file_path, display_name = attachment
                        self._add_attachment(msg, file_path, display_name)
                    else:
                        # 文件路径字符串
                        self._add_attachment(msg, attachment)
            
            # 发送邮件
            with self._create_smtp_connection() as server:
                text = msg.as_string()
                server.sendmail(self.config.sender_email, to_emails, text)
                self.logger.info(f"邮件发送成功: {subject} -> {', '.join(to_emails)}")
                return True
                
        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_simple_email(self, 
                         to_email: str, 
                         subject: str, 
                         body: str) -> bool:
        """
        发送简单的纯文本邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            
        Returns:
            bool: 发送是否成功
        """
        return self.send_email(to_email, subject, body)
    
    def test_connection(self) -> bool:
        """测试SMTP连接"""
        try:
            with self._create_smtp_connection() as server:
                self.logger.info("SMTP连接测试成功")
                return True
        except Exception as e:
            self.logger.error(f"SMTP连接测试失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建邮件配置（示例配置）
    email_config = ModelEmailInfo(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="your_email@gmail.com",
        password="your_password",
        use_tls=True,
        sender_email="your_email@gmail.com",
        sender_name="发送者名称",
        config_name="Gmail配置"
    )
    
    # 创建邮件发送器
    sender = EmailSender(email_config)
    
    # 测试连接
    if sender.test_connection():
        print("连接测试成功！")
        
        # 发送带附件的邮件
        success = sender.send_email(
            to_emails=["recipient@example.com"],
            subject="测试邮件",
            body="这是纯文本内容",
            html_body="<h1>这是HTML内容</h1><p>支持HTML格式</p>",
            attachments=[
                "document.pdf",  # 简单文件路径
                ("image.jpg", "我的图片.jpg"),  # 自定义显示名称
            ]
        )
        
        if success:
            print("邮件发送成功！")
        else:
            print("邮件发送失败！")
    else:
        print("连接测试失败！")