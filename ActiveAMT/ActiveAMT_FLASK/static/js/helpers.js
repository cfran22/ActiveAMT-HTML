
function getAnswer() {
    var request = new XMLHttpRequest();
    var url = "https://127.0.0.1:5000/getAnswers";
    var method = "POST";
    var async = false;
    var field = $('input[name="answer"]').val();
    var answer = "answers=" + field;

    request.open(method, url, async);
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.send(answer);
}
