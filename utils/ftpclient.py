from dataclasses import dataclass, field
from ftplib import FTP, FTP_TLS
from typing import List, Optional
import os
from pathlib import Path


@dataclass
class ModelFtpInfo:
    # 服务器信息
    ftp_server: str                    # FTP服务器地址
    ftp_port: int = 21                 # FTP端口
    
    # 认证信息
    username: str = ''                 # FTP用户名
    password: str = ''                 # FTP密码
    
    # 安全设置
    use_tls: bool = False              # 使用FTPS加密
    passive_mode: bool = True          # 被动模式
    
    # 连接设置
    timeout: int = 30                  # 连接超时时间
    
    # 工作目录
    remote_dir: str = '/'              # 远程工作目录
    local_dir: str = './'              # 本地工作目录
    
    # 配置名称
    config_name: str = ''              # 配置名称，便于管理


class FtpClient:
    def __init__(self, config: ModelFtpInfo):
        self.config = config
        self.ftp = None
    
    def connect(self) -> bool:
        """连接到FTP服务器"""
        try:
            if self.config.use_tls:
                self.ftp = FTP_TLS()
            else:
                self.ftp = FTP()
            
            # 设置超时
            self.ftp.timeout = self.config.timeout
            
            # 连接服务器
            self.ftp.connect(self.config.ftp_server, self.config.ftp_port)
            
            # 登录
            self.ftp.login(self.config.username, self.config.password)
            
            # 如果使用TLS，需要设置数据连接保护
            if self.config.use_tls:
                self.ftp.prot_p()
            
            # 设置被动模式
            self.ftp.set_pasv(self.config.passive_mode)
            
            # 切换到工作目录
            if self.config.remote_dir != '/':
                self.ftp.cwd(self.config.remote_dir)
            
            return True
            
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开FTP连接"""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                self.ftp.close()
            self.ftp = None
    
    def upload_file(self, local_path: str, remote_filename: Optional[str] = None) -> bool:
        """
        上传文件
        
        Args:
            local_path: 本地文件路径
            remote_filename: 远程文件名，如果不指定则使用本地文件名
        
        Returns:
            bool: 上传是否成功
        """
        if not self.ftp:
            print("未连接到FTP服务器")
            return False
        
        try:
            local_file = Path(local_path)
            if not local_file.exists():
                print(f"本地文件不存在: {local_path}")
                return False
            
            # 确定远程文件名
            if remote_filename is None:
                remote_filename = local_file.name
            
            # 上传文件
            with open(local_path, 'rb') as file:
                self.ftp.storbinary(f'STOR {remote_filename}', file)
            
            print(f"上传成功: {local_path} -> {remote_filename}")
            return True
            
        except Exception as e:
            print(f"上传失败: {e}")
            return False
    
    def upload_string(self, content: str, remote_filename: str, encoding: str = 'utf-8') -> bool:
        """
        直接上传字符串内容到远程文件
        
        Args:
            content: 要上传的字符串内容
            remote_filename: 远程文件名
            encoding: 文件编码，默认为utf-8
        
        Returns:
            bool: 上传是否成功
        """
        if not self.ftp:
            print("未连接到FTP服务器")
            return False
        
        try:
            from io import BytesIO
            
            # 将字符串编码为字节并创建内存缓冲区
            content_bytes = content.encode(encoding)
            buffer = BytesIO(content_bytes)
            
            # 上传内容
            self.ftp.storbinary(f'STOR {remote_filename}', buffer)
            
            print(f"字符串上传成功: {remote_filename} (大小: {len(content_bytes)} 字节)")
            return True
            
        except Exception as e:
            print(f"字符串上传失败: {e}")
            return False
    
    def download_file(self, remote_filename: str, local_path: Optional[str] = None) -> bool:
        """
        下载文件
        
        Args:
            remote_filename: 远程文件名
            local_path: 本地保存路径，如果不指定则保存到本地工作目录
        
        Returns:
            bool: 下载是否成功
        """
        if not self.ftp:
            print("未连接到FTP服务器")
            return False
        
        try:
            # 确定本地保存路径
            if local_path is None:
                local_path = os.path.join(self.config.local_dir, remote_filename)
            
            # 确保本地目录存在
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # 下载文件
            with open(local_path, 'wb') as file:
                self.ftp.retrbinary(f'RETR {remote_filename}', file.write)
            
            print(f"下载成功: {remote_filename} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def delete_file(self, remote_filename: str) -> bool:
        """
        删除远程文件
        
        Args:
            remote_filename: 要删除的远程文件名
        
        Returns:
            bool: 删除是否成功
        """
        if not self.ftp:
            print("未连接到FTP服务器")
            return False
        
        try:
            self.ftp.delete(remote_filename)
            print(f"删除成功: {remote_filename}")
            return True
            
        except Exception as e:
            print(f"删除失败: {e}")
            return False
    
    def read_file(self, remote_filename: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        直接读取远程文件内容并返回字符串
        
        Args:
            remote_filename: 远程文件名
            encoding: 文件编码，默认为utf-8
        
        Returns:
            Optional[str]: 文件内容字符串，失败时返回None
        """
        if not self.ftp:
            print("未连接到FTP服务器")
            return None
        
        try:
            from io import BytesIO
            
            # 创建内存缓冲区
            buffer = BytesIO()
            
            # 将文件内容读取到缓冲区
            self.ftp.retrbinary(f'RETR {remote_filename}', buffer.write)
            
            # 获取缓冲区内容并解码为字符串
            buffer.seek(0)
            content = buffer.read().decode(encoding)
            
            print(f"读取文件成功: {remote_filename}")
            return content
            
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None
    
    def get_file_list(self, path: str = '.') -> List[str]:
        """
        获取文件列表
        
        Args:
            path: 要列出的目录路径，默认为当前目录
        
        Returns:
            List[str]: 文件名列表
        """
        if not self.ftp:
            print("未连接到FTP服务器")
            return []
        
        try:
            file_list = []
            self.ftp.retrlines(f'NLST {path}', file_list.append)
            return file_list
            
        except Exception as e:
            print(f"获取文件列表失败: {e}")
            return []
    
    def get_detailed_list(self, path: str = '.') -> List[str]:
        """
        获取详细文件列表（包含权限、大小、日期等信息）
        
        Args:
            path: 要列出的目录路径，默认为当前目录
        
        Returns:
            List[str]: 详细文件信息列表
        """
        if not self.ftp:
            print("未连接到FTP服务器")
            return []
        
        try:
            detailed_list = []
            self.ftp.retrlines(f'LIST {path}', detailed_list.append)
            return detailed_list
            
        except Exception as e:
            print(f"获取详细文件列表失败: {e}")
            return []
    
    def change_dir(self, path: str) -> bool:
        """
        切换远程目录
        
        Args:
            path: 目标目录路径
        
        Returns:
            bool: 切换是否成功
        """
        if not self.ftp:
            print("未连接到FTP服务器")
            return False
        
        try:
            self.ftp.cwd(path)
            return True
            
        except Exception as e:
            print(f"切换目录失败: {e}")
            return False
    
    def get_current_dir(self) -> str:
        """
        获取当前远程目录
        
        Returns:
            str: 当前目录路径
        """
        if not self.ftp:
            return ""
        
        try:
            return self.ftp.pwd()
        except Exception as e:
            print(f"获取当前目录失败: {e}")
            return ""
    
    def __enter__(self):
        """支持with语句的上下文管理器"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句的上下文管理器"""
        self.disconnect()


# 使用示例
if __name__ == "__main__":
    # 创建FTP配置
    ftp_config = ModelFtpInfo(
        ftp_server="ftp.example.com",
        ftp_port=21,
        username="your_username",
        password="your_password",
        use_tls=False,
        remote_dir="/upload",
        local_dir="./downloads",
        config_name="示例FTP配置"
    )
    
    # 使用方式1：手动管理连接
    client = FtpClient(ftp_config)
    if client.connect():
        # 获取文件列表
        files = client.get_file_list()
        print("文件列表:", files)
        
        # 上传文件
        # client.upload_file("local_file.txt")
        
        # 下载文件
        # client.download_file("remote_file.txt")
        
        # 读取文件内容
        # content = client.read_file("remote_file.txt")
        # print("文件内容:", content)
        
        client.disconnect()
    
    # 使用方式2：使用with语句（推荐）
    with FtpClient(ftp_config) as client:
        files = client.get_file_list()
        print("文件列表:", files)
        
        # 直接上传CSV字符串
        # csv_data = "姓名,年龄,城市\n张三,25,北京\n李四,30,上海\n王五,28,广州"
        # client.upload_string(csv_data, "employees.csv", encoding="utf-8")
        
        # 直接读取文件内容
        # content = client.read_file("config.txt", encoding="utf-8")
        # if content:
        #     print("文件内容:", content)