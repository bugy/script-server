export const nameField = {
    name: 'Name',
    required: true
};

export const descriptionField = {
    name: 'Description'
};

export const argField = {
    name: 'Arg',
    description: 'Allows to specify command-line argument for the parameter (e.g. -q or --quiet)'
};

export const envVarField = {
    name: 'Env variable',
    description: 'Environment variable, which will be associated with the parameter (by default PARAM_{uppercase name})'
};

export const typeField = {
    name: 'Type',
    type: 'list',
    values: ['text', 'int', 'list', 'multiselect', 'file_upload', 'server_file', 'ip', 'ip4', 'ip6']
};

export const noValueField = {
    name: 'Without value',
    withoutValue: true,
    description: 'Pass only flag (Arg) to the script, without any value'
};

export const repeatParamField = {
    name: 'Space after Arg',
    withoutValue: true,
    description: 'Separate Arg and value with space (--Arg= value) or not (--Arg=value)'
};

export const constantField = {
    name: 'Constant',
    withoutValue: true,
    description: 'The parameter is constant: the default value is always used and user cannot see or change it'
};

export const requiredField = {
    name: 'Required',
    withoutValue: true
};

export const secureField = {
    name: 'Secret value',
    withoutValue: true,
    description: 'The secret value will not be shown anywhere on the server (logs, history, etc.)'
};

export const minField = {
    name: 'Min',
    type: 'int'
};

export const maxField = {
    name: 'Max',
    type: 'int'
};

export const allowedValuesScriptField = {
    name: 'Script',
    required: true
};

export const maxLengthField = {
    name: 'Max characters length',
    type: 'int'
};

export const allowedValuesFromScriptField = {
    name: 'Load from script',
    withoutValue: true,
    description: 'Fill values based on defined script'
};

export const defaultValueField = {
    name: 'Default value'
};

export const multipleArgumentsField = {
    name: 'As multiple arguments',
    withoutValue: true,
    description: 'Pass each value as a separate argument (single comma-separated argument otherwise)'
};

export const sameArgParamField = {
    name: 'Repeat Arg with each value',
    withoutValue: true,
    description: 'Add argument name to each value (Arg val1 Arg val2), one time argument otherwise (Arg val1 val2)'
};

export const separatorField = {
    name: 'Separator',
    required: true
};

export const fileDirField = {
    name: 'File directory',
    required: true
};

export const recursiveField = {
    name: 'Recursive',
    withoutValue: true,
    description: 'Allows recursive file selection'
};

export const fileTypeField = {
    name: 'File type',
    type: 'list',
    default: 'any',
    values: ['any', 'file', 'dir']
};