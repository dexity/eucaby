angular.module('starter.controllers', [])

.controller('MapCtrl', function($scope, $ionicModal, $ionicPopup, $ionicLoading, $timeout) {
    var initialize = function() {
        var lat = 37.7833;
        var lng = -122.4167;
        var mapOptions = {
            center: new google.maps.LatLng(lat, lng),
            zoom: 13,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };
        var map = new google.maps.Map(document.getElementById("map"), mapOptions);

        // Stop the side bar from dragging when mousedown/tapdown on the map
        google.maps.event.addDomListener(document.getElementById('map'), 'mousedown', function(e) {
            e.preventDefault();
            return false;
        });

        $scope.map = map;
    }
    initialize();

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

    $scope.sendRequest = function() {
        console.log('Sending request', $scope.requestData);
        $timeout(function() {
            $scope.closeRequest();
        }, 1000);
    };

    $scope.showIamhere = function() {
       var alertPopup = $ionicPopup.alert({
         title: 'I am here',
         template: 'Send location notification to specified email'
       });
       alertPopup.then(function(res) {
         console.log('Location notification has been sent');
       });
    };

    $scope.centerOnMe = function() {
        if(!$scope.map) {
            return;
        }

//        $scope.loading = $ionicLoading.show({
//            content: 'Getting current location...',
//            showBackdrop: false
//        });

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
})

.controller('RequestCtrl', function($scope) {

})

.controller('LoginCtrl', function($scope) {

})

.controller('FriendsCtrl', function($scope, Friends) {
  $scope.friends = Friends.all();
})

.controller('FriendDetailCtrl', function($scope, $stateParams, Friends) {
  $scope.friend = Friends.get($stateParams.friendId);
})

.controller('DownCtrl', function($scope) {
})

.controller('MainCtrl', function($scope, $ionicSideMenuDelegate) {
    $scope.toggleRight = function(){
        $ionicSideMenuDelegate.toggleRight($scope.$$childHead);
    }
//  $scope.rightButtons = [{
//    type: 'button-icon button-clear ion-navicon',
//    tap: function(e) {
//      $ionicSideMenuDelegate.toggleRight($scope.$$childHead);
//    }
//  }];
});
