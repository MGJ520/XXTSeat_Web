function pustSignIn() {
    alert("登录！")
}

function postSignUp() {
    alert("注册！")
}


function signUp() {
    document.querySelector('.sign-in').classList.toggle('is-hidden');
    document.querySelector('.sign-up').classList.toggle('is-hidden');  
}

function backSighIn() {
    document.querySelector('.sign-in').classList.toggle("is-hidden")
    document.querySelector('.sign-up').classList.toggle("is-hidden")
}