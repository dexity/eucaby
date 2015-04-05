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

.factory('utils',
    ['$ionicPopup', '$ionicLoading',
     function($ionicPopup, $ionicLoading){
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
            $ionicPopup.alert({title: title, template: text});
        },
        toast: function(text){
            $ionicLoading.show({
                template: text, noBackdrop: true, duration: 2000});
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
}])

.factory('dateUtils', function(){
    return {
        timeList: function(ts){
            // Converts timestamp to list: [day, hour, minute]
            ts = ts/1000;   // Timestamp in seconds
            var d = Math.floor(ts/(60*60*24));
            var h = Math.floor(ts/(60*60)) - d*24;
            var m = Math.floor(ts/60) - h*60 - d*24*60;
            return [d, h, m];
        },
        showYear: function(ts0, ts1){
            // Returns true when years for ts0 and ts1 are different
            var y0 = new Date(ts0).getFullYear();
            var y1 = new Date(ts1).getFullYear();
            return y0 != y1
        },
        ts2hd: function(ts, show_year){
            // Converts timestamp to date string
            if (show_year === undefined){
                show_year = true;
            }
            var df = 'MMM D, ';
            if (show_year) {
                df += 'YYYY ';
            }
            df += 'h:mm a';
            return moment(ts).format(df);
        },

        ts2h: function(ts0, ts1, full){
            var self = this;
            var ht = '';  // Human time
            if (full === undefined){
                full = true;
            }
            if (!ts1){
                ts1 = new Date().getTime();
            }
            var dt = ts1 - ts0;
            if (dt < 0){
                return '';
            }
            var sy = self.showYear(ts0, ts1);
            if (dt > 432000*1000) {    // More than 5 days
                var ht = self.ts2hd(ts0, sy);
                if (full){
                    ht = 'on ' + ht;
                }
                return ht;
            }
            var tl = self.timeList(dt);
            // Compose string
            if (tl[0] !== 0) {
                ht = tl[0] + ' d ' + tl[1] + ' hr';
            } else if (tl[1] !== 0) {
                ht  = tl[1] + ' hr ' + tl[2] + ' min';
            } else if (tl[2] !== 0) {
                ht = tl[2] + ' min';
            } else {
                ht  = '1 min';
            }
            if (full){
                ht  += ' ago';
            }
            return ht
        }
    }
 });
