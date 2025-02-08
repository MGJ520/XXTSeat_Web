function pustSignIn() {
    event.preventDefault()
    const email_login_local = document.getElementById('email_login_local').value;
    const password_login_local = document.getElementById('password_login_local').value;
    const data = {email_login_local, password_login_local};

    fetch('/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/home';
            } else {
                document.getElementById('login_error').innerText = data.error;
            }
        })
        .catch(error => console.error('Error:', error));
}

function postSignUp() {
    event.preventDefault()
    const username_register_local = document.getElementById('username_register_local').value;
    const email_register_local = document.getElementById('email_register_local').value;
    const password_register_local = document.getElementById('password_register_local').value;
    const data = {username_register_local, email_register_local, password_register_local};

    fetch('/api/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('成功注册')
                window.location.href = '/login';
            } else {
                document.getElementById('register_error').innerText = data.error;
            }
        })
        .catch(error => console.error('Error:', error));
}

// 在每次请求中添加JWT
function addJwtToRequest(requestOptions) {
    const token = localStorage.getItem('auth_token');
    if (token) {
        requestOptions.headers['Authorization'] = `Bearer ${token}`;
    }
    return requestOptions;
}

function signUp() {
    document.querySelector('.sign-in').classList.toggle('is-hidden');
    document.querySelector('.sign-up').classList.toggle('is-hidden');
}

function backSighIn() {
    document.querySelector('.sign-in').classList.toggle("is-hidden")
    document.querySelector('.sign-up').classList.toggle("is-hidden")
}