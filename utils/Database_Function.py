from datetime import time, datetime
import mysql
from flask import jsonify
from mysql.connector import Error

from werkzeug.security import generate_password_hash, check_password_hash

from Program_configuration import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD


class DatabaseManager:
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
            print(f"Error:connect {e}")

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
                passwd=self.passwd,  # 数据库密码
            )

            # 创建cursor对象
            cursor = conn.cursor()
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            # 选择数据库
            cursor.execute(f"USE {self.database}")
            # 预约表 SQL
            reservation_table_sql = """
            CREATE TABLE IF NOT EXISTS Reservation (
                platform_email           VARCHAR(255)     COMMENT '用户邮箱地址',
                account_status           INT              COMMENT '账户状态',
                reservation_account      VARCHAR(255)     COMMENT '用户预约账号',
                reservation_password     VARCHAR(255)     COMMENT '预约密码',
                start_time               TIME             COMMENT '预约开始时间',
                end_time                 TIME             COMMENT '预约结束时间',
                reservation_end_time     DATETIME         COMMENT '预约结束日期',
                room_location            VARCHAR(255)     COMMENT '预约房间的位置',
                seat_location            VARCHAR(255)     COMMENT '预约座位的位置',
                refresh_status           BOOLEAN          COMMENT '是否启动检查服务',
                reservation_status       BOOLEAN          COMMENT '是否启动预约服务',
                sign_in_status           BOOLEAN          COMMENT '签到服务是否启动',
                sign_back_status         BOOLEAN          COMMENT '签退服务是否启动',
                monitor_sign_in_status   BOOLEAN          COMMENT '监控签到服务是否启动',
                reservation_times        INT              COMMENT '预约服务剩余次数', -- 修正为 INT
                sign_in_times            INT              COMMENT '签到服务剩余次数',
                sign_back_times          INT              COMMENT '签退服务剩余次数',
                monitor_sign_in_times    INT              COMMENT '监控签到服务剩余次数',
                operation_failure_times  INT              COMMENT '操作失败次数',
                
                PRIMARY KEY (reservation_account),
                FOREIGN KEY (platform_email) REFERENCES User(platform_email)
                ) ENGINE=InnoDB;
            """

            # 用户表 SQL
            user_table_sql = """
            CREATE TABLE IF NOT EXISTS User (
                platform_email        VARCHAR(255) PRIMARY KEY COMMENT '用户邮箱地址',
                platform_nickname     VARCHAR(255) COMMENT '用户在平台的昵称',
                platform_password     VARCHAR(255) COMMENT '用户在平台的密码',
                
                platform_account_time DATETIME     COMMENT '注册日期',
                last_login_time       DATETIME     COMMENT '用户上次登录的时间',
                latest_login_ip       VARCHAR(255) COMMENT '用户最近一次登录的IP地址',
                
                account_count         INT          COMMENT '用户用户预约账号数',
                login_count           INT          COMMENT '用户登录的总次数',
                login_failure_count   INT          COMMENT '用户登录失败的总次数',
                
                permission_level      INT          COMMENT '用户的权限级别'
            )
            """

            # 创建触发器
            trigger_sql = """
            DELIMITER //
            CREATE TRIGGER IF NOT EXISTS after_reservation_insert
            AFTER INSERT ON Reservation
            FOR EACH ROW
            BEGIN
                UPDATE User
                SET account_count = account_count + 1
                WHERE platform_email = NEW.platform_email;
            END; //
            DELIMITER ;
            """
            # 创建删除操作的触发器
            trigger_delete_sql = """
            DELIMITER //
            CREATE TRIGGER IF NOT EXISTS after_reservation_delete
            AFTER DELETE ON Reservation
            FOR EACH ROW
            BEGIN
                UPDATE User
                SET account_count = account_count - 1
                WHERE platform_email = OLD.platform_email;
            END; //
            DELIMITER ;
            """
            cursor.execute(user_table_sql)
            cursor.execute(reservation_table_sql)

            cursor.execute(trigger_delete_sql)
            cursor.execute(trigger_sql)
            # 提交事务
            conn.commit()
            # print("Tables created successfully.")
            conn.close()
        except Error as e:
            print(f"Error: creat_table {e}")
            return None

    def login_user(self, platform_email, platform_password, user_ip):
        """
        用户登录，记录登录总次数，记录登录ip，返回密码
        """
        try:
            self.connect()
            cursor = self.conn.cursor()

            # 查询用户信息
            sql = "SELECT platform_password, login_count FROM User WHERE platform_email = %s"
            cursor.execute(sql, (platform_email,))
            result = cursor.fetchone()

            # 检查用户是否存在以及密码是否正确
            if result and check_password_hash(result[0], platform_password):
                sql_update_count = "UPDATE User SET login_count = login_count + 1, latest_login_ip = %s ,last_login_time=%s  WHERE platform_email = %s"
                cursor.execute(sql_update_count, (user_ip, datetime.now(), platform_email,))
                self.conn.commit()
                return True
            else:
                if result:
                    sql_update_count = "UPDATE User SET login_failure_count = login_failure_count + 1, latest_login_ip = %s WHERE platform_email = %s"
                    cursor.execute(sql_update_count, (user_ip, platform_email,))
                    self.conn.commit()
                    return False
        except Exception as e:
            print(f"Error: login_user {e}")
            return False
        finally:
            self.close()

    def register_user(self, platform_email, platform_nickname, platform_password, user_ip):
        """
        注册新用户，并检查邮箱是否已被占用。
        """
        try:
            self.connect()
            cursor = self.conn.cursor()
            # 检查邮箱是否已被占用
            sql_check_email = "SELECT platform_email FROM User WHERE platform_email = %s"
            cursor.execute(sql_check_email, (platform_email,))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Email already exists'})  # 邮箱已被占用，直接返回失败

            # 插入新用户
            sql = """
            INSERT INTO User (
                platform_email, platform_nickname, platform_password,platform_account_time, last_login_time, 
                latest_login_ip, login_count, login_failure_count, permission_level
            ) VALUES (%s, %s, %s, %s,%s, %s, %s, %s, %s)
            """
            values = (
                platform_email,
                platform_nickname,
                generate_password_hash(platform_password),
                datetime.now(),
                None,
                user_ip,
                0,
                0,
                1  # 初始权限级别设为1，可以根据实际情况调整
            )
            cursor.execute(sql, values)
            self.conn.commit()
            if cursor.rowcount > 0:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to register new user.'})
        except Error as e:
            print(f"Error:register_user {e}")
            return jsonify({'success': False, 'error': 'Failed to register new user.'})
        finally:
            self.close()

    # 定义一个函数来读取所有预约或者根据指定email读取预约
    def read_reservations(self, platform_email=None, read_all=False):
        try:
            self.connect()
            cursor = self.cursor
            if not read_all:
                # 如果提供了platform_email，则只查询该用户的预约
                sql = "SELECT * FROM Reservation WHERE platform_email = %s"
                cursor.execute(sql, (platform_email,))
            else:
                # 否则查询所有预约
                sql = "SELECT * FROM Reservation"
                cursor.execute(sql)
            # 获取所有结果
            return self.cursor.fetchall()
        except Error as e:
            print(f"查询email预约记录时发生错误：{e}")
            return None
        finally:
            self.close()

    def read_reservations_by_account(self, platform_email=None, reservation_account=None):
        try:
            self.connect()
            cursor = self.cursor
            if platform_email and reservation_account:
                sql = "SELECT * FROM Reservation WHERE platform_email = %s and reservation_account= %s"
                cursor.execute(sql, (platform_email, reservation_account,))
            else:
                return None
            # 获取所有结果
            return self.cursor.fetchall()
        except Error as e:
            print(f"查询email-account预约记录时发生错误：{e}")
            return None
        finally:
            self.close()

    # 更新特定预约的状态
    def update_reservations_new_status(self, reservation_account=None, new_account_status=9):
        success = False
        try:
            self.connect()
            if reservation_account:
                cursor = self.conn.cursor()
                # 更新指定用户的预约账户状态
                sql = """
                UPDATE Reservation
                SET account_status = %s
                WHERE reservation_account = %s
                """
                cursor.execute(sql, (new_account_status, reservation_account))
                self.conn.commit()
                success = True
            else:
                print("platform_email and reservation_account must be provided.")
                success = False
            return success
        except Error as e:
            print(f"Error:update_reservations_new_status {e}")
            return success
        finally:
            self.close()

    def insert_reservations(self, platform_email, reservation_account, reservation_password, start_time, end_time,
                            reservation_end_time, room_location, seat_location, account_status, refresh_status,
                            reservation_status,
                            sign_in_status, sign_back_status, monitor_sign_in_status, reservation_times,
                            sign_in_times, sign_back_times, monitor_sign_in_times, operation_failure_times):
        """
        插入新的预约记录。
        """
        success = False
        try:
            self.connect()
            cursor = self.conn.cursor()
            sql = """
            INSERT INTO Reservation (
                platform_email, reservation_account, reservation_password, start_time, end_time,
                reservation_end_time, room_location, seat_location, account_status,refresh_status, reservation_status,
                sign_in_status, sign_back_status, monitor_sign_in_status, reservation_times,
                sign_in_times, sign_back_times, monitor_sign_in_times, operation_failure_times
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s)
            """
            values = (
                platform_email, reservation_account, reservation_password, start_time, end_time,
                reservation_end_time, room_location, seat_location, account_status, refresh_status, reservation_status,
                sign_in_status, sign_back_status, monitor_sign_in_status, reservation_times,
                sign_in_times, sign_back_times, monitor_sign_in_times, operation_failure_times
            )
            cursor.execute(sql, values)
            self.conn.commit()
            if cursor.rowcount > 0:
                success = True
                print(f"New reservation inserted for {platform_email}.")
            else:
                print("Failed to insert new reservation.")
                success = False
            return success
        except Error as e:
            print(f"Error:insert_reservations {e}")
        finally:
            self.close()

    def update_reservation(self, platform_email, start_time=None, end_time=None, reservation_end_time=None,
                           room_location=None, seat_location=None, account_status=None, refresh_status=None,
                           reservation_status=None, sign_in_status=None, sign_back_status=None,
                           monitor_sign_in_status=None, reservation_times=None, sign_in_times=None,
                           sign_back_times=None, monitor_sign_in_times=None, operation_failure_times=None):
        """
        更新预约记录。
        platform_email 是必须的，其他字段是可选的。
        """
        success = False
        try:
            self.connect()
            cursor = self.conn.cursor()

            # 构建SQL语句和参数
            set_parts = []
            params = []
            if start_time is not None:
                set_parts.append("start_time = %s")
                params.append(start_time)
            if end_time is not None:
                set_parts.append("end_time = %s")
                params.append(end_time)
            if reservation_end_time is not None:
                set_parts.append("reservation_end_time = %s")
                params.append(reservation_end_time)
            if room_location is not None:
                set_parts.append("room_location = %s")
                params.append(room_location)
            if seat_location is not None:
                set_parts.append("seat_location = %s")
                params.append(seat_location)
            if account_status is not None:
                set_parts.append("account_status = %s")
                params.append(account_status)
            if refresh_status is not None:
                set_parts.append("refresh_status = %s")
                params.append(refresh_status)
            if reservation_status is not None:
                set_parts.append("reservation_status = %s")
                params.append(reservation_status)
            if sign_in_status is not None:
                set_parts.append("sign_in_status = %s")
                params.append(sign_in_status)
            if sign_back_status is not None:
                set_parts.append("sign_back_status = %s")
                params.append(sign_back_status)
            if monitor_sign_in_status is not None:
                set_parts.append("monitor_sign_in_status = %s")
                params.append(monitor_sign_in_status)
            if reservation_times is not None:
                set_parts.append("reservation_times = %s")
                params.append(reservation_times)
            if sign_in_times is not None:
                set_parts.append("sign_in_times = %s")
                params.append(sign_in_times)
            if sign_back_times is not None:
                set_parts.append("sign_back_times = %s")
                params.append(sign_back_times)
            if monitor_sign_in_times is not None:
                set_parts.append("monitor_sign_in_times = %s")
                params.append(monitor_sign_in_times)
            if operation_failure_times is not None:
                set_parts.append("operation_failure_times = %s")
                params.append(operation_failure_times)

            if not set_parts:
                print("No fields to update.")
                return success

            set_clause = ", ".join(set_parts)
            sql = f"""
            UPDATE Reservation
            SET {set_clause}
            WHERE platform_email = %s
            """
            params.append(platform_email)  # platform_email 作为WHERE子句的条件

            cursor.execute(sql, params)
            self.conn.commit()

            if cursor.rowcount > 0:
                success = True
                print(f"Reservation updated for {platform_email}.")
            else:
                print("No changes made to the reservation.")

            return success
        except Error as e:
            print(f"Error:update_reservation {e}")
        finally:
            self.close()

    def delete_reservation_by_account(self, reservation_account):
        """
        根据提供的reservation_account删除预约表中的记录。
        """
        try:
            self.connect()  # 确保这个方法正确地连接到数据库
            cursor = self.conn.cursor()

            # SQL 删除语句
            sql = """
            DELETE FROM Reservation
            WHERE reservation_account = %s
            """

            # 执行删除操作
            cursor.execute(sql, (reservation_account,))
            self.conn.commit()

            return True

        except Exception as e:  # 使用更一般的异常捕获，具体取决于你的数据库模块
            print(f"Error: delete_reservation_by_reservation_account {e}")
            return False
        finally:
            self.close()  # 确保这个方法正确地关闭数据库连接

    def update_auto_reservation(self, account, reservation_status):
        print(f"Updating auto reservation for account: {account}, setting to: {reservation_status}")
        try:
            self.connect()
            # 构造参数化的 SQL 语句
            sql = """
                UPDATE Reservation
                SET reservation_status = %s
                WHERE account = %s
            """
            # print(f"Executing SQL: {sql}")  # 调试：打印 SQL 语句

            # 将布尔值转换为 TINYINT(1) 的值
            is_auto_reservation_value = 1 if reservation_status else 0

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
        finally:
            self.close()

    def check_account_exists(self, reservation_account, conn):
        """
        检查预约表中是否存在特定的reservation_account。

        参数:
        reservation_account -- 要检查的预约账户
        conn -- 数据库连接对象

        返回:
        布尔值，表示账户是否存在
        """
        try:
            self.connect()
            cursor = conn.cursor()

            # SQL 查询语句
            sql = """
            SELECT EXISTS(
                SELECT 1 FROM Reservation
                WHERE reservation_account = %s
            )
            """

            # 执行查询
            cursor.execute(sql, (reservation_account,))
            exists = cursor.fetchone()[0]

            return exists
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        finally:
            self.close()

    # 返回用户预约信息
    def fetch_check_information(self, user_email=None):
        try:
            self.connect()
            # 执行查询操作，获取所有预约记录，如果提供了 user_email，则只获取该用户的记录
            query_sql = """
            SELECT reservation_account, reservation_password, start_time, end_time, room_location, seat_location, refresh_status, reservation_status 
            FROM Reservation
            {}
            """.format("WHERE platform_email = %s" if user_email else "")
            params = (user_email,) if user_email else ()
            self.cursor.execute(query_sql, params)
            rows = self.cursor.fetchall()

            # 初始化一个空列表来存储转换后的预约数据
            appointments_data = []
            # 遍历查询结果，将每条记录转换为所需的字典格式
            for row in rows:
                # 检查时间字段是否为 datetime.time 类型
                start_time_str = row[2].strftime('%H:%M') if isinstance(row[2], (time, datetime)) else str(row[2])[:5]
                end_time_str = row[3].strftime('%H:%M') if isinstance(row[3], (time, datetime)) else str(row[3])[:5]

                # 将seat_location转换为三位数的字符串格式
                seat_location_str = f"{int(row[5]):03d}"  # 确保转换为整数后再格式化

                appointment = {
                    "username": row[0],
                    "password": row[1],
                    "time": [start_time_str, end_time_str],
                    "roomid": str(row[4]),  # 假设room_location是整数类型
                    "seatid": [seat_location_str],  # 确保seatid是三位数的字符串格式
                    "daysofweek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    'is_auto_reservation': row[7]
                }
                appointments_data.append(appointment)
            return appointments_data
        except Exception as e:
            print(f"查询预约记录时发生错误：{e}")
            return []
        finally:
            self.close()
