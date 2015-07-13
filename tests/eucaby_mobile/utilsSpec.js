'use strict';

describe('map tests', function(){
    var map, utils, $window, mapsMock;

    beforeEach(module('eucaby.utils'));
    beforeEach(inject(function(_map_, _utils_, _$window_){
        map = _map_;
        utils = _utils_;
        $window = _$window_;
        // Google maps mock
        $window.google = {
            maps: {
                LatLng: function(lat, lng){
                    return {
                        lat: lat,
                        lng: lng
                    }
                },
                Map: function(el, options){
                    return options;
                },
                Size: function(width, height) {
                    return [width, height];
                },
                Point: function(x, y) {
                    return [x, y];
                },
                Marker: function(options){
                    return options;
                },
                event: {
                    addDomListener: function(el, event, callback){
                        return el;
                    }
                },
                MapTypeId: {
                    ROADMAP: 'ROADMAP'
                }
            }
        };
        mapsMock = $window.google.maps;
        spyOn($window.document, 'getElementById').and.callFake(function(id){
            return id;
        });
    }));

    it('should create map', function(){
        var expectedOptions = {
            center: { lat: 1.2, lng: 3.4 }, zoom: 5, mapTypeId: 'ROADMAP'
        };
        spyOn(mapsMock, 'LatLng').and.callThrough();
        spyOn(mapsMock, 'Map').and.callThrough();
        spyOn(mapsMock.event, 'addDomListener');
        var res = map.createMap('map', 1.2, 3.4, {zoom: 5});
        expect(res).toEqual(expectedOptions);
        expect(mapsMock.LatLng).toHaveBeenCalledWith(1.2, 3.4);
        expect(mapsMock.Map).toHaveBeenCalledWith(
            'map', expectedOptions);
        expect(mapsMock.event.addDomListener).toHaveBeenCalled();
    });

    it('should create marker', function(){
        var mapMock = {
            setCenter: function(position){
                return position;
            }
        };
        spyOn(mapsMock, 'LatLng').and.callThrough();
        spyOn(mapsMock, 'Size').and.callThrough();
        spyOn(mapsMock, 'Point').and.callThrough();
        spyOn(mapsMock, 'Marker');
        map.createMarker(mapMock, 1.2, 3.4, 2);
        expect(mapsMock.LatLng).toHaveBeenCalledWith(1.2, 3.4);
        expect(mapsMock.Size).toHaveBeenCalledWith(31, 41);
        expect(mapsMock.Point).toHaveBeenCalledWith(71, 0);
        expect(mapsMock.Marker).toHaveBeenCalled();

        var cases = [
            {number: -1, is_web: false, x: 3081, y: 0},
            {number: -1, is_web: true, x: 3081, y: 91},
            {number: 1, is_web: false, x: 36, y: 0},
            {number: 1, is_web: true, x: 36, y: 91}
        ];
        for (var i = 0; i < cases.length; i++){
            var c = cases[i];
            map.createMarker(mapMock, 1.2, 3.4, c.number, c.is_web);
            expect(mapsMock.Point).toHaveBeenCalledWith(c.x, c.y);
        }
    });

    it('should clear markers', function() {
        var markerMock = {
            setMap: jasmine.createSpy('setMap')
        };
        var markers = [markerMock, markerMock];
        map.clearMarkers(markers);
        expect(markerMock.setMap.calls.count()).toEqual(2);
        expect(markerMock.setMap).toHaveBeenCalledWith(null);
    });

    it('should set current location', function(){
        var successHandler = jasmine.createSpy();
        var errorHandler = jasmine.createSpy();
        // Success
        var positionMock = spyOn(
            $window.navigator.geolocation, 'getCurrentPosition');
        positionMock.and.callFake(
            function() {
            var pos = {coords: {latitude: 1.2, longitude: 3.4}};
            arguments[0](pos);
        });
        map.currentLocation(successHandler, errorHandler);
        expect(successHandler).toHaveBeenCalledWith(1.2, 3.4);

        // Error
        positionMock.and.callFake(
            function() {
            arguments[1]();
        });
        map.currentLocation(successHandler, errorHandler);
        expect(errorHandler).toHaveBeenCalled();
    });
});

describe('utils tests', function(){
    var map, utils;

    beforeEach(module('eucaby.utils'));
    beforeEach(inject(function(_map_, _utils_) {
        map = _map_;
        utils = _utils_;
    }));

    it('should serialize data', function(){
        expect(utils.toPostData({testA: 'A', testB: 'B'}))
            .toEqual('testA=A&testB=B');
        expect(utils.toPostData({})).toEqual('');
        expect(utils.toPostData(undefined)).toEqual('');
    });

    it('should create activity params', function(){
        var cases = [
            [{}, {message: ''}],  // Empty form
            // Email set
            [{email: 'some@email'}, {message: '', email: 'some@email'}],
            // Email and username are set. Email has preference over username
            [{email: 'some@email', username: 'user'},
             {message: '', email: 'some@email'}],
            // Email, username and token are set. Email has preference over
            // others
            [{email: 'some@email', username: 'user', token: 123},
             {message: '', email: 'some@email'}],
            // Non-empty message
            [{email: 'some@email', message: 'test'},
             {message: 'test', email: 'some@email'}],
            // Username and token are set. Username has preference over token
            [{username: 'user', message: 'test', token: 123},
             {message: 'test', username: 'user'}],
            // Token is set
            [{message: 'test', token: 123},
             {message: 'test', token: 123}],
        ];
        for (var i = 0; i < cases.length; i++){
            var c = cases[i];
            expect(utils.activityParams(c[0])).toEqual(c[1]);
        }
    });

    it('should validate email', function(){
        var i;
        var validEmails = ['hello@world.com', 'he-llo@world.com',
            'hello@world.info', 'hello@world.message', 'some@email', '!@email'];
        var invalidEmails = ['', 'test', '@email', '@email.com'];
        for (i = 0; i < validEmails.length; i++){
            expect(utils.validEmail(validEmails[i])).toBeTruthy();
        }
        for (i = 0; i < invalidEmails.length; i++){
            expect(utils.validEmail(invalidEmails[i])).toBeFalsy();
        }
    });
});

describe('date utils tests', function(){

});

describe('map ionic tests', function(){

});

describe('utils ionic tests', function(){

    beforeEach(module('ionic'));
//    beforeEach(inject(function(_$ionicPopup_){
//        $ionicPopup = _$ionicPopup_;
//    }));

});

describe('storage manager tests', function(){

});

