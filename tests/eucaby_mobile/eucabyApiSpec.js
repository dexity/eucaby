'use strict';

describe('eucaby api tests', function(){
    var $scope, $window, $httpBackend, OpenFB, $q, EucabyApi;
    var storage = {};
    var defaultStorage = {
        ec_access_token: 'some_access_token',
        ec_refresh_token: 'some_refresh_token'
    };
    var authHandler, friendsHandler;
    // Constants
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
        ]};
    var INVALID_TOKEN = {
        code: 'invalid_token',
        message: 'Invalid bearer token'
    };
    var EXPIRED_TOKEN = {
        code: 'token_expired',
        message: 'Bearer token is expired'
    };
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
        spyOn($window.localStorage, 'removeItem').and.callFake(function(key, value) {
            delete storage[key];
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

    // Init test
    it('should init eucaby api', function(){
        // EucabyApi.init() ->
        // OpenFB.init()
        spyOn(OpenFB, 'init');
        EucabyApi.init();
        expect(OpenFB.init).toHaveBeenCalled();
    });

    // Login tests
    it('should return error when fb auth fails', function(){
        // EucabyApi.login() ->
        // OpenFB.oauthCallback() (Facebook access token request failed)

        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?error=some_error#');
        };
        var errorHandler = jasmine.createSpy('error');
        EucabyApi.login().then(null, errorHandler);
        $scope.$digest();
        expect(errorHandler).toHaveBeenCalledWith({error: 'some_error'});
    });

    it('should return error when fb profile request fails', function(){
        // EucabyApi.login() ->
        // OpenFB.oauthCallback() (Facebook access token request success) ->
        // OpenFB.get('/me') (Facebook profile request failed)

        var deferred = $q.defer();
        var errorHandler = jasmine.createSpy('error');
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferred.promise;
        };
        // Failed to get Facebook profile
        deferred.reject('FB profile error');
        EucabyApi.login().then(null, errorHandler);
        $scope.$digest();
        expect(errorHandler).toHaveBeenCalledWith('FB profile error');
        // Key fbtoken has to be set
        expect($window.localStorage.fbtoken).toBe('some_token');
    });

    it('should return error when eucaby auth fails', function(){
        // EucabyApi.login() ->
        // OpenFB.oauthCallback() (Facebook access token request success) ->
        // OpenFB.get('/me') (Facebook profile request success) ->
        // 'POST /oauth/token' (error)

        var deferred = $q.defer();
        var authError = {error: 'Server error'};
        var errorHandler = jasmine.createSpy('error');
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferred.promise;
        };
        // Facebook profile succeeded
        deferred.resolve(FB_PROFILE);
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
        // EucabyApi.login() ->
        // OpenFB.oauthCallback() (Facebook access token request success) ->
        // OpenFB.get('/me') (Facebook profile request success) ->
        // 'POST /oauth/token' (success)

        var deferred = $q.defer();
        var successHandler = jasmine.createSpy('success');
        // Facebook authenticated succeeded
        $window.open = function(){
            OpenFB.oauthCallback('oauthcallback.html?#access_token=some_token');
        };
        OpenFB.get = function(){
            return deferred.promise;
        };
        // Facebook profile succeeded
        deferred.resolve(FB_PROFILE);
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

    it('should use stored access token when login', function(){
        // No external requests are made
        // EucabyApi.login() ->
        // (use stored access token)

        storage = defaultStorage;
        var successHandler = jasmine.createSpy('success');
        EucabyApi.login().then(successHandler);
        $scope.$digest();
        expect(successHandler).toHaveBeenCalledWith('some_access_token');
    });

    // API tests
    it('should call OpenFB.login if access token is not stored', function(){
        // EucabyApi.api() ->
        // EucabyApi.login() ->
        // OpenFB.login()

        var deferred = $q.defer();
        spyOn(OpenFB, 'login').and.returnValue(deferred.promise);
        spyOn(EucabyApi, 'login').and.callThrough();
        EucabyApi.api({path: '/friends'});
        expect(OpenFB.login).toHaveBeenCalledWith('email,user_friends');
        expect(EucabyApi.login).toHaveBeenCalled();
    });

    it('should login when access token not stored during api request',
        function(){
        // EucabyApi.api() ->
        // EucabyApi.login() (error)

        var deferred = $q.defer();
        var errorHandler = jasmine.createSpy('error');
        spyOn(EucabyApi, 'login').and.returnValue(deferred.promise);
        EucabyApi.api({path: '/friends'}).then(null, errorHandler);
        deferred.reject('Some error');
        $scope.$digest();  // Call this after reject() but before expect()
        expect(errorHandler).toHaveBeenCalledWith('Some error');
    });

    it('should successfully make api request when access token is invalid',
       function(){
        // EucabyApi.api() ->
        // 'GET /friends' (invalid_token error) ->
        // EucabyApi.login() (get new access_token) ->
        // 'GET /friends' (friends list)

        storage = defaultStorage;
        friendsHandler.respond(401, INVALID_TOKEN);
        var deferred = $q.defer();
        var successHandler = jasmine.createSpy('success');
        spyOn(EucabyApi, 'login').and.callFake(function(){
            friendsHandler.respond(FRIENDS_LIST);
            $httpBackend.expectGET(
                ENDPOINT + '/friends',
                    {Authorization: 'Bearer AABBCC',
                     Accept: 'application/json, text/plain, */*'});
            return deferred.promise;
        });
        EucabyApi.api({path: '/friends'}).then(successHandler);
        deferred.resolve(EC_AUTH);
        $scope.$digest();
        $httpBackend.flush();
        expect(successHandler).toHaveBeenCalledWith(FRIENDS_LIST);
        expect(EucabyApi.login).toHaveBeenCalled();
    });

    it('should make refresh token request if access token expired',
       function(){
        // Eucaby.api() ->
        // 'GET /friends' (token_expired error) ->
        // 'POST /oauth/token grant_type=refresh_token' (access_token) ->
        // 'GET /friends' (friends list)

        storage = defaultStorage;
        // Using refresh token doesn't do authentication so we can call through.
        spyOn(EucabyApi, 'login').and.callThrough();
        // First friends request fails
        friendsHandler.respond(
            401, {code: 'token_expired', message: 'Bearer token is expired'});
        var successHandler = jasmine.createSpy('success');
        var refreshHandler = authHandler;
        refreshHandler.respond(function(){
            // Change friends response to success friends list
            friendsHandler.respond(FRIENDS_LIST);
            return [200, EC_AUTH];
        });
        // API request succeeds due to refresh request
        EucabyApi.api({path: '/friends'}).then(successHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(EucabyApi.login).toHaveBeenCalled();
        expect(successHandler).toHaveBeenCalledWith(FRIENDS_LIST);
    });

    it('should return error if access token stored without refresh token',
       function(){
        // Eucaby.api() ->
        // 'GET /friends' (token_expired error) ->
        // 'POST /oauth/token grant_type=refresh_token' (no refresh_token)

        // Missing refresh_token in storage causes internal error
        storage = {
            ec_access_token: 'some_access_token'
        };
        spyOn(EucabyApi, 'login').and.callThrough();
        friendsHandler.respond(401, EXPIRED_TOKEN);
        var errorHandler = jasmine.createSpy('error');
        EucabyApi.api({path: '/friends'}).then(null, errorHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(EucabyApi.login).toHaveBeenCalled();
        expect(errorHandler).toHaveBeenCalledWith('Internal error');
    });

    it('should give up when access token request fails during api request',
       function(){
        // Eucaby.api() ->
        // 'GET /friends' (invalid_token error)
        // Eucaby.login() (access_token) ->
        // 'GET /friends' (still invalid_token or any other error)
        // Return the error

        storage = defaultStorage;
        var deferred = $q.defer();
        friendsHandler.respond(401, INVALID_TOKEN);
        var errorHandler = jasmine.createSpy('error');
        // Invalid token causes the actual authentication so can't just
        // call through without patching other requests (Facebook auth,
        // Facebook me, Eucaby auth) so we just fake it. It is a more
        // complicated request than refresh token
        spyOn(EucabyApi, 'login').and.callFake(function(){
            return deferred.promise;
        });
        deferred.resolve(EC_AUTH);
        // Friends list request keeps responding with error so after 2 trials
        // it returns the error.
        EucabyApi.api({path: '/friends'}).then(null, errorHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(errorHandler).toHaveBeenCalledWith(INVALID_TOKEN);
        expect(EucabyApi.login).toHaveBeenCalled();
    });

    it('should give up when refresh token request fails during api request',
       function(){
        // Eucaby.api() ->
        // 'GET /friends' (expired_token error)
        // 'POST /oauth/token grant_type=refresh_token' (access_token) ->
        // 'GET /friends' (still expired_token or any other error)
        // Return the error

        storage = defaultStorage;
        friendsHandler.respond(401, EXPIRED_TOKEN);
        var errorHandler = jasmine.createSpy('error');
        spyOn(EucabyApi, 'login').and.callThrough();
        var refreshHandler = authHandler;
        refreshHandler.respond(EC_AUTH);
        // Friends list request keeps responding with error so after 2 trials
        // it returns the error.
        EucabyApi.api({path: '/friends'}).then(null, errorHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(errorHandler).toHaveBeenCalledWith(EXPIRED_TOKEN);
        expect(EucabyApi.login).toHaveBeenCalled();
    });

    it('should fail during api request', function(){
        // Eucaby.api() ->
        // 'GET /friends' (non-token related error)

        storage = defaultStorage;
        spyOn(EucabyApi, 'login').and.callThrough();
        friendsHandler.respond(500, 'Some internal error');
        var errorHandler = jasmine.createSpy('error');
        // Only two types of error responses can be recovered:
        //  - invalid_token
        //  - token_expired
        // All other errors explicitly fail
        $httpBackend.expectGET(ENDPOINT + '/friends').respond(
            500, 'Some internal error');
        EucabyApi.api({path: '/friends'}).then(null, errorHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(EucabyApi.login).toHaveBeenCalled();
        expect(errorHandler).toHaveBeenCalledWith('Some internal error');
    });

    it('should successfully make api request, typical scenario', function(){
        // Eucaby.api() ->
        // 'GET /friends' (friends list)

        storage = defaultStorage;
        spyOn(EucabyApi, 'login').and.callThrough();
        friendsHandler.respond(FRIENDS_LIST);
        var successHandler = jasmine.createSpy('success');
        $httpBackend.expectGET(
            ENDPOINT + '/friends', {Authorization: 'Bearer some_access_token',
                                    Accept: 'application/json, text/plain, */*'})
            .respond(FRIENDS_LIST);
        EucabyApi.api({path: '/friends'}).then(successHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(EucabyApi.login).toHaveBeenCalled();
        expect(successHandler).toHaveBeenCalledWith(FRIENDS_LIST);
    });

    // Logout tests
    it('should call OpenFB.logout', function(){
        // Eucaby.logout() ->
        // OpenFB.logout()
        storage = defaultStorage;
        spyOn(OpenFB, 'logout').and.callThrough();
        EucabyApi.logout();
        expect(OpenFB.logout).toHaveBeenCalled();
        expect(angular.equals(storage, {})).toBeTruthy();
    });
});