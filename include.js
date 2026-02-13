async function loadHTML(id, file) {
    const target = document.getElementById(id);
    if (!target) {
        return;
    }

    try {
        const response = await fetch(file);
        if (!response.ok) {
            throw new Error(`Failed to fetch ${file}: ${response.status}`);
        }

        target.innerHTML = await response.text();
    } catch (error) {
        console.error(error);
    }
}

Promise.all([
    loadHTML("main", "main.html"),
    loadHTML("publications", "pubs.html")
]);
