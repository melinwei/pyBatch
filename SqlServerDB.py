import pyodbc
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple, Union
from Config_manager import ConfigManager
from dataclasses import dataclass
from typing import Any

@dataclass
class SqlParameter:
    param_name: str
    param_value: Any


class SqlServerDB:
    """SQL Server 数据库连接管理类，支持连接池和事务管理"""    
    def __init__(self, pool_size: int = 10, connection_timeout: int = 30):
        self.connection_string = ConfigManager.get_connection_string()
        self.pool_size = pool_size
        self.connection_timeout = connection_timeout
        self.conn = None       
   
        
    def connect(self) -> None:
        """建立数据库连接"""
        if self.conn is None or self._is_connection_closed():
            try:
                self.conn = pyodbc.connect(
                    self.connection_string,
                    timeout=self.connection_timeout
                )
                self.conn.autocommit = False
            except pyodbc.Error as e:
                raise ConnectionError(f"数据库连接失败: {e}")
                
    def _is_connection_closed(self) -> bool:
        """检查连接是否已关闭"""
        if self.conn is None:
            return True
        try:
            # 尝试执行简单查询来检查连接状态
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return False
        except:
            return True
            
    def close(self) -> None:
        """关闭数据库连接"""
        if self.conn:
            try:
                self.conn.close()
            except Exception as e:
                raise
            finally:
                self.conn = None
                
    def __enter__(self):
        """支持 with 语句的上下文管理器"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器时关闭连接"""
        if exc_type:
            self.rollback()
        self.close()
        
    # ---------- 事务控制 ----------
    def begin_transaction(self) -> None:
        """显式开始事务"""
        self.connect()
        
        
    def commit(self) -> None:
        """提交事务"""
        if not self.conn:
            raise RuntimeError("没有活动的数据库连接")
        try:
            self.conn.commit()
        except pyodbc.Error as e:
            raise
            
    def rollback(self) -> None:
        """回滚事务"""
        if not self.conn:           
            return
        try:
            self.conn.rollback()           
        except pyodbc.Error as e:
           return
            
    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        self.begin_transaction()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise
            
    # ---------- SQL 执行方法 ----------
    def execute(self, sql: str, params: Optional[Union[Tuple, List, Dict]] = None) -> int:
        """执行 SQL 语句并返回受影响的行数"""
        self.connect()
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            affected_rows = cursor.rowcount
            return affected_rows
        except pyodbc.Error as e:
            raise
        finally:
            cursor.close()
            
    def execute_many(self, sql: str, params_list: List[Union[Tuple, List, Dict]]) -> int:
        """批量执行 SQL 语句"""
        self.connect()
        cursor = self.conn.cursor()
        try:
            cursor.executemany(sql, params_list)
            affected_rows = cursor.rowcount
            return affected_rows
        except pyodbc.Error as e:
            raise
        finally:
            cursor.close()
            
    def fetch_one(self, sql: str, params: Optional[Union[Tuple, List, Dict]] = None) -> Optional[pyodbc.Row]:
        """执行查询并返回单行结果"""
        self.connect()
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            result = cursor.fetchone()
            return result
        except pyodbc.Error as e:
            raise
        finally:
            cursor.close()
            
    def fetch_all(self, sql: str, params: Optional[Union[Tuple, List, Dict]] = None) -> List[pyodbc.Row]:
        """执行查询并返回所有结果"""
        self.connect()
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            results = cursor.fetchall()
            return results
        except pyodbc.Error as e:
            raise
        finally:
            cursor.close()
            
    def fetch_many(self, sql: str, size: int, params: Optional[Union[Tuple, List, Dict]] = None) -> List[pyodbc.Row]:
        """执行查询并返回指定数量的结果"""
        self.connect()
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            results = cursor.fetchmany(size)
            return results
        except pyodbc.Error as e:
            raise
        finally:
            cursor.close()
            
    def execute_scalar(self, sql: str, params: Optional[Union[Tuple, List, Dict]] = None) -> Any:
        """执行查询并返回第一行第一列的值"""
        result = self.fetch_one(sql, params)
        return result[0] if result else None
        
    def table_exists(self, table_name: str, schema: str = 'dbo') -> bool:
        """检查表是否存在"""
        sql = """
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        """
        count = self.execute_scalar(sql, (schema, table_name))
        return count > 0
        
    def get_table_columns(self, table_name: str, schema: str = 'dbo') -> List[str]:
        """获取表的列名"""
        sql = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        results = self.fetch_all(sql, (schema, table_name))
        return [row[0] for row in results]
    
        
    # ---------- 便捷方法 ----------
    def insert(self, table: str, data: Dict[str, Any], schema: str = 'dbo') -> int:
        """便捷的插入方法"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {schema}.{table} ({columns}) VALUES ({placeholders})"
        return self.execute(sql, tuple(data.values()))
        
    def update(self, table: str, data: Dict[str, Any], where_clause: str, 
               where_params: Optional[Union[Tuple, List]] = None, schema: str = 'dbo') -> int:
        """便捷的更新方法"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {schema}.{table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values())
        if where_params:
            params.extend(where_params)
        return self.execute(sql, params)
        
    def delete(self, table: str, where_clause: str, 
               where_params: Optional[Union[Tuple, List]] = None, schema: str = 'dbo') -> int:
        """便捷的删除方法"""
        sql = f"DELETE FROM {schema}.{table} WHERE {where_clause}"
        return self.execute(sql, where_params)
        
    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()








# 使用示例
if __name__ == "__main__":
    # 基本使用
    db = SqlServerDB()
    
    # 方式1: 手动管理连接
    try:
        db.connect()
        
        # 插入数据
        affected = db.insert('users', {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30
        })
        
        db.commit()
        print(f"插入了 {affected} 行")
        
    except Exception as e:
        db.rollback()
        print(f"操作失败: {e}")
    finally:
        db.close()
    
    # 方式2: 使用上下文管理器
    with SqlServerDB() as db:
        # 查询数据
        users = db.fetch_all("SELECT * FROM users WHERE age > ?", (25,))
        for user in users:
            print(f"用户: {user.name}, 邮箱: {user.email}")
    
    # 方式3: 使用事务上下文管理器
    with SqlServerDB() as db:
        with db.transaction():
            # 批量操作
            db.execute("INSERT INTO logs (message) VALUES (?)", ("操作开始",))
            db.update('users', {'last_login': 'GETDATE()'}, 'id = ?', (1,))
            # 如果出现异常，事务会自动回滚