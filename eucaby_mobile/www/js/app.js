'use strict';

var EucabyApp = angular.module('eucaby', [
    'ionic',
    'btford.socket-io',
    'eucaby.controllers',
    'eucaby.services'
])
.factory('socket', function (socketFactory) {
    return socketFactory({
        ioSocket: io('http://localhost:4000') // rt.eucaby-dev.appspot.com, 146.148.67.189
    });
})
.run(function($ionicPlatform) {
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


