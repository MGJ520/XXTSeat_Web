import json
import requests
import re
import time
import logging
import datetime
from urllib3.exceptions import InsecureRequestWarning
from utils.General_Function import AES_Encrypt, enc


class XxTWebApi:
    def __init__(self, sleep_time=0.2, max_attempt=50, enable_slider=False, reserve_next_day=False):
        # 登录页面
        self.login_page = "https://passport2.chaoxing.com/mlogin?loginType=1&newversion=true&fid="
        # 座位页面
        self.url = "https://office.chaoxing.com/front/third/apps/seat/code?id={}&seatNum={}"
        # 签到
        self.sign_url = "https://office.chaoxing.com/data/apps/seat/sign"
        # 退座
        self.signback_url = "https://office.chaoxing.com/data/apps/seat/signback"
        # 取消
        self.cancel_url = "https://office.chaoxing.com/data/apps/seat/cancel"
        # 预约
        self.submit_url = "https://office.chaoxing.com/data/apps/seat/submit"
        # 座位
        self.seat_url = "https://office.chaoxing.com/data/apps/seat/getusedtimes"
        # 登录
        self.login_url = "https://passport2.chaoxing.com/fanyalogin"

        self.token = ""
        self.success_times = 0
        self.fail_dict = []
        self.submit_msg = []
        self.my_seat_id = []
        self.requests = requests.session()
        self.token_pattern = re.compile("token = '(.*?)'")
        self.headers = {
            "Referer": "https://office.chaoxing.com/",
            "Host": "captcha.chaoxing.com",
            "Pragma": 'no-cache',
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Linux"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }

        self.login_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.3 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1 wechatdevtools/1.05.2109131 MicroMessenger/8.0.5 Language/zh_CN webview/16364215743155638",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "passport2.chaoxing.com"
        }

        self.sleep_time = sleep_time
        self.max_attempt = max_attempt
        self.enable_slider = enable_slider
        self.reserve_next_day = reserve_next_day
        self.status = {
            '0': '待履约',
            '1': '学习中',
            '2': '已履约',
            '3': '暂离中',
            '5': '被监督中',
            '7': '已取消',
        }

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # login and page token
    def _get_page_token(self, url):
        response = self.requests.get(url=url, verify=False)
        html = response.content.decode('utf-8')
        token = re.findall(
            'token: \'(.*?)\'', html)[0] if len(re.findall('token: \'(.*?)\'', html)) > 0 else ""
        return token

    def get_login_status(self):
        self.requests.headers = self.login_headers
        self.requests.get(url=self.login_page, verify=False)

    def login(self, username, password):
        username_aes = AES_Encrypt(username)
        password_aes = AES_Encrypt(password)
        parm = {
            "fid": -1,
            "uname": username_aes,
            "password": password_aes,
            "refer": "http%3A%2F%2Foffice.chaoxing.com%2Ffront%2Fthird%2Fapps%2Fseat%2Fcode%3Fid%3D4219%26seatNum%3D380",
            "t": True
        }
        jsons = self.requests.post(
            url=self.login_url, params=parm, verify=False)
        obj = jsons.json()
        if obj['status']:
            # logging.info(f"[login] - User {username} login successfully")
            return (True, '')
        else:
            logging.error(f"[login] - User {username} login failed. Please check you password and username! ")
            return (False, obj['msg2'])

        # 时间戳转换1

    @classmethod
    def t_time(cls, timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(str(timestamp)[0:10])))

    # 获取到最近一次预约座位ID 默认的取消 签到 暂离都是默认这个 请自行发挥
    def get_my_seat_id(self):
        # 注意 老版本的系统需要将url中的seat改为seatengine
        response = self.requests.get(url='https://office.chaoxing.com/data/apps/seat/reservelist?'
                                         'indexId=0&'
                                         'pageSize=100&'
                                         'type=-1').json()['data']['reserveList']
        return response[0]['id']

    # 获全部预约记录
    def get_seat_reservation_info(self, username):
        # deptId: 部门ID，通常指代图书馆或机构的特定部门。
        # endTime: 结束时间，通常是一个时间戳，表示某个事件或预约的结束时间。
        # expireTime: 过期时间，通常是一个时间戳，表示某个预约或活动的有效期限。
        # firstLevelName: 第一级名称，可能是图书馆或机构的顶层分类名称。
        # id: 唯一标识符，用于标识该记录的唯一性。
        # inserttime: 插入时间，表示该记录被创建或插入数据库的时间戳。
        # learnDuration: 学习时长，可能表示学习或使用资源的持续时间（在这个例子中为0，可能表示尚未开始或未记录时长）。
        # pushFormUserId: 推送表单用户ID，可能指代推送某个表单或通知的用户ID。
        # rDeptId: 相关部门ID，可能表示与该记录相关的另一个部门ID。
        # roomId: 房间ID，表示特定房间的唯一标识符。
        # seatNum: 座位号，表示在图书馆或特定房间中的座位编号。
        # secondLevelName: 第二级名称，可能是图书馆或机构的次级分类名称。
        # startTime: 开始时间，通常是一个时间戳，表示某个事件或预约的开始时间。
        # status: 状态可能表示已预订等）。
        # thirdLevelName: 第三级名称，可能是图书馆或机构的更具体分类名称。
        # today: 日期，表示记录对应的日期。
        # type:  # 可能表示一个特定的类型
        # uid: 用户ID，表示与该记录相关的用户唯一标识符。
        # updatetime: 更新时间，表示该记录最后被更新的时间戳。

        # 注意 老版本的系统需要将url中的seat改为seatengine
        response = self.requests.get(url='https://office.chaoxing.com/data/apps/seat/reservelist?'
                                         'indexId=0&'
                                         'pageSize=100&'
                                         'type=-1').json()['data']['reserveList']
        index = response[0]

        # '0': '待履约',
        # '1': '学习中',
        # '2': '已履约',
        # '3': '暂离中',
        # '5': '被监督中',
        # '7': '已取消',
        if index['type'] == -1:
            if (index['status'] != 7 | index['status'] != 2):
                logging.info(f"[Get]--{username}--{index['firstLevelName']}--"
                             f"{index['secondLevelName']}--{index['thirdLevelName']}--{index['seatNum']}--"
                             f"{self.t_time(index['startTime'])}--{self.t_time(index['endTime'])}--"
                             f"{self.status[str(index['status'])]}")
        else:
            logging.info(f"[Get]--{username}--{index['firstLevelName']}--"
                         f"{index['secondLevelName']}--{index['thirdLevelName']}--{index['seatNum']}--"
                         f"{self.t_time(index['startTime'])}--{self.t_time(index['endTime'])}--违约")
        index1 = response[0]
        return index1

    # 签到
    def sign(self, username, times, roomid, seatid):
        self.my_seat_id = self.get_my_seat_id()
        # token = self._get_page_token(self.url.format(roomid, seatid))
        parm = {
            "id": self.my_seat_id
            # "token": token
        }
        html = self.requests.post(
            url=self.sign_url, params=parm, verify=True).content.decode('utf-8')
        logging.info(f"[Sign]-- {username} -- {times} -- {roomid} -- {seatid} -- {json.loads(html)} ---")
        return json.loads(html)["success"]

    # 退座
    def signback(self, username, times, roomid, seatid):
        self.my_seat_id = self.get_my_seat_id()
        # token = self._get_page_token(self.url.format(roomid, seatid))
        parm = {
            "id": self.my_seat_id
        }
        html = self.requests.post(url=self.signback_url, params=parm, verify=True).content.decode('utf-8')
        logging.info(f"[Signback]-- {username} -- {times} -- {roomid} -- {seatid} -- {json.loads(html)} ---")
        return json.loads(html)["success"]

    def cancel(self, username, times, roomid, seatid):
        self.my_seat_id = self.get_my_seat_id()
        parm = {
            "id": self.my_seat_id
        }
        html = self.requests.post(url=self.cancel_url, params=parm, verify=True).content.decode('utf-8')
        logging.info(f"[Cancel]-- {username} -- {times} -- {roomid} -- {seatid} -- {json.loads(html)} ---")
        return json.loads(html)["success"]

    def submit(self, times, roomid, seatid, action, username):
        for seat in seatid:
            suc = False
            while ~suc and self.max_attempt > 0:
                token = self._get_page_token(self.url.format(roomid, seat))
                suc = self.get_submit(self.submit_url, times=times, token=token, roomid=roomid, seatid=seat, captcha="",
                                      action=action, username=username)
                if suc:
                    return suc
                time.sleep(self.sleep_time)
                self.max_attempt -= 1
        return suc

    def submit_sign(self, username, times, roomid, seatid):
        suc = False
        while ~suc and self.max_attempt > 0:
            suc = self.sign(username=username, times=times, roomid=roomid, seatid=seatid)
            if suc:
                return suc
            time.sleep(self.sleep_time)
            self.max_attempt -= 1
        return suc

    def submit_signback(self, username, times, roomid, seatid):
        suc = False
        while ~suc and self.max_attempt > 0:
            suc = self.signback(username=username, times=times, roomid=roomid, seatid=seatid)
            if suc:
                return suc
            time.sleep(self.sleep_time)
            self.max_attempt -= 1
        return suc

    def submit_cancel(self, username, times, roomid, seatid):
        suc = False
        while ~suc and self.max_attempt > 0:
            suc = self.cancel(username=username, times=times, roomid=roomid, seatid=seatid)
            if suc:
                return suc
            time.sleep(self.sleep_time)
            self.max_attempt -= 1
        return suc

    def get_submit(self, url, times, token, roomid, seatid, username, captcha="", action=False):
        delta_day = 1 if self.reserve_next_day else 0
        day = datetime.date.today() + datetime.timedelta(days=0 + delta_day)  # 预约今天，修改days=1表示预约明天
        if action:
            day = datetime.date.today() + datetime.timedelta(days=1 + delta_day)  # 由于action时区问题导致其早+8区一天
        parm = {
            "roomId": roomid,
            "startTime": times[0],
            "endTime": times[1],
            "day": str(day),
            "seatNum": seatid,
            "captcha": captcha,
            "token": token
        }
        # logging.info(f"submit parameter {parm} ")
        parm["enc"] = enc(parm)
        html = self.requests.post(
            url=url, params=parm, verify=True).content.decode('utf-8')
        self.submit_msg.append(
            times[0] + "~" + times[1] + ':  ' + str(json.loads(html)))

        # logging.info(str(username)+' --- ' +str(json.loads(html)))
        logging.info(f"[Get]-- {username} -- {times} -- {roomid} -- {seatid} -- {json.loads(html)} ---")
        return json.loads(html)["success"]
