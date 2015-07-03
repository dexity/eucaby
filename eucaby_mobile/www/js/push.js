'use strict';

angular.module('eucaby.push', ['ionic','eucaby.api', 'eucaby.utils'])

.factory('push',
    ['$cordovaPush', 'EucabyApi', 'utils', 'storageManager',
     function($cordovaPush, EucabyApi, utils, storageManager) {

    var registerDevice_ = function(deviceKey, platform){
        // Registers device or does nothing if it has already been registered
        if (storageManager.getDeviceStatus()){
            return;  // Device is already registered with GCM or APNs
        }
        if (!deviceKey || !storageManager.userLoggedIn()) {
            console.error(
                'Either device key is invalid or user is not logged in');
            return;
        }

        EucabyApi.api({method: 'POST', path: '/device/register',
                       data: {device_key: deviceKey, platform: platform}})
            .then(function(){
                storageManager.setDeviceStatus(true);
            });  // Silently fail if device registration fails
    };

    var registerAndroid = function(){
        var config = {
            senderID: '376614047301'
        };

        $cordovaPush.register(config).then(function(result) {
            // No registration id at the stage
            console.log('Android registration accepted');
        });
    };

    var registerIOS = function(){
        var config = {
            badge: true,
            sound: true,
            alert: true
        };
        $cordovaPush.register(config).then(function(deviceToken) {
            registerDevice_(deviceToken, 'ios');
            console.log("deviceToken: " + deviceToken);
        }, function(err) {
            console.error("Registration error: " + err);
        });
    };

    var initAndroid = function($scope) {
        // Init push notifications for Android
        registerAndroid();

        $scope.$on('$cordovaPush:notificationReceived',
                       function(event, notification) {
          console.log('Received notification: ', notification);

          switch(notification.event) {
            case 'registered':
              registerDevice_(notification.regid, 'android');
              break;
            case 'message':
                if (notification.foreground) {
                    utils.confirm(
                        'New request', 'Show the new request?',
                        'Show', 'Later', function(){
                            console.debug(notification);
                        })
                } else {
                    if (notification.coldstart){
                        console.debug('Coldstart');
                    } else {
                        console.debug('Background');
                    }
                }
              break;
            case 'error':
              console.error('GCM error: ' + notification.msg);
              break;
            default:
              console.error('An unknown GCM event has occurred');
              break;
          }
        });
    };

    var initIOS = function($scope){
        // Init push notifications for iOS
        registerIOS();

        $scope.$on('$cordovaPush:notificationReceived',
                       function(event, notification) {

            // XXX: Finish
            console.debug(event, notification);
            utils.confirm('New request', 'world', 'Show', 'Later');
        });
    };

    var platformDependent = function(
        AndroidFunction, iOSFunction, $scope){
        // This method should be called when device is ready!
        try {
            // XXX: Fix 'device' is not defined.
            switch(device.platform){
                case 'Android':
                    AndroidFunction($scope);
                    break;
                case 'iOS':
                    iOSFunction($scope);
                    break;
                default:
                    console.error(
                        'Platform ' + device.platform + ' not supported');
                    break;
            }
        } catch (err){
            console.error(err);
        }
     };

    return {
        initNotifications: function($scope) {
            // Set up push notifications to receive messages
            console.log('Registering device and notification event ...');
            platformDependent(initAndroid, initIOS, $scope);
        }
    }
}]);
