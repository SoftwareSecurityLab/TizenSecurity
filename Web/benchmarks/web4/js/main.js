document.getElementById('btn').addEventListener('click', function () {
    var text = document.getElementById('inp').innerText;
    if (text[0] == 'a') {
        document.getElementById('theId').innerHTML = text;
    }
})