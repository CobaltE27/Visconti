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
const florin = "&fnof;";

var isHost = document.querySelector("#isHost").value;
var hostIP = document.querySelector("#hostIP").value;
var joinButton = document.querySelector("#join");
joinButton.addEventListener("click", join);

var playersArea = document.querySelector("#players");
var playerBoxPrefab = document.querySelector("#prefab-player-box");
var username = undefined;

var mainBoard = document.querySelector("#main-board");
var bidView = document.querySelector("#bid-view");
var bidBoxes = document.querySelector("#bid-boxes");
var bidBoxPrefab = document.querySelector("#prefab-bid-box");
var bidFormPrefab = document.querySelector("#prefab-bid-form");
var chooseDisplay = document.querySelector("#choose-display");
var chooseForm = document.querySelector("#choose-form");
var drawButton = document.querySelector("#draw");
drawButton.addEventListener("click", (event) => choose(event, true));
var startBidButton = document.querySelector("#start-bid");
startBidButton.addEventListener("click", (event) => choose(event, false));
var phase = Phase.JOINING;
var day = 1;
var dayCounter = document.querySelector("#day-counter");
var phaseDisplay = document.querySelector("#phase-display");
var deckCounter = document.querySelector("#deck-counter");
var winnerDisplay = document.querySelector("#winner");

var pyramidsArea = document.querySelector("#pyramids");
var threeRank = document.querySelector("#three-rank");
var fourRank = document.querySelector("#four-rank");
var fiveRank = document.querySelector("#five-rank");
var sixRank = document.querySelector("#six-rank");

var lotPrefab = document.querySelector("#prefab-lot");

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
    updateMainBoardStatics(data);
    updateStartButton(data);
    displayPlayers(data);
    updatePyramids(data);
    updateMainBoardContent(data);

    setTimeout(refreshData, 5000);
}

function updateStartButton(data){
    let startButton = document.querySelector("#start");
    if (startButton != null) {
        if (data.players.length >= 3 && data.players.length <= 6 && data.host[0].fields.phase == Phase.JOINING){
            startButton.removeAttribute("disabled");
        }
        else
            startButton.setAttribute("disabled", true);
    }
}

function updateMainBoardStatics(data){
    dayCounter.textContent = data.host[0].fields.day;
    phaseDisplay.textContent = data.host[0].fields.phase;
    mainBoard.querySelector(".lot-container").replaceChildren(...makeLotsFromString(data.host[0].fields.group_lots));
    deckCounter.textContent = countLotsFromString(data.host[0].fields.deck);

    let pCount = data.players.length;
    threeRank.classList.add("hide");
    fourRank.classList.add("hide");
    fiveRank.classList.add("hide");
    sixRank.classList.add("hide");
    if (pCount <= 3)
        threeRank.classList.remove("hide");
    else if (pCount == 4)
        fourRank.classList.remove("hide");
    else if (pCount == 5)
        fiveRank.classList.remove("hide");
    else
        sixRank.classList.remove("hide");
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

function updatePyramids(data){
    let goods = [Good.GRAIN, Good.CLOTH, Good.DYE, Good.SPICE, Good.FURS];
    for (let good of goods){
        let pyramidRows = pyramidsArea.querySelectorAll("table." + good + " tbody tr td");
        for (let row of pyramidRows)
            row.textContent = "";
        for (let pData of data.players){
            pyramidRows[pyramidRows.length - 1 - pData.fields[good]].textContent += pData.fields.name + " ";
        }
    }
}

function updateMainBoardContent(data){
    switch (phase) {
        case Phase.JOINING:
            bidView.classList.add("hide");
            chooseDisplay.classList.add("hide");
            chooseForm.classList.add("hide");
            break;
        case Phase.END:
            bidView.classList.add("hide");
            chooseDisplay.classList.add("hide");
            chooseForm.classList.add("hide");
            let winnerList = [];
            let highestMoney = 0;
            for (let pData of data.players)
                if (pData.fields.money >= highestMoney){
                    if (pData.fields.money > highestMoney)
                        winnerList = [];
                    winnerList.push(pData.fields.name);
                    highestMoney = pData.fields.money;
                }
            if (winnerList.length == 1)
                winnerDisplay.textContent = winnerList[0] + " wins!";
            else {
                for (let i = 0; i < winnerList.length; i++){
                    if (i == winnerList.length - 1)
                        winnerDisplay.textContent += "and " + winnerList[i];
                    else
                        winnerDisplay.textContent += winnerList[i] + ", ";
                    winnerDisplay.textContent += " tied!";
                }
            }
            winnerDisplay.classList.remove("hide");
            break;
        case Phase.CHOOSING: {
            const chooser = data.host[0].fields.chooser
            if (username == chooser){ //user is choosing
                let groupCount = countLotsFromString(data.host[0].fields.group_lots);
                let canDraw = false;
                if (groupCount < 3)
                    for (let pData of data.players){
                        if (5 - countLotsFromString(pData.fields.lots) >= groupCount + 1)
                            canDraw = true;
                    }

                if (canDraw) {
                    drawButton.removeAttribute("disabled");
                    startBidButton.removeAttribute("disabled");
                }
                else {
                    drawButton.setAttribute("disabled", true);
                    startBidButton.setAttribute("disabled", true);
                    choose(undefined, false); //start bid
                }

                chooseForm.classList.remove("hide");
                chooseDisplay.classList.add("hide");

            } else { //someone else is choosing
                chooseDisplay.querySelector(".player-name").textContent = chooser;

                chooseForm.classList.add("hide");
                chooseDisplay.classList.remove("hide");
            }
            bidView.classList.add("hide");
            break;
        }
        case Phase.BIDDING: {
            let bidElements = [];
            let highestBid = 0;
            for (let pData of data.players){
                if (Number(pData.fields.current_bid) > highestBid)
                    highestBid = Number(pData.fields.current_bid);
            }
            let pCount = data.players.length;
            let chooserIndex = data.players.findIndex((elt) => elt.fields.name == data.host[0].fields.chooser);
            let i = (chooserIndex) % pCount;
            do {
                i = (i + 1) % pCount
                let bidElt = undefined;
                if (data.players[i].fields.name == data.host[0].fields.bidder && username == data.host[0].fields.bidder){ //user is the bidder
                    bidElt = instantiate(bidFormPrefab);
                    let bidInput = bidElt.querySelector("form label .bid-input");
                    bidInput.min = highestBid + 1;
                    bidInput.value = highestBid + 1;
                    bidInput.max = data.players[i].fields.money;
                    bidElt.querySelector("form .bid-button").addEventListener("click", (event) => submitBid(event, false));
                    bidElt.querySelector("form .pass-button").addEventListener("click", (event) => submitBid(event, true));
                } else {
                    bidElt = instantiate(bidBoxPrefab);
                    bidElt.querySelector(".player-name").textContent = data.players[i].fields.name;
                    bidElt.querySelector(".bid").textContent = data.players[i].fields.current_bid;
                }

                bidElements.push(bidElt);
            } while (i != chooserIndex)
            bidBoxes.replaceChildren(...bidElements);

            let currentBidderName = data.host[0].fields.bidder;
            let passedBidder = false;
            let newBoxes = bidBoxes.children;
            for (let i = 0; i < newBoxes.length; i++){
                let bid = newBoxes[i].querySelector(".bid");
                let bName = newBoxes[i].querySelector(".player-name");
                if (bid && bName){
                    if (bName.textContent == currentBidderName) {
                        bid.textContent = "Bidding";
                        bid.classList.remove("money");
                        passedBidder = true;
                    } else if (passedBidder){
                        bid.textContent = "";
                        bid.classList.remove("money");
                    } else {
                        if (bid.textContent == 0) {
                            bid.textContent = "pass";
                            bid.classList.remove("money");
                        }
                    }
                } else { //this user is the current bidder, psace occupied by a form
                    passedBidder = true;
                }
            }
            
            chooseForm.classList.add("hide");
            chooseDisplay.classList.add("hide");
            bidView.classList.remove("hide");
            break;
        }
    }
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
    try {
        const response = await fetch(url, {
            method: "POST",
            body: submitData,
            headers: {'X-CSRFToken': csrfToken},
        });
        if (!response.ok)
            throw Error()
    } catch (e) {
        nameInput.value = "";
        nameInput.removeAttribute("disabled");
        joinButton.removeAttribute("disabled");
    }
    username = document.querySelector("#username").value;
}

async function start(event){
    event.preventDefault();
    document.querySelector("#start").setAttribute("disabled", true);
    let url = "http://" + hostIP + ":8000/start/";
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {'X-CSRFToken': csrfToken},
        });
        if (!response.ok)
            throw Error()
    } catch (e) {
        document.querySelector("#start").removeAttribute("disabled");
    }
}

async function choose(event, drawOrBid){
    if (event)
        event.preventDefault();
    drawButton.setAttribute("disabled", true);
    startBidButton.setAttribute("disabled", true);

    let url = "http://" + hostIP + ":8000/choose/";
    let submitData = new FormData();
    submitData.append("drawOrBid", drawOrBid);
    submitData.append("username", username);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(url, {
            method: "POST",
            body: submitData,
            headers: {'X-CSRFToken': csrfToken},
        });
        if (!response.ok)
            throw Error()
    } catch (e) {
        drawButton.removeAttribute("disabled");
        startBidButton.removeAttribute("disabled");
    }
}

async function submitBid(event, passed){
    event.preventDefault();
    let input = bidBoxes.querySelector(".bid-form form label .bid-input");
    let bidButton = bidBoxes.querySelector(".bid-form form .bid-button");
    let passButton = bidBoxes.querySelector(".bid-form form .pass-button");
    input.setAttribute("disabled", true);
    bidButton.setAttribute("disabled", true);
    passButton.setAttribute("disabled", true);

    let bid = 0;
    if (!passed)
        bid = Number(input.value);

    let url = "http://" + hostIP + ":8000/bid/";
    let submitData = new FormData();
    submitData.append("bid", bid);
    submitData.append("username", username);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(url, {
            method: "POST",
            body: submitData,
            headers: {'X-CSRFToken': csrfToken},
        });
        if (!response.ok)
            throw Error()
    } catch (e) {
        input.removeAttribute("disabled");
        bidButton.removeAttribute("disabled");
        passButton.removeAttribute("disabled");
    }
}

function instantiate(element){
    let instance = element.cloneNode(true);
    instance.classList.remove("hide");
    instance.removeAttribute("id");
    return instance;
}

function makeLotsFromString(lots){
    let lotElements = [];
    if (lots == "")
        return lotElements;

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

function countLotsFromString(lots){
    if (lots == "")
        return 0;
    return lots.split(" ").length;
}