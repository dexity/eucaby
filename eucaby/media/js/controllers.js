'use strict';

angular.module('eucaby.controllers', [])

.controller('MapCtrl', ['$scope', '$http', function($scope, $http) {
    var self = this;
    var map_id = 'map';

    angular.element(document).ready(function(){
        // Creates map
        var mapOptions = {
            center: new google.maps.LatLng($scope.lat, $scope.lng),
            zoom: 13,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };
        var map = new google.maps.Map(document.getElementById(map_id), mapOptions);
        var position = new google.maps.LatLng($scope.lat, $scope.lng);
        map.setCenter(position);
        // Creates marker
        new google.maps.Marker({
            position:  	position,
            title:      $scope.message,
            map:        map
        });
    });

//    if (navigator.geolocation) {
//        navigator.geolocation.getCurrentPosition(function(pos){
//            // Send location to the Django app
//            $http.post('/location/send', 'session=' + $scope.session +
//                '&latlng=' + pos.coords.latitude + ',' + pos.coords.longitude,
//                {headers: {
//                    'Content-Type': 'application/x-www-form-urlencoded'}})
//            .success(function(data){
//                $scope.message_type = 'success';
//                $scope.message = data.message;
//            }).error(function(){
//                $scope.message_type = 'error';
//                $scope.message = 'Error acquiring the location';
//            });
//        }, function(e){
//            $scope.message_type = 'error';
//            $scope.message = 'Location request has been denied. ' + e;
//        });
//    } else {
//        $scope.message_type = 'error';
//        $scope.message = 'Geolocation is not supported in your browser';
//    }
}]);
