import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QDateEdit, QPushButton, QGridLayout, QMessageBox, QDesktopWidget
)
from PyQt5.QtCore import QDate,Qt


from config.settings import Settings
from config.database import MsSqlDataBase,MsSqlParameter

from utils.ftpclient import ModelFtpInfo,FtpClient
from utils.emailsender import ModelEmailInfo,EmailSender



OutLog = Settings.get_logger()




class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("用户登录")
        self.resize(350, 200)  # 先设置窗口大小
        self.center()  # 居中显示

        # 创建控件
        label_id = QLabel("用户ID：")
        self.input_id = QLineEdit()

        label_name = QLabel("用户名：")
        self.input_name = QLineEdit()

        label_birth = QLabel("生日：")
        self.input_birth = QDateEdit()
        self.input_birth.setCalendarPopup(True)
        self.input_birth.setDate(QDate.currentDate())

        self.button_login = QPushButton("登录")
        self.button_login.clicked.connect(self.on_login)
        self.button_login.setFixedSize(120, 40)

        label_Config = QLabel("Config")
        self.input_Config = QLineEdit()


        

        # 网格布局
        layout = QGridLayout()
        layout.addWidget(label_id, 0, 0)
        layout.addWidget(self.input_id, 0, 1)

        layout.addWidget(label_name, 1, 0)
        layout.addWidget(self.input_name, 1, 1)

        layout.addWidget(label_birth, 2, 0)
        layout.addWidget(self.input_birth, 2, 1)

        layout.addWidget(self.button_login, 3, 0, 1, 2, Qt.AlignRight)
        
        layout.addWidget(label_Config, 4, 0)
        layout.addWidget(self.input_Config, 4, 1)

        self.setLayout(layout)

    def center(self):
        """让窗口居中"""
        screen = QDesktopWidget().availableGeometry().center()  # 获取屏幕中心
        frame_geo = self.frameGeometry()  # 获取窗口的几何信息
        frame_geo.moveCenter(screen)  # 移动到屏幕中心
        self.move(frame_geo.topLeft())  # 移动窗口位置



        
        

    def on_login(self):    


        kMail=Settings.get_Email_Info_01()

        send=EmailSender(kMail)

        if send.test_connection():
         print("连接测试成功！")
        
        # 发送带附件的邮件
         success = send.send_email(
            to_emails=["w_lin@data-trade.co.jp"],
            subject="测试邮件",
            body="这是纯文本内容",
            html_body="<h1>这是HTML内容</h1><p>支持HTML格式</p>"
        )
         
        if success:
            print("邮件发送成功！")
        else:
            print("邮件发送失败！")


        k1=Settings.get_Ftp_Info_01()



        client = FtpClient(k1)
        if client.connect():
            client.upload_string("fff","kkke.txt")
            





        OutLog.info(f"FTP信息: {k1}")


        OutLog.info(Settings.APP_NAME) 


        now = datetime.now()
        time_str = now.strftime("%y%m%d%H%M%S")


        db = MsSqlDataBase()


        try:
            db.begin_transaction()
            params = [
            MsSqlParameter("UPD_USR", "881"),
            MsSqlParameter("LOG_KEY", "10000061")
          ]
            sql = "SELECT TOP 10 * FROM  TRN_LOG "
            query = """
                    SELECT id, name, email
                    FROM users
                    WHERE status = ?
                    ORDER BY created_at DESC
                    """
            
            affected_rows = db.fetch_all_data(sql)
            print(f"更新了 {affected_rows} 行")
            db.commit()            

        except Exception as e:
            db.rollback()          
            print("❌ 事务提交失败:", e)

        finally:
            db.close()  

     
        uid = self.input_id.text()
        uname = self.input_name.text()
        birth = self.input_birth.date().toString("yyyy-MM-dd")
        QMessageBox.information(self, "登录信息", f"用户ID: {uid}\n用户名: {uname}\n生日: {birth}{time_str}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
