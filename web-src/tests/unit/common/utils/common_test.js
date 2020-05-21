'use strict';

import {randomInt, trimTextNodes} from '@/common/utils/common';

describe('Test common.js', function () {

    describe('test randomInt', function () {

        it('Test range of 5, starting with 0', function () {
            let values = new Set();
            for (let i = 0; i < 10000; i++) {
                values.add(randomInt(0, 5));
            }

            expect(values).toEqual(new Set([0, 1, 2, 3, 4]));
        });

        it('Test range of 5, starting with positive', function () {
            let values = new Set();
            for (let i = 0; i < 10000; i++) {
                values.add(randomInt(123, 128));
            }

            expect(values).toEqual(new Set([123, 124, 125, 126, 127]));
        });

        it('Test range of 5, starting with negative', function () {
            let values = new Set();
            for (let i = 0; i < 10000; i++) {
                values.add(randomInt(-128, -123));
            }

            expect(values).toEqual(new Set([-128, -127, -126, -125, -124]));
        });

        it('Test range of 5, with 0 in the middle', function () {
            let values = new Set();
            for (let i = 0; i < 10000; i++) {
                values.add(randomInt(-2, 3));
            }

            expect(values).toEqual(new Set([-2, -1, 0, 1, 2]));
        });

        it('Test range of 2', function () {
            let values = new Set();
            for (let i = 0; i < 10000; i++) {
                values.add(randomInt(3, 5));
            }

            expect(values).toEqual(new Set([3, 4]));
        });

        it('Test range of 1', function () {
            let values = new Set();
            for (let i = 0; i < 100; i++) {
                values.add(randomInt(3, 4));
            }

            expect(values).toEqual(new Set([3]));
        });

        it('Test range of 0', function () {
            let values = new Set();
            for (let i = 0; i < 100; i++) {
                values.add(randomInt(3, 3));
            }

            expect(values).toEqual(new Set([3]));
        });

        it('Test range of reversed', function () {
            let values = new Set();
            for (let i = 0; i < 10000; i++) {
                values.add(randomInt(6, 2));
            }

            expect(values).toEqual(new Set([6, 5, 4, 3]));
        });

        it('Test range of reversed when negative', function () {
            let values = new Set();
            for (let i = 0; i < 10000; i++) {
                values.add(randomInt(-13, -17));
            }

            expect(values).toEqual(new Set([-13, -14, -15, -16]));
        });
    });

    describe('test trimTextNodes', function () {

        it('Test trim single text node', function () {
            const div = document.createElement('div');
            div.innerHTML = '  \n hello  world !\t '
            trimTextNodes(div);

            expect(div.innerHTML).toBe('hello  world !')
        });

        it('Test trim multiple text nodes', function () {
            const div = document.createElement('div');
            div.innerHTML = '  \n hello  world !\t '
            div.appendChild(document.createTextNode(' another record '))
            div.appendChild(document.createTextNode('+ one more  '))
            trimTextNodes(div);

            expect(div.innerHTML).toBe('hello  world !another record+ one more')
        });

        it('Test trim multiple text nodes with spans', function () {
            const div = document.createElement('div');
            div.innerHTML = '  \n hello  world !\t '

            const child = document.createElement('span');
            child.innerHTML = ' another record ';
            div.appendChild(child)

            div.appendChild(document.createTextNode(' + one more  '))

            trimTextNodes(div);

            expect(div.innerHTML).toBe('hello  world !<span> another record </span>+ one more')
        });
    });
});