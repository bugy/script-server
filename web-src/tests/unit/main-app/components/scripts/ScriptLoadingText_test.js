'use strict';
import {mount} from '@vue/test-utils';
import {attachToDocument, timeout, vueTicks} from '../../../test_utils';

// Vue 3 / Vitest replacement for babel-plugin-rewire: ScriptLoadingText imports
// `randomInt` from common utils to pick loading phrases. Mock just that export
// with a reconfigurable vi.fn (keeping all other real utils via importActual).
const {randomIntMock} = vi.hoisted(() => ({randomIntMock: vi.fn(() => 0)}));
vi.mock('@/common/utils/common', async (importActual) => ({
    ...(await importActual()),
    randomInt: randomIntMock
}));

import ScriptLoadingText from '@/main-app/components/scripts/ScriptLoadingText';

const DEFAULT_DELAY = 10;

function rewireRandomInt(newRandom) {
    randomIntMock.mockImplementation(newRandom);
}

describe('Test ScriptLoadingText', function () {
    let loadingText;

    beforeEach(function () {
        randomIntMock.mockReset();
        randomIntMock.mockImplementation(() => 0);
        loadingText = mount(ScriptLoadingText, {
            attachTo: attachToDocument(),
            props: {
                delay: DEFAULT_DELAY
            }
        });
    });

    afterEach(function () {
        loadingText.unmount();
    });

    describe('Test dynamic loading text', function () {

        it('test initial text', async function () {
            loadingText.setProps({loading: true, delay: 1000});

            await vueTicks();

            expect(loadingText.text()).toBe('Loading ..');
        });

        it('test single text after delay', async function () {
            rewireRandomInt(() => {
                return 3;
            });

            loadingText.setProps({loading: true});

            await timeout(DEFAULT_DELAY * 10 + 50);

            expect(loadingText.text()).toStartWith('Loading ....... thanks for waiting ...');
        });

        it('test 2 texts after delay', async function () {
            let counter = 0;
            rewireRandomInt(() => {
                return counter++;
            });

            loadingText.setProps({loading: true});

            await timeout(DEFAULT_DELAY * 20 + 50);

            expect(loadingText.text()).toStartWith('Loading ....... wait a bit more ........ doing my best ..');
        });

        it('test full text', async function () {
            let counter = 10;
            rewireRandomInt(() => {
                return counter--;
            });

            loadingText.setProps({loading: true});

            await timeout(DEFAULT_DELAY * 40 + 50);

            expect(loadingText.text()).toBe(
                'Loading ....... almost done ........ patience is power ......... '
                + 'some bits got stuck .......... loading time is unknown');
        });

        it('test reset after script change', async function () {
            loadingText.setProps({loading: true});
            await timeout(DEFAULT_DELAY * 5);

            loadingText.setProps({script: 'script 2', delay: 1000});

            await vueTicks();

            expect(loadingText.text()).toBe('Loading ..');
        });

        it('test reset after script change twice', async function () {
            loadingText.setProps({loading: true});
            await timeout(DEFAULT_DELAY * 5);

            loadingText.setProps({script: 'script 2', delay: 1});

            await timeout(20);

            loadingText.setProps({script: 'script 3', delay: 1000});

            await vueTicks();

            expect(loadingText.text()).toBe('Loading ..');
        });
    })
});
