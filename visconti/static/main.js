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

var canv = document.querySelector("#bid-view canvas");
var waveRefresh = 30;
var waveCounter = 0;
var waveAmplitude = 7;
var waveTarget = 0.1;
var waveLevel = 0.1;

var playerStats = undefined;
var dotsStyle = document.head.appendChild(document.createElement("style"));
dotsStyle.innerHTML = ".in-progress:after { content: \"\" }";
var dotsCounter = 0;
setTimeout(animateDots, 500);
setTimeout(animateWaves, waveRefresh);

const urlQuery = new URLSearchParams(window.location.search);
const queryIsHost = urlQuery.get("hosting");
if (isHost == "True" || queryIsHost == "1"){
    hostIP = "127.0.0.1"
    let startButton = document.querySelector("#start");
    startButton.addEventListener("click", start);
    let addAIButton = document.querySelector("#add-ai");
    addAIButton.addEventListener("click", joinAI);
    setTimeout(refreshData, checkPeriod);
}
else{
    setTimeout(refreshData, checkPeriod);
}

async function refreshData(){
    let submitData = new FormData();
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    submitData.append("action", "data");
    try {
        const response = await fetch(document.URL, {
            method: "POST",
            body: submitData,
            headers: {'X-CSRFToken': csrfToken},
        });
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
            if (typeof phase !== "undefined") {
                if (phase != Phase.CHOOSING && data.host[0].fields.phase == Phase.CHOOSING)
                    playSound("choose_start.mp3");
                else if (phase != Phase.BIDDING && data.host[0].fields.phase == Phase.BIDDING) {
                    playSound("bid_start.mp3");
                    waveTarget = 0.1;
                    waveLevel = 0.1;
                }
            }
            phase = data.host[0].fields.phase;
            if (typeof day === "undefined" || day < data.host[0].fields.day)
                playSound("day_start.mp3");
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
    if (groupLots.length > 0 && data.host[0].fields.phase == Phase.CHOOSING) {
        groupLots[groupLots.length - 1].classList.add("new-lot");
        if (Number(groupLots[groupLots.length - 1].querySelector("span").textContent) >= 10)
            playSound("gold.mp3");
    }
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
    let nextChooserIndex = undefined;
    let afterChooser = false;
    if ((phase == Phase.BIDDING || phase == Phase.CHOOSING) && countLotsFromString(data.host[0].fields.deck) > 0 && data.players.length > 0){
        for (let i = 0; data.host[0].fields.chooser != data.players[i].fields.name || !afterChooser; i = (i + 1) % data.players.length){
            if (afterChooser && countLotsFromString(data.players[i].fields.lots) < 5){
                nextChooserIndex = i;
                break;
            }
            if (data.players[i].fields.name == data.host[0].fields.chooser)
                afterChooser = true;
        }
    }
    for (const [i, pData] of data.players.entries()){
        let newPlayerBox = instantiate(playerBoxPrefab);
        newPlayerBox.querySelector(".player-name").textContent = (pData.fields.ai == "" ? "" : "🤖") + pData.fields.name;
        newPlayerBox.querySelector(".player-money").textContent = pData.fields.money;
        let newDeltaMoney = newPlayerBox.querySelector(".delta-money");
        switch (phase) {
            case Phase.WAITING:
            case Phase.END: {
                let deltaValue = pData.fields.reward_rank + pData.fields.reward_pyramid + pData.fields.reward_pyramid_rank - pData.fields.money_spent;
                newDeltaMoney.textContent = stringifyDeltaMoney(deltaValue);
                if (deltaValue > 0)
                    newDeltaMoney.classList.add("gain");
                else
                    newDeltaMoney.classList.add("loss");
                break;
            }
            case Phase.BIDDING:
            case Phase.CHOOSING:
                newDeltaMoney.classList.add("loss");
                newDeltaMoney.textContent = stringifyDeltaMoney(-pData.fields.money_spent);
                break;
            case Phase.JOINING:
                newDeltaMoney.textContent = "";
        }

        newPlayerBox.querySelector(".lot-container").replaceChildren(...makeLotsFromString(pData.fields.lots, 5));
        let lotValue = valueOfLotsString(pData.fields.lots);
        if (lotValue != 0)
            newPlayerBox.querySelector(".value-display").innerHTML = "<strong>" + lotValue + "</strong> total ship value";

        if (username == pData.fields.name)
            newPlayerBox.classList.add("me");

        if (typeof nextChooserIndex !== "undefined" && i == nextChooserIndex){
            let nextIndicator = document.createElement("span");
            nextIndicator.textContent = "↓ " + data.players[i].fields.name + " chooses next ↓";
            newChildren.push(nextIndicator);
        }

        newChildren.push(newPlayerBox);
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
            playSound("win.mp3");
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
            waitingForm.querySelector("#waiting-list").classList.add("hide");
            waitingForm.classList.remove("hide");
            break;
        case Phase.CHOOSING: {
            const chooser = data.host[0].fields.chooser
            if (username == chooser){ //user is choosing
                let groupCount = countLotsFromString(data.host[0].fields.group_lots);
                let deckCount = countLotsFromString(data.host[0].fields.deck);
                let canDraw = false;
                if (groupCount < 3 && deckCount > 0)
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
            let numBids = 0;
            for (let i = 0; i < newBoxes.length; i++){
                let bid = newBoxes[i].querySelector(".bid");
                let bName = newBoxes[i].querySelector(".player-name");
                if (bid && bName){
                    if (bName.textContent == currentBidderName) {
                        bid.textContent = "Bidding";
                        bid.classList.remove("money");
                        bid.classList.add("in-progress");
                        passedBidder = true;
                    } else if (passedBidder){
                        bid.textContent = "";
                        bid.classList.remove("money");
                    } else {
                        if (bid.textContent == 0) {
                            bid.textContent = "pass";
                            bid.classList.remove("money");
                        } else {
                            numBids++;
                        }
                    }
                } else { //this user is the current bidder, psace occupied by a form
                    passedBidder = true;
                }
            }

            waveTarget = 0.1 + 0.8 * (numBids / newBoxes.length)
            
            chooseForm.classList.add("hide");
            chooseDisplay.classList.add("hide");
            bidView.classList.remove("hide");
            break;
        }
        case Phase.WAITING:
            playSound("day_end.mp3");
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
    submitData.append("action", "setname");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        if (!nameInput.value.match(/^\w*$/)) //only allows word characters
            throw Error()
        const response = await fetch(document.URL, {
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

async function joinAI(event){
    event.preventDefault();
    let aiDropdown = document.querySelector("#ai-dropdown");
    let submitData = new FormData();
    let aiName = aiDropdown.options[aiDropdown.selectedIndex].value;
    submitData.append("name", aiName);
    submitData.append("action", "setname");
    submitData.append("ai", aiName);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(document.URL, {
            method: "POST",
            body: submitData,
            headers: {'X-CSRFToken': csrfToken},
        });
        if (!response.ok)
            throw Error();
    } catch (e) {
        console.log(e);
    }
}

async function start(event){
    event.preventDefault();
    document.querySelector("#start").setAttribute("disabled", true);
    document.querySelector("#add-ai").setAttribute("disabled", true);
    let submitData = new FormData();
    submitData.append("action", "start");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(document.URL, {
            method: "POST",
            body: submitData,
            headers: {'X-CSRFToken': csrfToken},
        });
        if (!response.ok)
            throw Error();
    } catch (e) {
        document.querySelector("#start").removeAttribute("disabled");
        document.querySelector("#add-ai").removeAttribute("disabled");
    }
}

async function choose(event, drawOrBid){
    if (event)
        event.preventDefault();
    drawButton.setAttribute("disabled", true);
    startBidButton.setAttribute("disabled", true);

    let submitData = new FormData();
    submitData.append("drawOrBid", drawOrBid);
    submitData.append("username", username);
    submitData.append("action", "choose");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(document.URL, {
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

    let submitData = new FormData();
    submitData.append("bid", bid);
    submitData.append("username", username);
    submitData.append("action", "bid");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(document.URL, {
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

    let submitData = new FormData();
    submitData.append("username", username);
    submitData.append("action", "ready");
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(document.URL, {
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

function makeLotsFromString(lots, outOf = 0){
    let lotElements = [];
    if (lots != "") {
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
    }
    while (lotElements.length < outOf){
        let ghost = instantiate(lotPrefab);
        ghost.classList.add("ghost");
        lotElements.push(ghost);
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
        let newStatTables = [];
        for (let pData of data.players){
            let statTable = instantiate(playerStatsPrefab);
            let headRowInner = "<th>" + pData.fields.name + "</th>";
            let footRowInner = "<th>Net Profit</th>";
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
                let currentStat = playerStats.days[i][pData.fields.name];
                headRowInner += "<th>Day " + (i + 1) + "</th>";
                footRowInner += "<td>" + stringifyDeltaMoney(currentStat.rewardRank + currentStat.rewardPyramidRank + currentStat.rewardPyramid - currentStat.moneySpent) + "</td>";
                spentRow.appendChild(createEltWithText("td", currentStat.moneySpent));
                spentSum += Number(currentStat.moneySpent);
                rankRow.appendChild(createEltWithText("td", currentStat.rewardRank));
                rankSum += Number(currentStat.rewardRank);
                pyramidRankRow.appendChild(createEltWithText("td", currentStat.rewardPyramidRank));
                pyrRankSum += Number(currentStat.rewardPyramidRank);
                pyramidRow.appendChild(createEltWithText("td", currentStat.rewardPyramid));
                pyrSum += Number(currentStat.rewardPyramid);
            }
            spentRow.appendChild(createEltWithText("td", spentSum));
            rankRow.appendChild(createEltWithText("td", rankSum));
            pyramidRankRow.appendChild(createEltWithText("td", pyrRankSum));
            pyramidRow.appendChild(createEltWithText("td", pyrSum));
            statTable.querySelector("thead tr").innerHTML = headRowInner + "<th>Total</th>";
            statTable.querySelector("tfoot tr").innerHTML = footRowInner + "<td>" + stringifyDeltaMoney(rankSum + pyrRankSum + pyrSum - spentSum) + "</td>";
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

function stringifyDeltaMoney(delta){
    if (Number(delta) < 0)
        return String(delta);
    else if (Number(delta) == 0)
        return "";
    return "+" + String(delta);
}

function animateDots() {
    dotsCounter = (dotsCounter + 1) % 4;
    let dots = ".".repeat(dotsCounter) + " ".repeat(3 - dotsCounter);
    dotsStyle.innerHTML = ".in-progress:after { content: \"" + dots + "\" }";
    setTimeout(animateDots, 500);
}

function playSound(filename) {
    let snd = new Audio("media/" + filename);
    snd.play();
}

function animateWaves() {
    if (typeof phase !== "undefined" && phase == Phase.BIDDING) {
        let width = bidView.clientWidth;
        let height = bidView.clientHeight;
        canv.width = width;
        canv.height = height;
        let ctx = canv.getContext("2d");
        let horizRezolution = 200;
        waveLevel = waveLevel + (waveTarget - waveLevel) * 0.1;
        let vOffset = height - height * waveLevel;
        ctx.fillStyle = "#005EB8";
        ctx.moveTo(0, waveFunc(waveCounter) + vOffset);
        ctx.beginPath();
        for (let x = 1; x < width; x += (width / horizRezolution)) {
            ctx.lineTo(x, waveFunc(x * 0.005 + waveCounter) + vOffset);
        }
        ctx.lineTo(width, waveFunc(width * 0.005 + waveCounter) + vOffset);
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.lineTo(0, waveFunc(waveCounter) + vOffset);
        ctx.fill();

        ctx.strokeStyle = "#669ACC";
        ctx.lineWidth = 7.0;
        ctx.moveTo(0, waveFunc(waveCounter) + vOffset);
        ctx.beginPath();
        for (let x = 1; x < width; x += (width / horizRezolution)) {
            ctx.lineTo(x, waveFunc(x * 0.005 + waveCounter) + vOffset);
        }
        ctx.lineTo(width, waveFunc(width * 0.005 + waveCounter) + vOffset);
        ctx.stroke();
    }
    waveCounter += 1.0 / 50.0;
    if (waveCounter > 1) waveCounter = 0
    setTimeout(animateWaves, waveRefresh);
}

function waveFunc(x) {
    return Math.sin(x * 2 * Math.PI) * waveAmplitude;
}