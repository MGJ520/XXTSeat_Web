from utils.Database_Function import DatabaseManager

# 测试插入预约记录成功的情况
platform_email = 'vxtb@qq.com'
reservation_account = '15795126651'
reservation_password = 'Y2002z11m17'
start_time = '09:00'
end_time = '10:00'
reservation_end_time = '2025-12-31 17:00:00'
room_location = '8685'
seat_location = '001'
account_status = 1
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

db_manager = DatabaseManager()
# 检查reservation_account是否已存在
if db_manager.check_reservation_account_exists(reservation_account):
    print( "Error: Reservation account already exists.")

# 检查时间重叠
if db_manager.check_time_overlap(room_location, seat_location, start_time, end_time):
    print("Error: Time overlap detected for the given room and seat.")

db_manager.insert_reservations(platform_email, reservation_account, reservation_password, start_time, end_time,
                               reservation_end_time, room_location, seat_location, account_status,
                               refresh_status,
                               reservation_status, sign_in_status, sign_back_status, monitor_sign_in_status,
                               reservation_times, sign_in_times, sign_back_times, monitor_sign_in_times,
                               operation_failure_times)

# from utils.Database_Function import DatabaseManager
#
# db_manager = DatabaseManager()
# db_manager.update_reservations_new_status('157951262651',2)
