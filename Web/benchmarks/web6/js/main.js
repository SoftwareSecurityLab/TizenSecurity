document.getElementById('btn2').addEventListener('click', function () {
    var a = document.getElementById('inp').innerHTML;
    if (!a.includes('<')) {
        document.getElementById('theId').innerHTML = a;
    }

})
document.getElementById('btn').addEventListener('click', function () {
    var text = document.getElementById('inp2').innerText;
    document.getElementById('theId').innerHTML = text;

})
