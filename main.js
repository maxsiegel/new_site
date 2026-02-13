function preload(impath) {
    var img = new Image();
    img.src = impath;
}

preload('laser.png');

var html = document.documentElement;

function laser() {
    html.style.cursor = "url('laser.png'), auto";
}

function brain() {
    html.style.cursor = "url('cursor.png'), auto";
}

document.addEventListener("DOMContentLoaded", function () {
    brain();
    html.onmousedown = laser;
    html.onmouseup = brain;
});
