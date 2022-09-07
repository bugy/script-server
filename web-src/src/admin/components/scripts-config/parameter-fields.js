export const nameField = {
    name: 'Name',
    required: true
};

export const descriptionField = {
    name: 'Description'
};

export const paramField = {
    name: 'Param',
    description: 'Allows to specify command-line option for the parameter (e.g. -q or --quiet)'
};

export const envVarField = {
    name: 'Env variable',
    description: 'Environment variable, which will be associated with the parameter (by default PARAM_{uppercase name})'
};

export const typeField = {
    name: 'Type',
    type: 'list',
    values: [
        'text',
        'int',
        'list',
        'multiselect',
        'editable_list',
        'file_upload',
        'server_file',
        'multiline_text',
        'ip',
        'ip4',
        'ip6']
};

export const noValueField = {
    name: 'Without value',
    withoutValue: true,
    description: 'Pass only flag (param) to the script, without any value'
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

export const allowedValuesScriptShellEnabledField = {
    name: 'Enable bash operators',
    withoutValue: true,
    description: 'Enables bash operators (e.g. | && ||) in script section. ' +
        'Be careful!! If a script has dependant values, it will be a subject to script injection'
};

export const defaultValueField = {
    name: 'Default value'
};

export const sameArgParamField = {
    name: 'Combine param with value',
    withoutValue: true,
    description: 'If true, param and value will be sent as a single argument, e.g. -param=value'
};

export const multiselectArgumentTypeField = {
    name: 'Value split type',
    type: 'list',
    values: ['single_argument', 'argument_per_value', 'repeat_param_value'],
    default: 'single_argument',
    description: 'Defines how multiselect values will be passed to a script: \n'
        + 'single_argument: -param value1,value2,value3 \n'
        + 'argument_per_value: -param value1 value2 value3 \n'
        + 'repeat_param_value: -param value1 -param value2 -param value3'
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