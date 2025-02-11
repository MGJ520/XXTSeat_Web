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

// 示例：设置用户昵称为"张三"
    setUserAvatar("张三");
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

            // 加载 CSS 文件
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
            document.getElementById('content').innerHTML = '<p>Error loading content.</p>';
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
    avatar.querySelector('.emoji').style.color = color; // 设置emoji颜色
}


