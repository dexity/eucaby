'use strict'

angular.module('eucaby.api', ['openfb'])

//.factory('EucabyApi', ['$http', function($http){

.factory('EucabyApi', ['$rootScope', '$http', '$q', '$window', 'OpenFB',
         function ($rootScope, $http, $q, $window, OpenFB) {

    var ENDPOINT = 'http://api.eucaby-dev.appspot.com';
    var runningInCordova = false;
    var storage = window.localStorage;
    var deferredLogin = $q.defer();
    $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
//    var ACCESS_TOKEN =

    document.addEventListener("deviceready", function () {
        runningInCordova = true;
    }, false);

    var provideAccessToken = function(){
        var accessToken = storage.getItem('ec_access_token');

        // FB access token is invalid

        // No Eucaby access token and refresh token
        if (accessToken) {
            deferredLogin.resolve();
            return accessToken;
        }

        /*
        Steps:
            - Get short-lived Facebook access token
            - Get Facebook user id with '/me' request
            - Get Eucaby access token
         */
        OpenFB.login('email,user_friends').then(
            function(data) {
                // Success
                var fb_access_token = storage.getItem('fbtoken');
                OpenFB.get('/me').success(function(data){
                    var fb_user_id = data.id;
                    var params = {
                        service: 'facebook', grant_type: 'password',
                        username: fb_user_id, password: fb_access_token};
                    var url_params = Object.keys(params).map(function(prop) {
                      return [prop, params[prop]].map(encodeURIComponent).join("=");
                    }).join("&");
                    $http.post(ENDPOINT + '/oauth/token', url_params)
                        .success(function(data, status, headers, config) {
                            accessToken = data.access_token;
                            storage.setItem('ec_access_token', accessToken);
                            storage.setItem('ec_refresh_token', data.refresh_token);
                            storage.removeItem('fbtoken');

                            deferredLogin.resolve();
                            console.debug(data);
                            return accessToken;
                        })
                        .error(function(data, status, headers, config) {
                            console.log('OpenFB failed: ' + data);
                        })
                })
                .error(function(){
                    // Handle error
                })


            },
            function() {
                // XXX: Handle FB error
            });
        }


    return {
        init: function(){
            OpenFB.init('809426419123624', 'http://localhost:8100/oauthcallback.html', storage);
        },
        api: function(obj, deferred){
            var method = obj.method || 'GET';
            var params = obj.params || {};
            var deferred = $q.defer();
            var accessToken = provideAccessToken();

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
                })
            return deferred.promise;
        },
        login: function(){
            provideAccessToken();
            return deferredLogin.promise;
        },
        logout: function(){

            OpenFB.logout();
        }
    }
}]);
