import logging
import datetime
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from config import TIME_Check_TIME, TIME_MAX_ATTEMPT, TIME_SLEEP_TIME, TIME_START_TIME, TIME_END_TIME
from utils.Database_Function import DatabaseManager
from utils.Xxt_WebApi import XxTWebApi
from utils.General_Function import is_tomorrow, get_current_hour, \
    is_within_m_minutes, is_within_m_minutes_num, parse_time, is_within_time_range


class ReservationCheckService:
    def __init__(self):
        self.TIME_SLEEP_TIME        = TIME_SLEEP_TIME
        self.TIME_MAX_ATTEMPT      = TIME_MAX_ATTEMPT
        self.TIME_RESERVE_NEXT_DAY = True
        self.TIME_Check_TIME       = TIME_Check_TIME
        self.task_map              = {}
        # 配置日志的基本设置，设置日志级别为INFO，并定义日志的格式
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        # 设置为守护线程，这样主线程结束时子线程也会结束
        thread_rs = threading.Thread(target=self.location_serve_main)
        thread_rs.daemon = True
        # 启动学习通座位检查线程
        thread_rs.start()

    def sign(self, user):
        # 这里是单个用户登录并尝试预约的逻辑
        # 解包用户信息，包括用户名、密码、预约时间、房间ID、座位ID和预约星期
        username, password, times, roomid, seatid, daysofweek,is_auto_reservation = user.values()
        # 尝试预约
        logging.info(f"[Try_Sign] - {username} -- {times} -- {roomid} -- {seatid} ---- ")
        s = XxTWebApi(sleep_time=self.TIME_SLEEP_TIME, max_attempt=self.TIME_MAX_ATTEMPT, reserve_next_day=self.TIME_RESERVE_NEXT_DAY)
        s.get_login_status()
        s.login(username, password)
        s.requests.headers.update({'Host': 'office.chaoxing.com'})
        suc = s.submit_sign(username, times, roomid, seatid)
        return suc

    def signback(self, user):
        # 这里是单个用户登录并尝试预约的逻辑
        # 解包用户信息，包括用户名、密码、预约时间、房间ID、座位ID和预约星期
        username, password, times, roomid, seatid, daysofweek,is_auto_reservation = user.values()
        # 尝试预约
        logging.info(f"[Try_signback] - {username} -- {times} -- {roomid} -- {seatid} ---- ")
        s = XxTWebApi(sleep_time=self.TIME_SLEEP_TIME, max_attempt=self.TIME_MAX_ATTEMPT, reserve_next_day=self.TIME_RESERVE_NEXT_DAY)
        s.get_login_status()
        s.login(username, password)
        s.requests.headers.update({'Host': 'office.chaoxing.com'})
        suc = s.submit_signback(username, times, roomid, seatid)
        return suc



    def check(self, user):
        '''
            检查用户状态
        :param user:
        :return:
        '''
        # 这里是单个用户登录并尝试预约的逻辑
        # 解包用户信息，包括用户名、密码、预约时间、房间ID、座位ID和预约星期
        db = DatabaseManager()
        username, password, times, roomid, seatid, daysofweek,is_auto_reservation = user.values()
        # 尝试预约
        # logging.info(f" ---- [Try_Check] - {username}  ---- ")
        s = XxTWebApi(sleep_time=self.TIME_SLEEP_TIME, max_attempt=self.TIME_MAX_ATTEMPT, reserve_next_day=self.TIME_RESERVE_NEXT_DAY)
        s.get_login_status()
        out_login=s.login(username, password)
        # 密码错误
        if not out_login[0]:
            db.update_reservations_new_status(username, 8)
            return False

        s.requests.headers.update({'Host': 'office.chaoxing.com'})
        # 获取第一个信息
        Seat_info = s.get_seat_reservation_info(username)
        # print(Seat_info['status'])
        # 正常状态
        if Seat_info['type'] == -1:
            db.update_reservations_new_status(username, Seat_info['status'])
            # '0': '待履约',
            if Seat_info['status'] == 0:
                # 判断是否为今天
                if not is_tomorrow(Seat_info['startTime']):
                    # 如果在15min内
                    if is_within_m_minutes(int(time.time() * 1000), Seat_info['startTime'], 15):
                        logging.info(f"发现预约：{username}")
                        # 签到
                        self.sign(user)
                    else:
                        # 如果在30min后，为什么？因为服务器是中间时间段启动的
                        if is_within_m_minutes_num(int(time.time() * 1000), Seat_info['startTime'], 30):
                            #马上签到
                            self.sign(user)

            # '1': '学习中', 少于15分钟，自动退签
            if Seat_info['status'] == 1:
                # 如果在15min内
                if is_within_m_minutes(int(time.time() * 1000), Seat_info['endTime'], 15):
                    # 签到
                    logging.info(f"发现退签：{username}")
                    self.signback(user)

            # '5': '被监督中', 自动签到
            if Seat_info['status'] == 5:
                # 签到
                logging.info(f"发现监督：{username}")
                self.sign(user)

        # 违约，标注违约
        else:
            logging.error(f"呜呜呜呜呜,违约了！！！！")
            #更新数据库，-1表示违约了
            db.update_reservations_new_status(username, -1)
            return

    def run_periodically(self, interval):
        while True:
            if not is_within_time_range(TIME_START_TIME, TIME_END_TIME):
                logging.info("[Check] --------------------Reached end time.不更新.---------------------")
            else:
                logging.info(f"-----------------------------{get_current_hour()}--------------------------------")
                # 建立连接
                db = DatabaseManager()
                # 读取数据 获取用户信息
                users = db.fetch_check_information()
                # 修复bug
                if len(users) > 0:
                   with ThreadPoolExecutor(max_workers=len(users)) as executor:
                        futures = []
                        for index, user in enumerate(users):
                            # 将每个用户的登录和预约作为一个任务提交到线程池
                            futures.append(executor.submit(self.check, user))

            time.sleep(interval)

    def location_serve_main(self):
        # 设置结束时间为当天的22:05结束程序
        # 设置每5分钟（300秒）执行一次my_function函数，并传入参数
        self.run_periodically(self.TIME_Check_TIME)

if __name__ == '__main__':
    RS = ReservationCheckService()
    # 设置为守护线程，这样主线程结束时子线程也会结束
    thread = threading.Thread(target=RS.location_serve_main)
    thread.daemon = True
    # 启动学习通座位检查线程
    thread.start()