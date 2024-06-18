document.addEventListener('DOMContentLoaded', function() {
    if (!firebase.apps.length) {
        var firebaseConfig = window.firebaseConfig;
        console.log("Firebase Config: ", firebaseConfig);  // 초기화 확인 로그
        firebase.initializeApp(firebaseConfig);
    } else {
        firebase.app();
    }

    var auth = firebase.auth();
    console.log("Firebase initialized: ", auth);  // 초기화 확인 로그

    // LOGIN TABS
    var tab = document.querySelectorAll('.tabs h3 a');
    tab.forEach(function(element) {
        element.addEventListener('click', function(event) {
            event.preventDefault();
            tab.forEach(function(el) {
                el.classList.remove('active');
            });
            this.classList.add('active');
            var tab_content = document.querySelector(this.getAttribute('href'));
            document.querySelectorAll('div[id$="tab-content"]').forEach(function(content) {
                content.classList.remove('active');
            });
            tab_content.classList.add('active');
        });
    });

    // LOGIN FUNCTION
    document.getElementById('login-btn').addEventListener('click', function() {
        var email = document.getElementById('user_login').value;
        var password = document.getElementById('user_pass').value;
        auth.signInWithEmailAndPassword(email, password)
            .then((userCredential) => {
                console.log("User signed in: ", userCredential.user);
                userCredential.user.getIdToken().then(function(idToken) {
                    fetch('/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({idToken: idToken})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            window.location.href = '/index';
                        } else {
                            alert('Login failed: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Login failed: ' + error.message);
                    });
                });
            })
            .catch((error) => {
                console.error("Error signing in: ", error.code, error.message);
                alert(error.message);
            });
    });

    // SIGNUP FUNCTION
    document.getElementById('signup-btn').addEventListener('click', function() {
        var email = document.getElementById('user_email').value;
        var password = document.getElementById('user_pass_signup').value;
        auth.createUserWithEmailAndPassword(email, password)
            .then((userCredential) => {
                console.log("User signed up: ", userCredential.user);
                alert("User signed up successfully");
                location.reload();  // Refresh the page upon successful signup
            })
            .catch((error) => {
                console.error("Error signing up: ", error.code, error.message);
                alert(error.message);
            });
    });

    // PASSWORD RESET FUNCTION
    document.getElementById('reset-password-btn').addEventListener('click', function(event) {
        event.preventDefault();
        console.log("Reset password button clicked");  // 이벤트 트리거 확인 로그
        var email = document.getElementById('user_recover').value;
        console.log("Email for password reset: ", email); // 이메일 값을 콘솔에 출력

        if (email) {
            auth.sendPasswordResetEmail(email)
                .then(() => {
                    console.log("Password reset email sent");
                    alert("Password reset email sent. Please check your inbox.");
                })
                .catch((error) => {
                    console.error("Error sending password reset email: ", error.code, error.message);
                    alert(error.message);
                });
        } else {
            console.error("Email is required for password reset");
            alert("Please enter your email.");
        }
    });

    // TOGGLE TERMS AND RECOVERY PANELS
    var toggleElements = document.querySelectorAll('.agree, .forgot, #toggle-terms, .log-in, .sign-up');
    toggleElements.forEach(function(element) {
        element.addEventListener('click', function(event) {
            event.preventDefault();
            var user = document.querySelector('.user');
            var terms = document.querySelector('.terms');
            var form = document.querySelector('.form-wrap');
            var recovery = document.querySelector('.recovery');
            var close = document.querySelector('#toggle-terms');
            var arrow = document.querySelector('.tabs-content .fa');

            if (this.classList.contains('agree') || this.classList.contains('log-in') || (this.id === 'toggle-terms' && terms.classList.contains('open'))) {
                if (terms.classList.contains('open')) {
                    form.classList.remove('open');
                    form.classList.add('closed');
                    terms.classList.remove('open');
                    terms.classList.add('closed');
                    close.classList.remove('open');
                    close.classList.add('closed');
                } else {
                    if (this.classList.contains('log-in')) {
                        return;
                    }
                    form.classList.remove('closed');
                    form.classList.add('open');
                    terms.classList.remove('closed');
                    terms.classList.add('open');
                    terms.scrollTop = 0;
                    close.classList.remove('closed');
                    close.classList.add('open');
                    user.classList.add('overflow-hidden');
                }
            } else if (this.classList.contains('forgot') || this.classList.contains('sign-up') || this.id === 'toggle-terms') {
                if (recovery.classList.contains('open')) {
                    form.classList.remove('open');
                    form.classList.add('closed');
                    recovery.classList.remove('open');
                    recovery.classList.add('closed');
                    close.classList.remove('open');
                    close.classList.add('closed');
                } else {
                    if (this.classList.contains('sign-up')) {
                        return;
                    }
                    form.classList.remove('closed');
                    form.classList.add('open');
                    recovery.classList.remove('closed');
                    recovery.classList.add('open');
                    close.classList.remove('closed');
                    close.classList.add('open');
                    user.classList.add('overflow-hidden');
                }
            }
        });
    });

    // DISPLAY MESSAGE
    document.querySelector('.recovery .button').addEventListener('click', function(event) {
        event.preventDefault();
        document.querySelector('.recovery .mssg').classList.add('animate');
        setTimeout(function() {
            document.querySelector('.form-wrap').classList.remove('open');
            document.querySelector('.form-wrap').classList.add('closed');
            document.querySelector('.recovery').classList.remove('open');
            document.querySelector('.recovery').classList.add('closed');
            document.querySelector('#toggle-terms').classList.remove('open');
            document.querySelector('#toggle-terms').classList.add('closed');
            document.querySelector('.tabs-content .fa').classList.remove('active');
            document.querySelector('.tabs-content .fa').classList.add('inactive');
            document.querySelector('.recovery .mssg').classList.remove('animate');
        }, 2500);
    });

    // DISABLE SUBMIT FOR DEMO
    document.querySelectorAll('.button').forEach(function(element) {
        element.addEventListener('click', function(event) {
            event.preventDefault();
            return false;
        });
    });
});
