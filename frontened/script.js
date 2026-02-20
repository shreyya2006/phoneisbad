// ===== UI ELEMENTS =====
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const statusText = document.getElementById("status");
const alertBox = document.getElementById("alertBox");
const audio = document.getElementById("alertAudio");

let isRunning = false;

// ===== START BUTTON =====
startBtn.addEventListener("click", () => {
    isRunning = true;
    statusText.innerText = "Monitoring...";
    statusText.style.color = "green";
});

// ===== STOP BUTTON =====
stopBtn.addEventListener("click", () => {
    isRunning = false;
    statusText.innerText = "Stopped";
    statusText.style.color = "red";
});

// ===== ALERT FUNCTION =====
function triggerAlert() {
    alertBox.style.display = "block";
    statusText.innerText = "Distracted!";
    statusText.style.color = "red";

    // Play sound if added later
    if (audio) {
        audio.play().catch(() => {});
    }

    // Hide alert after 3 seconds
    setTimeout(() => {
        alertBox.style.display = "none";
        statusText.innerText = "Monitoring...";
        statusText.style.color = "green";
    }, 3000);
}

// ===== BACKEND POLLING =====
// This checks backend every second
setInterval(async () => {
    if (!isRunning) return;

    try {
        const response = await fetch("http://localhost:5000/status");
        const data = await response.json();

        if (data.alert) {
            triggerAlert();
        }
    } catch (err) {
        console.log("Backend not running...");
    }
}, 1000);
