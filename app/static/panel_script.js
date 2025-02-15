// 初始化函数
init_all();


function init_all() {

    document.getElementById("myModal").addEventListener('onclick', function () {
        this.style.display = "none";
    });

    document.getElementById("add_button").onclick = function () {
        document.getElementById("myModal").style.display = "block";
        // 示例：高亮显示从 09:00 到 11:30 的时间段
        // highlightTimeRange("09:00", "11:30");
    };

    document.getElementsByClassName("close")[0].onclick = function () {
        document.getElementById("myModal").style.display = "none";
    };


    // 生成时间段
    for (let hour = startTime; hour < endTime; hour++) {
        for (let minute = 0; minute < 60; minute += 30) {
            const start = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
            const endHour = hour + (minute === 30 ? 1 : 0);
            const endMinute = minute === 30 ? 0 : 30;
            const end = `${String(endHour).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`;
            timeSlots.push({start, end});
        }
    }

    timeSlots.forEach((slot, index) => {
        const slotDiv = document.createElement('div');
        slotDiv.classList.add('time-slot');
        slotDiv.textContent = `${slot.start} - ${slot.end}`;
        slotDiv.addEventListener('click', () => selectTimeSlot(index));
        document.getElementById('time-slots').appendChild(slotDiv);
    });


    fetchReservations().then(r => {
        const room_select = document.getElementById('room_select');
        roomData.forEach(room => {
            const option = document.createElement('option');
            option.value = room[2];
            option.textContent = room[2];
            room_select.appendChild(option);
        });
    });


}


// 选择时间段

function selectTimeSlot(index) {
    if (firstSelectedIndex === null) {
        // 第一次选择，记录第一个选中的时间点
        firstSelectedIndex = index;
        selectedSlots = [index]; // 正式选中第一个时间点
        highlightMaxDuration(index); // 高亮显示最长时间范围
    } else {
        // 第二次选择，判断是否是同一个时间点
        if (firstSelectedIndex === index) {
            // 如果是同一个时间点，直接确认选择这个时间段
            firstSelectedIndex = null; // 重置第一个选中的时间点
            highlightedSlots = []; // 清空高亮状态

            // 获取选择的开始时间和结束时间
            const selectedStart = timeSlots[index].start;
            const selectedEnd = timeSlots[index].end;

            // 打印或记录选择的开始时间和结束时间
            console.log(`选择的开始时间: ${selectedStart}`);
            console.log(`选择的结束时间: ${selectedEnd}`);

            // 可以将开始时间和结束时间存储到全局变量中
            const selectedTimeRange = {
                start: selectedStart,
                end: selectedEnd
            };

            console.log(`选择的时间范围: ${JSON.stringify(selectedTimeRange)}`);
        } else {
            // 不是同一个时间点，根据两个时间点确定正式选中的范围
            const start = Math.min(firstSelectedIndex, index);
            const end = Math.max(firstSelectedIndex, index);

            // 计算选择的时长是否超过最大时长限制
            const duration = (end - start) / 2 + 0.5; // 每个时间槽代表半小时
            if (duration > maxDuration) {
                // alert(`选择的时长不能超过${maxDuration}小时，请重新选择！`);
                // 取消选择
                firstSelectedIndex = null;
                selectedSlots = [];
                highlightedSlots = [];
                selectTimeSlot(index);
            } else {
                selectedSlots = []; // 清空之前的正式选中状态
                for (let i = start; i <= end; i++) {
                    selectedSlots.push(i);
                }
                firstSelectedIndex = null; // 重置第一个选中的时间点
                highlightedSlots = []; // 清空高亮状态

                // 获取选择的开始时间和结束时间
                selectedStart = timeSlots[start].start;
                selectedEnd = timeSlots[end].end;

                console.log(`选择的时间范围: ${JSON.stringify(selectedTimeRange)}`);
            }
        }
    }

    // 更新UI
    updateTimeSlotsUI();
}

// 高亮显示最长时间范围
function highlightMaxDuration(startIndex) {
    highlightedSlots = [];
    const maxSlots = maxDuration * 2; // 最长选择时长对应的槽位数
    for (let i = 0; i < maxSlots; i++) {
        const nextIndex = startIndex + i;
        if (nextIndex < timeSlots.length) {
            highlightedSlots.push(nextIndex);
        } else {
            break; // 防止超出时间槽范围
        }
    }
}

// 更新时间槽的UI
function updateTimeSlotsUI() {
    const slots = document.querySelectorAll('.time-slot');
    slots.forEach((slot, index) => {
        if (selectedSlots.includes(index)) {
            slot.classList.add('selected');
            slot.classList.remove('highlight');
        } else if (highlightedSlots.includes(index)) {
            slot.classList.add('highlight');
            slot.classList.remove('selected');
        } else {
            slot.classList.remove('selected', 'highlight');
        }
    });
}

// 清空选择
function clearSelection() {
    firstSelectedIndex = null;
    selectedSlots = [];
    highlightedSlots = [];
    updateTimeSlotsUI();
}

// 高亮显示指定的时间范围
function highlightTimeRange(start, end) {
    clearSelection(); // 清空当前选择和高亮
    const startSlot = timeSlots.findIndex(slot => slot.start === start);
    const endSlot = timeSlots.findIndex(slot => slot.end === end);

    if (startSlot !== -1 && endSlot !== -1) {
        const startIdx = Math.min(startSlot, endSlot);
        const endIdx = Math.max(startSlot, endSlot);
        for (let i = startIdx; i <= endIdx; i++) {
            selectedSlots.push(i);
        }
        // 获取选择的开始时间和结束时间
        selectedStart = timeSlots[startIdx].start;
        selectedEnd = timeSlots[endIdx].end;
        updateTimeSlotsUI();
    } else {
        console.error("输入的时间范围无效");
    }
}


// 根据选定的房间更新座位选项的函数
function updateSeats(selectedRoomName) {
    var seatsSelect = document.getElementById('seat_show_num');
    seatsSelect.innerHTML = ''; // 清空当前座位选项

    // 在全局变量 roomData 中查找对应的房间数据
    var roomInfo = roomData.find(room => room[2] === selectedRoomName);
    if (roomInfo) {
        // 假设第一个元素是座位数量，第二个元素是房间ID，第三个元素是房间名称
        var seatCount = roomInfo[0]; // 座位数量
        var roomId = roomInfo[1]; // 房间ID

        // 根据座位数量生成座位数组
        var availableSeats = Array.from({length: seatCount}, (_, i) => i + 1);

        // 为每个座位创建一个选项
        availableSeats.forEach(function (seat) {
            var option = document.createElement('option');
            option.value = seat; // 座位编号
            option.textContent = `座位${seat}`; // 座位显示文本
            seatsSelect.appendChild(option);
        });
        // 在找到房间信息后，设置隐藏字段的值为房间ID
        var roomIdInput = document.getElementById('roomId');
        if (roomInfo) {
            roomIdInput.value = roomInfo[1]; // roomInfo[1] 是房间ID
        }
    } else {
        console.error('Room info not found for:', selectedRoomName);
    }
}


// 添加数据处理函数
function SyncData() {
    const reservation_account = document.getElementById('reservation_account').value;
    const reservation_password = document.getElementById('reservation_password').value;
    const start_time = selectedStart;
    const end_time = selectedEnd; // 获取结束时间
    const room = document.getElementById('room_select').value;
    const seat = document.getElementById('seat_show_num').value;

    // 验证用户名是否为11位数字的手机号码
    if (!/^\d{11}$/.test(reservation_account)) {
        alert('请输入11位数字的手机号码！');
        return;
    }

    // 检查每个字段是否为空
    if (!reservation_account) {
        console.error("账号不能为空！");
        alert("账号不能为空！");
        return;
    } else if (!reservation_password) {
        console.error("密码不能为空！");
        alert("密码不能为空！");
        return;
    } else if (!start_time) {
        console.error("开始时间不能为空！");
        alert("开始时间不能为空！");
        return;
    } else if (!end_time) {
        console.error("结束时间不能为空！");
        alert("结束时间不能为空！");
        return;
    } else if (!room) {
        console.error("房间选择不能为空！");
        alert("房间选择不能为空！");
        return;
    } else if (!seat) {
        console.error("座位选择不能为空！");
        alert("座位选择不能为空！");
        return;
    }


    const room_info = roomData.find(room1 => room1[2] === room);
    if (!room_info) {
        console.error('No room found for room_id:', room);
    }
    const room_name = room_info ? room : '未知房间';
    const room_id = room_info ? room_info[1] : '未知ID';

    // 创建要发送到服务器的数据对象
    const data = {
        reservation_account: reservation_account,
        reservation_password: reservation_password,
        start_time: start_time,
        end_time: end_time,
        room_id: room_id,
        seat_id: seat
    };

    // 发送POST请求到服务器
    fetch('/api/new_reservation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    }).then(response => response.json())
        .then(result => {
            // 处理服务器返回的数据
            if (result.success) {
                alert('同步成功！');
                location.replace(location.href);
            } else {
                alert('同步失败: ' + result.message);
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            alert('发生错误，请稍后再试。');
        });
}


function createUserCard(data) {
    const card = document.createElement("div");
    card.className = "card user-card";

    // 使用模板字符串生成模块内容
    card.innerHTML = `
        <div class="box overview">
            <div class="simple">
                <div class="simple-1">
                    <i class="fa-solid fa-user"></i>
                    <p>预约账户</p>
                </div>
                <div id="show-account">
                    <p>${data.account}</p>
                </div>
            </div>
            <div class="status">
                <h2 class="status-text">${data.status}</h2>
            </div>
        </div>

        <div class="user-info">
            <div class="info">
                <div class="info-text">
                    <p><i class="fa-solid fa-lock"></i> 预约密码</p>
                    <p class="password-toggle" data-password="${data.password}" title="点击切换显示密码" >***********</p>
                </div>
                <div class="info-text">
                    <p><i class="fa-solid fa-clock"></i> 预约时间</p>
                    <p id="show-time">${data.time}</p>
                </div>
                <div class="info-text">
                    <p><i class="fa-solid fa-couch"></i> 预约房间</p>
                    <p id="show-room-seat">${data.room_seat}</p>
                </div>
                <div class="info-text">
                    <p><i class="fa-solid fa-chair"></i></i> 预约座位</p>
                    <p id="show-room-seat">${data.seat_id}座位</p>
                </div>
            </div>
            <div class="box">
                <div class="btn-box">
                    <button onclick="service(this)">服务</button>
                    <button onclick="releaseSeat(this)">退座</button>
                    <button onclick="editInfo(this)">修改</button>
                    <button onclick="deleteCard(event)">删除</button>
                </div>
            </div>
        </div>
    `;

    // 为密码切换功能添加事件监听
    const passwordToggle = card.querySelector(".password-toggle");
    passwordToggle.addEventListener("click", function () {
        const realPassword = this.getAttribute("data-password");
        const currentText = this.textContent;

        if (currentText === "***********") {
            this.textContent = realPassword; // 显示真实密码
        } else {
            this.textContent = "***********"; // 隐藏密码
        }
    });

    // 根据状态设置背景颜色
    const statusDiv = card.querySelector(".status");
    const statusColor = statusColors[data.status];
    if (statusColor) {
        statusDiv.style.backgroundColor = statusColor;
    }

    return card;

}

// 动态添加模块到指定位置的函数
function addCardsToContent(dataArray) {
    // 找到 <div class="content" id="content"> 容器
    const contentContainer = document.getElementById("content");
    if (!contentContainer) {
        console.error("未找到 ID 为 'content' 的容器");
        return;
    }

    // 找到 <div class="top"> 元素
    const topElement = contentContainer.querySelector(".top");
    if (!topElement) {
        console.error("未找到类名为 'top' 的元素");
        return;
    }

    // 在 <div class="top"> 的下方插入模块
    dataArray.forEach(data => {
        const card = createUserCard(data); // 调用封装的函数生成模块
        contentContainer.insertBefore(card, topElement.nextSibling); // 插入到 <div class="top"> 的下一个兄弟元素之前
    });
}

function service() {
    alert("服务功能尚未实现！");
}

function releaseSeat() {
    alert("退坐功能尚未实现！");
}

function editInfo() {
    alert("修改功能尚未实现！");
}

function deleteCard(event) {

    const card = event.target.closest(".card");
    // 获取当前点击的按钮
    const button = event.target;

    // 找到按钮所在的卡片（向上查找直到找到 class="card user-card" 的元素）
    const user_card = button.closest(".card.user-card");

    // 从卡片中提取 data.account 等信息
    const account = user_card.querySelector("#show-account p").textContent;
    const time = user_card.querySelector("#show-time").textContent;
    const roomSeat = user_card.querySelector("#show-room-seat").textContent;
    // 弹出确认对话框
    const isConfirmed = confirm(`确定要删除以下预约信息吗？\n\n预约账户: ${account}\n预约时间: ${time}\n预约位置: ${roomSeat}`);

    // 如果用户确认删除
    if (!isConfirmed) {
        return;
    }
    // 创建要发送到服务器的数据对象
    const dataToDelete = {
        account: account
    };

    if (card) {
        // 发送删除请求到服务器
        fetch('/api/delete/reservation', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataToDelete),
        }).then(response => response.json())
            .then(result => {
                if (result.success) {
                    // 添加动画类
                    card.classList.add("shrink-and-fade"); // 缩小并淡出1
                    // card.classList.add("slide-out-right"); // 滑出
                    // 设置一个短暂的延迟，等待动画完成后再删除
                    setTimeout(() => {
                        card.remove();
                    }, 300); // 动画时长为 0.3s，延迟 300ms
                } else {
                    // 处理失败情况
                    alert('删除失败: ' + result.message);
                }
            })
            .catch(error => {
                console.error('Error deleting seat:', error);
                alert('发生错误，请稍后再试。');
            });
    }
}

// 根据 room_id 查找房间名称
function findRoomName(roomId) {
    // 尝试将 roomId 转换为数字
    const roomIdNum = Number(roomId);

    // 查找房间信息，确保 roomIdNum 是数字
    const roomInfo = roomData.find(room => Number(room[1]) === roomIdNum);
    return roomInfo ? roomInfo[2] : '未知房间';
}


async function fetchReservations() {
    return fetch('/api/get/reservation', {
        method: 'GET',
        credentials: 'include'  // 确保cookies被发送
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // console.log(data.data);
                // 处理数据，例如更新页面内容
                reservationsData = data.data.map(item => ({
                    account: item.username,
                    password: item.password,
                    time: `${item.time[0]}-${item.time[1]}`,
                    room_seat: findRoomName(item.room_id),
                    seat_id: item.seat_id[0],
                    // status: status[item.account_status] || '未知状态'
                    status: item.account_status || '未知状态'
                }));
                addCardsToContent(reservationsData)
            } else {
                // alert(data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching reservations:', error);
        });
}


