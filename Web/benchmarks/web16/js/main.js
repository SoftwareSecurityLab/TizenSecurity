
window.onload = function () {
    var textbox = document.querySelector('.contents');
    textbox.addEventListener("click", function (e) {
        box = document.querySelector('#textbox');
        box.innerHTML = box.innerHTML == "Basic" ? "Sample" : "Basic";
    });
};

function myFunction(val) {
    if (val[0] == 'a') {
        document.getElementById("demo").innerHTML = "Hello " + val;
    }
}
