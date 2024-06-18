if (!firebase.apps.length) {
    firebase.initializeApp({
        apiKey: "AIzaSyD2rtOS7GcYURKouuO1DmPkGYaN3BiERL8",
        authDomain: "brain-tumor-2ea99.firebaseapp.com",
        databaseURL: "https://brain-tumor-2ea99-default-rtdb.firebaseio.com",
        projectId: "brain-tumor-2ea99",
        storageBucket: "brain-tumor-2ea99.appspot.com",
        messagingSenderId: "393430095565",
        appId: "1:393430095565:web:67482c41fec8524a7bbb84",
        measurementId: "G-1EXK7R1VSG"
    });
} else {
    firebase.app(); // 이미 초기화된 앱을 사용
}