'use strict';

var EUCABY_ENDPOINT = 'http://api.eucaby-dev.appspot.com';
var TEMP_TOKEN = 'Dvhn5yO4E6EMtJnJ0PQDI0fpROMqN2';
var SF_LAT = 37.7833;
var SF_LNG = -122.4167;

angular.module('eucaby.controllers', ['eucaby.services', 'eucaby.utils', 'eucaby.api'])

.controller('MapCtrl', ['$scope', // 'socket',
    '$http', '$ionicModal', '$ionicPopup', '$ionicLoading', 'map',
    function($scope, //socket,
             $http, $ionicModal, $ionicPopup, $ionicLoading, map) {

    var RT_URL = 'localhost'; //'146.148.67.189'; //'rt.eucaby-dev.appspot.com'; //
    var RT_PORT = 4000;

    $scope.map = map.createMap('map', SF_LAT, SF_LNG);
    $scope.markers = [];

    var registerModal = function(template, modalName){
        var name = modalName + 'Modal';
        $ionicModal.fromTemplateUrl(template, {
            scope: $scope
        }).then(function(modal) {
            $scope[name] = modal;
        });
    }

    registerModal('templates/request.html', 'request');
    registerModal('templates/notify.html', 'notify');


//    $scope.showNotifyModal = function(){
//        $scope.notifyModal.show();
//        console.debug('Hello');
//    }
    $scope.$on('modal.shown', function(a, b) {
        // 1. Move to current location
        // 2. Display map for notifyModal
        $scope.notify_map = map.createMap('notifymap', SF_LAT, SF_LNG);
        $scope.current_marker = map.createMarker($scope.notify_map, SF_LAT, SF_LNG, 'Hello');
//        console.debug(a, b)
    });



//    // I am here action
//    $scope.showIamhere = function() {
//       var alertPopup = $ionicPopup.alert({
//         title: 'I am here',
//         template: 'Send location notification to specified email'
//       });
//       alertPopup.then(function(res) {
//         console.log('Location notification has been sent');
//       });
//    };

    // Center on me action
    $scope.centerOnMe = function() {
        if(!$scope.map) {
            return;
        }
//        $scope.loading = $ionicLoading.show({
//            content: 'Getting current location...',
//            showBackdrop: false
//        });

        // Not working yet
        navigator.geolocation.getCurrentPosition(function(pos) {
            $scope.map.setCenter(new google.maps.LatLng(pos.coords.latitude, pos.coords.longitude));
            $scope.loading.hide();
        }, function(error) {
            $ionicPopup.alert({
                title: 'Location Error',
                template: 'Unable to get location: ' + error.message
            });
        });
    };

    /*
    // Socket.io
    socket.on('connect', function(){
        console.log("Connected");
    });

    socket.on('message', function(message) {
        var msg = JSON.parse(message);
        clearOverlays($scope.markers);
        var marker = markerFactory(
            $scope.map, msg.location.lat, msg.location.lng,
            msg.session.receiver_email);
        $scope.markers.push(marker);
    });
    */
}])

.controller('MessageCtrl', ['$scope', '$http', 'Friends', 'utils',
                function($scope, $http, Friends, utils) {

    $scope.form = {};
    Friends.all().then(function(data){
        $scope.friends = data;
    });

    // Send request action
    $scope.sendRequest = function(){
        utils.sendMessage($scope, $http, 'request', EUCABY_ENDPOINT + '/location/request');
    }
    $scope.sendLocation = function(){
        utils.sendMessage($scope, $http, 'notify', EUCABY_ENDPOINT + '/location/notification',
                    {latlng: SF_LAT + ',' + SF_LNG});
    }
}])

.controller('LoginCtrl', ['$scope', '$http', '$location', '$state', 'EucabyApi',
                function($scope, $http, $location, $state, EucabyApi
                    ) {
    $scope.facebookLogin = function(){
        EucabyApi.login().then(
            function () {
                $location.path('/app/tab/map');
                //$state.go('app.tabs.map')
                // Authenticate with Eucaby service using FB token

            },
            function () {
                alert('EucabyApi login failed');
            });
    }
}])

.controller('LogoutCtrl', function($scope) {
})

.controller('ProfileCtrl', function($scope) {
})

.controller('SettingsCtrl', function($scope) {
})

.controller('ActivityCtrl', ['$scope', '$stateParams', 'Activity',
    function($scope, $stateParams, Activity) {

    var formatOutgoing = function(data){
        var items = [];
        for (var i=0; i < data.length; i++){
            var item = data[i];
            var description = item.type.charAt(0).toUpperCase()
                + item.type.slice(1);
            description += ' sent on ' + item.created_date;  // XXX: Format date
            var url = '';
            if (item.type === 'notification'){
                url = '#/app/tab/outgoing_notification/' + item.id;
            } else if (item.type === 'request' && item.session.complete) {
                url = '#/app/tab/outgoing_request/' + item.id;
            }
            items.push({
                item: item,
                complete: item.session.complete,
                name: item.recipient.name || item.recipient.email,
                description: description,
                url: url
            });
        }
        return items;
    }
    var formatIncoming = function(data){
        var items = [];
        for (var i=0; i < data.length; i++){
            var item = data[i];
            var description = item.type.charAt(0).toUpperCase()
                + item.type.slice(1);
            description += ' received on ' + item.created_date;  // XXX: Format date
            var url = '';
            if (item.type === 'notification'){
                url = '#/app/tab/incoming_notification/' + item.id;
            } else if (item.type === 'request') {
                url = '#/app/tab/incoming_request/' + item.id;
            }
            items.push({
                item: item,
                complete: item.session.complete,
                name: item.sender.name,
                description: description,
                url: url
            });
        }
        return items;
    }
    Activity.outgoing().then(function(data){
        $scope.outgoing = formatOutgoing(data.data);
    });
    Activity.incoming().then(function(data){
        $scope.incoming = formatIncoming(data.data);
    })
}])

.controller('NotificationDetailCtrl',
            ['$scope', '$stateParams', 'map',
             'NotificationDetail',
    function($scope, $stateParams, map, NotificationDetail) {

        var stateName = $scope.$viewHistory.currentView.stateName;
        $scope.isOutgoing = stateName.indexOf('outgoing') > -1;

        NotificationDetail.get($stateParams.id).then(function(data){
            var item = {
                data: data.data
            };
            $scope.item = item;
            var loc = $scope.item.data.location;
            $scope.map = map.createMap('locmap', loc.lat, loc.lng);
            $scope.marker = map.createMarker($scope.map, loc.lat, loc.lng, 'Hello');
        });
    }
])

.controller('RequestDetailCtrl',
            ['$scope', '$http', '$stateParams', 'map', 'utils',
             'RequestDetail',
    function($scope, $http, $stateParams, map, utils, RequestDetail) {

        var stateName = $scope.$viewHistory.currentView.stateName;
        $scope.isOutgoing = stateName.indexOf('outgoing') > -1;
        $scope.form = {};
        $scope.sendLocation = function(){
            utils.sendMessage($scope, $http, null, EUCABY_ENDPOINT + '/location/notification',
                        {latlng: SF_LAT + ',' + SF_LNG});
            // XXX: Reload the request view
        }
        RequestDetail.get($stateParams.id).then(function(data){
            var item = {
                data: data.data
            };
            $scope.markers = [];
            $scope.map;
            $scope.item = item;
            $scope.form.token = item.data.session.token;
            for (var i = 0; i < item.data.notifications.length; i++){
                var notif = item.data.notifications[i];
                var loc = notif.location;
                if (!$scope.map) {
                    $scope.map = map.createMap('locmap', loc.lat, loc.lng);
                }
                $scope.markers.push(map.createMarker($scope.map, loc.lat, loc.lng, 'Hello'));
            }
        });
    }
])

.controller('MainCtrl', function($scope, $state, $ionicSideMenuDelegate){//, EucabyApi) {

    $scope.showSideMenu = function(){
        return $scope.showHeader();
    }

    $scope.toggleRight = function(){
        $ionicSideMenuDelegate.toggleRight(!$ionicSideMenuDelegate.isOpenRight());
    }

    $scope.showHeader = function(){
        return $state.is('app.tab.map');  //!$state.is('app.login') || !
    }

    $scope.logout = function () {
        $state.go('app.login');
    };

//  $scope.rightButtons = [{
//    type: 'button-icon button-clear ion-navicon',
//    tap: function(e) {
//      $ionicSideMenuDelegate.toggleRight($scope.$$childHead);
//    }
//  }];
});
