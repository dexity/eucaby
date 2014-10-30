'use strict';

var EucabyApp = angular.module('eucaby',
    ['ionic', 'openfb', 'btford.socket-io', 'eucaby.controllers',
     'eucaby.services'])

.factory('socket', function (socketFactory) {
    return socketFactory({
        ioSocket: io('http://localhost:4000') // rt.eucaby-dev.appspot.com, 146.148.67.189
    });
})

.run(function($ionicPlatform, OpenFB) {

    OpenFB.init('809426419123624', 'http://localhost:8100/oauthcallback.html');

    $ionicPlatform.ready(function() {
    // Hide the accessory bar by default (remove this to show the accessory bar above the keyboard
    // for form inputs)
    if(window.cordova && window.cordova.plugins.Keyboard) {
        cordova.plugins.Keyboard.hideKeyboardAccessoryBar(true);
    }
    if(window.StatusBar) {
        // org.apache.cordova.statusbar required
        StatusBar.styleDefault();
    }
    });
})

.config(function($stateProvider, $urlRouterProvider) {

    // Ionic uses AngularUI Router which uses the concept of states
    // Learn more here: https://github.com/angular-ui/ui-router
    // Each state's controller can be found in controllers.js
    $stateProvider

    // Abstract states
    .state('app', {
        url: "/app",
        abstract: true,
        templateUrl: "templates/menu.html"
    })

    .state('app.tabs', {
        url: "/tab",
        abstract: true,
        views: {
            'menu-content': {
                templateUrl: "templates/tabs.html"
            }
        }
    })

    // States with navigation history stack
    .state('app.login', {
        url: "/login",
        views: {
            'menu-content': {
                templateUrl: "templates/login.html",
                controller: "LoginCtrl"
            }
        }
    })

    .state('app.tabs.map', {
        url: '/map',
        views: {
            'tab-map': {
                templateUrl: 'templates/tab-map.html',
                controller: 'MapCtrl'
            }
        }
    })
    .state('app.tabs.map.request', { // Not working
        url: '/request',
        views: {
            'tab-map': {
                template: 'templates/tab-down.html',
                controller: 'RequestCtrl'
            }
        }
    })
    .state('app.tabs.friends', {
        url: '/friends',
        views: {
            'tab-friends': {
                templateUrl: 'templates/tab-friends.html',
                controller: 'FriendsCtrl'
            }
        }
    })
    .state('app.tabs.friend-detail', {
        url: '/friend/:friendId',
        views: {
            'tab-friends': {
                templateUrl: 'templates/friend-detail.html',
                controller: 'FriendDetailCtrl'
            }
        }
    })

    .state('app.tabs.down', {
        url: '/down',
        views: {
            'tab-down': {
                templateUrl: 'templates/tab-down.html',
                controller: 'DownCtrl'
            }
        }
    });

  // if none of the above states are matched, use this as the fallback
  $urlRouterProvider.otherwise('/app/tab/map');

});



