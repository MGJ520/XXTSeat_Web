import mysql
from mysql.connector import Error
import datetime

from Program_configuration import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD


class AppointmentDB:
    def __init__(self, host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, database='XXT_Booking'):
        """
        初始化数据库连接。

        :param host: 数据库主机地址
        :param user: 数据库用户名
        :param passwd: 数据库密码
        :param database: 数据库名
        """
        self.host = host
        self.user = user
        self.passwd = passwd
        self.database = database
        self.creat_table()
        self.conn = None
        self.cursor = None
        self.connect()

    def is_connected(self):
        try:
            # 尝试执行一个简单的查询来检查连接是否活跃
            self.cursor.execute("SELECT 1")
            return True
        except Error:
            # 如果发生错误，则可能连接已经断开
            return False
        except AttributeError:
            # 如果 cursor 为 None，则说明连接尚未建立
            return False

    def connect(self):
        """
        建立与MySQL数据库的连接。
        """
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                passwd=self.passwd,
                database=self.database
            )
            self.cursor = self.conn.cursor()
        except Error as e:
            print(f"Error: {e}")

    def close(self):
        """
        关闭数据库连接。
        """
        if self.conn.is_connected():
            self.cursor.close()
            self.conn.close()


    def creat_table(self):
        try:
            # 连接MySQL数据库
            conn = mysql.connector.connect(
                host=self.host,  # 数据库主机地址
                user=self.user,  # 数据库用户名
                passwd=self.passwd  # 数据库密码
            )
            # 创建cursor对象
            cursor = conn.cursor()
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            # 选择数据库
            cursor.execute(f"USE {self.database}")
            # 创建表
            # TODO :多用户多账号表格
            create_table_query = """
       CREATE TABLE IF NOT EXISTS appointment (
    account VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    appointment_start_time TIME NOT NULL,
    appointment_end_time TIME NOT NULL,
    reservation_end_time DATETIME NOT NULL,
    room_location INT NOT NULL,
    seat_location INT NOT NULL,
    current_status INT NOT NULL,
    is_auto_reservation BOOLEAN NOT NULL DEFAULT FALSE,  
    is_auto_check_in BOOLEAN NOT NULL DEFAULT FALSE      
);
        """
            cursor.execute(create_table_query)
            # 提交事务
            conn.commit()
            # print("MySQL数据库配置成功！")
            conn.close()
            cursor.close()
        except Error as e:
            print(f"Error: {e}")
            return None


    def query_appointments(self):
        """
        查询所有预约记录。

        :return: 查询结果列表
        """
        try:
            self.cursor.execute("SELECT * FROM appointment")
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
            return None

    def query_appointments_by_account(self, account):
        """
        查询指定账号的所有预约记录。

        :param account: 预约账户
        :return: 查询结果列表
        """
        try:
            # 构建查询语句，包含WHERE子句以过滤特定账号的记录
            query_sql = "SELECT * FROM appointment WHERE account = %s"
            params = (account,)

            # 执行查询操作
            self.cursor.execute(query_sql, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"查询预约记录时发生错误：{e}")
            return None

    def update_appointment_new_status(self, account, new_status):
        """
        更新特定预约的状态。
        :param account: 预约账户
        :param new_status: 新的预约状态
        """
        try:
            self.cursor.execute("UPDATE appointment SET current_status = %s WHERE account = %s", (new_status, account))
            self.conn.commit()
        except Error as e:
            print(f"Error: {e}")




    def insert_appointment(self, account, password, start_time, end_time, reservation_end_time, room_location,
                           seat_location, current_status, is_auto_reservation, is_auto_checkin):
        """
        插入新的预约记录。

        :param account: 预约账户
        :param password: 密码
        :param start_time: 预约开始时间
        :param end_time: 预约结束时间
        :param reservation_end_time: 预约截止时间
        :param room_location: 房间位置
        :param seat_location: 座位位置
        :param current_status: 当前状态
        :param is_auto_reservation: 是否自动预约
        :param is_auto_checkin: 是否自动签到
        """
        try:
            self.cursor.execute(
                "INSERT INTO appointment (account, password, appointment_start_time, appointment_end_time, reservation_end_time, room_location, seat_location, current_status, is_auto_reservation, is_auto_check_in) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (account, password, start_time, end_time, reservation_end_time, room_location, seat_location,
                 current_status, is_auto_reservation, is_auto_checkin))
            self.conn.commit()
        except Error as e:
            print(f"Error: {e}")

    def update_appointment(self, account, password=None, start_time=None, end_time=None, reservation_end_time=None,
                           room_location=None, seat_location=None, current_status=None, is_auto_reservation=None,
                           is_auto_checkin=None):
        """
        更新预约记录。

        :param account: 预约账户
        :param password: 新密码（可选）
        :param start_time: 新预约开始时间（可选）
        :param end_time: 新预约结束时间（可选）
        :param reservation_end_time: 新预约截止时间（可选）
        :param room_location: 新房间位置（可选）
        :param seat_location: 新座位位置（可选）
        :param current_status: 新当前状态（可选）
        :param is_auto_reservation: 是否自动预约（可选）
        :param is_auto_checkin: 是否自动签到（可选）
        """
        try:
            # 构建更新语句和参数列表
            update_fields = []
            params = []
            if password is not None:
                update_fields.append("password = %s")
                params.append(password)
            if start_time is not None:
                update_fields.append("appointment_start_time = %s")
                params.append(start_time)
            if end_time is not None:
                update_fields.append("appointment_end_time = %s")
                params.append(end_time)
            if reservation_end_time is not None:
                update_fields.append("reservation_end_time = %s")
                params.append(reservation_end_time)
            if room_location is not None:
                update_fields.append("room_location = %s")
                params.append(room_location)
            if seat_location is not None:
                update_fields.append("seat_location = %s")
                params.append(seat_location)
            if current_status is not None:
                update_fields.append("current_status = %s")
                params.append(current_status)
            if is_auto_reservation is not None:
                update_fields.append("is_auto_reservation = %s")
                params.append(is_auto_reservation)
            if is_auto_checkin is not None:
                update_fields.append("is_auto_check_in = %s")
                params.append(is_auto_checkin)

            # 如果没有要更新的字段，则直接返回
            if not update_fields:
                print("没有要更新的字段。")
                return

            # 构建完整的更新语句
            update_sql = f"UPDATE appointment SET {', '.join(update_fields)} WHERE account = %s"
            params.append(account)

            # 执行更新操作
            self.cursor.execute(update_sql, tuple(params))
            self.conn.commit()
            print(f"预约记录更新成功，账户：{account}")
        except Exception as e:
            print(f"更新预约记录时发生错误：{e}")

    def delete_appointment(self, account):
        """
        删除特定账户的预约记录。

        :param account: 预约账户
        """
        try:
            self.cursor.execute("DELETE FROM appointment WHERE account = %s", (account,))
            self.conn.commit()
        except Error as e:
            print(f"Error: {e}")



    def database_exists(self, db_name):
        """
        检查数据库是否存在。

        :param db_name: 数据库名
        :return: 如果数据库存在则返回True，否则返回False
        """
        try:
            self.cursor.execute("SHOW DATABASES")
            databases = self.cursor.fetchall()
            for (database,) in databases:
                if db_name == database:
                    return True
            return False
        except Error as e:
            print(f"Error: {e}")
            return False

    def update_auto_reservation(self, account, is_auto_reservation):
        print(f"Updating auto reservation for account: {account}, setting to: {is_auto_reservation}")
        try:
            # 构造参数化的 SQL 语句
            sql = """
                UPDATE appointment
                SET is_auto_reservation = %s
                WHERE account = %s
            """
            # print(f"Executing SQL: {sql}")  # 调试：打印 SQL 语句

            # 将布尔值转换为 TINYINT(1) 的值
            is_auto_reservation_value = 1 if is_auto_reservation else 0

            # 更新 is_auto_reservation 列
            self.cursor.execute(sql, (is_auto_reservation_value, account))

            # 提交更改
            self.conn.commit()
            if self.cursor.rowcount == 0:
                print("No record found for the given account.")
                return False
            else:
                print("Auto reservation updated successfully.")
                return True
        except Exception as e:  # 使用更通用的 Exception 来捕获所有异常
            print(f"Error updating auto reservation: {e}")
            return False

    def update_auto_check_in(self, account, is_auto_check_in):
        print(f"Updating auto check-in for account: {account}, setting to: {is_auto_check_in}")
        try:
            # 构造参数化的 SQL 语句
            sql = """
                UPDATE appointment
                SET is_auto_check_in = %s
                WHERE account = %s
            """
            print(f"Executing SQL: {sql}")  # 调试：打印 SQL 语句

            # 将布尔值转换为 TINYINT(1) 的值
            is_auto_check_in_value = 1 if is_auto_check_in else 0

            # 更新 is_auto_check_in 列
            self.cursor.execute(sql, (is_auto_check_in_value, account))

            # 提交更改
            self.conn.commit()
            if self.cursor.rowcount == 0:
                print("No record found for the given account.")
                return False
            else:
                print("Auto check-in updated successfully.")
                return True
        except Exception as e:  # 使用更通用的 Exception 来捕获所有异常
            print(f"Error updating auto check-in: {e}")
            return False

    def check_account_exists(self, account):
        """
        判断数据库中是否存在指定的 account 账户。

        :param account: 要检查的账户
        :return: 如果账户存在，返回 True；否则返回 False
        """
        try:
            # 构建查询语句
            query_sql = "SELECT COUNT(*) FROM appointment WHERE account = %s"

            # 执行查询操作
            self.cursor.execute(query_sql, (account,))

            # 获取查询结果
            result = self.cursor.fetchone()

            # 检查账户是否存在
            if result[0] > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"检查账户存在性时发生错误：{e}")
            return False

    import datetime

    def fetch_appointments(self):
        try:
            # 执行查询操作，获取所有预约记录
            query_sql = """
            SELECT account, password, appointment_start_time, appointment_end_time, room_location, seat_location,is_auto_reservation
            FROM appointment
            """
            self.cursor.execute(query_sql)
            rows = self.cursor.fetchall()

            # 初始化一个空列表来存储转换后的预约数据
            appointments_data = []

            # 遍历查询结果，将每条记录转换为所需的字典格式
            for row in rows:
                # 将时间字段格式化为'HH:MM'格式
                start_time_str = row[2].strftime('%H:%M') if isinstance(row[2], datetime.time) else str(row[2])[:5]
                end_time_str = row[3].strftime('%H:%M') if isinstance(row[3], datetime.time) else str(row[3])[:5]

                # 将seat_location转换为三位数的字符串格式
                seat_location_str = f"{row[5]:03d}"

                appointment = {
                    "username": row[0],
                    "password": row[1],
                    "time": [start_time_str, end_time_str],
                    "roomid": str(row[4]),  # 假设room_location是整数类型
                    "seatid": [seat_location_str],  # 确保seatid是三位数的字符串格式
                    "daysofweek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    'is_auto_reservation':row[6]
                }
                appointments_data.append(appointment)

            return appointments_data
        except Exception as e:
            print(f"查询预约记录时发生错误：{e}")
            return []

    def find_password_by_account(self, account):
        """
        通过账号查找密码。

        :param account: 预约账户
        :return: 与账号关联的密码，如果未找到则返回None
        """
        try:
            # 构建查询语句
            query_sql = "SELECT password FROM appointment WHERE account = %s"
            params = (account,)

            # 执行查询操作
            self.cursor.execute(query_sql, params)
            result = self.cursor.fetchone()  # 获取查询结果的第一行

            # 检查是否找到结果
            if result:
                return result[0]  # 返回密码
            else:
                return None  # 如果没有找到结果，返回None
        except Exception as e:
            print(f"查找密码时发生错误：{e}")
            return None


# 使用示例
# if __name__ == "__main__":
#     db = AppointmentDB()
#     # 添加预约
#     db.insert_appointment('user1', 'pass123', '10:00', '12:00', '2025-01-10 12:00', 101, 1, 1,True,True)
#     # 查询预约
#     appointments = db.query_appointments()
#     for appointment in appointments:
#         print(appointment)
#     db.update_appointment_new_status('user1', 2)
#     # 删除预约
#     print("\n删除账号 'user1' 的预约：")
#     db.delete_appointment('user1')
#     db.close()
