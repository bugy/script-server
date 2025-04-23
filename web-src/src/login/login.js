import '@/assets/css/index.css';
import '@/common/materializecss/imports/cards';
import '@/common/materializecss/imports/input-fields';
import '@/common/style_imports';
import '@/common/style_imports.js';
import { axiosInstance } from '@/common/utils/axios_utils'
import {
    addClass,
    contains,
    createTemplateElement,
    getQueryParameter,
    getUnparameterizedUrl,
    guid,
    logError,
    removeClass,
    toQueryArgs
} from '@/common/utils/common';
import get from 'lodash/get'

var NEXT_URL_KEY = 'next';
var OAUTH_RESPONSE_KEY = 'code';

var loginMethod = 'POST';
var loginUrl = 'login';

window.onload = onLoad;

function checkRedirectReason() {
    let redirectReason = getQueryParameter('redirectReason');
    if (redirectReason === 'prohibited') {
        return 'Access if prohibited for this user'
    }

    return redirectReason;
}

function validateURL(url) {
    if (!url || url.startsWith('http') || url.startsWith('/')) {
        return url;
    }
    return '/';
}

function onLoad() {
    axiosInstance.get('auth/config').then(({ data: config }) => {
        const loginContainer = document.getElementById('login-content-container');

        if (config['type'] === 'google_oauth') {
            setupGoogleOAuth(loginContainer, config);
        } else if (config['type'] === 'azure_ad_oauth') {
            setupAzureAdOAuth(loginContainer, config);
        } else if (config['type'] === 'keycloak_openid') {
            setupKeycloakOpenid(loginContainer, config);
        } else if (config['type'] === 'authentik') {
            setupAuthentikAuth(loginContainer, config);
        } else if (config['type'] === 'gitlab') {
            setupGitlabOAuth(loginContainer, config);
        } else {
            setupCredentials(loginContainer);
        }

        const redirectError = checkRedirectReason()
        if (redirectError) {
            showError(redirectError)
        }
    })
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

function setupAzureAdOAuth(loginContainer, authConfig) {
    setupOAuth(
        loginContainer,
        authConfig,
        'login-azure_ad_oauth-template',
        'login-azure_ad_oauth-button')
}

function setupKeycloakOpenid(loginContainer, authConfig) {
    setupOAuth(
        loginContainer,
        authConfig,
        'login-keycloak-template',
        'login-keycloak-button')
}

function setupAuthentikAuth(loginContainer, authConfig) {
    setupOAuth(
        loginContainer,
        authConfig,
        'login-authentik-template',
        'login-authentik-button')
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
        localState[NEXT_URL_KEY] = validateURL(getQueryParameter(NEXT_URL_KEY));

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
            showError('Invalid client state. Please try to relogin');
            return;
        }

        var nextUrl = validateURL(oauthState[NEXT_URL_KEY]);
        var urlFragment = oauthState['urlFragment'];

        var previousLocation = getUnparameterizedUrl();
        if (nextUrl) {
            previousLocation += '?' + toQueryArgs({ 'next': nextUrl });
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

    var nextUrl = validateURL(getQueryParameter(NEXT_URL_KEY));
    var nextUrlFragment = window.location.hash;

    if (nextUrl) {
        formData.append(NEXT_URL_KEY, nextUrl);
    }

    const onSuccess = function (response) {
        hideError();
        hideInfo();
        getLoginButton().removeAttribute('disabled');

        var redirect = response.headers['location']
        if (!redirect) {
            showError('Invalid server response. Please contact the administrator');
            return;
        }

        if (nextUrlFragment) {
            redirect += nextUrlFragment;
        }

        window.location = redirect;
    };

    const onError = function (error) {
        const status = get(error, 'response.status');

        const loginButton = getLoginButton();
        loginButton.removeAttribute('disabled');

        if (contains([400, 401, 403, 500], status)) {
            showError(error.response.data);

        } else {
            showError('Unknown error occurred. Please contact the administrator');
            logError(error)
        }
    };

    showInfo('Verifying credentials...');

    const loginButton = getLoginButton();
    loginButton.setAttribute('disabled', 'disabled');

    axiosInstance.post(loginUrl, formData, { maxRedirects: 0 })
        .then(onSuccess)
        .catch(onError)
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
