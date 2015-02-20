'use strict'

angular.module('eucaby.utils', [])

.factory('map', function(){
    return {
        createMap: function(id, lat, lng){
            // Creates map
            var mapOptions = {
                center: new google.maps.LatLng(lat, lng),
                zoom: 13,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            };
            var map = new google.maps.Map(document.getElementById(id), mapOptions);

            // Stop the side bar from dragging when mousedown/tapdown on the map
            google.maps.event.addDomListener(
                document.getElementById(id), 'mousedown', function(e) {
                    e.preventDefault();
                    return false;
                });
            return map
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
        }
    }
})

.factory('utils', function(){
    return {
        activityParams: function(form){
            var email = form.email;
            var username = form.username;
            var token = form.token;

            if (email && username){
                // XXX: Display error
            }
            // XXX: If not email or username set also display error
            var params = {};
            if (email){
                params.email = email;
            } else if (username){
                params.username = username;
            } else if (token) {
                params.token = token
            }
            return params;
        }
    }
})