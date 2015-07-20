'use strict';

describe('application tests', function(){

    var EucabyApi;

    beforeEach(module('ionic'));
    beforeEach(module('eucaby.api'));
    beforeEach(module('eucaby', function($provide){
        $provide.value('EucabyApi', {
            init: jasmine.createSpy('init')
        });
    }));
    beforeEach(inject(function(_EucabyApi_){
        EucabyApi = _EucabyApi_;
    }));

    it('should init app', function(){
        expect(EucabyApi.init).toHaveBeenCalled();
    });
});
