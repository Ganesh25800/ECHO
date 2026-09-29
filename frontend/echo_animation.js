const echoWave = document.getElementById("echoWave");

function startListening() {

    const echoWave =
        document.getElementById("echoWave");

    if (!echoWave) {
        return;
    }

    echoWave.classList.remove(
        "speaking"
    );

    echoWave.classList.add(
        "listening"
    );
}


function stopListening() {

    const echoWave =
        document.getElementById("echoWave");

    if (!echoWave) {
        return;
    }

    echoWave.classList.remove(
        "listening"
    );
}


function startSpeaking() {

    if (!echoWave) {
        return;
    }

    echoWave.classList.add("speaking");
}


function stopSpeaking() {

    if (!echoWave) {
        return;
    }

    echoWave.classList.remove("speaking");
}

const socket = new WebSocket(
    `ws://${window.location.host}/ws`
);


socket.onopen = function () {

    console.log(
        "Connected to ECHO WebSocket."
    );

};


socket.onmessage = function (message) {

    const data = JSON.parse(
        message.data
    );


    if (data.event === "TTS_STARTED") {

        startSpeaking();

    }

    else if (data.event === "TTS_FINISHED") {

        stopSpeaking();

    }

    else if (data.event === "LISTENING_STARTED") {
        startListening();
    }

    else if (data.event === "LISTENING_FINISHED") {
        stopListening();
    }

};


socket.onclose = function () {

    console.log(
        "Disconnected from ECHO WebSocket."
    );

};


socket.onerror = function (error) {

    console.error(
        "ECHO WebSocket error:",
        error
    );

};

