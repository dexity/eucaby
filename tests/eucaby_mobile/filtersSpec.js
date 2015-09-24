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

    it('should localize date time', inject(function(localizeFilter){
        var tsDate = new Date(1437338776000);  // July 19, 2015
        jasmine.clock().mockDate(tsDate);  // Mock current date with tsDate
        expect(localizeFilter('2015-07-17T22:43:19.245050+00:00'))
            .toEqual('1 d 22 hr ago');
        expect(localizeFilter('2015-07-17T22:43:19+00:00'))
            .toEqual('1 d 22 hr ago');
        expect(localizeFilter('2015-07-07T22:43:19+00:00'))
            .toEqual('Jul 7, 3:43 pm');
        expect(localizeFilter('2014-07-07T22:43:19+00:00'))
            .toEqual('Jul 7, 2014 3:43 pm');
    }));
});