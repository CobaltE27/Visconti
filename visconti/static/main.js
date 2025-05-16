const Good = {
    GRAIN: "grain",
    CLOTH: "cloth",
    DYE: "dye",
    SPICE: "spice",
    FURS: "furs",
    GOLD: "gold"
};
const Phase = {
    JOINING: "joining",
    CHOOSING: "choosing",
    BIDDING: "bidding",
    END: "end"
};

var isHost = document.querySelector("#isHost").value;
var hostIP = document.querySelector("#hostIP").value;
var joinButton = document.querySelector("#join");
joinButton.addEventListener("click", join);
var playersArea = document.querySelector("#players");
var username = undefined;
var lotPrefab = document.querySelector("#prefab-lot");
var playerBoxPrefab = document.querySelector("#prefab-player-box");
var bidView = document.querySelector("#bid-view");
var bidBoxes = document.querySelector("#bid-boxes");
var bidBoxPrefab = document.querySelector("#prefab-bid-box");
var chooseDisplay = document.querySelector("#choose-display");
var chooseForm = document.querySelector("#choose-form");
var phase = Phase.JOINING;
var day = 1;

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
    phase = data.host[0].fields.phase;
    day = Number(data.host[0].fields.day);
    updateStartButton(data);
    displayPlayers(data);

    setTimeout(refreshData, 5000);
}

function readPhase(data){
    return 
}

function updateStartButton(data){
    let startButton = document.querySelector("#start");
    if (startButton != null) {
        if (data.players.length >= 3 && data.players.length <= 6){
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
        newPlayerBox.querySelector(".lot-container").replaceChildren(...makeLotsFromString(pData.fields.lots));

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
    startButton.setAttribute("disabled", true);
    let url = "http://" + hostIP + ":8000/start/";
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const response = await fetch(url, {
        method: "POST",
        headers: {'X-CSRFToken': csrfToken},
    });
}

function instantiate(element){
    let instance = element.cloneNode(true);
    instance.classList.remove("hide");
    instance.removeAttribute("id");
    return instance;
}

function makeLotsFromString(lots){
    let lotElements = [];
    let lotStrings = lots.split(" ");
    for (let lotString of lotStrings){
        let lotElement = instantiate(lotPrefab);
        switch (lotString[0]) {
            case "g":
                lotElement.classList.add(Good.GRAIN);
                break;
            case "c":
                lotElement.classList.add(Good.CLOTH);
                break;
            case "d":
                lotElement.classList.add(Good.DYE);
                break;
            case "s":
                lotElement.classList.add(Good.SPICE);
                break;
            case "f":
                lotElement.classList.add(Good.FURS);
                break;
            case "G":
                lotElement.classList.add(Good.GOLD);
                break;
        }
        lotElement.textContent = lotString.substring(1);
        lotElements.push(lotElement);
    }
    return lotElements;
}