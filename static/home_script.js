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


});

// 定义清除Cookie并跳转页面的函数
function clearCookiesAndRedirect() {

}

function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    if (sidebar.classList.contains('active')) {
        sidebar.classList.remove('active');
    } else {
        sidebar.classList.add('active');
    }
}


// 加载内容的函数
function loadContent(path) {
    fetch(path)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            document.getElementById('content').innerHTML = html;
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
            // 在这里可以添加错误处理逻辑，例如显示错误消息给用户
            document.getElementById('content').innerHTML = '<p>Error loading content.</p>';
        });
}


function activateButton(event) {
    var buttons = document.querySelectorAll('.nav-button');
    buttons.forEach(function (button) {
        button.classList.remove('active');
    });
    event.target.classList.add('active');
}

