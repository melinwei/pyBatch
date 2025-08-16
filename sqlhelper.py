from dataclasses import dataclass
from typing import Any, List, Optional
import pyodbc
import re
from Config_manager import ConfigManager

@dataclass
class SqlParameter:
    param_name: str
    param_value: Any

class SqlHelper:
    def __init__(self):
        self.connection_string = ConfigManager.get_connection_string()

    def _get_connection(self):
        return pyodbc.connect(self.connection_string, autocommit=False)

    def execute(self, sql: str, params: Optional[List[SqlParameter]] = None) -> int:
        sql, param_list = self._convert_named_to_qmark(sql, params)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, param_list)
                conn.commit()
                return cursor.rowcount

    def query(self, sql: str, params: Optional[List[SqlParameter]] = None) -> list:
        sql, param_list = self._convert_named_to_qmark(sql, params)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, param_list)
                columns = [column[0] for column in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results

    def transaction(self, actions: List[tuple]):
        with self._get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    for sql, params in actions:
                        sql, param_list = self._convert_named_to_qmark(sql, params)
                        cursor.execute(sql, param_list)
                conn.commit()
            except Exception as ex:
                conn.rollback()
                raise ex

    def _convert_named_to_qmark(self, sql: str, params: Optional[List[SqlParameter]]):
        if not params:
            return sql, []
        # 构建参数字典，方便后续取值
        param_dict = {p.param_name: p.param_value for p in params}
        keys = []
        def repl(match):
            key = match.group(1)
            keys.append(key)
            return "?"
        sql = re.sub(r'[:@]([A-Za-z_][A-Za-z0-9_]*)', repl, sql)
        param_list = [param_dict[k] for k in keys]
        return sql, param_list

# 用法示例
if __name__ == "__main__":
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=testdb;UID=sa;PWD=yourpassword"
    db = SqlHelper(conn_str)

    # 增
    db.execute(
        "INSERT INTO users(name, age) VALUES(:name, :age)",
        [SqlParameter("name", "Alice"), SqlParameter("age", 22)]
    )

    # 查
    users = db.query(
        "SELECT * FROM users WHERE age>:age",
        [SqlParameter("age", 20)]
    )
    print(users)

    # 事务
    db.transaction([
        ("UPDATE users SET age=age+1 WHERE id=:id", [SqlParameter("id", 1)]),
        ("INSERT INTO logs(action) VALUES(:action)", [SqlParameter("action", "add age")]),
    ])