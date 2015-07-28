'use strict';

//Module for push notifications.
/* global device */

angular.module('eucaby.push', [
    'ionic',
    'ngCordova',
    'eucaby.api',
    'eucaby.utils'
])

.constant('ANDROID_ID', '376614047301')

.factory('notifications', [
    '$rootScope',
    '$state',
    '$cordovaPush',
    'EucabyApi',
    'utils',
    'utilsIonic',
    'storageManager',
    'ANDROID_ID',
function($rootScope, $state, $cordovaPush, EucabyApi, utils, utilsIonic,
    storageManager, ANDROID_ID) {

    return {
        init: function() {
            var self = this;
            // Set up push notifications to receive messages
            console.log('Registering device and notification event ...');
            // This should be executed when device is ready!
            try {
                // XXX: Fix 'device' is not defined.
                switch(device.platform){
                    case 'Android':
                        self.$registerAndroid();
                        $rootScope.$on('$cordovaPush:notificationReceived',
                                   self.$receivedHandlerAndroid);
                        break;
                    case 'iOS':
                        self.$registerIOS();
                        $rootScope.$on('$cordovaPush:notificationReceived',
                                   self.$receivedHandlerIOS);
                        break;
                    default:
                        console.error(
                            'Platform ' + device.platform + ' not supported');
                        break;
                }
            } catch (err){
                console.error(err);
            }
        },
        $registerDevice: function(deviceKey, platform){
            // Registers device or does nothing if it has already been registered
            if (storageManager.getDeviceStatus()){
                return;  // Device is already registered with GCM or APNs
            }
            if (platform !== 'ios' && platform !== 'android'){
                console.error('Invalid platform');
                return;
            }
            if (!deviceKey || !storageManager.userLoggedIn()) {
                console.error(
                    'Either device key is invalid or user is not logged in');
                return;
            }
            EucabyApi.api({method: 'POST', path: '/device/register',
                           data: {device_key: deviceKey, platform: platform}})
                .then(function(){
                    storageManager.setDeviceStatus('true');
                });  // Silently fail if device registration fails
        },
        $registerAndroid: function(){
            $cordovaPush.register({
                senderID: ANDROID_ID
            }).then(function(result) {
                // No registration id at the stage
                console.log('Android registration accepted');
            }, function(err) {
                console.error("Registration error: " + err);
            });
        },
        $registerIOS: function(){
            var self = this;
            $cordovaPush.register({
                badge: true,
                sound: true,
                alert: true
            }).then(function(deviceToken) {
                self.$registerDevice(deviceToken, 'ios');
                console.log("deviceToken: " + deviceToken);
            }, function(err) {
                console.error("Registration error: " + err);
            });
        },
        $redirect: function(data, show){
            if (show){
                $state.go('app.tab.' + data.type, {id: data.id});
            } else {
                $state.go('app.tab.incoming');
            }
        },
        $handleMessage: function(payload, is_foreground){
            var self = this;
            // Handles messages both for Android and iOS
            var typeLabel = payload.type;
            var showDetails = true;
            if (typeLabel === 'notification'){
                typeLabel = 'location';
            }
            // Handle invalid format (this shouldn't happen)
            if (typeLabel !== 'request' && typeLabel !== 'location'){
                typeLabel = 'message';
                showDetails = false;
            }

            // XXX: Exclude case for request when sender and receiver are
            //      the same and request has no locations. In this case
            //      redirect to incoming list. Compare currently logged in user
            //      with the payload.user (should have backend support)
            if (is_foreground) {
                var header = 'New ' + typeLabel;
                var body = 'Show the new ' + typeLabel + '?';
                utilsIonic.confirm(
                    header, body, 'Show', 'Later', function(){
                        self.$redirect(payload, showDetails);
                    });
            } else {
                self.$redirect(payload, showDetails);
                /*
                Note for Android only:
                    If you need to differentiate cold start
                    (app is closed) from app in background use the
                    code:
                    if (notif.coldstart){ // Coldstart  }
                    else { // Background }
                    Object notif will contain all necessary data!
                */
            }
        },
        $receivedHandlerAndroid: function(event, notif) {
            var self = this;
            switch(notif.event) {
                case 'registered':
                    self.$registerDevice(notif.regid, 'android');
                    break;
                case 'message':
                    self.$handleMessage(notif.payload, notif.foreground);
                    break;
                case 'error':
                    console.error('GCM error: ' + notif.msg);
                    break;
                default:
                    console.error('An unknown GCM event has occurred');
                    break;
            }
        },
        $receivedHandlerIOS: function(event, notif) {
            this.$handleMessage(notif, notif.foreground === '1');
        }
    };
}]);
