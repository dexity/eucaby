'use strict';

describe('utils tests', function(){

    beforeEach(module('eucaby.utils'));

    it('should serialize data', inject(function(utils){
        expect(utils.toPostData({testA: 'A', testB: 'B'}))
            .toBe('testA=A&testB=B');
        expect(utils.toPostData({})).toBe('');
        expect(utils.toPostData(undefined)).toBe('');
    }));

});