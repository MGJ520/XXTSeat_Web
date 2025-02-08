import os
import threading
from utils.Xxt_WebApi import XxTWebApi
from utils.MySql_Function import AppointmentDB
from Program_configuration import Room_data, status
from service.Reservation_Service import ReservationService
from utils.General_Function import timedelta_to_time_str, get_local_ip
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# ------------------------------------初始化-----------------------------------------------
# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 允许所有来源访问
# 配置静态文件位置
app.config['STATIC_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
# 初始化预约服务
RS = ReservationService()




# 处理下载请求
# ------------------------------------分发数据-----------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')


@app.route('/get-room-data', methods=['GET'])
def get_room_data():
    return jsonify(Room_data)


@app.route('/get-seats-data', methods=['GET'])
def get_seats_data_ajax():
    # 调用之前定义的 get_seats_data 函数来获取数据
    seats_data = get_seats_data()
    return jsonify(seats_data)

#TODO 登录注销页面请求

# 提供静态网页文件
@app.route('/<path:filename>', methods=['GET', 'POST'])
def static_files(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

# ------------------------------------上传数据-----------------------------------------------
#TODO 登录处理函数

# @app.route('/')
# def login():



#TODO 注销处理函数




@app.route('/contact', methods=['POST'])
def contact():
    db = AppointmentDB()
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
        if db.check_account_exists(username):
            db.update_appointment(username, password, timeSlot, endTime, '2025-01-10 12:00', room, seat, 9, True, True)
        # 这里应该有一个逻辑来处理预约，例如保存到数据库
        else:
            db.insert_appointment(username, password, timeSlot, endTime, '2025-01-10 12:00', room, seat, 9, True, True)
        # 预约成功，返回成功信息
        return jsonify({'success': True, 'message': 'Reservation successful'}), 200

    except Exception as e:
        # 如果在保存预约时发生错误，返回错误信息
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/delete-appointment', methods=['DELETE'])
def delete_seat():
    db = AppointmentDB()
    # 从请求中获取数据
    data = request.json
    account = data.get('account')

    # 记录日志
    print(f"Attempting to delete appointment for account: {account}")

    # 检查数据库是否存在该账号的预约
    appointments = db.query_appointments()
    account_exists = any(appointment[0] == account for appointment in appointments)

    if not account_exists:
        # 如果不存在，返回操作结果
        return jsonify({'success': False, 'message': "没有找到该账号的预约"})

    # 如果存在，在数据库中删除该账号的预约
    db.delete_appointment(account)
    # 返回操作结果
    return jsonify({'success': True})


@app.route('/enable-auto-reservation', methods=['POST'])
def enable_auto_reservation():
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
        db = AppointmentDB()
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


@app.route('/cancel-seat', methods=['POST'])
def cancel_seat():
    db = AppointmentDB()
    data = request.json
    account = data.get('account')
    # 这里添加退座的逻辑
    # print("退座")

    appointments = db.query_appointments_by_account(account)

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
        if current_status in [0 , 1, 3, 5]:
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
            db.update_appointment_new_status(account, 2)
            return jsonify(success=False, message='退座失败,当前不可以退座')

        # 如果所有允许退座的预约都成功退座，则返回成功消息
    return jsonify(success=True, message='退座成功')


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
    db = AppointmentDB()

    appointments = db.query_appointments()

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
        seat        = f"{seat_location}"

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

# ------------------------------主函数--------------------------------------------------
if __name__ == '__main__':
    #数据库初始化
    AppointmentDB()

    # 设置为守护线程，这样主线程结束时子线程也会结束
    thread = threading.Thread(target=RS.location_serve_main)
    thread.daemon = True

    #启动学习通座位检查线程
    thread.start()

    #获取ip
    local_ip = get_local_ip()

    if local_ip:
        print(f"本机内网IP地址: {local_ip}")
        # 使用获取到的IP地址启动Flask应用
        app.run(host=local_ip, port=8088, debug=False)
    else:
        print("无法获取本机内网IP地址。")
        # 如果无法获取IP地址，不传递 host 参数，使用默认的 localhost 启动
        app.run(port=8088, debug=True)
