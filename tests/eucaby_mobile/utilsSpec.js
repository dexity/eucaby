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

    it('should sort array by key', function () {
        // Empty array
        expect(utils.sortByKey([], 'name')).toEqual([]);
        // Array of strings doesn't get altered
        expect(utils.sortByKey(['b', 'a'], 'name')).toEqual(['b', 'a']);
        // Array item has no key
        expect(utils.sortByKey([{x: 'b'}, {x: 'a'}], 'name'))
            .toEqual([{x: 'b'}, {x: 'a'}]);
        // Array is sorted by key
        expect(utils.sortByKey([{name: 'b'}, {name: 'A'}], 'name')).toEqual(
            [{name: 'A'}, {name: 'b'}]);
        // Sort is not natural
        expect(utils.sortByKey([{name: '10'}, {name: '2'}], 'name')).toEqual(
            [{name: '10'}, {name: '2'}]);
    });

    it('should format messages', inject(function(_storageManager_){
        var storageManager = _storageManager_;
        var formatter = function(item) {
            return {
                description: item.name,
                name: item.name,
                notification_url: '#/notification/' + item.id,
                request_url: '#/request/' + item.id
            }
        };
        var data = [{
            id: 1, type: 'notification', session: {complete: false},
            name: 'test1', message: null
        }, {
            id: 2, type: 'notification', session: {complete: true},
            name: 'test2', message: 'msg2'
        }, {
            id: 3, type: 'request', session: {complete: false},
            sender: {username: 'user1'}, name: 'test3', message: 'msg3'
        }, {
            id: 4, type: 'request', session: {complete: true},
            sender: {username: 'user2'}, name: 'test4', message: null
        }];
        var expectedRes = [{
            item: data[0], complete: false, name: 'test1', description: 'test1',
            message: '', url: '#/notification/1',
            icon: 'ion-ios-location-outline'
        }, {
            item: data[1], complete: true, name: 'test2', description: 'test2',
            message: 'msg2', url: '#/notification/2',
            icon: 'ion-ios-location'
        }, {
            // Note: url is empty because request is not complete and request
            //       user is the current user
            item: data[2], complete: false, name: 'test3', description: 'test3',
            message: 'msg3', url: '', icon: 'ion-ios-bolt-outline'
        }, {
            item: data[3], complete: true, name: 'test4', description: 'test4',
            message: '', url: '#/request/4', icon: 'ion-ios-bolt'
        }];
        // user1 is the logged in user
        spyOn(storageManager, 'getCurrentUsername').and.returnValue('user1');

        // Stub formatter
        var res = utils.formatMessages(data, function(item){return {}});
        expect(res).toEqual(jasmine.arrayContaining([{
            item: data[2], complete: false, name: '', description: '',
            message: 'msg3', url: '', icon: 'ion-ios-bolt-outline'
        }]));
        storageManager.getCurrentUsername.calls.reset();

        // Valid formatter
        var res = utils.formatMessages(data, formatter);
        expect(storageManager.getCurrentUsername).toHaveBeenCalled();
        expect(res).toEqual(expectedRes);
    }));

    it('should find index of the field', function(){
        // Empty array
        expect(utils.indexOfField([], 'name', 'a')).toEqual(-1);
        // Array has no object with name field
        expect(utils.indexOfField([{x: 'a'}], 'name', 'a')).toEqual(-1);
        // Array has object with name field and it has matching value
        expect(utils.indexOfField([{name: 'b'}], 'name', 'a')).toEqual(-1);
        // Array has object with matching value and it returns the first match
        expect(utils.indexOfField([{name: 'b'}, {name: 'a'}, {name: 'a'}],
                                  'name', 'a')).toEqual(1);
    });

    it('should move recent contact to friends', function(){
        var recentFriends = {
            user1: {name: 'User 1', username: 'user1'},
            user2: {name: 'User 2', username: 'user2'}
        };
        var friends = [
            {name: 'User X', username: 'userx'}];
        var recentFriends1 = angular.copy(recentFriends);
        var friends1 = angular.copy(friends);

        var cases = [
            'user3',  // Friend is in recent but username is not
            'userx'   // Friend is not in recent
        ];
        for (var i = 0; i < cases.length; i++) {
            // No change
            utils.moveRecentToFriends(recentFriends1, friends1, cases[i]);
            expect(recentFriends1).toEqual(recentFriends);
            expect(friends1).toEqual(friends);
        }
        // Friend and username are in recent
        utils.moveRecentToFriends(recentFriends1, friends1, 'user2');
        // user2 will be removed from recent and prepended to friends list
        expect(recentFriends1).toEqual({
            user1: {name: 'User 1', username: 'user1'}
        });
        expect(friends1).toEqual([
            {name: 'User 2', username: 'user2'},
            {name: 'User X', username: 'userx'}
        ]);
    });

    it('should move friend to recent contact', function(){

    });

    it('should sync friend with recent contacts', function(){

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

