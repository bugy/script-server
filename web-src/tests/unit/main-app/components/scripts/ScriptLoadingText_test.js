'use strict';
import ScriptLoadingText, {__RewireAPI__ as CommonRewire} from '@/main-app/components/scripts/ScriptLoadingText';
import {mount} from '@vue/test-utils';
import {config as chaiConfig} from 'chai';
import {timeout, vueTicks} from '../../../test_utils';

chaiConfig.truncateThreshold = 0;

const DEFAULT_DELAY = 10;

function rewireRandomInt(newRandom) {
    CommonRewire.__Rewire__('randomInt', newRandom);
}

describe('Test ScriptLoadingText', function () {
    let loadingText;

    beforeEach(function () {
        loadingText = mount(ScriptLoadingText, {
            attachToDocument: true,
            props: {
                delay: DEFAULT_DELAY
            }
        });
    });

    afterEach(function () {
        loadingText.destroy();
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
