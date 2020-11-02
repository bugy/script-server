export const repeatPeriodField = {
    required: true,
    type: 'int',
    min: 1,
    max: 50
};

export const repeatTimeUnitField = {
    type: 'list',
    values: ['hours', 'days', 'weeks', 'months']
}
