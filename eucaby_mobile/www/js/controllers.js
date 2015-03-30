'use strict';

var SF_LAT = 37.7833;
var SF_LNG = -122.4167;

angular.module('eucaby.controllers',
               ['eucaby.services', 'eucaby.utils', 'eucaby.api'])

.controller('MainCtrl',
    ['$scope', '$rootScope', '$state', '$ionicSideMenuDelegate', 'EucabyApi',
    function($scope, $rootScope, $state, $ionicSideMenuDelegate, EucabyApi) {

    $rootScope.currentZoom = 13;

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
}])

.controller('LoginCtrl',
    ['$scope', '$location', '$ionicLoading', 'EucabyApi', 'utils',
     function($scope, $location, $ionicLoading, EucabyApi, utils) {

    $scope.facebookLogin = function(){

        $ionicLoading.show();
        EucabyApi.login().then(function () {
                $location.path('/app/tab/map');
            }, function(data) {
                utils.alert('Error', 'Error during log in. ' +
                                     'Please try again in a moment.');
                console.error(data);
            })
            .finally(function(){
                $ionicLoading.hide();
            });
    };
}])

.controller('MapCtrl', ['$scope', '$rootScope',
    '$http', '$ionicModal', '$ionicLoading', 'map', 'utils', 'Friends',
    function($scope, $rootScope,
             $http, $ionicModal, $ionicLoading, map, utils, Friends) {

    // Center on me action
    $scope.centerOnMe = function() {
        $ionicLoading.show();

        map.currentLocation(function(lat, lng){
            $scope.map = map.createMap('map', lat, lng,
                                       {zoom: $scope.currentZoom});
            google.maps.event.addListener(
                $scope.map, 'zoom_changed', function() {
                $rootScope.currentZoom = $scope.map.getZoom();
            });
            $scope.marker = map.createMarker($scope.map, lat, lng, 'Hello');
            $ionicLoading.hide();
        },
        function(data){
            $scope.map = map.createMap('map', SF_LAT, SF_LNG);
            $ionicLoading.hide();
            utils.alert('Location Error',
                        'Unable to get location: ' + data.message);
        });
    };

    $scope.centerOnMe();
    $scope.markers = [];
    $rootScope.friends = [];

    var registerModal = function(template, modalName){
        $ionicModal.fromTemplateUrl(template, {
            scope: $scope
        }).then(function(modal) {
            $scope[modalName] = modal;
        });
    };

    registerModal('templates/request.html', 'requestModal');
    registerModal('templates/notify.html', 'notifyModal');

    $scope.loadFriends = function(){
        // Loads friends
        return Friends.all().then(function(data){
            console.debug('Friends.all');
            $rootScope.friends = data.data;
        }, function(data){
            utils.alert('Error', 'Error loading friends');
            console.error(data);
        });
    };

    $scope.refreshFriends = function(){
        $ionicLoading.show();
        $scope.loadFriends().finally(function(){
            $ionicLoading.hide();
        });
    };

    // Modal shown event
    $scope.$on('modal.shown', function(event, modal) {
        // XXX: Update friends once a day
        angular.equals($scope.friends, []) && $scope.loadFriends();

        if ($scope.notifyModal === modal) {
            $ionicLoading.show();
            map.currentLocation(function (lat, lng) {
                $scope.notifyMap = map.createMap(
                    'notifymap', lat, lng, {zoom: 16});
                $scope.currentMarker = map.createMarker(
                    $scope.notifyMap, lat, lng, 'Current location');
                $rootScope.currentLatLng = {lat: lat, lng: lng};
                $ionicLoading.hide();
            }, function (data) {
                $ionicLoading.hide();
                utils.alert('Error', 'Failed to find the current location.');
                console.error(data);
            });
        }

    });

    $scope.isFormValid = function(form){
        // Main form validation
        var emailValue = form.email.$viewValue;
        var userValue = form.user.$viewValue;
        if ((!emailValue && !userValue) || (emailValue && userValue)){
            utils.alert(
                'Error', 'Please either provide an email or select a friend');
            return false;
        }
        if (form.email.$dirty && form.email.$invalid) {
            utils.alert('Error', 'Please provide a valid email');
            return false;
        }
        return true;
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

.controller('NotificationCtrl',
    ['$scope', '$rootScope', '$ionicLoading', 'utils', 'Notification',
    function($scope, $rootScope, $ionicLoading, utils, Notification) {

    $scope.form = {};
    // Hack for deselected radio button. This will avoid creating a custom radio
    // button directive. Idea: http://jsfiddle.net/8s4m2e5e/3/
    $scope.selectedUser;
    $scope.clickRadio = function(event) {
        if ($scope.selectedUser === $scope.form.username){
            $scope.form.username = false;
        }
        $scope.selectedUser = $scope.form.username;
    };

    $scope.sendLocation = function(){
        // Send location action
        if (!$scope.isFormValid($scope.notificationForm)){
            return;
        }

        $ionicLoading.show();
        Notification.post($scope.form, $rootScope.currentLatLng.lat,
                          $rootScope.currentLatLng.lng)
        .then(function(data){
            $ionicLoading.hide();
            $scope.notifyModal.hide();
            utils.toast('Location is submitted');
        }, function(data){
            $ionicLoading.hide();
            utils.alert('Error', data.message || 'Failed to send request');
        });
    };
}])

.controller('RequestCtrl',
    ['$scope', '$rootScope', '$ionicLoading', 'utils', 'Request',
    function($scope, $rootScope, $ionicLoading, utils, Request) {

    $scope.form = {};
    // Hack for deselected radio button.
    $scope.selectedUser;
    $scope.clickRadio = function(event) {
        if ($scope.selectedUser === $scope.form.username){
            $scope.form.username = false;
        }
        $scope.selectedUser = $scope.form.username;
    };

    $scope.sendRequest = function(){
        // Send request action
        if (!$scope.isFormValid($scope.requestForm)){
            return;
        }

        $ionicLoading.show();
        Request.post($scope.form).then(function(data){
            $ionicLoading.hide();
            $scope.requestModal.hide();
            utils.toast('Request is submitted');
        }, function(data){
            $ionicLoading.hide();
            utils.alert('Error', data.message || 'Failed to send request');
        });
    };
}])

.controller('LogoutCtrl', function($scope) {

})

.controller('ProfileCtrl', function($scope) {
})

.controller('SettingsCtrl', function($scope) {
})

.controller('OutgoingCtrl',
    ['$scope', '$stateParams', '$ionicLoading', 'utils', 'Activity',
    function($scope, $stateParams, $ionicLoading, utils, Activity) {

    $ionicLoading.show();
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

    var loadItems = function(){
        // Load outgoing items
        return Activity.outgoing().then(function(data){
            $scope.outgoing = formatOutgoing(data.data);
        }, function(data){
            utils.alert('Error', 'Error loading data');
            console.error(data);
        });
    };

    loadItems().finally(function(){
        $ionicLoading.hide();
    });

    $scope.refresh = function(){
        loadItems().finally(function(){
            $scope.$broadcast('scroll.refreshComplete');
        });
    };
}])

.controller('IncomingCtrl',
    ['$scope', '$stateParams', '$ionicLoading', 'utils', 'Activity',
    function($scope, $stateParams, $ionicLoading, utils, Activity) {

    $ionicLoading.show();
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

    var loadItems = function() {
        // Load incoming items
        return Activity.incoming().then(function (data) {
            $scope.incoming = formatIncoming(data.data);
        }, function (data) {
            utils.alert('Error', 'Error loading data');
            console.error(data);
        }).finally(function () {
            $ionicLoading.hide();
        });
    };

    loadItems().finally(function(){
        $ionicLoading.hide();
    });

    $scope.refresh = function(){
        loadItems().finally(function(){
            $scope.$broadcast('scroll.refreshComplete');
        });
    };
}])

.controller('NotificationDetailCtrl',
            ['$scope', '$ionicHistory', '$stateParams', 'map',
             'Notification',
    function($scope, $ionicHistory, $stateParams, map, Notification) {

        var stateName = $ionicHistory.currentView().stateName;
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
