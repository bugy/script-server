'use strict';

import Combobox from '@/common/components/combobox'
import {mount} from '@vue/test-utils';
import {attachToDocument, setDeepProp, timeout, vueTicks, wrapVModel} from './test_utils';

// Vuetify migration: the dropdown is a v-select / v-autocomplete menu rendered
// in a teleported v-overlay (document.body), so options are queried from the
// document, not from the component subtree.

describe('Test ComboBox', function () {
    let comboBox;

    beforeEach(async function () {
        comboBox = mount(Combobox, {
            attachTo: attachToDocument(),
            props: {
                config: {
                    required: false,
                    name: 'List param X',
                    description: 'some param',
                    values: ['Value A', 'Value B', 'Value C'],
                    multiselect: false
                },
                modelValue: 'Value B',
                forceValue: false
            }
        });
        await comboBox.vm.$nextTick();

        wrapVModel(comboBox);
    });

    afterEach(async function () {
        await vueTicks();
        comboBox.unmount();
    });

    async function openDropdown() {
        await comboBox.get('.combobox input').trigger('focus');
        await comboBox.get('.combobox input').trigger('mousedown');
        await comboBox.get('.combobox input').trigger('click');
        await timeout(150);
    }

    async function closeDropdown() {
        await comboBox.get('.combobox input').trigger('keydown', {key: 'Escape'});
        await timeout(150);
    }

    function getMenuItems() {
        return [...document.querySelectorAll('.v-overlay .v-list-item')];
    }

    function itemText(item) {
        // multiselect items also contain the checkbox icon, whose Material
        // Icons ligature is plain text under jsdom — read the title only
        return item.querySelector('.v-list-item-title').textContent.trim();
    }

    function getMenuItemTexts() {
        return getMenuItems().map(itemText);
    }

    function findMenuItem(text) {
        return getMenuItems().find(item => itemText(item) === text);
    }

    async function clickMenuItem(text) {
        findMenuItem(text).click();
        await timeout(50);
    }

    function displayedSelection() {
        const spans = comboBox.element.querySelectorAll(
            '.v-select__selection-text, .v-autocomplete__selection-text');
        // multiple selections render with a trailing comma separator
        return [...spans].map(span => span.textContent.trim().replace(/,$/, ''));
    }

    async function assertListElements(expectedTexts) {
        await openDropdown();
        expect(getMenuItemTexts()).toEqual(expectedTexts);
        await closeDropdown();
    }

    function assertNoSelection() {
        expect(comboBox.vm.modelValue).toBeNull();
        expect(displayedSelection()).toEqual([]);
        expect(comboBox.get('.combobox input').attributes('placeholder'))
            .toBe('Choose your option');
    }

    describe('Test config', function () {

        it('Test initial name', function () {
            expect(comboBox.get('label').text()).toBe('List param X');
        });

        it('Test change name', async function () {
            setDeepProp(comboBox, 'config.name', 'testName1');

            await vueTicks();

            expect(comboBox.get('label').text()).toBe('testName1');
        });

        it('Test initial required', function () {
            expect(comboBox.get('input').element.required).toBe(false);
        });

        it('Test change required', async function () {
            setDeepProp(comboBox, 'config.required', true);

            await vueTicks();

            expect(comboBox.get('input').element.required).toBe(true);
        });

        it('Test initial description', function () {
            // Vuetify forwards non class/style/id/data-* attrs to the inner
            // input, so the description tooltip lives there (same as the
            // migrated Textfield).
            expect(comboBox.get('input').element.title).toBe('some param');
        });

        it('Test change description', async function () {
            setDeepProp(comboBox, 'config.description', 'My new desc');

            await vueTicks();

            expect(comboBox.get('input').element.title).toBe('My new desc');
        });

        it('Test initial allowed values', async function () {
            await assertListElements(['Value A', 'Value B', 'Value C']);
        });

        it('Test change allowed values', async function () {
            const values = ['val1', 'val2', 'hello', 'another option'];
            setDeepProp(comboBox, 'config.values', values);

            await vueTicks();

            await assertListElements(values);
        });

        it('Test hide header', async function () {
            comboBox.setProps({showHeader: false})
            await vueTicks();

            expect(comboBox.get('.combobox input').attributes('placeholder')).toBeUndefined();
        });
    });

    describe('Test values', function () {

        it('Test initial value', async function () {
            await vueTicks();

            expect(comboBox.vm.modelValue).toBe('Value B');
            expect(displayedSelection()).toEqual(['Value B']);
        });

        it('Test external value change', async function () {
            comboBox.setProps({modelValue: 'Value C'});

            await vueTicks();

            expect(comboBox.vm.modelValue).toBe('Value C');
            expect(displayedSelection()).toEqual(['Value C']);
        });

        it('Test select another value', async function () {
            await openDropdown();

            await clickMenuItem('Value A');
            await vueTicks();

            expect(comboBox.vm.modelValue).toBe('Value A');
            expect(displayedSelection()).toEqual(['Value A']);
        });

        it('Test set unknown value', async function () {
            comboBox.setProps({modelValue: 'Xyz'});

            await vueTicks();

            assertNoSelection()
        });

        it('Test set multiselect single value', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({modelValue: 'Value A'});

            await vueTicks();
            expect(comboBox.vm.modelValue).toEqual(['Value A']);
            expect(displayedSelection()).toEqual(['Value A']);
        });

        it('Test set multiselect multiple values', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({modelValue: ['Value A', 'Value C']});

            await vueTicks();
            expect(comboBox.vm.modelValue).toEqual(['Value A', 'Value C']);
            expect(displayedSelection()).toEqual(['Value A', 'Value C']);
        });

        it('Test set multiselect unknown value from multiple', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({modelValue: ['Value A', 'Value X']});

            await vueTicks();
            expect(comboBox.vm.modelValue).toEqual(['Value A']);
            expect(displayedSelection()).toEqual(['Value A']);
        });

        it('Test select multiple values in multiselect without closing', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            comboBox.setProps({modelValue: []});
            await vueTicks()

            await openDropdown()

            await clickMenuItem('Value A');
            await clickMenuItem('Value C');

            await vueTicks()

            expect(comboBox.vm.modelValue).toEqual(['Value A', 'Value C'])
        });

        it('Test change allowed values with matching value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'Value B', 'another option']);

            await vueTicks();

            expect(comboBox.vm.modelValue).toBe('Value B');
            expect(displayedSelection()).toEqual(['Value B']);
        });

        it('Test change allowed values with unmatching value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'another option']);

            await vueTicks();

            assertNoSelection();
        });

        it('Test change allowed values and then a value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'another option']);
            comboBox.setProps({modelValue: 'val2'});

            await vueTicks();

            expect(comboBox.vm.modelValue).toBe('val2');
            expect(displayedSelection()).toEqual(['val2']);
        });
    });

    describe('Test errors', function () {
        it('Test set external empty value when required', async function () {
            setDeepProp(comboBox, 'config.required', true);
            await vueTicks();

            comboBox.setProps({modelValue: ''});

            await vueTicks();

            expect(comboBox.currentError).toBe('required');
        });

        it('Test set external value after empty', async function () {
            setDeepProp(comboBox, 'config.required', true);
            comboBox.setProps({modelValue: ''});
            await vueTicks();

            comboBox.setProps({modelValue: 'Value A'});
            await vueTicks();

            expect(comboBox.currentError).toBe('');
        });
    });

    describe('Test search', function () {
        async function makeSearchable() {
            const values = Array(20).fill(0).map((v, i) => 'Value ' + i);
            setDeepProp(comboBox, 'config.values', values);
            await vueTicks();

            return values;
        }

        it('Test switch to autocomplete when many options', async function () {
            await makeSearchable();

            // the searchable rendering is a v-autocomplete: the field input
            // itself is the search field (replaces the materialize
            // in-dropdown ComboboxSearch)
            expect(comboBox.find('.v-autocomplete').exists()).toBeTrue();
        });

        it('Test no autocomplete for short lists', async function () {
            expect(comboBox.find('.v-autocomplete').exists()).toBeFalse();
            expect(comboBox.find('.v-select').exists()).toBeTrue();
        });

        it('Test show all options on open', async function () {
            const values = await makeSearchable();

            await openDropdown();

            expect(getMenuItemTexts()).toEqual(values);
        });

        it('Test show search options when one element disabled', async function () {
            const values = await makeSearchable()
            comboBox.setProps({modelValue: 'Xyz', forceValue: true})

            await vueTicks()

            await openDropdown();
            expect(getMenuItemTexts()).toEqual(['Xyz'].concat(values));
        });

        it('Test filter on search', async function () {
            await makeSearchable();

            await openDropdown();

            await comboBox.get('.combobox input').setValue('Value 2');
            await timeout(50);

            expect(getMenuItemTexts()).toEqual(['Value 2']);
        });

        it('Test filter on search second input', async function () {
            await makeSearchable();

            await openDropdown();

            await comboBox.get('.combobox input').setValue('2');
            await timeout(50);

            await comboBox.get('.combobox input').setValue('12');
            await timeout(50);

            expect(getMenuItemTexts()).toEqual(['Value 12']);
        });

        it('Test filter on search clear input', async function () {
            const values = await makeSearchable();

            await openDropdown();

            await comboBox.get('.combobox input').setValue('2');
            await timeout(50);

            await comboBox.get('.combobox input').setValue('');
            await timeout(50);

            expect(getMenuItemTexts()).toEqual(values);
        });
    });

    describe('Test forced values', function () {
        it('Test initial forced value', async function () {
            comboBox.setProps({forceValue: true, modelValue: 'Value X'})

            await vueTicks()

            expect(comboBox.vm.modelValue).toEqual('Value X')
            expect(displayedSelection()).toEqual(['Value X'])
            expect(comboBox.currentError).toBe('Obsolete value')

            await openDropdown();
            expect(getMenuItemTexts()).toEqual(['Value X', 'Value A', 'Value B', 'Value C'])
            expect(findMenuItem('Value X').classList.contains('v-list-item--disabled')).toBe(true)
        })

        it('Test set forcedValue to false when wrong value', async function () {
            comboBox.setProps({modelValue: 'Value X', forceValue: true})
            await vueTicks()

            comboBox.setProps({forceValue: false})
            await vueTicks()

            assertNoSelection()
            expect(comboBox.currentError).toBeEmpty()
            await assertListElements(['Value A', 'Value B', 'Value C'])
        })

        it('Test initial forced value when values change', async function () {
            comboBox.setProps({forceValue: true})
            await vueTicks()

            setDeepProp(comboBox, 'config.values', ['New 1', 'New 2'])
            await vueTicks()

            expect(comboBox.vm.modelValue).toEqual('Value B');
            expect(displayedSelection()).toEqual(['Value B'])
            expect(comboBox.currentError).toBe('Obsolete value')

            await openDropdown();
            expect(getMenuItemTexts()).toEqual(['Value B', 'New 1', 'New 2'])
            expect(findMenuItem('Value B').classList.contains('v-list-item--disabled')).toBe(true)
        })

        it('Test initial forced value when values change to allowed', async function () {
            comboBox.setProps({forceValue: true, modelValue: 'New 2'})
            await vueTicks()

            setDeepProp(comboBox, 'config.values', ['New 1', 'New 2'])
            await vueTicks()

            expect(comboBox.vm.modelValue).toEqual('New 2');
            expect(displayedSelection()).toEqual(['New 2'])
            expect(comboBox.currentError).toBeEmpty()

            await openDropdown();
            expect(getMenuItemTexts()).toEqual(['New 1', 'New 2'])
            expect(findMenuItem('New 2').classList.contains('v-list-item--disabled')).toBe(false)
        })

        it('Test initial forced values when multiselect', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks()
            comboBox.setProps({forceValue: true, modelValue: ['Value C', 'Value X', 'Hi']})
            await vueTicks()

            expect(comboBox.vm.modelValue).toEqual(['Value C', 'Value X', 'Hi']);
            expect(displayedSelection().sort()).toEqual(['Hi', 'Value C', 'Value X'])
            expect(comboBox.currentError).toBe('Obsolete values: Value X,Hi')

            await openDropdown();
            expect(getMenuItemTexts()).toEqual(['Value X', 'Hi', 'Value A', 'Value B', 'Value C'])
        })

        it('Test click disabled value', async function () {
            comboBox.setProps({forceValue: true, modelValue: 'Value X'})
            await vueTicks()

            await openDropdown();

            await clickMenuItem('Value X');

            expect(comboBox.vm.modelValue).toEqual('Value X');
            expect(comboBox.currentError).toBe('Obsolete value')
        })

        it('Test click enabled value', async function () {
            comboBox.setProps({forceValue: true, modelValue: 'Value X'})
            await vueTicks()

            await openDropdown();

            await clickMenuItem('Value B');
            await vueTicks();

            expect(comboBox.vm.modelValue).toEqual('Value B');
            expect(comboBox.currentError).toBe('')
        })

        it('Test click disabled value when multiselect', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks()
            comboBox.setProps({forceValue: true, modelValue: ['Value C', 'Value X', 'Hi']})
            await vueTicks()

            await openDropdown()

            await clickMenuItem('Value X');
            await closeDropdown()

            expect(comboBox.vm.modelValue).toEqual(['Value C', 'Value X', 'Hi']);
            expect(comboBox.currentError).toBe('Obsolete values: Value X,Hi')
        })

        it('Test click enabled value when multiselect', async function () {
            // materialize parity: any user change to the selection drops the
            // forced obsolete values from the emitted value
            setDeepProp(comboBox, 'config.multiselect', true)
            await vueTicks()
            comboBox.setProps({forceValue: true, modelValue: ['Value C', 'Value X', 'Hi']})
            await vueTicks()

            await openDropdown()

            await clickMenuItem('Value A');
            await closeDropdown()

            expect([...comboBox.vm.modelValue].sort()).toEqual(['Value A', 'Value C'])
            expect(comboBox.currentError).toBe('')
        })
    })

    describe('Test loading', function () {
        it('Test set loading true', async function () {
            setDeepProp(comboBox, 'config.loading', true)
            await vueTicks()

            expect(comboBox.get('input').element.disabled).toBe(true)
            expect(comboBox.get('.combobox').classes()).toContain('loading')
            expect(comboBox.find('.v-progress-linear').exists()).toBeTrue()
        })

        it('Test set loading false', async function () {
            setDeepProp(comboBox, 'config.loading', true)
            await vueTicks()
            setDeepProp(comboBox, 'config.loading', false)
            await vueTicks()

            expect(comboBox.get('input').element.disabled).toBe(false)
            expect(comboBox.get('.combobox').classes()).not.toContain('loading')
        })
    })
});
