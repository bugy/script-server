var loginMethod = 'POST';
var loginUrl = 'login';

function onLoad() {
    callHttp('auth/type', null, 'GET', function (authType) {
        var loginContainer = document.getElementById('login-content-container');

        if (authType === 'google_oauth') {
            setupGoogleOAuth(loginContainer);
        } else {
            setupCredentials(loginContainer);
        }
    });

    var form = document.getElementById('login-form');
    form.action = loginUrl;
    form.method = loginMethod;

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        sendLoginRequest(form);
    });
}

function setupGoogleOAuth(loginContainer) {
    var credentialsTemplate = createTemplateElement('login-google_oauth-template');
    loginContainer.appendChild(credentialsTemplate);
}

function setupCredentials(loginContainer) {
    var credentialsTemplate = createTemplateElement('login-credentials-template');
    loginContainer.appendChild(credentialsTemplate);

    var labels = document.getElementsByTagName("label");
    for (var i = 0; i < labels.length; i++) {
        var label = labels[i];

        //workaround for browser autofill - it's not updating label position and label overlap with value
        addClass(label, "active");
    }
}

function sendLoginRequest(form) {
    var formData = new FormData(form);

    var request = new XMLHttpRequest();

    if (window.location.hash && (window.location.hash.length > 1)) {
        formData.append('url_fragment', window.location.hash.substr(1))
    }

    // if the server is behind a reverse proxy, then it needs real URL in order to send redirect_uri to oauth
    var requestUrl = window.location.origin + '/' + getUrlDir() + '/' + loginUrl;
    requestUrl = requestUrl.replace(/([^:]\/)\/+/g, "$1");
    formData.append('request_url', requestUrl);

    var queryParameters = readQueryParameters(window.location.href);
    for (var paramIndex = 0; paramIndex < queryParameters.length; paramIndex++) {
        var key = queryParameters[paramIndex].key;
        var value = queryParameters[paramIndex].value;

        formData.append(key, value);
    }

    request.addEventListener("load", function (event) {
        var status = request.status;
        var response = request.responseText;

        if (status === 200) {
            hideError();

            var redirect = request.getResponseHeader('Location');
            if (!redirect) {
                showError('Invalid server response. Please contact the administrator');
                return;
            }

            window.location = redirect;

        } else if ((status === 401) || (status === 500)) {
            showError(response);

        } else {
            showError("Unknown error occurred. Please contact the administrator");
        }
    });

    request.addEventListener("error", function (event) {
        showError("Unknown error occurred. Please contact the administrator")
    });

    request.open(loginMethod, loginUrl);
    request.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    request.send(formData);
}

function showError(text) {
    $('.login-error-label').text(text);
}

function hideError(text) {
    showError('');
}
