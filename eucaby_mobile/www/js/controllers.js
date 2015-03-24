'use strict';

var SF_LAT = 37.7833;
var SF_LNG = -122.4167;

angular.module('eucaby.controllers', ['eucaby.services', 'eucaby.utils', 'eucaby.api'])

.controller('MainCtrl', function($scope, $state, $ionicSideMenuDelegate, EucabyApi) {

    $scope.showSideMenu = function(){
        return $scope.showHeader();
    };

    $scope.toggleRight = function(){
        $ionicSideMenuDelegate.toggleRight(!$ionicSideMenuDelegate.isOpenRight());
    };

    $scope.showHeader = function(){
        return $state.is('app.tab.map');  //!$state.is('app.login') || !
    };

    $scope.logout = function () {
        EucabyApi.logout();
        $state.go('app.login');
    };

//  $scope.rightButtons = [{
//    type: 'button-icon button-clear ion-navicon',
//    tap: function(e) {
//      $ionicSideMenuDelegate.toggleRight($scope.$$childHead);
//    }
//  }];
})

.controller('LoginCtrl', ['$scope', '$location', '$ionicPopup', 'EucabyApi',
                function($scope, $location, $ionicPopup, EucabyApi) {
    $scope.facebookLogin = function(){
        EucabyApi.login().then(function () {
                $location.path('/app/tab/map');
            }, function(data) {
                $ionicPopup.alert({
                    title: 'Error',
                    template: 'Error during log in.' +
                              ' Please try again in a moment.'
                });
                console.debug(data);
            });
    };
}])

.controller('MapCtrl', ['$scope', '$rootScope',
    '$http', '$ionicModal', '$ionicPopup', '$ionicLoading', 'map', 'Friends',
    function($scope, $rootScope,
             $http, $ionicModal, $ionicPopup, $ionicLoading, map, Friends) {

    // Center on me action
    $scope.centerOnMe = function() {

//        $scope.loading = $ionicLoading.show({
//            content: 'Getting current location...',
//            showBackdrop: false
//        });

        map.currentLocation(function(lat, lng){
            $scope.map = map.createMap('map', lat, lng);
            $scope.marker = map.createMarker($scope.map, lat, lng, 'Hello');
//            $scope.loading.hide();
        },
        function(data){
            $scope.map = map.createMap('map', SF_LAT, SF_LNG);
            $ionicPopup.alert({
                title: 'Location Error',
                template: 'Unable to get location: ' + data.message
            });
        });
    };

    $scope.centerOnMe();
    $scope.markers = [];

    var registerModal = function(template, modalName){
        $ionicModal.fromTemplateUrl(template, {
            scope: $scope
        }).then(function(modal) {
            $scope[modalName] = modal;
        });
    };

    registerModal('templates/request.html', 'requestModal');
    registerModal('templates/notify.html', 'notifyModal');

    $scope.$on('modal.shown', function(event, modal) {
        Friends.all().then(function(data){
            $scope.friends = data;
        });

        if ($scope.notifyModal === modal){
            map.currentLocation(function(lat, lng){
                $scope.notifyMap = map.createMap('notifymap', lat, lng, {zoom: 16});
                $scope.currentMarker = map.createMarker($scope.notifyMap, lat, lng, 'Hello');
                $rootScope.currentLatLng = {lat: lat, lng: lng};
            }, function(data){
                console.debug('Error');
            });
        }
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

.controller('MessageCtrl', ['$scope', '$rootScope', '$http', 'Friends', 'Request', 'Notification',
                function($scope, $rootScope, $http, Friends, Request, Notification) {

    console.debug('MessageCtrl');
    $scope.form = {};

    // Send request action
    $scope.sendRequest = function(){
        Request.post($scope.form).then(function(data){
            console.debug('Request submitted');
            $scope.requestModal.hide();
        });
    };
    $scope.sendLocation = function(){
        console.debug($rootScope.currentLatLng);
        Notification.post($scope.form, $rootScope.currentLatLng.lat, $rootScope.currentLatLng.lng).then(function(data){
            console.debug('Location submitted');
            $scope.notifyModal.hide();
        });
    };
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
    };
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
    };
    Activity.outgoing().then(function(data){
        $scope.outgoing = formatOutgoing(data.data);
    });
    Activity.incoming().then(function(data){
        $scope.incoming = formatIncoming(data.data);
    });
}])

.controller('NotificationDetailCtrl',
            ['$scope', '$stateParams', 'map',
             'Notification',
    function($scope, $stateParams, map, Notification) {

        var stateName = $scope.$viewHistory.currentView.stateName;
        $scope.isOutgoing = stateName.indexOf('outgoing') > -1;

        Notification.get($stateParams.id).then(function(data){
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
            ['$scope', '$http', '$stateParams', 'map',
             'Request', 'Notification',
    function($scope, $http, $stateParams, map, Request, Notification) {

        var stateName = $scope.$viewHistory.currentView.stateName;
        $scope.isOutgoing = stateName.indexOf('outgoing') > -1;
        $scope.form = {};
        $scope.sendLocation = function(){
            Notification.post($scope.form, SF_LAT, SF_LNG).then(function(data){
                console.debug('Location submitted');
                // XXX: Reload the request view
            });
        };
        Request.get($stateParams.id).then(function(data){
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
]);
