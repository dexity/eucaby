'use strict';

angular.module('eucaby',
    ['ionic', 'eucaby.controllers', 'eucaby.filters', 'eucaby.api'])

.run(function($rootScope, $state, $ionicPlatform, $window, EucabyApi) {

    var storage = $window.localStorage;
    EucabyApi.init(storage);

    $ionicPlatform.ready(function() {
        if(window.StatusBar) {
            // org.apache.cordova.statusbar required
            window.StatusBar.styleDefault();
        }
    });

    $rootScope.$on('$stateChangeStart', function(event, toState) {
        if (toState.name !== 'app.login' && toState.name !== 'app.logout' &&
            !storage.getItem('ec_access_token')) {
            $state.go('app.login');
            event.preventDefault();
        }
    });

    $rootScope.$on('OAuthException', function() {
        $state.go('app.login');
    });

})

.constant('$ionicLoadingConfig', {
    template: '<ion-spinner icon="lines"/>',
    noBackdrop: true,
    duration: 30000    // 30 seconds
})

.config(function($stateProvider, $urlRouterProvider, $ionicConfigProvider) {

    $ionicConfigProvider.tabs.position('bottom');

    $stateProvider
    // Abstract states
    .state('app', {
        url: '/app',
        abstract: true,
        templateUrl: 'templates/menu.html'
    })

    .state('app.tab', {
        url: '/tab',
        abstract: true,
        views: {
            'menu-content': {
                templateUrl: 'templates/tabs.html'
            }
        }
    })

    // States with navigation history stack
    .state('app.login', {
        url: '/login',
        views: {
            'menu-content': {
                templateUrl: 'templates/login.html',
                controller: 'LoginCtrl'
            }
        }
    })
    .state('app.profile', {
        url: '/profile',
        views: {
            'menu-content': {
                templateUrl: 'templates/profile.html',
                controller: 'ProfileCtrl'
            }
        }
    })
    .state('app.settings', {
        url: '/settings',
        views: {
            'menu-content': {
                templateUrl: 'templates/settings.html',
                controller: 'SettingsCtrl'
            }
        }
    })
    .state('app.tab.map', {
        url: '/map',
        views: {
            'tab-map': {
                templateUrl: 'templates/tab-map.html',
                controller: 'MapCtrl'
            }
        }
    })
    .state('app.tab.outgoing', {
        url: '/outgoing',
        views: {
            'tab-outgoing': {
                templateUrl: 'templates/tab-outgoing.html',
                controller: 'OutgoingCtrl'
            }
        }
    })
    .state('app.tab.outgoing_notification', {
        url: '/outgoing_notification/:id',
        views: {
            'tab-outgoing': {
                templateUrl: 'templates/notification-detail.html',
                controller: 'NotificationDetailCtrl'
            }
        }
    })
    .state('app.tab.outgoing_request', {
        url: '/outgoing_request/:id',
        views: {
            'tab-outgoing': {
                templateUrl: 'templates/request-detail.html',
                controller: 'RequestDetailCtrl'
            }
        }
    })
    .state('app.tab.incoming', {
        url: '/incoming',
        views: {
            'tab-incoming': {
                templateUrl: 'templates/tab-incoming.html',
                controller: 'IncomingCtrl'
            }
        }
    })

    .state('app.tab.incoming_notification', {
        url: '/incoming_notification/:id',
        views: {
            'tab-incoming': {
                templateUrl: 'templates/notification-detail.html',
                controller: 'NotificationDetailCtrl'
            }
        }
    })
    .state('app.tab.incoming_request', {
        url: '/incoming_request/:id',
        views: {
            'tab-incoming': {
                templateUrl: 'templates/request-detail.html',
                controller: 'RequestDetailCtrl'
            }
        }
    });

  $urlRouterProvider.otherwise('/app/tab/map');

});



