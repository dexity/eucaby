'use strict';

angular.module('eucaby.push', ['eucaby.api', 'eucaby.utils'])

.factory('push',
    ['$cordovaPush', '$rootScope',
     function($cordovaPush, $rootScope) {

    var initAndroid = function() {
        var config = {
            senderID: '376614047301'
        };

        $cordovaPush.register(config).then(function(result) {
            console.debug(result);
            // Store registration id in localStorage
            // Send the registration id to the server
        }, function(err) {
            console.error(err);
            // Error
        });

        $rootScope.$on('$cordovaPush:notificationReceived', function(event, notification) {

          console.debug(arguments);

          switch(notification.event) {

            case 'registered':
              if (notification.regid.length > 0 ) {
                  console.debug('registration ID = ' + notification.regid);
              }
              break;

            case 'message':
              // this is the actual push notification. its format depends on the data model from the push server
              console.debug('message = ' + notification.message +
                            ' msgCount = ' + notification.msgcnt);
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
            alert(deviceToken);
            console.log("deviceToken: " + deviceToken);
        }, function(err) {
            alert("Registration error: " + err)
        });

        $rootScope.$on('$cordovaPush:notificationReceived', function(event, notification) {
          if (notification.alert) {
            navigator.notification.alert(notification.alert);
          }

          if (notification.sound) {
            var snd = new Media(event.sound);
            snd.play();
          }

          if (notification.badge) {
            $cordovaPush.setBadgeNumber(notification.badge).then(function(result) {
              // Success!
            }, function(err) {
              // An error occurred. Show a message to the user
            });
          }
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
            console.log(device);
            if (device.platform === 'iOS') {
                initIOS();
            } else if (device.platform === 'Android') {
                initAndroid();
            }
      }
  }
}]);
