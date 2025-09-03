import pyodbc
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass
import re
from config.settings import Settings
import pandas as pd


@dataclass
class MsSqlParameter:
    param_name: str
    param_value: Any


class MsSqlDataBase:
    """SQL Server データベース操作クラス、自動コミットと明示的トランザクションをサポート"""

    def __init__(self, connection_timeout: int = 30):
        self.connection_string = Settings.get_connection_string()
        self.connection_timeout = connection_timeout
        self.conn = None
        self.in_transaction = False  # 手動でトランザクションを開始したかどうかのフラグ

    def connect(self) -> None:
        if self.conn is None or self._is_connection_closed():
            self.conn = pyodbc.connect(
                self.connection_string,
                timeout=self.connection_timeout
            )
            self.conn.autocommit = False   # 統一してオフにし、手動制御
            self.in_transaction = False    # 新しい接続はデフォルトで非トランザクションモード

    def _is_connection_closed(self) -> bool:
        if self.conn is None:
            return True
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return False
        except:
            return True

    def close(self) -> None:
        if self.conn:
            try:
                # トランザクション中でコミット/ロールバックされていない場合、自動ロールバック
                if self.in_transaction:
                    self.conn.rollback()
            finally:
                self.conn.close()
                self.conn = None
                self.in_transaction = False

    # ---------- トランザクション ----------
    def begin_transaction(self) -> None:
        """手動トランザクションを開始"""
        self.connect()
        self.in_transaction = True

    def commit(self) -> None:
        if not self.conn:
            raise RuntimeError("アクティブなデータベース接続がありません")
        self.conn.commit()
        self.in_transaction = False

    def rollback(self) -> None:
        if self.conn:
            self.conn.rollback()
        self.in_transaction = False

    # ---------- パラメータ処理 ----------
    def _convert_named_params(self, sql: str, params: List[MsSqlParameter]) -> Tuple[str, List[Any]]:
        if not params:
            return sql, []
        param_dict = {p.param_name: p.param_value for p in params}
        pattern = r':(\w+)'
        matches = re.findall(pattern, sql)
        param_values = [param_dict[name] for name in matches]
        converted_sql = re.sub(pattern, '?', sql)
        return converted_sql, param_values

    def _process_parameters(
        self, sql: str, params: Optional[Union[List[MsSqlParameter], Tuple, List, Dict]]
    ) -> Tuple[str, Optional[Union[Tuple, List, Dict]]]:
        if params is None:
            return sql, None
        if isinstance(params, list) and params and isinstance(params[0], MsSqlParameter):
            return self._convert_named_params(sql, params)
        return sql, params

    # ---------- 実行 ----------
    def execute(self, sql: str, params: Optional[Union[List[MsSqlParameter], Tuple, List, Dict]] = None) -> int:
        self.connect()
        cursor = self.conn.cursor()
        try:
            sql, params = self._process_parameters(sql, params)
            cursor.execute(sql, params) if params else cursor.execute(sql)
            affected = cursor.rowcount

            # トランザクションがない場合、自動コミット
            if not self.in_transaction:
                self.conn.commit()

            return affected
        finally:
            cursor.close()

    def fetch_one(self, sql: str, params: Optional[Union[List[MsSqlParameter], Tuple, List, Dict]] = None) -> Optional[Dict[str, Any]]:
        self.connect()
        cursor = self.conn.cursor()
        try:
            sql, params = self._process_parameters(sql, params)
            cursor.execute(sql, params) if params else cursor.execute(sql)
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None
        finally:
            cursor.close()

    def fetch_all(self, sql: str, params: Optional[Union[List[MsSqlParameter], Tuple, List, Dict]] = None) -> List[Dict[str, Any]]:
        self.connect()
        cursor = self.conn.cursor()
        try:
            sql, params = self._process_parameters(sql, params)
            cursor.execute(sql, params) if params else cursor.execute(sql)
            rows = cursor.fetchall()
            if rows:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        finally:
            cursor.close()

    def fetch_all_data(self, sql: str, params: Optional[Union[List[MsSqlParameter], Tuple, List, Dict]] = None) -> pd.DataFrame:
        """複数行データをクエリしてpandas DataFrameを返す"""
        data = self.fetch_all(sql, params)
        if not data:
            return pd.DataFrame()  # 空のテーブル
        return pd.DataFrame(data)

    def fetch_all_json(self, sql: str, params: Optional[Union[List[MsSqlParameter], Tuple, List, Dict]] = None) -> List[Dict[str, Any]]:
         df = self.fetch_all_data(sql, params)
         return df.to_json(orient='records', force_ascii=False)  #


# 使用例
if __name__ == "__main__":
    db = MsSqlDataBase()
    try:
        # --- 自動コミットモード（begin_transactionを呼び出していない）---
        db.execute("INSERT INTO TRN_LOG (LOG_KEY, UPD_USR) VALUES (?, ?)", ("100", "auto"))
        print("自動コミット完了")

        # --- 手動トランザクションモード ---
        db.begin_transaction()
        db.execute("INSERT INTO TRN_LOG (LOG_KEY, UPD_USR) VALUES (?, ?)", ("200", "manual"))
        db.execute("UPDATE TRN_LOG SET UPD_USR=? WHERE LOG_KEY=?", ("manual2", "200"))
        db.commit()
        print("手動トランザクションコミット完了")

    except Exception as e:
        print("操作失敗:", e)
        db.rollback()
    finally:
        db.close()

