angular.module('starter.controllers', [])

.controller('MapCtrl', function($scope) {
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
})

.controller('FriendsCtrl', function($scope, Friends) {
  $scope.friends = Friends.all();
})

.controller('FriendDetailCtrl', function($scope, $stateParams, Friends) {
  $scope.friend = Friends.get($stateParams.friendId);
})

.controller('AccountCtrl', function($scope) {
})

.controller('MenuCtrl', function($scope, $ionicSideMenuDelegate) {
  $scope.toggleLeft = function() {
    $ionicSideMenuDelegate.toggleLeft();
  };
});
