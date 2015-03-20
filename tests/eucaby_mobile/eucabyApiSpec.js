'use strict';

describe('eucaby api tests', function(){
    var $scope, $window, $httpBackend, OpenFB, $q, EucabyApi;
    var storage = {};
    var authHandler, friendsHandler;
    var FB_PROFILE = {
        data: {
            first_name: 'Test', last_name: 'User', verified: true,
            name: 'Test User', locale: 'en_US', gender: 'male',
            email: 'test@example.com', id: 123,
            link: 'https://www.facebook.com/app_scoped_user_id/12345/',
            timezone: -8, updated_time: '2014-12-06T21:31:50+0000'
    }};
    var EC_AUTH = {
        access_token: 'AABBCC',
        expires_in: 2592000,
        refresh_token: 'ABCABC',
        scope: 'profile history location',
        token_type: 'Bearer'
    };
    var FRIENDS_LIST = {
        data: [
            {name: 'UserA', username: '123'},
            {name: 'UserB', username: '456'}
        ]}
    var ENDPOINT = 'http://api.eucaby-dev.appspot.com';

    beforeEach(module('eucaby.api'));
    beforeEach(inject(function($rootScope, _$window_, _$httpBackend_, _$q_,
                               _OpenFB_, _EucabyApi_){
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        $window = _$window_;
        $q = _$q_;
        OpenFB = _OpenFB_;
        EucabyApi = _EucabyApi_;
    }));
    beforeEach(function(){
        // LocalStorage mock.
        spyOn($window.localStorage, 'getItem').and.callFake(function(key) {
            return storage[key];
        });
        Object.defineProperty(sessionStorage, 'setItem', { writable: true });
        spyOn($window.localStorage, 'setItem').and.callFake(function(key, value) {
            storage[key] = value;
        });
    });
    beforeEach(function(){
        authHandler = $httpBackend.whenPOST(ENDPOINT + '/oauth/token');
        friendsHandler = $httpBackend.whenGET(ENDPOINT + '/friends');
        EucabyApi.init($window.localStorage);
    });

    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
        storage = {};
    });

    it('should init eucaby api', function(){
        spyOn(OpenFB, 'init');
        EucabyApi.init();
        expect(OpenFB.init).toHaveBeenCalled();
    });

    // Login tests
    it('should return error when fb auth fails', function(){
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?error=some_error#');
        };
        var errorHandler = jasmine.createSpy('error');
        EucabyApi.login().then(null, errorHandler);
        $scope.$digest();
        expect(errorHandler).toHaveBeenCalledWith({error: 'some_error'});
    });

    it('should return error when fb profile request fails', function(){
        var deferredGet = $q.defer();
        var errorHandler = jasmine.createSpy('error');
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferredGet.promise;
        };
        // Failed to get Facebook profile
        deferredGet.reject('FB profile error');
        EucabyApi.login().then(null, errorHandler);
        $scope.$digest();
        expect(errorHandler).toHaveBeenCalledWith('FB profile error');
        // Key fbtoken has to be set
        expect($window.localStorage.fbtoken).toBe('some_token');
    });

    it('should return error when eucaby auth fails', function(){
        var deferredGet = $q.defer();
        var authError = {error: 'Server error'};
        var errorHandler = jasmine.createSpy('error');
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferredGet.promise;
        };
        // Facebook profile succeeded
        deferredGet.resolve(FB_PROFILE);
        authHandler.respond(500, authError);
        $httpBackend.expectPOST(ENDPOINT + '/oauth/token')
            .respond(500, authError);
        EucabyApi.login().then(null, errorHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(errorHandler).toHaveBeenCalledWith(authError);
        // Key fbtoken has to be set
        expect($window.localStorage.fbtoken).toBe('some_token');
    });

    it('should successfully login', function(){
        var deferredGet = $q.defer();
        var successHandler = jasmine.createSpy('success');
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferredGet.promise;
        };
        // Facebook profile succeeded
        deferredGet.resolve(FB_PROFILE);
        authHandler.respond(EC_AUTH);
        $httpBackend.expectPOST(ENDPOINT + '/oauth/token').respond(EC_AUTH);
        EucabyApi.login().then(successHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(successHandler).toHaveBeenCalledWith(EC_AUTH);
        expect($window.localStorage.getItem('ec_access_token')).toBe('AABBCC');
        expect($window.localStorage.getItem('ec_refresh_token')).toBe('ABCABC');
        expect($window.localStorage.fbtoken).toBe(undefined);
    });

    // API tests
    it('should call OpenFB.login if access token is not stored', function(){
        var deferred = $q.defer();
        spyOn(OpenFB, 'login').and.returnValue(deferred.promise);
        EucabyApi.api({path: '/friends'});
        expect(OpenFB.login).toHaveBeenCalledWith('email,user_friends');
    });

    it('should login when access token not stored during api request',
        function(){
        var deferred = $q.defer();
        var errorHandler = jasmine.createSpy('error');
        spyOn(OpenFB, 'login').and.returnValue(deferred.promise);
        EucabyApi.api({path: '/friends'}).then(null, errorHandler);
        deferred.reject('Some error');
        $scope.$digest();  // Call this after reject() but before expect()
        expect(errorHandler).toHaveBeenCalledWith('Some error');
    });

    it('should return error when', function(){

    });
    it('should ', function(){

    });
    it('should ', function(){

    });
    it('should ', function(){

    });

    it('should fail during api request', function(){
        storage = {
            ec_access_token: 'some_access_token',
            ec_refresh_token: 'some_refresh_token'
        };
        friendsHandler.respond(500);
        $httpBackend.expectGET(ENDPOINT + '/friends').respond(500);
        EucabyApi.api({path: '/friends'});
        $scope.$digest();
        $httpBackend.flush();
    });

    it('should successfully make api request', function(){
        storage = {
            ec_access_token: 'some_access_token',
            ec_refresh_token: 'some_refresh_token'
        };
        friendsHandler.respond(200, FRIENDS_LIST);
        $httpBackend.expectGET(
            ENDPOINT + '/friends', {Authorization: 'Bearer some_access_token',
                                    Accept: 'application/json, text/plain, */*'})
            .respond(200, FRIENDS_LIST);
        EucabyApi.api({path: '/friends'});
        $scope.$digest();
        $httpBackend.flush();
    });

    /*
    Cases
    - Access token not in storage:
        - Login request returns error
        - Login request returns success

     */
});