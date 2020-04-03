import {isNull} from '@/common/utils/common';

export const defaultFavicon = createDefaultFavicon();
export let executingFavicon;
export let finishedFavicon;

const FILL_COLOR = '#66FF00';
const STROKE_COLOR = '#444444';

let currentIcon = 'defaultFavicon';

const faviconImage = new Image();
faviconImage.src = defaultFavicon.href;

faviconImage.onload = function () {
    executingFavicon = createExecutingFavicon(faviconImage);
    finishedFavicon = createFinishedFavicon(faviconImage);

    setCurrentIcon();
};

export function setDefaultFavicon() {
    currentIcon = 'defaultFavicon';

    setFavicon(defaultFavicon);
}

export function setExecutingFavicon() {
    currentIcon = 'executingFavicon';

    if (!isNull(executingFavicon)) {
        setFavicon(executingFavicon);
    } else {
        setFavicon(defaultFavicon);
    }
}

export function setFinishedFavicon() {
    currentIcon = 'finishedFavicon';

    if (!isNull(finishedFavicon)) {
        setFavicon(finishedFavicon);
    } else {
        setFavicon(defaultFavicon);
    }
}

function setFavicon(favicon) {
    const head = document.getElementsByTagName('head')[0];

    for (let i = 0; i < head.childNodes.length; i++) {
        const child = head.childNodes[i];
        if ((child.tagName === 'LINK') && (child.type === 'image/x-icon')) {
            head.replaceChild(favicon, child);
            return;
        }
    }

    head.appendChild(favicon);
}

function setCurrentIcon() {
    switch (currentIcon) {
        case 'executingFavicon': {
            setFavicon(executingFavicon);
            return;
        }
        case 'finishedFavicon': {
            setFavicon(finishedFavicon);
            return;
        }
        default: {
            setFavicon(defaultFavicon);
        }
    }
}


function createLink(href) {
    const link = document.createElement('link');
    link.type = 'image/x-icon';
    link.rel = 'shortcut icon';
    link.href = href;
    return link;
}

function createDefaultFavicon() {
    return createLink('favicon.ico');
}

function createExecutingFavicon(baseImage) {
    const {canvas, context} = prepareCanvas(baseImage);

    const radius = baseImage.width / 5;
    const offsetX = baseImage.width / 4 * 3;
    const offsetY = baseImage.height / 4 * 3;

    context.beginPath();
    context.arc(offsetX, offsetY, radius, 0, 2 * Math.PI, true);
    context.fillStyle = FILL_COLOR;
    context.fill();

    context.lineWidth = 2;
    context.strokeStyle = STROKE_COLOR;
    context.stroke();

    return createLink(canvas.toDataURL('image/x-icon'));
}

function createFinishedFavicon(baseImage) {
    const {canvas, context} = prepareCanvas(baseImage);

    const offsetX = baseImage.width / 4 * 3;
    const offsetY = baseImage.height / 4 * 3;

    function drawTick(lineWidth, color) {
        context.beginPath();
        context.moveTo(offsetX - 10, offsetY - 8);
        context.lineTo(offsetX, offsetY + 8);
        context.lineTo(offsetX + 10, offsetY - 8);
        context.lineWidth = lineWidth;
        context.strokeStyle = color;
        context.stroke();
    }

    drawTick(8, STROKE_COLOR);
    drawTick(5, FILL_COLOR);

    return createLink(canvas.toDataURL('image/x-icon'));
}

function prepareCanvas(baseImage) {
    const canvas = document.createElement('canvas');
    canvas.width = baseImage.width;
    canvas.height = baseImage.height;

    const context = canvas.getContext('2d');
    context.drawImage(baseImage, 0, 0);

    return {canvas, context};
}
