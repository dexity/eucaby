'use strict';

describe('filter tests', function(){

    beforeEach(module('eucaby.filters'));

    it('should capitalize string', inject(function(capitalizeFilter){
        expect(capitalizeFilter('hello world')).toBe('Hello World');
        expect(capitalizeFilter('1world')).toBe('1world');
        expect(capitalizeFilter(' hello world ')).toBe(' Hello World ');
        expect(capitalizeFilter()).toBe('');
    }));

    it('should format username', inject(function(userNameFilter){
        expect(userNameFilter()).toBe('');
        expect(userNameFilter({name: 'A'})).toBe('A');
        expect(userNameFilter({email: 'B'})).toBe('B');
        expect(userNameFilter({name: 'A', email: 'B'})).toBe('A');
    }));
});