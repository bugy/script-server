'use strict';

import Combobox from '@/common/components/combobox'
import {contains} from '@/common/utils/common';
import {mount} from '@vue/test-utils';
import {
    attachToDocument,
    flushPromises,
    setDeepProp,
    timeout,
    triggerSingleClick,
    vueTicks,
    wrapVModel
} from './test_utils';


describe('Test ComboBox', function () {
    let comboBox;

    beforeEach(async function () {
        comboBox = mount(Combobox, {
            attachTo: attachToDocument(),
            propsData: {
                config: {
                    required: false,
                    name: 'List param X',
                    description: 'some param',
                    values: ['Value A', 'Value B', 'Value C'],
                    multiselect: false
                },
                value: 'Value B',
                forceValue: false
            }
        });
        comboBox.vm.$parent.$forceUpdate();
        await comboBox.vm.$nextTick();

        wrapVModel(comboBox);
    });

    afterEach(async function () {
        await vueTicks();
        comboBox.destroy();
    });

    function assertListElements(expectedTexts, searchHeader = false, showHeader = true) {
        const listChildren = comboBox.findAll('li');

        const extraChildrenCount = showHeader ? 1 : 0;

        expect(listChildren).toHaveLength(expectedTexts.length + extraChildrenCount);

        const headerText = listChildren.at(0).text();
        if (!searchHeader) {
            if (showHeader) {
                expect(headerText).toStartWith('Choose your option');
            }
        } else {
            expect(headerText.trim()).toBe('Search');
        }

        for (let i = 0; i < expectedTexts.length; i++) {
            const value = expectedTexts[i];
            expect(listChildren.at(i + extraChildrenCount).text()).toBe(value);
        }
    }

    async function openDropdown() {
        comboBox.get('.dropdown-trigger').trigger('click');

        await timeout(50);
    }

    async function closeDropdown() {
        comboBox.vm.comboboxWrapper.dropdown.options.outDuration = 1;

        triggerSingleClick(document.body)

        await timeout(50)
    }

    function findSelectedOptions() {
        return comboBox.findAll('option').filter(option => option.element.selected);
    }

    function assertNoSelection() {
        expect(comboBox.vm.value).toBeNull();
        expect(comboBox.get('.selected').text()).toBe('Choose your option');
        expect(findSelectedOptions()).toHaveLength(1);
    }

    describe('Test config', function () {

        it('Test initial name', function () {
            expect(comboBox.get('select').attributes('id')).toBe('List param X');
            expect(comboBox.get('label').text()).toBe('List param X');
        });

        it('Test change name', async function () {
            setDeepProp(comboBox, 'config.name', 'testName1');

            await vueTicks();

            expect(comboBox.get('select').attributes('id')).toBe('testName1');
            expect(comboBox.get('label').text()).toBe('testName1');
        });

        it('Test initial required', function () {
            expect(comboBox.get('select').attributes('required')).toBeFalsy();
        });

        it('Test change required', async function () {
            setDeepProp(comboBox, 'config.required', true);

            await vueTicks();

            expect(comboBox.get('select').attributes('required')).toBe('required');
        });

        it('Test initial description', function () {
            expect(comboBox.element.title).toBe('some param');
        });

        it('Test change description', async function () {
            setDeepProp(comboBox, 'config.description', 'My new desc');

            await vueTicks();

            expect(comboBox.element.title).toBe('My new desc');
        });

        it('Test initial multiselect', function () {
            expect(comboBox.find('select').attributes('multiple')).toBeNil();

            const listElement = comboBox.get('ul');
            expect(listElement.classes()).not.toContain('multiple-select-dropdown');
        });


        it('Test initial allowed values', function () {
            const values = ['Value A', 'Value B', 'Value C'];

            assertListElements(values);
        });

        it('Test change allowed values', async function () {
            const values = ['val1', 'val2', 'hello', 'another option'];
            setDeepProp(comboBox, 'config.values', values);

            await vueTicks();

            assertListElements(values);
        });

        it('Test hide header', async function () {
            comboBox.setProps({showHeader: false})
            await vueTicks();

            assertListElements(['Value A', 'Value B', 'Value C'], false, false);
        });
    });

    describe('Test values', function () {

        it('Test initial value', async function () {
            await vueTicks();

            expect(comboBox.vm.value).toBe('Value B');

            const selectedOption = comboBox.find('.selected').text();
            expect(selectedOption).toBe('Value B');
        });

        it('Test external value change', async function () {
            comboBox.setProps({value: 'Value C'});

            await vueTicks();

            expect(comboBox.vm.value).toBe('Value C');

            const selectedOption = comboBox.get('.selected').text();
            expect(selectedOption).toBe('Value C');
        });

        it('Test select another value', async function () {
            comboBox.get('select').setValue('Value A');

            await vueTicks();

            expect(comboBox.vm.value).toBe('Value A');

            const selectedOption = comboBox.get('.selected').text();
            expect(selectedOption).toBe('Value A');
        });

        it('Test set unknown value', async function () {
            comboBox.setProps({value: 'Xyz'});

            await vueTicks();

            assertNoSelection()
        });

        it('Test set multiselect single value', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({value: 'Value A'});

            await vueTicks();
            expect(comboBox.vm.value).toEqual(['Value A']);
            expect(comboBox.get('.selected').text()).toBe('Value A');
        });

        it('Test set multiselect multiple values', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({value: ['Value A', 'Value C']});

            await vueTicks();
            expect(comboBox.vm.value).toEqual(['Value A', 'Value C']);

            const selectedElements = findSelectedOptions();
            expect(selectedElements).toHaveLength(2);
            expect(selectedElements.at(0).text()).toBe('Value A');
            expect(selectedElements.at(1).text()).toBe('Value C');
        });

        it('Test set multiselect single unknown value', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({value: ['Value X']});

            await vueTicks();
            expect(comboBox.vm.value).toEqual([]);
            expect(comboBox.get('.selected').text()).toBe('Choose your options');
        });

        it('Test set multiselect unknown value from multiple', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks();

            comboBox.setProps({value: ['Value A', 'Value X']});

            await vueTicks();
            expect(comboBox.vm.value).toEqual(['Value A']);
            expect(comboBox.get('.selected').text()).toBe('Value A');
        });

        it('Test select multiple values in multiselect without closing', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks()

            await openDropdown()

            triggerSingleClick(getDropdownElement().childNodes[1])
            triggerSingleClick(getDropdownElement().childNodes[2])
            triggerSingleClick(getDropdownElement().childNodes[3])

            await vueTicks()

            expect(comboBox.vm.value).toEqual(['Value A', 'Value C'])

            const selectedElements = findSelectedOptions();
            expect(selectedElements).toHaveLength(2);
            expect(selectedElements.at(0).text()).toBe('Value A');
            expect(selectedElements.at(1).text()).toBe('Value C');
        });

        it('Test select multiple values in multiselect with closing', async function () {
            setDeepProp(comboBox, 'config.multiselect', true)
            await vueTicks()

            await openDropdown()

            triggerSingleClick(getDropdownElement().childNodes[1])
            triggerSingleClick(getDropdownElement().childNodes[2])
            triggerSingleClick(getDropdownElement().childNodes[3])

            await closeDropdown()

            expect(comboBox.vm.value).toEqual(['Value A', 'Value C'])

            const selectedElements = findSelectedOptions()
            expect(selectedElements).toHaveLength(2)
            expect(selectedElements.at(0).text()).toBe('Value A')
            expect(selectedElements.at(1).text()).toBe('Value C')
        });

        it('Test change allowed values with matching value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'Value B', 'another option']);

            await vueTicks();

            expect(comboBox.vm.value).toBe('Value B');
            expect(comboBox.get('.selected').text()).toBe('Value B');
        });

        it('Test change allowed values with unmatching value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'another option']);

            await vueTicks();

            expect(comboBox.vm.value).toBeNull();
            expect(comboBox.get('.selected').text()).toBe('Choose your option');
        });

        it('Test change allowed values and then a value', async function () {
            setDeepProp(comboBox, 'config.values', ['val1', 'val2', 'hello', 'another option']);
            comboBox.setProps({value: 'val2'});

            await vueTicks();

            expect(comboBox.vm.value).toBe('val2');
            expect(comboBox.get('.selected').text()).toBe('val2');
        });
    });

    describe('Test errors', function () {
        it('Test set external empty value when required', async function () {
            setDeepProp(comboBox, 'config.required', true);
            await vueTicks();

            comboBox.setProps({value: ''});

            await vueTicks();

            expect(comboBox.currentError).toBe('required');
        });

        it('Test unselect combobox when required', async function () {
            setDeepProp(comboBox, 'config.required', true);
            await vueTicks();

            comboBox.get('select').setValue('');

            await vueTicks();

            expect(comboBox.currentError).toBe('required');
        });

        it('Test set external value after empty', async function () {
            setDeepProp(comboBox, 'config.required', true);
            comboBox.setProps({value: ''});
            await vueTicks();

            comboBox.setProps({value: 'Value A'});
            await vueTicks();

            expect(comboBox.currentError).toBe('');
        });
    });

    function getSearchElement() {
        return getDropdownElement().childNodes[0]
    }

    function getDropdownElement() {
        return comboBox.get('.dropdown-content').element;
    }

    describe('Test search', function () {
        async function makeSearchable() {
            const values = Array(20).fill(0).map((v, i) => 'Value ' + i);
            setDeepProp(comboBox, 'config.values', values);
            await vueTicks();

            comboBox.vm.comboboxWrapper.dropdown.options.inDuration = 1;
            comboBox.vm.comboboxWrapper.dropdown.options.outDuration = 1;

            return values;
        }

        function assertVisible(element, visible) {
            const displayStyle = window.getComputedStyle(element).display;

            if (visible) {
                expect(displayStyle).not.toBe('none');
            } else {
                expect(displayStyle).toBe('none');
            }
        }

        function assertVisibleItems(combobox, expectedVisible) {
            const [header, ...listItems] = combobox.findAll('li').wrappers;

            expect(header.classes()).not.toContain('search-hidden');

            for (const listItem of listItems) {
                const text = listItem.text();

                const shouldBeVisible = contains(expectedVisible, text);
                if (shouldBeVisible) {
                    expect(listItem.classes()).not.toContain('search-hidden');
                } else {
                    expect(listItem.classes()).toContain('search-hidden');
                }
            }
        }

        it('Test show search field', async function () {
            const values = await makeSearchable();

            assertListElements(values, true);
        });

        it('Test show search field when one element disabled', async function () {
            const values = await makeSearchable()
            comboBox.setProps({value: 'Xyz', forceValue: true})

            await vueTicks()
            await flushPromises()

            assertListElements(['Xyz'].concat(values), true)
        });

        it('Test focus search field on open', async function () {
            await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');
            expect(document.activeElement).toBe(searchInput.element);
        });

        it('Test keep open on search click', async function () {
            await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');
            searchInput.trigger('click');

            await timeout(50);

            assertVisible(getDropdownElement(), true);
        });

        it('Test close on item click', async function () {
            await makeSearchable();

            await openDropdown();

            const firstItem = getDropdownElement().childNodes[1];
            triggerSingleClick(firstItem);

            await timeout(50);

            assertVisible(getDropdownElement(), false);
        });

        it('Test filter on search', async function () {
            await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');
            searchInput.setValue('2');

            await vueTicks();

            assertVisibleItems(comboBox, ['Value 2', 'Value 12']);
        });

        it('Test filter on search second input', async function () {
            await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');

            searchInput.setValue('2');
            await vueTicks();

            searchInput.setValue('12');
            await vueTicks();

            assertVisibleItems(comboBox, ['Value 12']);
        });

        it('Test filter on search clear input', async function () {
            const values = await makeSearchable();

            await openDropdown();

            const searchInput = comboBox.get('.dropdown-content input');

            searchInput.setValue('2');
            await vueTicks();

            searchInput.setValue('');
            await vueTicks();

            assertVisibleItems(comboBox, values);
        });
    });

    describe('Test forced values', function () {
        it('Test initial forced value', async function () {
            comboBox.setProps({forceValue: true, value: 'Value X'})

            await vueTicks()

            expect(comboBox.vm.value).toEqual('Value X')
            const selectedOption = comboBox.get('.selected')
            expect(selectedOption.text()).toBe('Value X')
            expect(selectedOption.classes()).toContain('disabled')
            expect(comboBox.currentError).toBe('Obsolete value')
            assertListElements(['Value X', 'Value A', 'Value B', 'Value C'])
        })

        it('Test set forcedValue to false when wrong value', async function () {
            comboBox.setProps({value: 'Value X', forceValue: true})
            await vueTicks()

            comboBox.setProps({forceValue: false})
            await vueTicks()

            assertNoSelection()
            assertListElements(['Value A', 'Value B', 'Value C'])
            expect(comboBox.currentError).toBeEmpty()
        })

        it('Test set forcedValue to false when wrong value and multiselect', async function () {
            setDeepProp(comboBox, 'config.multiselect', true)
            comboBox.setProps({value: ['Value X'], forceValue: true})
            await vueTicks()

            await openDropdown()

            comboBox.setProps({forceValue: false})
            await vueTicks()

            expect(comboBox.vm.value).toEqual(['Value X'])
            const selectedOption = comboBox.get('.selected')
            expect(selectedOption.text()).toBe('Value X');
            expect(selectedOption.classes()).toContain('disabled')
            expect(comboBox.currentError).toBe('Obsolete value')

            assertListElements(['Value X', 'Value A', 'Value B', 'Value C'])
        })

        it('Test set forcedValue to false when wrong value and multiselect, after close dropdown', async function () {
            setDeepProp(comboBox, 'config.multiselect', true)
            comboBox.setProps({value: ['Value X'], forceValue: true})
            await vueTicks()

            await openDropdown()

            comboBox.setProps({forceValue: false})
            await vueTicks()

            await closeDropdown()

            expect(comboBox.vm.value).toEqual([])
            const selectedOption = comboBox.get('.selected')
            expect(selectedOption.text()).toBe('Choose your options');
            expect(comboBox.currentError).toBe('')
            assertListElements(['Value A', 'Value B', 'Value C'])
        })

        it('Test initial forced value when values change', async function () {
            comboBox.setProps({forceValue: true})
            await vueTicks()

            setDeepProp(comboBox, 'config.values', ['New 1', 'New 2'])
            await vueTicks()

            expect(comboBox.vm.value).toEqual('Value B');
            const selectedOption = comboBox.get('.selected')
            expect(selectedOption.text()).toBe('Value B')
            expect(selectedOption.classes()).toContain('disabled')
            expect(comboBox.currentError).toBe('Obsolete value')
            assertListElements(['Value B', 'New 1', 'New 2'])
        })

        it('Test initial forced value when values change to allowed', async function () {
            comboBox.setProps({forceValue: true, value: 'New 2'})
            await vueTicks()

            setDeepProp(comboBox, 'config.values', ['New 1', 'New 2'])
            await vueTicks()

            expect(comboBox.vm.value).toEqual('New 2');
            const selectedOption = comboBox.get('.selected')
            expect(selectedOption.text()).toBe('New 2')
            expect(selectedOption.attributes('disabled')).toBeFalsy()
            expect(comboBox.currentError).toBeEmpty()
            assertListElements(['New 1', 'New 2'])
        })

        it('Test initial forced values when multiselect', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks()
            comboBox.setProps({forceValue: true, value: ['Value C', 'Value X', 'Hi']})
            await vueTicks()

            expect(comboBox.vm.value).toEqual(['Value C', 'Value X', 'Hi']);

            const selectedElements = findSelectedOptions();
            expect(selectedElements).toHaveLength(3);
            expect(selectedElements.at(0).text()).toBe('Value X');
            expect(selectedElements.at(1).text()).toBe('Hi');
            expect(selectedElements.at(2).text()).toBe('Value C');
            expect(comboBox.currentError).toBe('Obsolete values: Value X,Hi')
            assertListElements(['Value X', 'Hi', 'Value A', 'Value B', 'Value C'])
        })

        it('Test click disabled value', async function () {
            comboBox.setProps({forceValue: true, value: 'Value X'})
            await vueTicks()

            await openDropdown();

            const firstItem = getDropdownElement().childNodes[1];
            triggerSingleClick(firstItem);

            await timeout(50);

            expect(comboBox.vm.value).toEqual('Value X');
            expect(comboBox.currentError).toBe('Obsolete value')
        })

        it('Test click enabled value', async function () {
            comboBox.setProps({forceValue: true, value: 'Value X'})
            await vueTicks()

            await openDropdown();

            const enabledItem = getDropdownElement().childNodes[3];
            triggerSingleClick(enabledItem);

            await timeout(50);

            expect(comboBox.vm.value).toEqual('Value B');
            expect(comboBox.currentError).toBe('')
        })

        it('Test click disabled value when multiselect', async function () {
            setDeepProp(comboBox, 'config.multiselect', true);
            await vueTicks()
            comboBox.setProps({forceValue: true, value: ['Value C', 'Value X', 'Hi']})
            await vueTicks()

            await openDropdown()

            triggerSingleClick(getDropdownElement().childNodes[1])

            await closeDropdown()

            expect(comboBox.vm.value).toEqual(['Value C', 'Value X', 'Hi']);
            expect(comboBox.currentError).toBe('Obsolete values: Value X,Hi')
        })

        it('Test click enabled value when multiselect', async function () {
            setDeepProp(comboBox, 'config.multiselect', true)
            await vueTicks()
            comboBox.setProps({forceValue: true, value: ['Value C', 'Value X', 'Hi']})
            await vueTicks()

            await openDropdown()

            triggerSingleClick(getDropdownElement().childNodes[3])

            await closeDropdown()

            expect(comboBox.vm.value).toEqual(['Value A', 'Value C'])
            expect(comboBox.currentError).toBe('')
        })
    })

    describe('Test loading', function () {
        it('Test set loading true', async function () {
            setDeepProp(comboBox, 'config.loading', true)
            await vueTicks()

            const input = comboBox.get('input.dropdown-trigger')
            expect(input.attributes('disabled')).toBe('')

            const dropdownArrow = comboBox.get('svg')
            expect(dropdownArrow.element).not.toBeVisible()

            const spinner = comboBox.get('.loading-spinner')
            expect(spinner.element).toBeVisible()
        })

        it('Test set loading false', async function () {
            setDeepProp(comboBox, 'config.loading', true)
            await vueTicks()
            setDeepProp(comboBox, 'config.loading', false)
            await vueTicks()

            const input = comboBox.get('input.dropdown-trigger')
            expect(input.attributes('disabled')).toBeNil()

            const dropdownArrow = comboBox.get('svg')
            expect(dropdownArrow.element).toBeVisible()

            const spinner = comboBox.find('.loading-spinner')
            expect(spinner.exists()).toBeFalse()
        })
    })
});