'use strict';

var EUCABY_ENDPOINT = 'http://api.eucaby-dev.appspot.com';
var TEMP_TOKEN = 'Dvhn5yO4E6EMtJnJ0PQDI0fpROMqN2';
var SF_LAT = 37.7833;
var SF_LNG = -122.4167;

angular.module('eucaby.controllers', ['eucaby.services', 'eucaby.utils'])

.controller('MapCtrl', ['$scope', // 'socket',
    '$http', '$ionicModal', '$ionicPopup', '$ionicLoading', 'map',
    function($scope, //socket,
             $http, $ionicModal, $ionicPopup, $ionicLoading, map) {

    var RT_URL = 'localhost'; //'146.148.67.189'; //'rt.eucaby-dev.appspot.com'; //
    var RT_PORT = 4000;

    $scope.map = map.createMap('map', SF_LAT, SF_LNG);
    $scope.markers = [];

    var registerModal = function(template, modal_name){
        $ionicModal.fromTemplateUrl(template, {
            scope: $scope
        }).then(function(modal) {
            $scope[modal_name + 'Modal'] = modal;
        });
    }

    registerModal('templates/request.html', 'request');
    registerModal('templates/notify.html', 'notify');

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

.controller('MessageCtrl', ['$scope', '$http', 'Friends', 'map',
                function($scope, $http, Friends, map) {

//    $scope.notify_map = map.createMap('notifymap', SF_LAT, SF_LNG);
//    $scope.current_marker = map.createMarker($scope.notify_map, SF_LAT, SF_LNG, 'Hello');

    $scope.form = {};
    $scope.friends = Friends.all();

    var sendMessage = function(modal_name, url, extra_params) {
        var email = $scope.form.email;
        var username = $scope.form.username;

        if (email && username){
            // XXX: Display error
        }
        // XXX: If not email or username set also display error
        var params = {};
        if (email){
            params.email = email;
        } else if (username){
            params.username = username;
        }
        // Update params
        for (var key in extra_params){
            if (extra_params.hasOwnProperty(key)){
                params[key] = extra_params[key];
            }
        }
        $http.post(url, params, {headers: {'Authorization': 'Bearer ' + TEMP_TOKEN}})
            .success(function(data){
                console.log(data);
                $scope[modal_name + 'Modal'].hide();
            })
            .error(function(e){
                console.log(e);
            });
    }

    // Send request action
    $scope.sendRequest = function(){
        sendMessage('request', EUCABY_ENDPOINT + '/location/request');
    }
    $scope.sendLocation = function(){
        sendMessage('notify', EUCABY_ENDPOINT + '/location/notify',
                    {latlng: SF_LAT + ',' + SF_LNG});
    }
}])

.controller('LoginCtrl', function($scope, $location, $state, OpenFB) {
    $scope.facebookLogin = function(){
        OpenFB.login('email,user_friends').then(
            function () {
                $location.path('/app/tab/map');
                //$state.go('app.tabs.map')
            },
            function () {
                alert('OpenFB login failed');
            });
    }
})

.controller('LogoutCtrl', function($scope) {
})

.controller('ActivityCtrl', ['$scope', '$rootScope', '$stateParams', 'Activity',
    function($scope, $rootScope, $stateParams, Activity) {

    var formatOutgoing = function(data){
        var items = [];
        for (var i=0; i < data.length; i++){
            var item = data[i];
            var description = item.type.charAt(0).toUpperCase()
                + item.type.slice(1);
            description += ' sent on ' + item.created_date;  // XXX: Format date
            var url = '';
            if (item.type ==='notification' || item.session.complete){
                url = '#/app/tab/detail/' + i;
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
            if (item.type ==='notification' || item.session.complete){
                url = '#/app/tab/detail/' + i;
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
    Activity.outgoing(function(data){
        $rootScope.outgoing = formatOutgoing(data.data);
    });
    Activity.incoming(function(data){
        $scope.incoming = formatIncoming(data.data);
    })
}])

.controller('ActivityDetailCtrl',
            ['$scope', '$rootScope', '$stateParams', 'map',
    function($scope, $rootScope, $stateParams, map) {
        $scope.out_item = $rootScope.outgoing[$stateParams.id];
        var loc = $scope.out_item.item.location;
        $scope.map = map.createMap('locmap', loc.lat, loc.lng);
        $scope.marker = map.createMarker($scope.map, loc.lat, loc.lng, 'Hello');
    }
])

.controller('MainCtrl', function($scope, $state, $ionicSideMenuDelegate, OpenFB) {

    $scope.showSideMenu = function(){
        return $scope.showHeader();
    }

    $scope.toggleRight = function(){
        $ionicSideMenuDelegate.toggleRight(!$ionicSideMenuDelegate.isOpenRight());
    }

    $scope.showHeader = function(){
        return $state.is('app.tabs.map');  //!$state.is('app.login') || !
    }

    $scope.logout = function () {
        OpenFB.logout();
        $state.go('app.login');
    };

//  $scope.rightButtons = [{
//    type: 'button-icon button-clear ion-navicon',
//    tap: function(e) {
//      $ionicSideMenuDelegate.toggleRight($scope.$$childHead);
//    }
//  }];
});
