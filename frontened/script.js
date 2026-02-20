const video = document.getElementById("webcam");
const statusText = document.getElementById("status");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const thresholdInput = document.getElementById("threshold");

let lookingDownStart = null;
let isRunning = false;

// Webcam access
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(error => {
        alert("Camera access denied!");
    });

function startTracking() {
    isRunning = true;
    statusText.textContent = "Status: Focused";
    statusText.style.color = "green";
}

function stopTracking() {
    isRunning = false;
    lookingDownStart = null;
    statusText.textContent = "Status: Stopped";
    statusText.style.color = "black";
}

startBtn.addEventListener("click", startTracking);
stopBtn.addEventListener("click", stopTracking);

// Demo simulation: Press D key to simulate looking down
document.addEventListener("keydown", function(event) {
    if (!isRunning) return;

    if (event.key === "d") {
        if (!lookingDownStart) {
            lookingDownStart = Date.now();
            statusText.textContent = "Status: Looking Down";
            statusText.style.color = "red";
        }

        let elapsed = (Date.now() - lookingDownStart) / 1000;
        let threshold = parseInt(thresholdInput.value);

        if (elapsed >= threshold) {
            triggerAlert();
        }
    }
});

function triggerAlert() {
    alert("⚠️ Please focus!");

    const soundType = document.getElementById("soundSelector").value;

    if (soundType === "beep") {
        new Audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3").play();
    } else {
        new Audio("https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3").play();
    }

    lookingDownStart = null;
}