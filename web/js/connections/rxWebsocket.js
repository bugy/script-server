'use strict';

var i = 0;

function ReactiveWebSocket(path, observer) {
    if (/^((https?)|(wss?)):\/\//.test(path)) {
        this.url = path;
    } else {
        this.url = getWebsocketUrl(path);
    }

    var self = this;

    this._finished = false;
    this._observer = observer;
    this._id = i++;

    try {
        this._websocket = new WebSocket(this.url);
    } catch (e) {
        this._observer.onError(e);
        return;
    }


    this._websocket.addEventListener('close', function (event) {
        if (self._finished) {
            return;
        }

        self._finished = true;

        if (event.code === 1000) {
            self._observer.onCompleted();
            return;
        }

        if ((event.code === 403) || (event.code === 404)) {
            self._observer.onError(new HttpUnauthorizedError(event.code, event.reason));
            return;
        }

        self._observer.onError(new SocketClosedError(event.code, event.reason));
    });

    this._websocket.addEventListener('message', function (rawMessage) {
        self._observer.onNext(rawMessage);
    });

    this.close = function () {
        self._finished = true;
        self._websocket.close();
    };

    this.send = function (data) {
        if (isWebsocketClosed(self._websocket) || self._finished) {
            console.log('Attempt to write to closed socket. Data: ' + data);
            return;
        }

        self._websocket.send(data);
    }
}