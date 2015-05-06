'use strict';

angular.module('eucaby.push', ['eucaby.api', 'eucaby.utils'])

.factory('push',
    ['$cordovaPush', '$rootScope',
     function($cordovaPush, $rootScope) {

    return {
        initNotifications: function(){
            var androidConfig = {
                'senderID': '376614047301'
            };

            document.addEventListener('deviceready', function(){
            $cordovaPush.register(androidConfig).then(function(result) {
                console.debug(result);
                // Store registration id in localStorage
                // Send the registration id to the server
            }, function(err) {
                console.error(err);
                // Error
            });

            $rootScope.$on('$cordovaPush:notificationReceived', function(event, notification) {

              console.debug(event, notification);

              switch(notification.event) {
                case 'registered':
                  if (notification.regid.length > 0 ) {
                      console.debug('registration ID = ' + notification.regid);
                  }
                  break;

                case 'message':
                  // this is the actual push notification. its format depends on the data model from the push server
                  console.debug('message = ' + notification.message + ' msgCount = ' + notification.msgcnt);
                  break;

                case 'error':
                  console.debug('GCM error = ' + notification.msg);
                  break;

                default:
                  console.debug('An unknown GCM event has occurred');
                  break;
              }
            });


            //    // WARNING: dangerous to unregister (results in loss of tokenID)
            //    $cordovaPush.unregister(options).then(function(result) {
            //      // Success!
            //    }, function(err) {
            //      // Error
            //    })

            }, false);
      }
  }
}]);
