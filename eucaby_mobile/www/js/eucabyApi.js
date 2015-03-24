'use strict';

/*
Module to perform the following operations:
    - Requests to Eucaby API and Facebook API services
	- Manage access token and related parameters
 */

angular.module('eucaby.api', ['openfb', 'eucaby.utils'])

.constant('ENDPOINT', 'http://api.eucaby-dev.appspot.com')

.factory('EucabyApi', ['$http', '$q', 'OpenFB', 'utils', 'ENDPOINT',
         function ($http, $q, OpenFB, utils, ENDPOINT) {

    var runningInCordova = false;
    var storage;
    $http.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded';

    document.addEventListener('deviceready', function () {
        runningInCordova = true;
    }, false);

    var storageManager = {
        saveAuth: function(data){
            storage.setItem('ec_access_token', data.access_token);
            storage.setItem('ec_refresh_token', data.refresh_token);
            delete storage.fbtoken;
        },
        getRefreshToken: function(){
            return storage.getItem('ec_refresh_token');
        },
        getFbToken: function(){
            // Storage in openfb-angular module has different interface
            // from localStorage so we look up by key
            return storage.fbtoken;
        },
        getAccessToken: function(){
            return storage.getItem('ec_access_token');
        },
        clearAuth: function(){
            storage.removeItem('ec_access_token');
            storage.removeItem('ec_refresh_token');
            delete storage.fbtoken;
        }
    };

    return {
        init: function(storage_){
            storage = storage_;
            OpenFB.init('809426419123624',
                        'http://localhost:8100/oauthcallback.html', storage_);
        },
        login: function(force){
            var deferred = $q.defer();
            var accessToken = storageManager.getAccessToken();
            if (accessToken && !force) {
                deferred.resolve(accessToken);
            } else {
                var fb_access_token = storageManager.getFbToken();
                /*
                Steps:
                    - Get short-lived Facebook access token
                    - Get Facebook user id with '/me' request to get user id
                    - Get Eucaby access token
                 */
                var ecLoginSuccess = function(data) {
                    // Success callback for Eucaby authentication
                    storageManager.saveAuth(data);
                    deferred.resolve(data);
                };

                var fbProfileSuccess = function(data){
                    // Success callback for Facebook user profile
                    var fb_user_id = data.data.id;
                    var params = {
                        service: 'facebook', grant_type: 'password',
                        username: fb_user_id, password: fb_access_token};
                    // Authenticate with Eucaby service
                    $http.post(ENDPOINT + '/oauth/token', utils.toPostData(params))
                        .success(ecLoginSuccess)
                        .error(function(data, status, headers, config) {
                            deferred.reject(data);
                        });
                };

                var fbLoginSuccess = function() {
                    // Success callback for Facebook authentication
                    OpenFB.get('/me').then(fbProfileSuccess,
                        function(data){
                            deferred.reject(data);
                        });
                };

                OpenFB.login('email,user_friends').then(fbLoginSuccess,
                    function(data) {
                        deferred.reject(data);
                    });
            }
            return deferred.promise;
        },
        api: function(obj){
            var self = this;
            var method = obj.method || 'GET';
            var params = obj.params || {};
            var data = obj.data && utils.toPostData(obj.data) || '';
            var deferred = $q.defer();
            var recoverCount = 0;

            var errorHandler = function(data, status, headers, config){
                deferred.reject(data);
            };
            var apiRequest = function(method, path, token, params){
                return $http({method: method, url: ENDPOINT + path,
                    params: params, data: data,
                    headers: {'Authorization': 'Bearer ' + token}});
            };
            var refreshTokenRequest = function(){
                var refreshToken = storageManager.getRefreshToken();
                if (!refreshToken){
                    deferred.reject('Internal error');
                    return;
                }
                var params = {
                    grant_type: 'refresh_token',
                    refresh_token: refreshToken
                };
                return $http.post(ENDPOINT + '/oauth/token', utils.toPostData(params))
                    .success(makeApiRequest).error(errorHandler);
            };
            var makeApiRequest = function(data){
                var token = data;
                // Parameter data can be either string or an object
                if (angular.isObject(data)){
                    token = data.access_token;
                }
                apiRequest(method, obj.path, token, params)
                    .success(function(data){
                        deferred.resolve(data);
                    })
                    .error(function(data, status, headers, config) {
                        // Note: As an alternative for failed request recovery
                        // you can use httpInterceptors
                        recoverCount++;
                        if (recoverCount > 1) {  // Limit recursion
                            errorHandler(data);
                            return;
                        }
                        // Eucaby access token is invalid - try to login again
                        if (data && data.code === 'invalid_token') {
                            self.login(true).then(makeApiRequest, errorHandler);
                        // Eucaby access token is expired - refresh token
                        } else if (data && data.code === 'token_expired'){
                            refreshTokenRequest();
                        } else {
                            deferred.reject(data);
                        }
                    });
            };

            self.login().then(makeApiRequest, errorHandler);
            return deferred.promise;
        },
        logout: function(){
            storageManager.clearAuth();
            OpenFB.logout();
        }
    };
}]);
