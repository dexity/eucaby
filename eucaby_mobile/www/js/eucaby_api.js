'use strict'

angular.module('eucaby.api', [])

.factory('EucabyApi', ['$scope', '$http', '$q', 'OpenFB', function ($scope, $http, $q, OpenFB) {

    var ENDPOINT = 'http://api.eucaby-dev.appspot.com';
    var runningInCordova = false;
    var storage = window.localStorage;
//    var ACCESS_TOKEN =

    document.addEventListener("deviceready", function () {
        runningInCordova = true;
    }, false);

    var provideAccessToken = function(){
        var accessToken = storage.getItem('ec_access_token');



        // FB access token is invalid

        // No Eucaby access token and refresh token
        if (!accessToken){
            OpenFB.login('email,user_friends').then(
                function(data) {
                    // Success
                    var fb_access_token = storage.getItem('fbtoken');
                    console.debug(fb_access_token, data);

//                    $http.post(ENDPOINT + '/oauth/token',
//                               {service: 'facebook', grant_type: 'password',
//                                username: 'FACEBOOK_USER_ID',
//                                password: fb_access_token})
//                        .success(function(data, status, headers, config) {
//                            accessToken = data.access_token;
//                            storage.setItem('ec_access_token', accessToken);
//                            storage.setItem('ec_refresh_token', data.refresh_token);
//
//                        })
//                        .error(function(data, status, headers, config) {
//                            console.log('OpenFB failed: ' + data);
//                        })
                },
                function() {
                    // XXX: Handle FB error
                });
        }
        return accessToken
    }

    return {
        init: function(){
            OpenFB.init('809426419123624', 'http://localhost:8100/oauthcallback.html', storage);
        },
        api: function(obj){
            var method = obj.method || 'GET';
            var params = obj.params || {};
            var accessToken = provideAccessToken();

            return $http({method: method, url: ENDPOINT + obj.path,
                          params: params, headers: {'Authorization': 'Bearer ' + accessToken}})
                .error(function(data, status, headers, config) {
                      // Eucaby access token is invalid
                      // Eucaby access token is expired
//                    if (data.error && data.error.type === 'OAuthException') {
//                        $rootScope.$emit('OAuthException');
//                    }
                })
        },
        login: function(){
            var deferredLogin = $q.defer();
            return deferredLogin.promise;
        },
        logout: function(){

            OpenFB.logout();
        }
    }
 }]);
