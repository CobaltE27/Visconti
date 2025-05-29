var dotsStyle = document.head.appendChild(document.createElement("style"));
dotsStyle.innerHTML = ".in-progress:after { content: \"\" }";
var dotsCounter = 0;
setTimeout(animateDots, 500);

function animateDots() {
    let dotted = document.getElementsByClassName("in-progress");
    dotsCounter = (dotsCounter + 1) % 4;
    dotsStyle.innerHTML = ".in-progress:after { content: \"" + ".".repeat(dotsCounter) + "\" }";
    setTimeout(animateDots, 500);
}