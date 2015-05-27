'use strict';

angular.module('eucaby.push', ['ionic','eucaby.api', 'eucaby.utils'])

.factory('push',
    ['$cordovaPush', '$rootScope', '$state', '$ionicPopup',
     function($cordovaPush, $rootScope, $state, $ionicPopup) {

    var initAndroid = function() {
        var config = {
            senderID: '376614047301'
        };

        $cordovaPush.register(config).then(function(result) {
            console.debug('$cordovaPush.register: ' + result);
            // Store registration id in localStorage
            // Send the registration id to the server
        }, function(err) {
            console.error(err);
            // Error
        });

        $rootScope.$on('$cordovaPush:notificationReceived', function(event, notification) {

          switch(notification.event) {

            case 'registered':
              if (notification.regid.length > 0 ) {
                  console.debug('registration ID = ' + notification.regid);
              }
              break;

            case 'message':
                $rootScope.checkMessages(true);
              break;

            case 'error':
              console.debug('GCM error = ' + notification.msg);
              break;

            default:
              console.debug('An unknown GCM event has occurred');
              break;
          }
        });

        /*
        // WARNING: dangerous to unregister (results in loss of tokenID)
        $cordovaPush.unregister(options).then(function(result) {
          // Success!
        }, function(err) {
          // Error
        })
        */
    };

    var initIOS = function(){
        var config = {
            badge: true,
            sound: true,
            alert: true
        };
        $cordovaPush.register(config).then(function(deviceToken) {
            console.log("deviceToken: " + deviceToken);
        }, function(err) {
            alert("Registration error: " + err);
        });

        $rootScope.$on('$cordovaPush:notificationReceived',
                       function(event, notification) {
            $rootScope.checkMessages(true);
        });

        /*
        // WARNING! dangerous to unregister (results in loss of tokenID)
        $cordovaPush.unregister(options).then(function(result) {
          // Success!
        }, function(err) {
          // Error
        });
        */
    };

    return {
        initNotifications: function(){
            try {
                if (device.platform === 'iOS') {
                    initIOS();
                } else if (device.platform === 'Android') {
                    initAndroid();
                }
            } catch (err){}
      }
  };
}]);
