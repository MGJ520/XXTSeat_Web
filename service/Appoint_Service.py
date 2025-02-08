import time
import logging

from concurrent.futures import ThreadPoolExecutor

from Program_configuration import SUB_SLEEP_TIME, SUB_MAX_ATTEMPT, RESERVE_NEXT_DAY
from utils.MySql_Function import AppointmentDB
from utils.Xxt_WebApi import XxTWebApi
from utils.General_Function import get_user_credentials

# 配置日志的基本设置，设置日志级别为INFO，并定义日志的格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 定义一个lambda函数，用于获取当前时间，如果action为True，则获取的是UTC+8时区的时间，否则获取本地时间
get_current_time = lambda action: time.strftime("%H:%M:%S", time.localtime(time.time() + 8*3600)) if action else time.strftime("%H:%M:%S", time.localtime(time.time()))
# 定义一个lambda函数，用于获取当前是星期几，如果action为True，则获取的是UTC+8时区的时间对应的星期，否则获取本地时间对应的星期
get_current_dayofweek = lambda action: time.strftime("%A", time.localtime(time.time() + 8*3600)) if action else time.strftime("%A", time.localtime(time.time()))

def login_and_reserve_single_user(user, username, password, action):
    # 这里是单个用户登录并尝试预约的逻辑
    # 解包用户信息，包括用户名、密码、预约时间、房间ID、座位ID和预约星期
    username, password, times, roomid, seatid, daysofweek,is_auto_reservation = user.values()
    # 如果自动预约关闭
    if is_auto_reservation==0:
        logging.info(f"[Try_NO] - {username} -- {times} -- {roomid} -- {seatid} ---- ")
        return

    # 如果当前星期不在用户设置的预约星期中，则跳过
    current_dayofweek = get_current_dayofweek(action)
    if current_dayofweek not in daysofweek:
        logging.error(f"[Time] -User {username} Today not set to reserve")
        return False
    # 尝试预约
    logging.info(f"[Try] - {username} -- {times} -- {roomid} -- {seatid} ---- ")
    s = XxTWebApi(sleep_time=SUB_SLEEP_TIME, max_attempt=SUB_MAX_ATTEMPT, reserve_next_day=RESERVE_NEXT_DAY)
    s.get_login_status()
    s.login(username, password)
    s.requests.headers.update({'Host': 'office.chaoxing.com'})
    s.max_attempt=1
    suc=s.submit_signback(username, times, roomid, seatid)
    print(f"退签: "+str(suc))
    s.max_attempt=SUB_MAX_ATTEMPT
    suc = s.submit(times, roomid, seatid, action,username)
    return suc


def main_parallel(action=False):
    db = AppointmentDB()


    # 转化数据
    users = db.fetch_appointments()
    # 数据类型如下
    # "username": row[0],
    # "password": row[1],
    # "time": [start_time_str, end_time_str],
    # "roomid": str(row[4]),  # 假设room_location是整数类型
    # "seatid": [seat_location_str],  # 确保seatid是三位数的字符串格式
    # "daysofweek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    # 'is_auto_reservation': row[6]


    usernames, passwords = None, None
    if action:
        usernames, passwords = get_user_credentials(action)

    # 使用ThreadPoolExecutor来并行化登录和预约过程
    with ThreadPoolExecutor(max_workers=len(users)) as executor:
        # 准备任务列表
        futures = []
        for index, user in enumerate(users):
            # 将每个用户的登录和预约作为一个任务提交到线程池
            futures.append(
                executor.submit(login_and_reserve_single_user, user, usernames.split(',')[index] if action else None,
                                passwords.split(',')[index] if action else None, action))

        # 等待所有任务完成，并收集结果
        success_list = [future.result() for future in futures]

    # 打印成功列表
    print(f"Success list: {success_list}")

# 当此脚本被直接运行时，以下代码块将被执行
if __name__ == "__main__":
    main_parallel()
