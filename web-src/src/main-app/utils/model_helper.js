export const PARAM_TYPE_LIST = 'list';
export const PARAM_TYPE_MULTISELECT = 'multiselect';
export const PARAM_TYPE_SERVER_FILE = 'server_file';
export const PARAM_TYPE_FILE_UPLOAD = 'file_upload';

export const comboboxTypes = [PARAM_TYPE_LIST, PARAM_TYPE_MULTISELECT, PARAM_TYPE_SERVER_FILE];

export function preprocessParameter(parameter, fileLoadFunction) {
    if (parameter.type === PARAM_TYPE_MULTISELECT) {
        parameter.multiselect = true;

    } else if (parameter.type === PARAM_TYPE_FILE_UPLOAD) {
        parameter.default = null;

    } else if (isRecursiveFileParameter(parameter)) {
        parameter.loadFiles = fileLoadFunction;
    }
}

export function isComboboxParameter(parameter) {
    return comboboxTypes.includes(parameter.type) && !isRecursiveFileParameter(parameter);
}

export function isRecursiveFileParameter(parameter) {
    return (parameter.type === PARAM_TYPE_SERVER_FILE) && (parameter.fileRecursive);
}

export function scriptNameToHash(scriptName) {
    return encodeURIComponent(scriptName);
}