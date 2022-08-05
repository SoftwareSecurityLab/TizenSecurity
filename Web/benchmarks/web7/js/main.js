document.getElementById('btn').addEventListener('click', function () {
    var text = document.getElementById('inp').innerText;
    var b;
    if (text[0] == 'a') {
        b = 2;
    }
    if (text[1] == 'b') {
        document.getElementById('theId').innerHTML = text;
    }
})