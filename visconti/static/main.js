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
    END: "end",
    WAITING: "waiting"
};
const florin = "ƒ";
const checkPeriod = 1000;
var steps = -1;
var failCounter = 0;

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
var waitingForm = document.querySelector("#waiting-form");
var readyButton = document.querySelector("#ready-button");
readyButton.addEventListener("click", sendReady);
var playerStatArea = document.querySelector("#player-stat-area");
var playerStatsPrefab = document.querySelector("#prefab-player-stats");

var pyramidsArea = document.querySelector("#pyramids");
var threeRank = document.querySelector("#three-rank");
var fourRank = document.querySelector("#four-rank");
var fiveRank = document.querySelector("#five-rank");
var sixRank = document.querySelector("#six-rank");

var logArea = document.querySelector("#log-area");

var lotPrefab = document.querySelector("#prefab-lot");

var playerStats = undefined;

if (isHost == "True"){
    hostIP = "127.0.0.1"
    let startButton = document.querySelector("#start");
    startButton.addEventListener("click", start);
    setTimeout(refreshData, checkPeriod);
}
else{
    setTimeout(refreshData, checkPeriod);
}

async function refreshData(){
    let url = "http://" + hostIP + ":8000/data/";
    try {
        const response = await fetch(url);
        if (!response.ok){
            throw new Error(response.status);
        }
        const data = await response.json();

        console.log(data);
        failCounter = 0;
        let hostSteps = data.host[0].fields.steps;
        if (steps < hostSteps){
            console.log("refresh!");
            steps = hostSteps;
            phase = data.host[0].fields.phase;
            day = Number(data.host[0].fields.day);
            updateMainBoardStatics(data);
            updateStartButton(data);
            displayPlayers(data);
            updatePyramids(data);
            updateMainBoardContent(data);
            if (phase == Phase.END)
                return; //don't continue querying server
        }
    } catch (e) {
        failCounter++;
        if (failCounter < 20)
            console.log(e + ", ignoring and querying again.");
        else {
            console.log(e + ", too many failures, giving up.");
            return;
        }
    }
    
    setTimeout(refreshData, checkPeriod);
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
    dayCounter.textContent = data.host[0].fields.day + " / 3";
    phaseDisplay.textContent = data.host[0].fields.phase;
    let groupLots = makeLotsFromString(data.host[0].fields.group_lots);
    if (groupLots.length > 0 && data.host[0].fields.phase == Phase.CHOOSING)
        groupLots[groupLots.length - 1].classList.add("new-lot");
    mainBoard.querySelector(".lot-container").replaceChildren(...groupLots);
    deckCounter.textContent = countLotsFromString(data.host[0].fields.deck);
    logArea.innerHTML = data.host[0].fields.log;

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
    for (const [i, pData] of data.players.entries()){
        let newPlayerBox = instantiate(playerBoxPrefab);
        newPlayerBox.querySelector(".player-name").textContent = pData.fields.name;
        newPlayerBox.querySelector(".player-money").textContent = pData.fields.money;
        newPlayerBox.querySelector(".lot-container").replaceChildren(...makeLotsFromString(pData.fields.lots));
        let lotValue = valueOfLotsString(pData.fields.lots);
        if (lotValue != 0)
            newPlayerBox.querySelector(".value-display").innerHTML = "<strong>" + lotValue + "</strong> total ship value";

        if (username == pData.fields.name)
            newPlayerBox.classList.add("me");

        newChildren.push(newPlayerBox);

        if ((data.host[0].fields.phase == Phase.BIDDING || data.host[0].fields.phase == Phase.CHOOSING) && pData.fields.name == data.host[0].fields.chooser){
            let nextIndicator = document.createElement("span");
            if (i < data.players.length - 1){
                nextIndicator.textContent = "↓ " + data.players[i + 1].fields.name + " chooses next ↓";
                newChildren.push(nextIndicator);
            } else { //current playerbox is last in order
                nextIndicator.textContent = "↓ " + data.players[0].fields.name + " chooses next ↓";
                newChildren.unshift(nextIndicator);
            }
        }
    }
    playersArea.replaceChildren(...newChildren);
}

function updatePyramids(data){
    let goods = [Good.GRAIN, Good.CLOTH, Good.DYE, Good.SPICE, Good.FURS];
    for (let good of goods){
        let pyramidRows = pyramidsArea.querySelectorAll("table." + good + " tbody tr td");
        for (let row of pyramidRows)
            row.innerHTML = "";
        for (let pData of data.players){
            pyramidRows[pyramidRows.length - 1 - pData.fields[good]].innerHTML += pData.fields.name + "<br>";
        }
    }
}

function updateMainBoardContent(data){
    switch (phase) {
        case Phase.JOINING:
            bidView.classList.add("hide");
            chooseDisplay.classList.add("hide");
            chooseForm.classList.add("hide");
            waitingForm.classList.add("hide");
            break;
        case Phase.END:
            bidView.classList.add("hide");
            chooseDisplay.classList.add("hide");
            chooseForm.classList.add("hide");
            document.querySelector("#deck-status").classList.add("hide");
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
            else
                winnerDisplay.textContent = stringifyList(winnerList) + " tied!";
            winnerDisplay.classList.remove("hide");
            readyButton.classList.add("hide");
            updatePlayerStats(data);
            waitingForm.classList.remove("hide");
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

                if (groupCount == 0)
                    startBidButton.setAttribute("disabled", true);

                chooseForm.classList.remove("hide");
                chooseDisplay.classList.add("hide");

            } else { //someone else is choosing
                chooseDisplay.querySelector(".player-name").textContent = chooser;

                chooseForm.classList.add("hide");
                chooseDisplay.classList.remove("hide");
            }
            bidView.classList.add("hide");
            waitingForm.classList.add("hide");
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
                    let bidInput = bidElt.querySelector(".bid-input");
                    bidInput.min = highestBid + 1;
                    bidInput.value = highestBid + 1;
                    bidInput.max = data.players[i].fields.money;
                    bidElt.querySelector(".bid-button").addEventListener("click", (event) => submitBid(event, false));
                    bidElt.querySelector(".pass-button").addEventListener("click", (event) => submitBid(event, true));
                    bidElt.classList.add("me");
                    bidElt.classList.add("active");
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
        case Phase.WAITING:
            chooseForm.classList.add("hide");
            chooseDisplay.classList.add("hide");
            bidView.classList.add("hide");
            waitingForm.classList.remove("hide");
            updatePlayerStats(data);
            let unreadyPlayerNames = [];
            for (let pData of data.players) {
                if (!pData.fields.ready){
                    unreadyPlayerNames.push(pData.fields.name);

                    if (pData.fields.name == username){
                            readyButton.classList.add("active");
                            readyButton.removeAttribute("disabled");
                    }
                }
            }
            document.querySelector("#waiting-list").textContent = "Waiting on " + stringifyList(unreadyPlayerNames) + ".";
            break;
    }
}

async function join(event){
    event.preventDefault();
    let nameInput = document.querySelector("#username");
    nameInput.setAttribute("disabled", true);
    joinButton.setAttribute("disabled", true);
    let submitData = new FormData();
    submitData.append("name", nameInput.value);
    let url = "http://" + hostIP + ":8000/setname/";
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        if (!nameInput.value.match(/^\w*$/)) //only allows word characters
            throw Error()
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
            throw Error();
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
    let input = bidBoxes.querySelector(".bid-input");
    let bidButton = bidBoxes.querySelector(".bid-button");
    let passButton = bidBoxes.querySelector(".pass-button");
    let bid = 0;
    if (!passed) {
        if (!input.value.match(/^\d*$/))
            return
        bid = Number(input.value);

        if (bid < input.min || bid > input.max){
            input.value = input.min;
            return;
        }
    }

    input.setAttribute("disabled", true);
    bidButton.setAttribute("disabled", true);
    passButton.setAttribute("disabled", true);

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

async function sendReady(event){
    event.preventDefault()
    
    readyButton.setAttribute("disabled", true);
    readyButton.classList.remove("active");

    let url = "http://" + hostIP + ":8000/ready/";
    let submitData = new FormData();
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
        readyButton.removeAttribute("disabled");
        readyButton.classList.add("active");
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
        let value = lotString.substring(1);
        lotElement.querySelector("span").textContent = value;
        if (Number(value) >= 5)
            lotElement.classList.add("shiny");
        lotElements.push(lotElement);
    }
    return lotElements;
}

function countLotsFromString(lots){
    if (lots == "")
        return 0;
    return lots.split(" ").length;
}

function valueOfLotsString(lots){
    let numeric = lots.replaceAll(/[a-zA-Z]/g, "");
    return numeric.split(" ").reduce((partial, next) => partial + Number(next), 0);
}

function stringifyList(list){
    if (list.length == 1)
        return list[0];
    if (list.length == 2)
        return list[0] + " and " + list[1];
    let result = ""
    for (let i = 0; i < list.length; i++){
        if (i == list.length - 1)
            result += "and " + list[i];
        else
            result += list[i] + ", ";
    }
    return result;
}

function updatePlayerStats(data){
    let dayIndex = day - 1;
    if (typeof playerStats === "undefined")
        playerStats = { days: [] };
    if (typeof playerStats.days[dayIndex] === "undefined") {
        playerStats.days[dayIndex] = {"day": day}; //necessary prep for further programatically named properties
        for (let pData of data.players){
            playerStats.days[dayIndex][pData.fields.name] = {
                moneySpent: pData.fields.money_spent,
                rewardRank: pData.fields.reward_rank,
                rewardPyramid: pData.fields.reward_pyramid,
                rewardPyramidRank: pData.fields.reward_pyramid_rank
            };
        }
        console.log(playerStats);
        let newStatTables = [];
        for (let pData of data.players){
            let statTable = instantiate(playerStatsPrefab);
            let headRowInner = "<th>" + pData.fields.name + "</th>";
            let spentRow = document.createElement("tr");
            spentRow.appendChild(createEltWithText("th", "Spent Money"));
            let rankRow = document.createElement("tr");
            rankRow.appendChild(createEltWithText("th", "Ship Rank Reward"));
            let pyramidRankRow = document.createElement("tr");
            pyramidRankRow.appendChild(createEltWithText("th", "Investment Rank Reward"));
            let pyramidRow = document.createElement("tr");
            pyramidRow.appendChild(createEltWithText("th", "Investment Reward"));
            let spentSum = 0;
            let rankSum = 0;
            let pyrRankSum = 0;
            let pyrSum = 0;
            for (let i = 0; i < playerStats.days.length; i++) {
                headRowInner += "<th>Day " + (i + 1) + "</th>";
                spentRow.appendChild(createEltWithText("td", playerStats.days[i][pData.fields.name].moneySpent));
                spentSum += Number(playerStats.days[i][pData.fields.name].moneySpent);
                rankRow.appendChild(createEltWithText("td", playerStats.days[i][pData.fields.name].rewardRank));
                rankSum += Number(playerStats.days[i][pData.fields.name].rewardRank);
                pyramidRankRow.appendChild(createEltWithText("td", playerStats.days[i][pData.fields.name].rewardPyramidRank));
                pyrRankSum += Number(playerStats.days[i][pData.fields.name].rewardPyramidRank);
                pyramidRow.appendChild(createEltWithText("td", playerStats.days[i][pData.fields.name].rewardPyramid));
                pyrSum += Number(playerStats.days[i][pData.fields.name].rewardPyramid);
            }
            spentRow.appendChild(createEltWithText("td", spentSum));
            rankRow.appendChild(createEltWithText("td", rankSum));
            pyramidRankRow.appendChild(createEltWithText("td", pyrRankSum));
            pyramidRow.appendChild(createEltWithText("td", pyrSum));
            statTable.querySelector("thead tr").innerHTML = headRowInner + "<th>Total</th>";
            let body = statTable.querySelector("tbody");
            body.appendChild(spentRow);
            body.appendChild(rankRow);
            body.appendChild(pyramidRankRow);
            body.appendChild(pyramidRow);
            newStatTables.push(statTable);
        }
        playerStatArea.replaceChildren(...newStatTables);
    }
}

function createEltWithText(tagName, text){
    let elt = document.createElement(tagName);
    elt.textContent = text;
    return elt;
}