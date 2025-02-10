import os
from collections import deque

import jwt
from datetime import timedelta, timezone
from utils.Xxt_WebApi import XxTWebApi
from utils.Database_Function import DatabaseManager
from Program_configuration import Room_data, status, WEB_EXPIRATION_DATE, WEB_SERVER_PORT, HIGN_MAX_REQUESTS, \
    HIGN_REQUEST_TIME_WINDOW, LOW_REQUEST_TIME_WINDOW, LOW_MAX_REQUESTS, HIGN_LONG_MAX_REQUESTS, \
    HIGN_LONG_REQUEST_TIME_WINDOW
from service.Reservation_Service import ReservationCheckService
from utils.General_Function import timedelta_to_time_str, get_local_ip
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session, \
    make_response
from functools import wraps
from flask_cors import CORS
from datetime import datetime, timedelta

# ------------------------------------初始化-----------------------------------------------
# 初始化Flask应用
app = Flask(__name__)

# 配置静态文件位置
app.config['STATIC_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# 用于JWT签名的密钥
app.config['SECRET_KEY'] = 'your_secret_key'

# 允许所有来源访问
CORS(app)

# ---------------------------------------------JWT配置-----------------------------------------------
# 使用Flask的SECRET_KEY作为JWT签名密钥
JWT_SECRET_KEY = app.config['SECRET_KEY']

# 使用HS256算法
JWT_ALGORITHM = 'HS256'

# JWT过期时间
JWT_EXPIRATION_DELTA = timedelta(hours=WEB_EXPIRATION_DATE)


# 模拟用户数据库，纯一维数组
users = {}

# 存储每个服务的IP地址和请求时间的字典
service_request_counts = {}


def rate_limit_ip(service_name, max_requests, time_window):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = datetime.now()

            # 初始化服务的数据结构
            if service_name not in service_request_counts:
                service_request_counts[service_name] = {}

            if client_ip not in service_request_counts[service_name]:
                service_request_counts[service_name][client_ip] = deque()

            # 清理过期的请求记录
            timestamps = service_request_counts[service_name][client_ip]
            while timestamps and current_time - timestamps[0] > time_window:
                timestamps.popleft()

            # 检查当前IP的请求次数
            if len(timestamps) >= max_requests:
                return jsonify({"error": "Please slow down,(,,Ծ‸Ծ,, )"}), 429

            # 添加当前请求的时间戳
            timestamps.append(current_time)

            return f(*args, **kwargs)

        return wrapped

    return decorator


# 创建JWT
def create_jwt(user_name, user_email):
    """
    创建JWT令牌。
    :param user_name:
    :param user_email: 用户的电子邮件地址，作为用户标识。
    :return: JWT令牌。
    """
    payload = {
        'user_email': user_email,
        'user_name': user_name,
        'exp': datetime.now(timezone.utc) + JWT_EXPIRATION_DELTA  # 使用时区感知的UTC时间
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


# 验证JWT
def verify_jwt(token):
    """
    验证JWT令牌。
    :param token: JWT令牌。
    :return: 如果验证成功，返回用户电子邮件地址；否则返回None。
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload['user_email']
    except jwt.ExpiredSignatureError:
        # 令牌已过期
        return None
    except jwt.InvalidTokenError:
        # 无效的令牌
        return None


@app.route('/control-panel', methods=['GET', 'POST'])
def control_panel():
    """
    主页路由。
    如果用户已登录（即请求头中包含有效的JWT），渲染主页模板。
    否则，重定向到登录页面。
    """
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            return render_template('index.html')  # 验证成功，渲染主页模板
    return redirect(url_for('login'))


# 根页面
@app.route('/', methods=['GET', 'POST'])
@rate_limit_ip("/",LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def index():
    """
    根页面路由。
    """
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            return redirect(url_for('home'))  # 验证成功，渲染主页模板
    return redirect(url_for('login'))


# 主页
@app.route('/home', methods=['GET', 'POST'])
@rate_limit_ip('/home',LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def home():
    """
    主页路由。
    如果用户已登录（即请求头中包含有效的JWT），渲染主页模板。
    否则，重定向到登录页面。
    """
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            return render_template('home.html')  # 验证成功，渲染主页模板
    return redirect(url_for('login'))


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
@rate_limit_ip('/login',LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def login():
    """
    登录页面路由。
    如果用户已登录（即请求头中包含有效的JWT），重定向到主页。
    否则，渲染登录页面模板。
    """
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            return redirect(url_for('home'))  # 验证成功，重定向到主页
    return render_template('login.html')  # 验证失败，渲染登录页面模板


# 登录接口
@app.route('/api/login', methods=['POST'])
@rate_limit_ip('/api/login', HIGN_MAX_REQUESTS, HIGN_REQUEST_TIME_WINDOW)
def api_login():
    """
    登录接口。
    验证用户提供的电子邮件和密码。
    如果验证成功，返回包含JWT的响应。
    如果验证失败，返回错误信息。
    """
    data = request.json
    email_local = data.get('email_login_local')
    password_local = data.get('password_login_local')
    db_manager = DatabaseManager()
    if db_manager.login_user(
            platform_email=email_local ,
            platform_password=password_local,
            user_ip=request.remote_addr
        ):
        # 用户验证成功，创建JWT
        token = create_jwt(email_local , email_local)
        response = make_response(jsonify({'success': True}))
        response.set_cookie('auth_token', token, httponly=True, samesite='Lax', path='/')
        return response
    else:
        # 用户验证失败，返回错误信息
        return jsonify({'success': False, 'error': 'Invalid username or password'})


# 注册接口
@app.route('/api/register', methods=['POST'])
@rate_limit_ip('/api/register',HIGN_LONG_MAX_REQUESTS, HIGN_LONG_REQUEST_TIME_WINDOW)
def api_register():
    """
    注册接口。
    注册新用户。
    如果用户已存在，返回错误信息。
    如果注册成功，返回成功信息。
    """
    data = request.json
    username_local = data.get('username_register_local')
    email_local = data.get('email_register_local')
    password_local = data.get('password_register_local')
    if email_local and username_local and password_local:
        # 注册新用户，存储密码哈希值
        db_manager = DatabaseManager()
        # 注册新用户
        register_result = db_manager.register_user(
            platform_email=email_local,
            platform_nickname=username_local,
            platform_password=password_local,
            user_ip=request.remote_addr
        )
        return register_result

    else:
        # 返回错误信息
        return jsonify({'success': False, 'error': 'Please input data'})


# 注销接口
@app.route('/api/logout', methods=['GET'])
@rate_limit_ip('/api/logout', LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def api_logout():
    response = make_response(jsonify({'success': True}))
    response.set_cookie('auth_token', '', expires=0)
    return response


@app.route('/api/get/room_data', methods=['GET'])
@rate_limit_ip('/api/get/room_data',LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def api_get_room_data():
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            return jsonify(Room_data)
    return jsonify({'success': False, 'error': 'Please login'})


@app.route('/api/get/seats_data', methods=['GET'])
@rate_limit_ip('/api/get/seats_data',LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def api_get_seats_data_ajax():
    # 调用之前定义的 get_seats_data 函数来获取数据
    seats_data = get_seats_data()
    return jsonify(seats_data)


# ------------------------------------上传数据-----------------------------------------------


@app.route('/api/set/reservation', methods=['POST'])
@rate_limit_ip('/api/set/reservation',HIGN_MAX_REQUESTS, HIGN_REQUEST_TIME_WINDOW)
def api_set_reservation():
    db = DatabaseManager()
    # 尝试从JSON请求体中获取数据
    try:
        data = request.json
        username = data['username']
        password = data['password']
        timeSlot = data['timeslot']
        endTime  = data['endtime']
        room     = data['roomid']
        seat     = data['seat']
        status   = data['status']  # 注意：这是前端新添加的字段
    except KeyError as e:
        # 如果JSON数据不完整，返回错误信息
        return jsonify({'success': False, 'message': f'Missing field: {e.args[0]}'}), 400

    try:
        # 假设'2025-01-10 12:00'是预约的日期和时间，最后一个参数是预约状态，这里假设为1表示已预约
        # 注意：这里的db.insert_appointment函数需要你根据实际数据库操作进行实现
        # if db.check_account_exists(username):
        #     db.update_reservation(username, password, timeSlot, endTime, '2025-01-10 12:00', room, seat, 9, True, True)
        # # 这里应该有一个逻辑来处理预约，例如保存到数据库
        # else:
        #     db.insert_appointment(username, password, timeSlot, endTime, '2025-01-10 12:00', room, seat, 9, True, True)
        # 预约成功，返回成功信息
        return jsonify({'success': True, 'message': 'Reservation successful'}), 200

    except Exception as e:
        # 如果在保存预约时发生错误，返回错误信息
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/delete/appointment', methods=['DELETE'])
@rate_limit_ip('/api/delete/appointment',HIGN_MAX_REQUESTS, HIGN_REQUEST_TIME_WINDOW)
def api_delete_seat():
    db = DatabaseManager()
    # 从请求中获取数据
    data = request.json
    account = data.get('account')

    # 记录日志
    print(f"Attempting to delete appointment for account: {account}")

    # 检查数据库是否存在该账号的预约
    appointments = db.read_reservations()
    account_exists = any(appointment[0] == account for appointment in appointments)

    if not account_exists:
        # 如果不存在，返回操作结果
        return jsonify({'success': False, 'message': "没有找到该账号的预约"})

    # 如果存在，在数据库中删除该账号的预约
    db.delete_reservation_by_account(account)
    # 返回操作结果
    return jsonify({'success': True})


@app.route('/api/set/auto_reservation', methods=['POST'])
@rate_limit_ip('/api/set/auto_reservation', HIGN_MAX_REQUESTS, HIGN_REQUEST_TIME_WINDOW)
def api_set_auto_reservation():
    """
    启用或关闭用户的自动预约功能

    接收前端POST请求，包含:
    - account: 用户账号
    - data: 是否启用自动预约的布尔值

    Returns:
        JSON响应，包含:
        - success: 操作是否成功
        - message: 操作结果消息
        - end: 是否启用标志
    """
    try:
        db = DatabaseManager()
        data = request.json
        account = data.get('account')
        auto_reservation = data.get('data')

        # 更新数据库中的自动预约状态
        db.update_auto_reservation(account, auto_reservation)

        # 根据操作返回相应消息
        if auto_reservation:
            return jsonify(success=True, message=f'{account}自动预约启用成功', end=True)
        else:
            return jsonify(success=True, message=f'{account}自动预约已关闭', end=False)

    except Exception as e:
        return jsonify(success=False, message=f'操作失败: {str(e)}', end=False)


@app.route('/api/set/cancel_seat', methods=['POST'])
@rate_limit_ip('/api/set/cancel_seat',HIGN_MAX_REQUESTS, HIGN_REQUEST_TIME_WINDOW)
def api_set_cancel_seat():
    db = DatabaseManager()
    data = request.json
    account = data.get('account')
    # 这里添加退座的逻辑
    # print("退座")

    appointments = db.read_reservations(account)

    # 检查appointments是否为空
    if not appointments:
        return jsonify(success=False, message='没有预约数据')

    for item in appointments:
        account, password, start_time, end_time, reservation_end_time, room_location, seat_location, current_status, is_auto_reservation, is_auto_checkin = item
        #     '-1': '违约',
        #     '0': '待履约',
        #     '1': '学习中',
        #     '2': '已履约',
        #     '3': '暂离中',
        #     '5': '被监督中',
        #     '7': '已取消',
        #     '8': '密码错误',
        #     '9': '等待更新'
        # 检查current_status是否为允许退座的状态
        if current_status in [0, 1, 3, 5]:
            # 登录
            s = XxTWebApi(sleep_time=1, max_attempt=1, reserve_next_day=False)
            s.get_login_status()
            s.login(account, password)
            s.requests.headers.update({'Host': 'office.chaoxing.com'})
            if current_status in [0]:
                suc = s.submit_cancel(account, 'time', room_location, seat_location)
            else:
                suc = s.submit_signback(account, 'time', room_location, seat_location)
            # 判断
            if not suc:
                return jsonify(success=False, message='退座失败')
        else:
            db.update_reservations_new_status(account, 2)
            return jsonify(success=False, message='退座失败,当前不可以退座')

        # 如果所有允许退座的预约都成功退座，则返回成功消息
    return jsonify(success=True, message='退座成功')


# 提供静态网页文件
@app.route('/<path:filename>', methods=['GET', 'POST'])
@rate_limit_ip('/filename',LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def static_files(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)


# ----------------------------------------数据库获取数据-------------------------------------------------
def get_seats_data():
    """
    从数据库获取所有座位预约信息并处理成前端所需的格式

    Returns:
        list: 包含所有预约信息的列表，每个预约为一个字典，包含:
            - account: 账号
            - password: 密码
            - time_period: 预约时间段
            - roomid: 房间ID
            - seat: 座位号
            - status: 预约状态文本
            - is_auto_reservation: 是否自动预约
            - is_auto_checkin: 是否自动签到
    """
    db = DatabaseManager()

    appointments = db.read_reservations()

    # 检查appointments是否为空
    if not appointments:
        print("未查询到任何预约数据")
        return []

    # Process the data
    processed_data = []
    for appointment in appointments:
        # 解构预约数据
        (
            account,
            password,
            start_time,
            end_time,
            reservation_end_time,
            room_location,
            seat_location,
            current_status,
            is_auto_reservation,
            is_auto_checkin
        ) = appointment

        # 格式化时间段字符串
        time_period = f"{timedelta_to_time_str(start_time)}-{timedelta_to_time_str(end_time)}"
        seat = f"{seat_location}"

        # 根据数字状态码获取对应的文本状态
        status_text = status.get(str(current_status), "未知状态")
        processed_data.append({
            'account': account,
            'password': password,
            'time_period': time_period,
            'roomid': room_location,
            'seat': seat,
            'status': status_text,
            'is_auto_reservation': is_auto_reservation,
            'is_auto_checkin': is_auto_checkin
        })
    return processed_data





def web_service():
    local_ip = get_local_ip()
    if local_ip:
        print(f"本机内网IP地址: {local_ip}")
        # 使用获取到的IP地址启动Flask应用
        app.run(host=local_ip, port=WEB_SERVER_PORT, debug=False)
    else:
        print("无法获取本机内网IP地址。")
        # 如果无法获取IP地址，不传递 host 参数，使用默认的 localhost 启动
        app.run(port=WEB_SERVER_PORT, debug=False)




# ------------------------------主函数--------------------------------------------------
if __name__ == '__main__':

    # 数据库初始化
    DatabaseManager()

    # 检查服务
    ReservationCheckService()

    # Web服务
    web_service()

