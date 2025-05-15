let isHost = document.querySelector("#isHost").value;
let hostIP = document.querySelector("#hostIP").value;
let joinButton = document.querySelector("#join");
joinButton.addEventListener("click", join);
let playerDiv = document.querySelector("#players");
let username = undefined;

if (isHost == "True"){
    hostIP = "127.0.0.1"
    let startButton = document.querySelector("#start");
    startButton.addEventListener("click", start);
    setTimeout(refreshData, 5000);
}
else{
    setTimeout(refreshData, 5000);
}

async function refreshData(){
    let url = "http://" + hostIP + ":8000/data/";
    const response = await fetch(url);
    if (!response.ok){
        throw new Error(response.status);
    }
    const data = await response.json();

    console.log(data);
    let startButton = document.querySelector("#start");
    if (startButton != null) {
        console.log("in");
        if (data.players.length >= 3){
            console.log("innest");
            startButton.removeAttribute("disabled");
        }
        else
            startButton.setAttribute("disabled", true);
    }

    setTimeout(refreshData, 5000);
}

async function join(event){
    event.preventDefault();
    let nameInput = document.querySelector("#username");
    nameInput.setAttribute("disabled", true);
    joinButton.setAttribute("disabled", true);
    let submitData = new FormData();
    submitData.append("name", document.querySelector("#username").value);
    let url = "http://" + hostIP + ":8000/setname/";
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const response = await fetch(url, {
        method: "POST",
        body: submitData,
        headers: {'X-CSRFToken': csrfToken},
    });
    username = document.querySelector("#username").value;
}

async function start(event){
    event.preventDefault();
}