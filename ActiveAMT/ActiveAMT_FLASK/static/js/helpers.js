
function getAnswer() {
                var xhr = new XMLHttpRequest();
                xhr.open('GET', "https://127.0.0.1:5000/getAnswer?answer=" + $('input[name="answer"]').val(), true);
                xhr.send();
            }
