'use strict';

angular.module('eucaby.push', ['ionic','eucaby.api', 'eucaby.utils'])

.factory('push',
    ['$cordovaPush', '$rootScope', 'EucabyApi', '$state', '$ionicPopup',
     function($cordovaPush, $rootScope, EucabyApi, $state, $ionicPopup) {

    var initAndroid = function() {
        // Init push notifications for Android
        var config = {
            senderID: '376614047301'
        };

        $cordovaPush.register(config).then(function(result) {
            // No registration id at the stage
            console.log('Android registration accepted');
        });

        $rootScope.$on('$cordovaPush:notificationReceived', function(event, notification) {

          switch(notification.event) {
            case 'registered':
              if (!notification.regid) {
                  break
              }
              EucabyApi.registerDevice(notification.regid, 'android');
              break;

            case 'message':
              $rootScope.checkMessages(true);
              break;

            case 'error':
              console.error('GCM error: ' + notification.msg);
              break;

            default:
              console.error('An unknown GCM event has occurred');
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
        // Init push notifications for iOS
        var config = {
            badge: true,
            sound: true,
            alert: true
        };
        $cordovaPush.register(config).then(function(deviceToken) {
            EucabyApi.registerDevice(deviceToken, 'ios');
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
            // Register device and set up notifications to receive messages
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
