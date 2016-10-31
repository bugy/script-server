function onLoad() {
    var usernameField = document.getElementById("username");
    usernameField.focus();

    var form = document.getElementById("login-form");
    form.addEventListener("submit", function (event) {
        event.preventDefault();

        sendData();
    });

    var labels = document.getElementsByTagName("label");

}

function sendData() {
    var form = document.getElementById("login-form");

    var request = new XMLHttpRequest();

    var formData  = new FormData(form);

    request.addEventListener("load", function(event) {
        var status = request.status;
        var response = request.responseText;

        if (status == 200) {
            hideError();

            window.location = request.responseURL;

        } else if ((status == 401) || (status == 500)){
            showError(response);

        } else {
            showError("Unknown error occurred. Please contact the administrator");
        }
    });

    request.addEventListener("error", function(event) {
        showError("Unknown error occurred. Please contact the administrator")
    });

    request.open("POST", form.action);
    request.send(formData);
}

function showError(text) {
    var errorLabel = document.getElementById("login-error-label");
    errorLabel.innerHTML = text;
}

function hideError(text) {
    showError("");
}