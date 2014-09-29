'use strict';

angular.module('eucaby.controllers', [])

.controller('MainCtrl', ['$scope', '$http', function($scope, $http) {
    var self = this;

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(pos){
            $http.post("/location/send", {
                session: $scope.session,
                latlng: pos.coords.latitude + ',' + pos.coords.longitude
            }).success(function(data){
                $scope.message_type = 'success';
                $scope.message = data.message;
            }).error(function(){
                $scope.message_type = 'error';
                $scope.message = 'Error acquiring the location';
            });
        }, function(e){
            $scope.message_type = 'error';
            $scope.message = 'Location request has been denied. ' + e;
        });
    } else {
        $scope.message_type = 'error';
        $scope.message = 'Geolocation is not supported in your browser';
    }

}])
