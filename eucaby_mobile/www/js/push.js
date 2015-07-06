'use strict';

angular.module('eucaby.push', ['ionic','eucaby.api', 'eucaby.utils'])

.factory('push',
    ['$state', '$cordovaPush', 'EucabyApi', 'utils', 'storageManager',
     function($state, $cordovaPush, EucabyApi, utils, storageManager) {

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
                       function(event, notif) {
          console.log('Received notification: ', notif);

          switch(notif.event) {
            case 'registered':
              registerDevice_(notif.regid, 'android');
              break;
              case 'message':
                var data = notif.payload;
                // XXX: Check if data.message_type is 'request' or 'location'
                // XXX: Exclude case for request when sender and receiver are
                //      the same and request has no locations. In this case
                //      redirect to incoming list
                if (notif.foreground) {
                    var header = 'New ' + data.type;
                    var body = 'Show the new ' + data.type + '?';
                    utils.confirm(
                        header, body, 'Show', 'Later', function(){
                            $state.go(
                                'app.tab.' + data.type, {id: data.id});
                        })
                } else {
                    $state.go('app.tab.' + data.type, {id: data.id});
                    // Note: If you need to differentiate cold start
                    //       (app is closed) from app in background use the
                    //       code. Object notif will contain all necessary data.
                    // if (notif.coldstart){ /* Coldstart */ }
                    // else { /* Background */ }
                }
              break;
            case 'error':
              console.error('GCM error: ' + notif.msg);
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
                       function(event, notif) {

            // XXX: Finish
            console.debug(event, notif);
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
