var out = document.querySelector("output");
var canv = document.querySelector("#bid-view canvas");
var bidView = document.querySelector("#bid-view");
canv.width = bidView.clientWidth;
canv.height = bidView.clientHeight;

var dotsStyle = document.head.appendChild(document.createElement("style"));
dotsStyle.innerHTML = ".in-progress:after { content: \"\" }";
var dotsCounter = 0;
setTimeout(animateDots, 500);

function animateDots() {
    dotsCounter = (dotsCounter + 1) % 4;
    dotsStyle.innerHTML = ".in-progress:after { content: \"" + ".".repeat(dotsCounter) + "\" }";
    setTimeout(animateDots, 500);
}