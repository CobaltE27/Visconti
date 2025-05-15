var isHost = document.querySelector("#isHost").value;
var hostIP = document.querySelector("#hostIP").value;
var joinButton = document.querySelector("#join");
joinButton.addEventListener("click", join);
var playersArea = document.querySelector("#players");
var username = undefined;
var playerBoxPrefab = document.querySelector("#prefab-player-box");

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
    updateStartButton(data);
    displayPlayers(data);

    setTimeout(refreshData, 5000);
}

function updateStartButton(data){
    let startButton = document.querySelector("#start");
    if (startButton != null) {
        if (data.players.length >= 3){
            startButton.removeAttribute("disabled");
        }
        else
            startButton.setAttribute("disabled", true);
    }
}

function displayPlayers(data){
    let newChildren = [];
    for (let pData of data.players){
        let newPlayerBox = instantiate(playerBoxPrefab);
        newPlayerBox.querySelector(".player-name").textContent = pData.fields.name;
        newPlayerBox.querySelector(".player-money").textContent = pData.fields.money;
        newChildren.push(newPlayerBox);
    }
    playersArea.replaceChildren(...newChildren);
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

function instantiate(element){
    let instance = element.cloneNode(true);
    instance.classList.remove("hide");
    instance.removeAttribute("id");
    return instance;
}