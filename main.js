function preload(impath) {
    var img = new Image();
    img.src = impath;
}

preload('laser.png');

var html = document.querySelector("html");

function laser() {
    html.style.cursor = "url('laser.png'), auto";
}

function brain() {
    // document.body.style.cursor = "url('cursor.png'), auto";
    html.style.cursor = "url('cursor.png'), auto";
}

html.onmousedown = laser;
html.onmouseup = brain;
