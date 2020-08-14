import '@/assets/css/index.css';
import '@/common/materializecss/imports/cards';
import '@/common/materializecss/imports/input-fields';
import '@/common/style_imports';
import '@/common/style_imports.js';
import {
    addClass,
    callHttp,
    contains,
    createTemplateElement,
    getQueryParameter,
    getUnparameterizedUrl,
    guid,
    removeClass,
    toQueryArgs
} from '@/common/utils/common';

var NEXT_URL_KEY = 'next';
var OAUTH_RESPONSE_KEY = 'code';

var loginMethod = 'POST';
var loginUrl = 'login';

window.onload = onLoad;

function onLoad() {
    callHttp('auth/config', null, 'GET', function (configResponse) {
        var loginContainer = document.getElementById('login-content-container');

        var config = JSON.parse(configResponse);
        if (config['type'] === 'google_oauth') {
            setupGoogleOAuth(loginContainer, config);
        } else if (config['type'] === 'gitlab') {
            setupGitlabOAuth(loginContainer, config);
        } else {
            setupCredentials(loginContainer);
        }
    });
}

function setupCredentials(loginContainer) {
    var credentialsTemplate = createTemplateElement('login-credentials-template');
    loginContainer.appendChild(credentialsTemplate);

    M.updateTextFields();

    const form = loginContainer.getElementsByClassName('login-form')[0];
    form.action = loginUrl;
    form.method = loginMethod;

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        var formData = new FormData(form);
        sendLoginRequest(formData);
    });
}

function setupGoogleOAuth(loginContainer, authConfig) {
    setupOAuth(
        loginContainer,
        authConfig,
        'login-google_oauth-template',
        'login-google_oauth-button')
}

function setupGitlabOAuth(loginContainer, authConfig) {
    setupOAuth(
        loginContainer,
        authConfig,
        'login-gitlab-template',
        'login-gitlab-button')
}

function setupOAuth(loginContainer, authConfig, templateName, buttonId) {
    var credentialsTemplate = createTemplateElement(templateName);
    loginContainer.appendChild(credentialsTemplate);

    var oauthLoginButton = document.getElementById(buttonId);
    oauthLoginButton.onclick = function () {
        var token = guid(32);

        var localState = {
            'token': token,
            'urlFragment': window.location.hash
        };
        localState[NEXT_URL_KEY] = getQueryParameter(NEXT_URL_KEY);

        saveState(localState);

        const queryArgs = {
            'redirect_uri': getUnparameterizedUrl(),
            'state': token,
            'client_id': authConfig['client_id'],
            'scope': authConfig['oauth_scope'],
            'response_type': OAUTH_RESPONSE_KEY
        };
        const query = toQueryArgs(queryArgs);
        window.location = authConfig['oauth_url'] + '?' + query;
    };

    processCurrentOauthState();
}

function processCurrentOauthState() {
    var oauthState = restoreState();

    var oauthResponseCode = getQueryParameter(OAUTH_RESPONSE_KEY);
    var queryStateToken = getQueryParameter('state');
    if (oauthState || oauthResponseCode) {
        if (!oauthState && oauthResponseCode) {
            console.log('oauth_state=' + oauthState);
            console.log('oauthResponseCode=' + oauthResponseCode);
            showError('Invalid client state. Please try to relogin');
            return;
        }

        var nextUrl = oauthState[NEXT_URL_KEY];
        var urlFragment = oauthState['urlFragment'];

        var previousLocation = getUnparameterizedUrl();
        if (nextUrl) {
            previousLocation += '?' + toQueryArgs({'next': nextUrl});
        }
        if (urlFragment) {
            previousLocation += urlFragment;
        }


        if (!oauthResponseCode) {
            if (getQueryParameter(NEXT_URL_KEY)) {
                return;
            }
            window.location = previousLocation;
        } else {
            window.history.pushState(null, '', previousLocation);
        }

        var localStateToken = oauthState.token;
        if (queryStateToken !== localStateToken) {
            showError('Invalid client state. Please try to relogin');
            return;
        }

        var formData = new FormData();
        formData.append(OAUTH_RESPONSE_KEY, oauthResponseCode);
        sendLoginRequest(formData);
    }
}

function getLoginButton() {
    return document.getElementsByClassName('login-button')[0];
}

function sendLoginRequest(formData) {
    var request;

    var nextUrl = getQueryParameter(NEXT_URL_KEY);
    var nextUrlFragment = window.location.hash;

    if (nextUrl) {
        formData.append(NEXT_URL_KEY, nextUrl);
    }

    var onSuccess = function () {
        hideError();
        hideInfo();
        getLoginButton().removeAttribute('disabled');

        var redirect = request.getResponseHeader('Location');
        if (!redirect) {
            showError('Invalid server response. Please contact the administrator');
            return;
        }

        if (nextUrlFragment) {
            redirect += nextUrlFragment;
        }

        window.location = redirect;
    };

    var onError = function (errorCode, errorText) {
        const loginButton = getLoginButton();
        loginButton.removeAttribute('disabled');

        if (contains([400, 401, 403, 500], errorCode)) {
            showError(errorText);

        } else {
            showError('Unknown error occurred. Please contact the administrator');
        }
    };

    showInfo('Verifying credentials...');

    const loginButton = getLoginButton();
    loginButton.setAttribute('disabled', 'disabled');

    request = callHttp(loginUrl, formData, loginMethod, onSuccess, onError);
}

function showError(text) {
    const label = document.getElementsByClassName('login-info-label')[0];
    label.innerText = text;

    if (text) {
        addClass(label, 'error');
    }
}

function hideError() {
    showError('');
}

function showInfo(text) {
    const label = document.getElementsByClassName('login-info-label')[0];
    label.innerText = text;

    if (text) {
        removeClass(label, 'error');
    }
}

function hideInfo() {
    showInfo('');
}

var LOCAL_STATE_KEY = 'oauth_state';

function saveState(localState) {
    sessionStorage.setItem(LOCAL_STATE_KEY, JSON.stringify(localState));
}

function restoreState() {
    var state = JSON.parse(sessionStorage.getItem(LOCAL_STATE_KEY));
    sessionStorage.removeItem(LOCAL_STATE_KEY);
    return state;
}
