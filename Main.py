import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QDateEdit, QPushButton, QGridLayout, QMessageBox, QDesktopWidget
)
from PyQt5.QtCore import QDate,Qt
from Config_manager import ConfigManager
import logging
from logging.handlers import TimedRotatingFileHandler
from SqlServerDB import SqlServerDB
from datetime import datetime
from SqlServerDB import SqlServerDB
from sqlhelper import SqlHelper
from sqlhelper import SqlParameter




handler = TimedRotatingFileHandler(
    filename='mydiary.log',
    when='D',           # 按天分割
    interval=1,
    backupCount=7,
    encoding='utf-8'
)

formatter = logging.Formatter(
    '%(asctime)s [%(threadName)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)



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

        now = datetime.now()
        time_str = now.strftime("%y%m%d%H%M%S")


        db = SqlHelper()

        try:

            db.transaction([
            ("update TRN_LOG set UPD_USR=:UPD_USR where LOG_KEY =:LOG_KEY"
             , [
                 SqlParameter("LOG_KEY", 10000061)
                ,SqlParameter("UPD_USR", 777)
                ]),
            ("update TRN_LOG set UPD_USR=:UPD_USR where LOG_KEY =:LOG_KEY"
             , [
                 SqlParameter("UPD_USR", 888)
                ,SqlParameter("LOG_KEY", 10000062)
                ]),
            ])

        except Exception as e:          
            print("❌ 事务提交失败:", e)
        finally:
            db.close()

        handler.setFormatter(formatter)

        logger = logging.getLogger('mydiary')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        conn_str = ConfigManager.get_connection_string()

        logger.info(conn_str)


       
        logger.info('今天记录了一条日22记11')
        logger.info('米ロ首脳会談始33まる11、ウクライナ停戦へ協議握手であいさつロイター')

        uid = self.input_id.text()
        uname = self.input_name.text()
        birth = self.input_birth.date().toString("yyyy-MM-dd")
        QMessageBox.information(self, "登录信息", f"用户ID: {uid}\n用户名: {uname}\n生日: {birth}{conn_str}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
