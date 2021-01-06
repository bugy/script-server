import {
    getWebsocketUrl,
    HttpForbiddenError,
    HttpRequestError,
    HttpUnauthorizedError,
    isWebsocketClosed,
    isWebsocketConnecting,
    isWebsocketOpen,
    SocketClosedError
} from '@/common/utils/common';

let i = 0;

export function ReactiveWebSocket(path, observer) {
    if (/^((https?)|(wss?)):\/\//.test(path)) {
        this.url = path;
    } else {
        this.url = getWebsocketUrl(path);
    }

    var self = this;

    this._finished = false;
    this._observer = observer;
    this._id = i++;
    this.queuedMessages = []

    try {
        this._websocket = new WebSocket(this.url);
    } catch (e) {
        if (this._observer.onError) {
            this._observer.onError(e);
        }
        return;
    }

    this._websocket.addEventListener('open', () => {
        for (const queuedMessage of this.queuedMessages) {
            this._websocket.send(queuedMessage);
        }
    })

    this._websocket.addEventListener('close', function (event) {
        if (self._finished) {
            return;
        }

        self._finished = true;

        if (event.code === 1000) {
            self._observer.onCompleted();
            return;
        }

        if (event.code === 403) {
            self._observer.onError(new HttpForbiddenError(event.code, event.reason));
            return;
        }

        if (event.code === 401) {
            self._observer.onError(new HttpUnauthorizedError(event.code, event.reason));
            return;
        }

        if (event.code === 404) {
            self._observer.onError(new HttpRequestError(event.code, event.reason));
            return;
        }

        if (self._observer.onError) {
            self._observer.onError(new SocketClosedError(event.code, event.reason));
        }
    });

    this._websocket.addEventListener('message', function (rawMessage) {
        self._observer.onNext(rawMessage.data);
    });

    this.close = function () {
        self._finished = true;
        self._websocket.close();
    };

    this.send = function (data) {
        if (isWebsocketClosed(self._websocket) || self._finished) {
            console.log('Attempt to write to closed socket. Data: ' + data);
            return false;
        }

        if (isWebsocketConnecting(self._websocket)) {
            this.queuedMessages.push(data)
            return
        }

        self._websocket.send(data);
    };

    this.isClosed = function () {
        return isWebsocketClosed(self._websocket) || self._finished;
    };

    this.isOpen = function () {
        return isWebsocketOpen(self._websocket);
    }
}