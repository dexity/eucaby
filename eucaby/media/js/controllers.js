'use strict';

angular.module('eucaby.controllers', ['eucaby.utils'])

.controller('LocationCtrl', ['$scope', 'map', function($scope, map) {

    angular.element(document).ready(function(){
        var locmap = map.createMap('map', $scope.lat, $scope.lng);
        map.createMarker(locmap, $scope.lat, $scope.lng, $scope.message);
    });

}])

.controller('RequestCtrl', ['$scope', 'map', function($scope, map) {
    map.currentLocation(function(lat, lng){
        $scope.lat = lat;
        $scope.lng = lng;
        var locmap = map.createMap('map', lat, lng);
        map.createMarker(locmap, lat, lng);
    });

    $scope.sendLocation = function(){
        console.debug($scope.lat, $scope.lng, $scope.message);
    }
}]);
