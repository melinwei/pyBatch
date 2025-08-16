import pyodbc
from contextlib import contextmanager
from Config_manager import ConfigManager


class SqlSerffverDB:
    
    def __init__(self):
        self.connection_string = ConfigManager.get_connection_string()
        self.conn = None
        self.cursor = None

    def connect(self):
        """建立连接"""
        if self.conn is not None:
            return
        try:
            self.conn = pyodbc.connect(self.connection_string)
            self.cursor = self.conn.cursor()
            print("✅ 数据库连接成功")
        except Exception as e:
            print("❌ 数据库连接失败:", e)
            raise

    def execute(self, sql, params=None, auto_commit=True):
        """
        执行 SQL 语句（增删改）
        :param sql: SQL 语句
        :param params: 参数（可选）
        :param auto_commit: 是否自动提交（默认True，事务中使用时应设为False）
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
            if auto_commit:
                self.conn.commit()
                print("✅ SQL 执行成功")
            return self.cursor.rowcount  # 返回受影响的行数
        except Exception as e:
            if auto_commit:
                self.conn.rollback()
            print("❌ SQL 执行失败:", e)
            raise

    def execute_many(self, sql, params_list, auto_commit=True):
        """
        批量执行 SQL 语句
        :param sql: SQL 语句
        :param params_list: 参数列表
        :param auto_commit: 是否自动提交
        """
        try:
            self.cursor.executemany(sql, params_list)
            if auto_commit:
                self.conn.commit()
                print(f"✅ 批量SQL执行成功，影响 {self.cursor.rowcount} 行")
            return self.cursor.rowcount
        except Exception as e:
            if auto_commit:
                self.conn.rollback()
            print("❌ 批量SQL执行失败:", e)
            raise

    def fetchall(self, sql, params=None):
        """
        查询多行数据
        :param sql: SQL 查询语句
        :param params: 参数（可选）
        :return: 查询结果 list
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as e:
            print("❌ 查询失败:", e)
            return []

    def fetchone(self, sql, params=None):
        """
        查询单行数据
        :param sql: SQL 查询语句
        :param params: 参数（可选）
        :return: 单行记录
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            return self.cursor.fetchone()
        except Exception as e:
            print("❌ 查询失败:", e)
            return None

    # ============== 事务相关方法 ==============
    
    def begin_transaction(self):
        """开始事务"""
        try:
            # pyodbc 默认自动提交，这里关闭自动提交来开始事务
            self.conn.autocommit = False
            print("🔄 事务已开始")
        except Exception as e:
            print("❌ 开始事务失败:", e)
            raise

    def commit_transaction(self):
        """提交事务"""
        try:
            self.conn.commit()
            self.conn.autocommit = True  # 恢复自动提交
            print("✅ 事务提交成功")
        except Exception as e:
            print("❌ 事务提交失败:", e)
            self.rollback_transaction()
            raise

    def rollback_transaction(self):
        """回滚事务"""
        try:
            self.conn.rollback()
            self.conn.autocommit = True  # 恢复自动提交
            print("🔄 事务已回滚")
        except Exception as e:
            print("❌ 事务回滚失败:", e)
            raise

    @contextmanager
    def transaction(self):
        """
        事务上下文管理器，推荐使用方式
        使用 with db.transaction(): 语法自动管理事务
        """
        self.begin_transaction()
        try:
            yield self
            self.commit_transaction()
        except Exception as e:
            self.rollback_transaction()
            print(f"❌ 事务执行失败，已回滚: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("🔌 数据库连接已关闭")

    # ============== 便捷方法 ==============
    
    def insert(self, table, data, auto_commit=True):
        """
        便捷插入方法
        :param table: 表名
        :param data: 字典格式数据 {"column1": "value1", "column2": "value2"}
        :param auto_commit: 是否自动提交
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.execute(sql, tuple(data.values()), auto_commit)

    def update(self, table, data, where_condition, where_params=None, auto_commit=True):
        """
        便捷更新方法
        :param table: 表名
        :param data: 字典格式数据
        :param where_condition: WHERE 条件
        :param where_params: WHERE 条件参数
        :param auto_commit: 是否自动提交
        """
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_condition}"
        params = list(data.values())
        if where_params:
            params.extend(where_params if isinstance(where_params, (list, tuple)) else [where_params])
        return self.execute(sql, params, auto_commit)

    def delete(self, table, where_condition, where_params=None, auto_commit=True):
        """
        便捷删除方法
        :param table: 表名
        :param where_condition: WHERE 条件
        :param where_params: WHERE 条件参数
        :param auto_commit: 是否自动提交
        """
        sql = f"DELETE FROM {table} WHERE {where_condition}"
        params = where_params if where_params else None
        return self.execute(sql, params, auto_commit)


# ============== 使用示例 ==============
if __name__ == "__main__":
    # 方式1: 使用连接字符串（推荐）
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=127.0.0.1;"
        "DATABASE=TestDB;"
        "UID=sa;"
        "PWD=yourpassword;"
        "TrustServerCertificate=yes;"
    )
    db = SqlServerDB(connection_string=connection_string)
    
    # 方式2: 使用分离的参数（兼容原有方式）
    # db = SqlServerDB(
    #     server="127.0.0.1",
    #     database="TestDB", 
    #     user="sa",
    #     password="yourpassword"
    # )
    
    # 方式3: 使用Windows集成身份验证
    # connection_string_windows = (
    #     "DRIVER={ODBC Driver 17 for SQL Server};"
    #     "SERVER=127.0.0.1;"
    #     "DATABASE=TestDB;"
    #     "Trusted_Connection=yes;"
    #     "TrustServerCertificate=yes;"
    # )
    # db = SqlServerDB(connection_string=connection_string_windows)

    db.connect()

    try:
        # ========== 方式1: 手动控制事务 ==========
        print("\n=== 手动事务控制示例 ===")
        db.begin_transaction()
        try:
            # 在事务中执行多个操作
            db.execute("INSERT INTO Users (Name, Age) VALUES (?, ?)", ("Alice", 30), auto_commit=False)
            db.execute("INSERT INTO Users (Name, Age) VALUES (?, ?)", ("Bob", 25), auto_commit=False)
            
            # 假设这里发生错误
            # raise Exception("模拟错误")
            
            db.commit_transaction()
            print("✅ 手动事务提交成功")
        except Exception as e:
            db.rollback_transaction()
            print(f"❌ 手动事务回滚: {e}")

        # ========== 方式2: 使用上下文管理器（推荐） ==========
        print("\n=== 上下文管理器事务示例 ===")
        try:
            with db.transaction():
                # 事务中的所有操作
                db.execute("INSERT INTO Users (Name, Age) VALUES (?, ?)", ("Charlie", 28), auto_commit=False)
                db.execute("UPDATE Users SET Age = ? WHERE Name = ?", (26, "Bob"), auto_commit=False)
                
                # 如果这里出错，会自动回滚
                # raise Exception("模拟错误")
                
            print("✅ 上下文管理器事务成功")
        except Exception as e:
            print(f"❌ 上下文管理器事务失败: {e}")

        # ========== 方式3: 使用便捷方法 ==========
        print("\n=== 便捷方法示例 ===")
        try:
            with db.transaction():
                # 使用便捷插入方法
                db.insert("Users", {"Name": "David", "Age": 35}, auto_commit=False)
                
                # 使用便捷更新方法
                db.update("Users", {"Age": 36}, "Name = ?", ["David"], auto_commit=False)
                
                # 使用便捷删除方法
                # db.delete("Users", "Name = ?", ["David"], auto_commit=False)
                
            print("✅ 便捷方法事务成功")
        except Exception as e:
            print(f"❌ 便捷方法事务失败: {e}")

        # ========== 查询数据 ==========
        print("\n=== 查询结果 ===")
        rows = db.fetchall("SELECT * FROM Users")
        for row in rows:
            print(row)

        # ========== 批量操作示例 ==========
        print("\n=== 批量操作示例 ===")
        try:
            with db.transaction():
                users_data = [
                    ("Eve", 22),
                    ("Frank", 27),
                    ("Grace", 31)
                ]
                db.execute_many("INSERT INTO Users (Name, Age) VALUES (?, ?)", users_data, auto_commit=False)
            print("✅ 批量插入事务成功")
        except Exception as e:
            print(f"❌ 批量插入事务失败: {e}")

    finally:
        db.close()