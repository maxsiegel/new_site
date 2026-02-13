function loadHTML(id, file) {
    fetch(file)
        .then(response => response.text())
        .then(data => {
            document.getElementById(id).innerHTML = data;
        });
}

loadHTML("main", "/main.html");
loadHTML("footer", "/pubs.html");