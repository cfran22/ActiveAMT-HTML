//Function to extract the name and value from each 'collectable' input
//POSTs this data back to flask as key val pairs, split by ':', separated by ',', as a single string
//For parsing purposes, name and value are wrapped with forward slashes.

$('form').submit(function(){
    var request = new XMLHttpRequest();
    var method = "POST";
    var url = 'https://127.0.0.1:5000/getAnswers';
    var async = false;
    var answers = [];
    var params;

    var inputs = document.getElementsByClassName('collectable');

    if(inputs.length > 1){
        var i;

        for(i = 0; i < inputs.length; i++){
            var name = inputs[i].name;
            var value = inputs[i].value;
            var name_val = '/' + name + ':' + value + '/';

            if(name != null && value != null){
                answers.push(name_val);
            }
        }
        params = "answers=" + answers;

    }else{
        params = "answers=" + inputs[0].value;
    }

    request.open(method, url, async);
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.send(params);
});