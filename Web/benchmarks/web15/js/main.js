var a = 0;
document.getElementById('btn').addEventListener('click', function () {
    if (a > 0) {
        var text = document.getElementById('inp').innerText;
        if (text[0] == 'a') {
            if (text[1] == 'b') {
                if (text.slice(-1) == 'x') {
                    if (!text.includes('XYZ')) {
                        document.getElementById('theId').innerHTML = text;
                    }
                }
            }
        }
    }
})

document.getElementById('btn2').addEventListener('click', function () {
    a += 1;
})