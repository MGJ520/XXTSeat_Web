from flask import request, make_response, jsonify

from config import Room_data
from utils.Database_Function import DatabaseManager
from utils.Jwt_Function import create_jwt, verify_jwt
from . import user


# 登录接口
@user.route('/api/login', methods=['POST'])
# @rate_limit_ip('/api/login', HIGN_MAX_REQUESTS, HIGN_REQUEST_TIME_WINDOW)
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
            platform_email=email_local,
            platform_password=password_local,
            user_ip=request.remote_addr
    ):
        # 用户验证成功，创建JWT
        token = create_jwt(email_local, email_local)
        response = make_response(jsonify({'success': True}))
        response.set_cookie('auth_token', token, httponly=True, samesite='Lax', path='/')
        return response
    else:
        # 用户验证失败，返回错误信息
        return jsonify({'success': False, 'error': 'Invalid username or password'})


# 注册接口
@user.route('/api/register', methods=['POST'])
# @rate_limit_ip('/api/register', HIGN_LONG_MAX_REQUESTS, HIGN_LONG_REQUEST_TIME_WINDOW)
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
@user.route('/api/logout', methods=['GET'])
# @rate_limit_ip('/api/logout', LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def api_logout():
    response = make_response(jsonify({'success': True}))
    response.set_cookie('auth_token', '', expires=0)
    return response


@user.route('/api/update/profile', methods=['POST'])
def update_profile():
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            data = request.json
            new_nickname = data.get('nickname')
            new_password = data.get('password')
            print(new_nickname, new_password)
            if not new_nickname or not new_password:
                return jsonify({'success': False, 'error': 'Missing data'}), 400
            else:
                db = DatabaseManager()
                if db.update_user_profile(user_email, new_nickname, new_password):
                    return jsonify({'success': True, 'message': 'Profile updated successfully'}), 200
                else:
                    return jsonify({'success': False, 'error': 'Missing data'}), 400
    return jsonify({'success': False, 'error': 'Please login'})


@user.route('/api/get/user_data', methods=['GET'])
# @rate_limit_ip('/api/get/user_data', LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def api_get_user_data():
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            db = DatabaseManager()
            user_data = db.fetch_user_information(user_email)
            if user_data is None:
                return jsonify({'error': "User is none"}), 500
            else:
                return jsonify(user_data)
    return jsonify({'success': False, 'error': 'Please login'})


@user.route('/api/get/room_data', methods=['GET'])
# @rate_limit_ip('/api/get/room_data', LOW_MAX_REQUESTS, LOW_REQUEST_TIME_WINDOW)
def api_get_room_data():
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            return jsonify(Room_data)
    return jsonify({'success': False, 'error': 'Please login'})


@user.route('/api/new_reservation', methods=['POST'])
def new_reservation():
    token = request.cookies.get('auth_token')  # 从Cookie中获取JWT
    if token:
        user_email = verify_jwt(token)  # 验证JWT
        if user_email:
            db_manager = DatabaseManager()
            # 尝试从JSON请求体中获取数据
            try:
                data = request.json
            except Exception as e:
                # 如果JSON数据不完整或解析失败，返回错误信息
                return jsonify({'success': False, 'message': f'Invalid JSON data: {str(e)}'}), 400

            # 解析前端发送的数据
            try:
                reservation_account = data.get('reservation_account')
                reservation_password = data.get('reservation_password')
                start_time = data.get('start_time')
                end_time = data.get('end_time')
                room_id = data.get('room_id')
                seat_id = str(data.get('seat_id')).zfill(3)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Missing or invalid field: {str(e)}'}), 400

            # 数据检查
            if not reservation_account:
                return jsonify({'success': False, 'message': 'Reservation account is required'}), 400
            if not reservation_password:
                return jsonify({'success': False, 'message': 'Reservation password is required'}), 400
            if not start_time:
                return jsonify({'success': False, 'message': 'Start time is required'}), 400
            if not end_time:
                return jsonify({'success': False, 'message': 'End time is required'}), 400
            if not room_id:
                return jsonify({'success': False, 'message': 'Room ID is required'}), 400
            if not seat_id:
                return jsonify({'success': False, 'message': 'Seat ID is required'}), 400

            try:
                # 检查预约账号是否已存在
                if db_manager.check_reservation_account_exists(reservation_account):
                    return jsonify({'success': False, 'message': 'Reservation account already exists'}), 400

                # 检查时间是否重叠
                if db_manager.check_time_overlap(room_id, seat_id, start_time, end_time):
                    return jsonify(
                        {'success': False, 'message': 'Time overlap detected for the given room and seat'}), 400

                reservation_end_time = '2025-12-31 17:00:00'

                account_status = 0
                refresh_status = True
                reservation_status = True
                sign_in_status = True
                sign_back_status = True
                monitor_sign_in_status = True
                reservation_times = 10
                sign_in_times = 10
                sign_back_times = 10
                monitor_sign_in_times = 10
                operation_failure_times = 0

                db_manager.insert_reservations(user_email, reservation_account, reservation_password, start_time,
                                               end_time,
                                               reservation_end_time, room_id, seat_id, account_status,
                                               refresh_status,
                                               reservation_status, sign_in_status, sign_back_status,
                                               monitor_sign_in_status,
                                               reservation_times, sign_in_times, sign_back_times, monitor_sign_in_times,
                                               operation_failure_times)
                return jsonify({'success': True, 'message': 'Reservation successful'}), 200

            except Exception as e:
                # 如果在保存预约时发生错误，返回错误信息
                return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': False, 'error': 'Please login'})


@user.route('/api/get/reservation', methods=['GET'])
def get_reservation():
    token = request.cookies.get('auth_token')
    if token:
        user_email = verify_jwt(token)
        if user_email:
            db_manager = DatabaseManager()
            data = db_manager.fetch_check_information(user_email)
            return jsonify({"success": True, "data": data})
    return jsonify({'success': False, 'error': 'Please login'})


@user.route('/api/delete/reservation', methods=['DELETE'])
def delete_seat():
    token = request.cookies.get('auth_token')
    if token:
        user_email = verify_jwt(token)
        if user_email:
            db_manager = DatabaseManager()

            # 从请求中获取数据
            data = request.json
            account = data.get('account')

            # 记录日志
            print(f"Attempting to delete appointment for account: {account}")

            # 检查数据库是否存在该账号的预约
            account_exists = db_manager.delete_reservation_account(user_email,account)

            if not account_exists:
                # 如果不存在，返回操作结果
                return jsonify({'success': False, 'message': "没有找到该账号的预约"})
            # 返回操作结果
            return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Please login'})