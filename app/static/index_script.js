const startTime = 8; // 开始时间
const endTime = 22; // 结束时间
const maxDuration = 4; // 最长选择时长（小时）
let timeSlots = []; // 存储时间段
let selectedSlots = []; // 存储正式选中的时间段
let highlightedSlots = []; // 存储高亮提示的时间段
let firstSelectedIndex = null; // 记录第一个选中的时间点索引
let selectedStart = [];
let selectedEnd = [];
let userData = [];
let roomData = [];
// 示例数据
const data = [
    {
        account: "15795126651",
        password: "123456",
        time: "12:00-15:00",
        roomSeat: "一教505",
        status: "学习中"
    },
    {
        account: "13800138000",
        password: "654321",
        time: "10:00-12:00",
        roomSeat: "二教303",
        status: "已完成"
    }
];

document.addEventListener('DOMContentLoaded', function () {


    const buttons = document.querySelectorAll('.nav-button');

    buttons.forEach(function (button) {
        button.addEventListener('click', activateButton);
    });


    document.getElementById('sidebar').addEventListener('click', function (event) {
        if (event.target.tagName === 'BUTTON') {
            const path = event.target.getAttribute('data-path');
            loadContent(path);
        }
    });


    document.getElementById('nav-button-logout').addEventListener('click', function (event) {
        fetch('/api/logout', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    localStorage.clear();   //   localStorage 清除所有
                    sessionStorage.clear(); // sessionStorage 清除所有
                    window.location.href = '/login';
                } else {
                    alert('注销失败')
                }
            })
            .catch(error => console.error('Error:', error));


    });

    getUserData().then(data => {
        if (data) {
            //设置用户昵称
            setUserAvatar(data.platformNickname);
            updateProfileInfo('text-info', {
                nickname: data.platformNickname,
                email: data.platformEmail
            });
            userData = data;
        } else {
            console.log('No data available');
        }
    });
    document.querySelector('.nav-button[data-path="/control-panel"]').click();
});


function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    if (sidebar.classList.contains('active')) {
        sidebar.classList.remove('active');
    } else {
        sidebar.classList.add('active');
    }
}

function loadContent(path) {

    timeSlots = []; // 存储时间段
    selectedSlots = []; // 存储正式选中的时间段
    highlightedSlots = []; // 存储高亮提示的时间段
    firstSelectedIndex = null; // 记录第一个选中的时间点索引
    selectedTimeRange = [];

    fetch(path)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // 加载 lib 文件
            const styles = Array.from(doc.querySelectorAll('link[rel="stylesheet"]'));
            styles.forEach(link => {
                const style = document.createElement('link');
                style.rel = 'stylesheet';
                style.href = link.href;
                document.head.appendChild(style);
            });

            // 加载 JavaScript 文件
            const scripts = Array.from(doc.querySelectorAll('script[src]'));
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                newScript.src = script.src;
                newScript.async = false; // 如果需要保持执行顺序
                document.body.appendChild(newScript);
            });

            // 设置 HTML 内容
            document.getElementById('content').innerHTML = doc.body.innerHTML;

            // 由于 innerHTML 不会执行内嵌的 script 标签，我们需要手动执行它们
            const inlineScripts = Array.from(doc.body.querySelectorAll('script:not([src])'));
            inlineScripts.forEach(script => {
                const inlineScript = document.createElement('script');
                inlineScript.textContent = script.textContent;
                document.body.appendChild(inlineScript);
            });
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
            document.getElementById('content').innerHTML = '<p>Under development.</p>';
        });
}


function activateButton(event) {
    const buttons = document.querySelectorAll('.nav-button');
    buttons.forEach(function (button) {
        button.classList.remove('active');
    });
    event.target.classList.add('active');
    const sidebar = document.getElementById('sidebar');
    if (sidebar.classList.contains('active')) {
        sidebar.classList.remove('active');
    }
}


// 根据昵称生成颜色
function nicknameToColor(nickname) {
    var hash = 0;
    for (var i = 0; i < nickname.length; i++) {
        hash = 31 * hash + nickname.charCodeAt(i);
    }
    var color = '#' + ((1 << 24) + (hash & 0xffffff)).toString(16).slice(1);
    return color;
}

// 设置头像昵称和颜色
function setUserAvatar(nickname) {
    var avatar = document.getElementById('avatar');
    var color = nicknameToColor(nickname);
    avatar.textContent = nickname.charAt(0).toUpperCase(); // 显示昵称的首字母大写
    avatar.style.backgroundColor = color; // 设置背景颜色
    avatar.style.borderColor = color; // 设置边框颜色
}


async function getUserData() {
    try {
        // permissionLevel
        // 0用户0
        // 1用户1
        // 2用户2
        // 3管理员A3
        // 使用提供的fetch配置发起请求
        const response = await fetch('/api/get/user_data', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
        });

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 解析JSON响应
        const userDataArray = await response.json();

        // 确保返回的是一个数组，并且至少有一个元素
        if (!Array.isArray(userDataArray) || userDataArray.length === 0) {
            throw new Error('User data is not an array or is empty');
        }

        // 解构赋值，从数组中的第一个对象获取数据
        const {
            account_count = undefined,
            last_login_time = undefined,
            latest_login_ip = undefined,
            login_count = undefined,
            login_failure_count = undefined,
            permission_level = undefined,
            platform_account_time = undefined,
            platform_email = undefined,
            platform_nickname = undefined
        } = userDataArray[0];
        // 返回转换后的数据
        return {
            accountCount: account_count,
            lastLoginTime: last_login_time,
            latestLoginIp: latest_login_ip,
            loginCount: login_count,
            loginFailureCount: login_failure_count,
            permissionLevel: permission_level,
            platformAccountTime: platform_account_time,
            platformEmail: platform_email,
            platformNickname: platform_nickname
        };
    } catch
        (error) {
        // 错误处理
        console.error('Failed to fetch user data:', error);
        return null;
    }
}


function updateProfileInfo(profileId, newInfo) {
    // 获取包含昵称和电子邮件的div元素
    const nicknameDiv = document.getElementById(profileId).querySelector('.nickname');
    const emailDiv = document.getElementById(profileId).querySelector('.email');

    // 检查元素是否存在
    if (nicknameDiv && emailDiv) {
        // 更新昵称和电子邮件内容
        nicknameDiv.textContent = newInfo.nickname;
        emailDiv.textContent = newInfo.email;
    } else {
        console.error('One or both elements were not found');
    }
}


