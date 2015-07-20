'use strict';

describe('services tests', function(){
    var $scope,
        $window,
        $httpBackend,
        $q,
        EucabyApi,
        Friends,
        User,
        Activity,
        Notification,
        Request,
        Settings,
        successHandler,
        errorHandler,
        storage;
    var defaultStorage = {
        ec_access_token: 'some_access_token',
        ec_refresh_token: 'some_refresh_token'
    };
    // Note: This is fake requests
    var FRIENDS_LIST = {
        data: [
            {name: 'UserA', username: '123'},
            {name: 'UserB', username: '456'}
        ]};
    var PROFILE = {
        data: {
            name: 'UserA',
            username: 'user1'
        }
    };
    var SETTINGS = {
        data: {
            email_subscription: true
        }
    };
    var ACTIVITY_LIST = {
        data: [
            {recipient: 'UserA', sender: 'UserB', type: 'request'},
            {recipient: 'UserB', sender: 'UserA', type: 'notification'}
        ]};
    var REQUEST_POST = {
        data: {
            recipient: 'UserA', sender: 'UserB', session: 'S',
            type: 'request'}};
    var REQUEST_GET = {
        data: {
            recipient: 'UserA', sender: 'UserB', session: 'S',
            type: 'request', notifications: ['N1', 'N2']}};
    var NOTIFICATION_POST = {
        data: {
            recipient: 'UserA', sender: 'UserB', session: 'S',
            type: 'notification', location: '1,2'}};
    var NOTIFICATION_GET = {
        data: {
            recipient: 'UserA', sender: 'UserB', session: 'S', request: 'R',
            type: 'notification', location: '1,2'}};
    var ENDPOINT = 'http://api.eucaby-dev.appspot.com';

    beforeEach(module('eucaby.services'));
    beforeEach(module('eucaby.api'));
    beforeEach(inject(function(
        _$rootScope_, _$window_, _$httpBackend_, _$q_, _EucabyApi_, _Friends_,
        _User_, _Activity_, _Notification_, _Request_, _Settings_){
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $window = _$window_;
        $q = _$q_;
        EucabyApi = _EucabyApi_;
        Friends = _Friends_;
        User = _User_;
        Activity = _Activity_;
        Notification = _Notification_;
        Request = _Request_;
        Settings = _Settings_;
        EucabyApi.init($window.localStorage);
    }));
    beforeEach(function() {
        spyOn(EucabyApi, 'api').and.callThrough();
        // LocalStorage mock
        spyOn($window.localStorage, 'getItem').and.callFake(function (key) {
            return storage[key];
        });
        successHandler = jasmine.createSpy('success');
        errorHandler = jasmine.createSpy('error');
        storage = defaultStorage;
    });
    afterEach(inject(function(_$httpBackend_){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    }));

    var cases = [
        {
            // User profile
            it: 'should get user profile',
            url: ENDPOINT + '/me',
            response: PROFILE,
            apiCall: function () {
                return User.profile();
            },
            apiParams: {path: '/me'}
        }, {
            // GET Settings
            it: 'should get user settings',
            url: ENDPOINT + '/settings',
            response: SETTINGS,
            apiCall: function () {
                return Settings.get();
            },
            apiParams: {path: '/settings'}
        }, {
            // POST Settings
            it: 'should post user settings',
            url: ENDPOINT + '/settings',
            response: SETTINGS,
            apiCall: function () {
                return Settings.post({email_subscription: false});
            },
            apiParams: {
                method: 'POST', path: '/settings',
                data: {email_subscription: false}
            }
        }, {
            // Outgoing list
            it: 'should return outgoing list',
            url: ENDPOINT + '/history?type=outgoing',
            response: ACTIVITY_LIST,
            apiCall: function () {
                return Activity.outgoing();
            },
            apiParams: {path: '/history', params: {type: 'outgoing'}}
        }, {
            // Incoming list
            it: 'should return incoming list',
            url: ENDPOINT + '/history?type=incoming',
            response: ACTIVITY_LIST,
            apiCall: function () {
                return Activity.incoming();
            },
            apiParams: {path: '/history', params: {type: 'incoming'}}
        }, {
            // GET Notification
            it: 'should get notification details',
            url: ENDPOINT + '/location/notification/123',
            response: NOTIFICATION_GET,
            apiCall: function () {
                return Notification.get('123');
            },
            apiParams: {path: '/location/notification/123'}
        }, {
            // POST Notification
            it: 'should post notification',
            url: ENDPOINT + '/location/notification',
            response: NOTIFICATION_POST,
            apiCall: function () {
                var form = {email: 'test@example.com', message: 'test'};
                return Notification.post(form, 1, 2);
            },
            apiParams: {
                method: 'POST', path: '/location/notification',
                data: {
                    email: 'test@example.com', latlng: '1,2', message: 'test'
                }
            }
        }, {
            // GET Request
            it: 'should get request details',
            url: ENDPOINT + '/location/request/123',
            response: REQUEST_GET,
            apiCall: function () {
                return Request.get('123');
            },
            apiParams: {path: '/location/request/123'}
        }, {
            // POST Request
            it: 'should post request',
            url: ENDPOINT + '/location/request',
            response: REQUEST_POST,
            apiCall: function () {
                var form = {email: 'test@example.com', message: 'test'};
                return Request.post(form);
            },
            apiParams: {
                method: 'POST', path: '/location/request',
                data: {
                    email: 'test@example.com', message: 'test'
                }
            }
        }, {
            // Friends list
            it: 'should return friends list',
            url: ENDPOINT + '/friends',
            response: FRIENDS_LIST,
            apiCall: function(){
                return Friends.all();
            },
            apiParams: {path: '/friends'}
        }
    ];

    var runTest = function(case_, respType){
        it(case_.it, function(){
            var method = case_.apiParams.method === 'POST' ? 'POST' : 'GET';
            // whenGET or whenPOST
            $httpBackend['when' + method](case_.url).respond(
                respType.statusCode, respType.response);
            $httpBackend['expect' + method](case_.url).respond(
                respType.statusCode, respType.response);
            case_.apiCall().then(successHandler, errorHandler);
            // Note: $scope.$apply() and $scope.$digest() are more or less
            //       equivalent. $scope.$apply() calls $rootScope.$digest()
            //       internally
            // http://www.sitepoint.com/understanding-angulars-apply-digest/
            $scope.$apply();
            $httpBackend.flush();
            if (respType.statusCode === 200){
                expect(successHandler).toHaveBeenCalledWith(respType.response);
            } else {
                expect(errorHandler).toHaveBeenCalledWith(respType.response);
            }
            expect(EucabyApi.api).toHaveBeenCalledWith(case_.apiParams);
        });
    };

    // Iterate over cases
    for (var i = 0; i < cases.length; i++){
        var c = cases[i];

        var respTypes = [{
            statusCode: 200,  // Success
            response: c.response
        }, {
            statusCode: 500,  // Error
            response: 'Some error'
        }];

        for (var j = 0; j < respTypes.length; j++){
            runTest(c, respTypes[j]);
        }
    }

});