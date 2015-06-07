'use strict';

angular.module('eucaby.push', ['ionic','eucaby.api', 'eucaby.utils'])

.factory('push',
    ['$cordovaPush', '$rootScope', 'EucabyApi', 'storageManager',
     function($cordovaPush, $rootScope, EucabyApi, storageManager) {

    var registerDevice = function(deviceKey, platform){
        if (storageManager.getDeviceStatus()){
            return;  // Device is already registered with GCM or APNs
        }
        EucabyApi.api({method: 'POST', path: '/device/register',
                       data: {device_key: deviceKey, platform: platform}})
            .then(function(){
                storageManager.setDeviceStatus(true);
            });  // Silently fail if device registration fails
    };
    var checkMessages = function(status){
        // Checks if new incoming messages have arrived
        if (status !== undefined){
            storageManager.setNewMessages(status);
            $rootScope.hasMessages = status;
        }
        return storageManager.hasNewMessages();
    };
    var initAndroid = function() {
        // Init push notifications for Android
        var config = {
            senderID: '376614047301'
        };

        $cordovaPush.register(config).then(function(result) {
            // No registration id at the stage
            console.log('Android registration accepted');
        });

        $rootScope.$on('$cordovaPush:notificationReceived',
                       function(event, notification) {

          console.log('Received notification: ' + notification);
          switch(notification.event) {
            case 'registered':
              if (notification.regid) {
                  registerDevice(notification.regid, 'android');
              }
              break;

            case 'message':
              checkMessages(true);
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
            registerDevice(deviceToken, 'ios');
            console.log("deviceToken: " + deviceToken);
        }, function(err) {
            console.error("Registration error: " + err);
        });

        $rootScope.$on('$cordovaPush:notificationReceived',
                       function(event, notification) {
            checkMessages(true);
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
        checkMessages: checkMessages,
        initNotifications: function(){
            console.log('Initialize notifications');
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
