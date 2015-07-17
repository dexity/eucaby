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

        // Friend is not in recent
        var cases = ['user3', 'userx'];
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
        var recentFriends = {
            user1: {name: 'User 1', username: 'user1'}
        };
        var friends = [
            {name: 'User X', username: 'userx'},
            {name: 'User 2', username: 'user2'}];
        var recentFriends1 = angular.copy(recentFriends);
        var friends1 = angular.copy(friends);

        // Friend is not in friends
        var cases = ['user3', 'user1'];
        for (var i = 0; i < cases.length; i++) {
            // No change
            utils.moveFriendToRecent(recentFriends1, friends1, cases[i]);
            expect(recentFriends1).toEqual(recentFriends);
            expect(friends1).toEqual(friends);
        }
        // Friend and username are in friends
        utils.moveFriendToRecent(recentFriends1, friends1, 'user2');
        // user2 will be removed from friends list and added to recent
        expect(recentFriends1).toEqual({
            user1: {name: 'User 1', username: 'user1'},
            user2: {name: 'User 2', username: 'user2'}
        });
        expect(friends1).toEqual([
            {name: 'User X', username: 'userx'}
        ]);
    });

    it('should sync friend with recent contacts', function(){
        var recentFriends1 = {
            user1: {name: 'User 1', username: 'user1'}
        };
        var friends1 = [
            {name: 'User X', username: 'userx'}];
        var recentFriends2 = {
            user1: {name: 'User 1', username: 'user1'},
            user2: {name: 'User 2', username: 'user2'}
        };
        var friends2 = [
            {name: 'User X', username: 'userx'},
            {name: 'User 2', username: 'user2'}];
        // user2 should be removed from friends because it's duplicate of
        // recent friends
        var expectedRecentFriends2 = {
            user1: {name: 'User 1', username: 'user1'},
            user2: {name: 'User 2', username: 'user2'}
        };
        var expectedFriends2 = [
            {name: 'User X', username: 'userx'}];
        var cases = [
            // Empty recent friends and friends
            [{}, [], {}, []],
            // Recent friends has no common friends with friends
            [recentFriends1, friends1, recentFriends1, friends1],
            // Recent friends has common friends with friends
            [recentFriends2, friends2, expectedRecentFriends2, expectedFriends2]
        ];
        for (var i = 0; i< cases.length; i++){
            var c = cases[i];
            utils.syncFriendsWithRecent(c[0], c[1]);
            expect(c[0]).toEqual(c[2]);
            expect(c[1]).toEqual(c[3]);
        }
    });

    it('should manage recent contacts', function(){
        var recentContacts = [],
            recentFriends = {}, recentFriendsCopy,
            friends = [], friendsCopy,
            form = {};
        // Case 1: Empty parameters
        utils.manageRecent(recentContacts, recentFriends, friends, form, '');
        expect(recentContacts).toEqual([]);
        expect(recentFriends).toEqual({});
        expect(friends).toEqual([]);

        // Case 2: Email form
        form = {email: 'some@email'};
        utils.manageRecent(
            recentContacts, recentFriends, friends, form, 'some label');
        expect(recentContacts).toEqual([
           {label: 'some@email', value: 'some@email', model: 'email',
            name: 'email'}]);
        expect(recentFriends).toEqual({});
        expect(friends).toEqual([]);

        // Case 3: Username form
        form = {username: 'user3'}
        recentFriends = {
            user1: {name: 'User 1', username: 'user1'}};
        friends = [
            {name: 'User X', username: 'userx'}];
        recentFriendsCopy = angular.copy(recentFriends);
        friendsCopy = angular.copy(friends);
        utils.manageRecent(
            recentContacts, recentFriends, friends, form, 'some label');
        expect(recentContacts).toEqual([
           {label: 'some label', value: 'user3', model: 'username',
            name: 'user'},
           {label: 'some@email', value: 'some@email', model: 'email',
            name: 'email'}]);
        expect(recentFriends).toEqual(recentFriendsCopy);
        expect(friends).toEqual(friendsCopy);

        // Case 4: Username matches friend
        form = {username: 'user2'};
        recentFriends = {
            user1: {name: 'User 1', username: 'user1'}};
        friends = [
            {name: 'User X', username: 'userx'},
            {name: 'User 2', username: 'user2'}];
        utils.manageRecent(
            recentContacts, recentFriends, friends, form, 'some label');
        expect(recentContacts).toEqual([
           {label: 'some label', value: 'user2', model: 'username',
            name: 'user'},
           {label: 'some label', value: 'user3', model: 'username',
            name: 'user'},
           {label: 'some@email', value: 'some@email', model: 'email',
            name: 'email'}]);
        expect(recentFriends).toEqual({
            user1: {name: 'User 1', username: 'user1'},
            user2: {name: 'User 2', username: 'user2'}});
        expect(friends).toEqual([
            {name: 'User X', username: 'userx'}]);

        // Case 5: Recent contacts have at most 3 items (other items are popped)
        form = {username: 'user1'};
        utils.manageRecent(
            recentContacts, {}, [], form, 'label 1');
        expect(recentContacts).toEqual([
           {label: 'label 1', value: 'user1', model: 'username',
            name: 'user'},
           {label: 'some label', value: 'user2', model: 'username',
            name: 'user'},
           {label: 'some label', value: 'user3', model: 'username',
            name: 'user'}]);
    });
});

describe('date utils tests', function(){

    var dateUtils,
        $window,
        ts1 = 1437116367000,    // July 17, 2015
        ts2 = 1436944091000,    // July 15, 2015
        ts3 = 1404976091000;    // July 10, 2014

    beforeEach(module('eucaby.utils'));
    beforeEach(inject(function(_dateUtils_, _$window_) {
        dateUtils = _dateUtils_;
        $window = _$window_;
    }));

    it('should return time list with days, hours and minutes', function(){
        // Invalid timestamps
        var cases = [null, '', 0, undefined];
        for (var i = 0; i < cases.length; i++){
            expect(dateUtils.timeList(cases[i])).toEqual(null);
        }
        expect(dateUtils.timeList(ts1)).toEqual([16633, 6, 59]);
    });

    it('should determine if show year', function(){
        expect(dateUtils.showYear(ts1, ts2)).toBeFalsy();  // Same year
        expect(dateUtils.showYear(ts1, ts3)).toBeTruthy();  // Different year
    });

    it('should convert timestamp to human date', function(){
        // Do not show year
        expect(dateUtils.ts2hd(ts1)).toEqual('Jul 16, 2015 11:59 pm');
        // Show year
        expect(dateUtils.ts2hd(ts1, false)).toEqual('Jul 16, 11:59 pm');
    });

    it('should convert timestamp to human format', function(){
        // Both timestamps are set and ts1 > ts2
        expect(dateUtils.ts2h(ts1, ts2)).toEqual('');
        // Both timestamps are set
        expect(dateUtils.ts2h(ts2, ts1)).toEqual('1 d 23 hr ago');
        expect(dateUtils.ts2h(ts3, ts1)).toEqual('Jul 10, 2014 12:08 am');
        // Both timestamps are set do not show full date
        expect(dateUtils.ts2h(ts2, ts1, false)).toEqual('1 d 23 hr');
        expect(dateUtils.ts2h(ts3, ts1, false))
            .toEqual('Jul 10, 2014 12:08 am');
        // One timestamps
        var ts1date = new Date(ts1);
        spyOn($window, 'Date').and.callFake(function(){
            return ts1date;
        });
        expect(dateUtils.ts2h(ts2)).toEqual('1 d 23 hr ago');
    });
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

