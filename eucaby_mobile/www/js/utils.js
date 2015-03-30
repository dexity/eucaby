'use strict';

angular.module('eucaby.utils', [])

.factory('map', function(){
    return {
        createMap: function(id, lat, lng, config){
            // Creates map
            var mapOptions = {
                center: new google.maps.LatLng(lat, lng),
                zoom: (config && config.zoom) || 13,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            };
            var map = new google.maps.Map(document.getElementById(id), mapOptions);

            // Stop the side bar from dragging when mousedown/tapdown on the map
            google.maps.event.addDomListener(
                document.getElementById(id), 'mousedown', function(e) {
                    e.preventDefault();
                    return false;
                });
            return map;
        },
        createMarker: function(map, lat, lng, title){
            var position = new google.maps.LatLng(lat, lng);
            map.setCenter(position);
            // Creates marker
            return new google.maps.Marker({
                position:  	position,
                title:      title,
                map:        map
            });
        },
        clearMarkers: function(markers) {
            // Clears markers from the map
            if (markers) {
                for (var i = 0; i < markers.length; i++) {
                    markers[i].setMap(null);
                }
            }
            markers = [];
        },
        currentLocation: function(success, error){
            navigator.geolocation.getCurrentPosition(function(pos) {
                success(pos.coords.latitude, pos.coords.longitude);
            }, error);
        }
    };
})

.factory('utils', ['$ionicPopup', function($ionicPopup){
    return {
        activityParams: function(form){
            // Creates parameters for activity request
            var email = form.email;
            var username = form.username;
            var token = form.token;

            // Note: Form validation (e.g. passing both or none of the email
            //       and username) is handled by the time
            var params = {};
            if (email){
                params.email = email;
            } else if (username){
                params.username = username;
            } else if (token) {
                params.token = token;
            }
            return params;
        },
        toPostData: function(params){
            // Converts object to post data
            if (!params){
                return '';
            }
            return Object.keys(params).map(function(prop) {
                return [prop, params[prop]].map(encodeURIComponent).join("=");
            }).join("&");
        },
        alert: function(title, text){
            // Convenience function for ionic alert popup
            $ionicPopup.alert({
                title: title,
                template: text
            });
        },
        sortByKey: function(array, key) {
            // Sort array of objects by key
            return array.sort(function(a, b) {
                var x = a[key];
                var y = b[key];

                if (angular.isString(x)){
                    x = x.toLowerCase();
                    y = y.toLowerCase();
                }
                return ((x < y) ? -1 : ((x > y) ? 1 : 0));
            });
        }
    };
}]);
