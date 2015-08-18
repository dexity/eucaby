'use strict';

angular.module('eucaby.controllers', ['eucaby.utils'])

.controller('LocationCtrl', ['$scope', 'map', function($scope, map) {

    angular.element(document).ready(function(){
        var locmap = map.createMap('map', $scope.lat, $scope.lng);
        map.createMarker(locmap, $scope.lat, $scope.lng, $scope.message);
    });

}])

.controller('RequestCtrl', ['$scope', '$http', 'map', 'utils',
            function($scope, $http, map, utils) {
    map.currentLocation(function(lat, lng){
        $scope.lat = lat;
        $scope.lng = lng;
        var locmap = map.createMap('map', lat, lng);
        map.createMarker(locmap, lat, lng);
    });

    $scope.sendLocation = function(){
        $http.post('/request/' + $scope.uuid,
           utils.toPostData({
               lat: $scope.lat, lng: $scope.lng,
               message: $scope.message || ''
           }), {
           headers: {
               'Content-Type': 'application/x-www-form-urlencoded'
           }}).then(function(data){
              window.location.href = '/';
           },
           function(data){
               console.debug(data);
           });
    }
}]);
