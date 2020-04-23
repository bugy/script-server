export const nameField = {
    name: 'Script name',
    required: true
};
export const groupField = {
    name: 'Group',
    description: 'Aggregates scripts from the same group into the same category on UI'
};
export const scriptPathField = {
    name: 'Script path',
    required: true
};
export const descriptionField = {
    name: 'Description'
};
export const workDirField = {
    name: 'Working directory'
};
export const allowAllField = {
    name: 'Allow all'
};
export const bashFormattingField = {
    name: 'Bash formatting',
    description: 'Enable ANSI escape sequences for text formatting and cursor moves'
};
export const requiresTerminalField = {
    name: 'Requires terminal',
    description: 'Enables pseudo-terminal. ' +
        'This is need for some utilities which behave differently, when executed from terminal'
};
export const includeScriptField = {
    name: 'Include config',
    description: 'Allows to include another shared config'
};