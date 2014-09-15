

EucabyApp.config(function($stateProvider, $urlRouterProvider) {

  // Ionic uses AngularUI Router which uses the concept of states
  // Learn more here: https://github.com/angular-ui/ui-router
  // Each state's controller can be found in controllers.js
  $stateProvider

    // Abstract states
    .state('main', {
      url: "/main",
      abstract: true,
      templateUrl: "templates/menu.html"
    })

    .state('main.tabs', {
      url: "/tab",
      abstract: true,
      views: {
        'menu-content': {
            templateUrl: "templates/tabs.html"
        }
      }
    })

    // States with navigation history stack
    .state('main.tabs.map', {
      url: '/map',
      views: {
        'tab-map': {
          templateUrl: 'templates/tab-map.html',
          controller: 'MapCtrl'
        }
      }
    })

    .state('main.tabs.friends', {
      url: '/friends',
      views: {
        'tab-friends': {
          templateUrl: 'templates/tab-friends.html',
          controller: 'FriendsCtrl'
        }
      }
    })
    .state('main.tabs.friend-detail', {
      url: '/friend/:friendId',
      views: {
        'tab-friends': {
          templateUrl: 'templates/friend-detail.html',
          controller: 'FriendDetailCtrl'
        }
      }
    })

    .state('main.tabs.down', {
      url: '/down',
      views: {
        'tab-account': {
          templateUrl: 'templates/tab-down.html',
          controller: 'DownCtrl'
        }
      }
    });

  // if none of the above states are matched, use this as the fallback
  $urlRouterProvider.otherwise('/main/tab/map');

});