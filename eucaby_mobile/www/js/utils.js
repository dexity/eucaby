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
        sendMessage: function(scope, http, modal_name, url, extra_params) {
            var email = scope.form.email;
            var username = scope.form.username;
            var token = scope.form.token;

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
            // Update params
            for (var key in extra_params){
                if (extra_params.hasOwnProperty(key)){
                    params[key] = extra_params[key];
                }
            }
            http.post(url, params, {headers: {'Authorization': 'Bearer ' + TEMP_TOKEN}})
                .success(function(data){
                    console.log(data);
                    modal_name && scope[modal_name + 'Modal'] && scope[modal_name + 'Modal'].hide();
                })
                .error(function(e){
                    console.log(e);
                });
        }
    }
})