'use strict';

angular.module('eucaby.controllers', [])

.controller('MapCtrl', ['$scope', 'socket', '$http', '$ionicModal',
    '$ionicPopup', '$ionicLoading',
    function($scope, socket, $http, $ionicModal, $ionicPopup, $ionicLoading) {

    var SENDER_EMAIL = 'alex@eucaby.com';
//    var REQUEST_URL = 'https://eucaby-dev.appspot.com/_ah/api/eucaby/v1/location/request';
//    var NOTIFY_URL = 'https://eucaby-dev.appspot.com/_ah/api/eucaby/v1/location/notify';
    var REQUEST_URL = 'http://localhost:8888/_ah/api/eucaby/v1/location/request';
    var NOTIFY_URL = 'http://localhost:8888/_ah/api/eucaby/v1/location/notify';
    var SF_LAT = 37.7833;
    var SF_LNG = -122.4167;
    var RT_URL = 'localhost'; //'rt.eucaby-dev.appspot.com'; //'146.148.67.189';
    var RT_PORT = 4000;

    var mapFactory = function(lat, lng) {
        // Creates map
        var mapOptions = {
            center: new google.maps.LatLng(lat, lng),
            zoom: 13,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };
        var map = new google.maps.Map(document.getElementById('map'), mapOptions);

        // Stop the side bar from dragging when mousedown/tapdown on the map
        google.maps.event.addDomListener(document.getElementById('map'), 'mousedown', function(e) {
            e.preventDefault();
            return false;
        });

        return map
    }

    var markerFactory = function(map, lat, lng, username) {
        var position = new google.maps.LatLng(lat, lng);
        map.setCenter(position);
        // Creates marker
        return new google.maps.Marker({
            position:  	position,
            title:      username,
            map:        map
        });
    }

    var clearOverlays = function(markers) {
        // Clears markers from the map
        if (markers) {
            for (var i = 0; i < markers.length; i++) {
                markers[i].setMap(null);
            }
        }
        markers = [];
    }

    $scope.map = mapFactory(SF_LAT, SF_LNG);
    $scope.markers = [];
    $scope.requestData = {};

    $ionicModal.fromTemplateUrl('templates/request.html', {
        scope: $scope
    }).then(function(modal) {
        $scope.modal = modal;
    });

    // Triggered in the login modal to close it
    $scope.closeRequest = function() {
        $scope.modal.hide();
    };

    // Open the login modal
    $scope.request = function() {
        $scope.modal.show();
    };

    // Send request action
    $scope.sendRequest = function() {
        console.log('Sending request', $scope.requestData);
        $http.post(REQUEST_URL, {receiver_email: $scope.requestData.email,
            sender_email: SENDER_EMAIL})
            .success(function(data){
                console.log(data);
                $scope.closeRequest();
            })
            .error(function(e){
                console.log(e);
            });
    };

    // I am here action
    $scope.showIamhere = function() {
       var alertPopup = $ionicPopup.alert({
         title: 'I am here',
         template: 'Send location notification to specified email'
       });
       alertPopup.then(function(res) {
         console.log('Location notification has been sent');
       });
    };

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
}])

.controller('RequestCtrl', function($scope) {

})

.controller('LoginCtrl', function($scope, $location, OpenFB) {
    $scope.facebookLogin = function(){
        OpenFB.login('email,user_friends').then(
            function () {
                $location.path('/app/tab/map');
            },
            function () {
                alert('OpenFB login failed');
            });
    }
})

.controller('FriendsCtrl', function($scope, Friends) {
    $scope.friends = Friends.all();
})

.controller('FriendDetailCtrl', function($scope, $stateParams, Friends) {
    $scope.friend = Friends.get($stateParams.friendId);
})

.controller('DownCtrl', function($scope) {
})

.controller('MainCtrl', function($scope, $state, $ionicSideMenuDelegate) {
    $scope.toggleRight = function(){
        $ionicSideMenuDelegate.toggleRight(!$ionicSideMenuDelegate.isOpenRight());
    }

    $scope.showHeader = function(){
        return !$state.is('app.login');
    }
//  $scope.rightButtons = [{
//    type: 'button-icon button-clear ion-navicon',
//    tap: function(e) {
//      $ionicSideMenuDelegate.toggleRight($scope.$$childHead);
//    }
//  }];
});
