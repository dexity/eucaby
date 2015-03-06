'use strict';

/*
Module to perform the following operations:
    - Requests to Eucaby API and Facebook API services
	- Manage access token and related parameters
 */

angular.module('eucaby.api', ['openfb'])

.constant('ENDPOINT', 'http://api.eucaby-dev.appspot.com')

.factory('EucabyApi', ['$http', '$q', 'OpenFB', 'ENDPOINT',
         function ($http, $q, OpenFB, ENDPOINT) {

    var runningInCordova = false;
    var storage;
    $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";

    document.addEventListener("deviceready", function () {
        runningInCordova = true;
    }, false);

    var storageManager = {
        saveAuth: function(data){
            storage.setItem('ec_access_token', data.access_token);
            storage.setItem('ec_refresh_token', data.refresh_token);
            delete storage.fbtoken;
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
            OpenFB.init('809426419123624', 'http://localhost:8100/oauthcallback.html', storage_);
        },
        login: function(){
            var deferred = $q.defer();
            var accessToken = storage.getItem('ec_access_token');
            if (accessToken) {
                deferred.resolve(accessToken);
            } else {
                // Storage in openfb-angular module has different interface
                // from localStorage so we look up by key
                var fb_access_token = storage.fbtoken;
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
                    var fb_user_id = data.id;
                    var params = {
                        service: 'facebook', grant_type: 'password',
                        username: fb_user_id, password: fb_access_token};
                    var url_params = Object.keys(params).map(function(prop) {
                      return [prop, params[prop]].map(encodeURIComponent).join("=");
                    }).join("&");
                    $http.post(ENDPOINT + '/oauth/token', url_params)
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
            var method = obj.method || 'GET';
            var params = obj.params || {};
            var deferred = $q.defer();
            var accessToken = storage.getItem('ec_access_token'); // XXX: Finish

            $http({method: method, url: ENDPOINT + obj.path,
                          params: params, headers: {'Authorization': 'Bearer ' + accessToken}})
                .success(function(data){
                    deferred.resolve(data);
                })
                .error(function(data, status, headers, config) {
                      // Eucaby access token is invalid
                      // Eucaby access token is expired
//                    if (data.error && data.error.type === 'OAuthException') {
//                        $rootScope.$emit('OAuthException');
//                    }
                });
            return deferred.promise;
        },
        logout: function(){
            storageManager.clearAuth();
            OpenFB.logout();
        }
    };
}]);
