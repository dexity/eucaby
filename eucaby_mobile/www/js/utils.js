'use strict';

angular.module('eucaby.utils', [])

// Default location: San Francisco
.constant('LATLNG', [37.7833, -122.4167])
.constant('MAX_RECENT_CONTACTS', 3)
// See: https://github.com/angular/angular.js/blob/master/src/ng/directive/input.js
.constant('EMAIL_REGEXP',
          /^[a-z0-9!#$%&'*+\/=?^_`{|}~.-]+@[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$/i)

.factory('map', ['$q', '$ionicLoading', 'utils', 'LATLNG',
    function($q, $ionicLoading, utils, LATLNG){
    return {
        createMap: function(id, lat, lng, config){
            // Creates map
            if (lat === undefined || lng === undefined) {
                lat = LATLNG[0];
                lng = LATLNG[1];
            }
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
        },
        getCurrentLocation: function(mapId) {
            var self = this;
            var deferred = $q.defer();
            $ionicLoading.show();
            self.currentLocation(function (lat, lng) {
                var map = self.createMap(mapId, lat, lng, {zoom: 16});
                var marker = self.createMarker(
                    map, lat, lng, 'Current location');
                $ionicLoading.hide();
                deferred.resolve(
                    {map: map, marker: marker, lat: lat, lng: lng});
            }, function(data) {
                $ionicLoading.hide();
                utils.alert('Error', 'Failed to find the current location.');
                console.error(data);
                deferred.reject(data);
            });
            return deferred.promise;
        }
    };
}])

.factory('utils',
    ['$rootScope', '$ionicPopup', '$ionicLoading', 'storageManager',
     'MAX_RECENT_CONTACTS', 'EMAIL_REGEXP',
     function($rootScope, $ionicPopup, $ionicLoading, storageManager,
              MAX_RECENT_CONTACTS, EMAIL_REGEXP){
    return {
        activityParams: function(form){
            // Creates parameters for activity request
            var email = form.email;
            var username = form.username;
            var token = form.token;

            // Note: Form validation (e.g. passing both or none of the email
            //       and username) is handled by the time
            var params = {
                message: form.message || ''
            };
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
                return [prop, params[prop]].map(encodeURIComponent).join('=');
            }).join('&');
        },
        validEmail: function(value){
            // Checks if value is a valid email address
            return EMAIL_REGEXP.test(value);
        },
        alert: function(title, text){
            // Convenience function for ionic alert popup
            $ionicPopup.alert({title: title, template: text});
        },
        confirm: function(title, text, okText, cancelText, okCallback){
            var opts = {title: title, template: text, okText: okText,
                        cancelText: cancelText};
            $ionicPopup.confirm(opts).then(
                function(res) {
                    if (res){
                        okCallback();
                    }
            });
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
        },
        formatMessages: function(data, formatter){
            // Formats location or request message
            var items = [];
            for (var i=0; i < data.length; i++){
                var item = data[i];
                var form = formatter(item);
                var url = '';
                var icon = '';
                if (item.type === 'notification') {
                    icon = 'ion-ios-location-outline';
                    url = form.notification_url;
                    if (item.session.complete) {
                        icon = 'ion-ios-location';
                    }
                } else if (item.type === 'request') {
                    icon = 'ion-ios-bolt-outline';
                    if (item.session.complete) {
                        url = form.request_url;
                        icon = 'ion-ios-bolt';
                    }
                }
                items.push({
                    item: item,
                    complete: item.session.complete,
                    name: form.name,
                    description: form.description,
                    message: item.message,
                    url: url,
                    icon: icon
                });
            }
            return items;
        },
        manageRecent: function(form, label){
            // Manages recent contacts
            // It it guaranteed that the most current contact will be on the top
            $rootScope.recentContacts = ($rootScope.recentContacts ||
                storageManager.getRecentContacts() || []);
            $rootScope.recentFriends = ($rootScope.recentFriends ||
                storageManager.getRecentFriends() || {});

            // Contact can only be either email or user
            var model = 'email';
            var name = 'email';
            var value = form.email;
            var text = value;
            var removedContact = null;

            if (form.username){
                model = 'username';
                name = 'user';
                value = form.username;
                text = label;
            }
            var indexOf = function(contacts, field, value){
                // Util for finding index of the matching value in array
                for (var i = 0; i < contacts.length; i++){
                    if (contacts[i][field] === value){
                        return i;
                    }
                }
                return -1;
            };
            var idx = indexOf($rootScope.recentContacts, 'value', value);
            // Move the existing contact to the top  (avoid duplicate contacts)
            if (idx >= 0){
                $rootScope.recentContacts.splice(idx, 1);
            }
            // Append a new recent contact
            $rootScope.recentContacts.unshift(
                {label: text, value: value, model: model, name: name}
            );
            // Remove extra contacts
            if ($rootScope.recentContacts.length > MAX_RECENT_CONTACTS){
                removedContact = $rootScope.recentContacts.pop();
            }
            // Remove from friends list for recent friend contact
            // Friends should be either in friends or recentFriends
            if (model === 'username') {
                idx = indexOf($rootScope.friends, 'username', value);
                if (idx >= 0){
                    // Remove from friends list
                    var contact = $rootScope.friends.splice(idx, 1)[0];
                    $rootScope.recentFriends[value] = contact;
                }
            }
            // If removed contact is in recent friends return it back to
            // friends array
            if (removedContact &&
                $rootScope.recentFriends.hasOwnProperty(removedContact.value)) {
                $rootScope.friends.unshift(
                    $rootScope.recentFriends[removedContact.value]);
                delete $rootScope.recentFriends[removedContact.value];
            }
            // Save recent contacts and friends to local storage
            storageManager.setRecentContacts($rootScope.recentContacts);
            storageManager.setRecentFriends($rootScope.recentFriends);
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
            return y0 != y1;
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
                return self.ts2hd(ts0, sy);
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
            return ht;
        }
    };
 })

.factory('storageManager', function(){

    var storage = window.localStorage;
    var ACCESS_TOKEN = 'ec_access_token';
    var REFRESH_TOKEN = 'ec_refresh_token';
    var FB_TOKEN = 'fbtoken';
    var DEVICE_STATUS = 'device_registered';
    var NEW_MESSAGES = 'incoming_messages';
    var RECENT_CONTACTS = 'recent_contacts';
    var RECENT_FRIENDS = 'recent_friends';

    return {
        getStorage: function(){
            return storage;
        },
        saveAuth: function(data){
            storage.setItem(ACCESS_TOKEN, data.access_token);
            storage.setItem(REFRESH_TOKEN, data.refresh_token);
            delete storage.fbtoken;
        },
        getRefreshToken: function(){
            return storage.getItem(REFRESH_TOKEN);
        },
        getFbToken: function(){
            // Note: Storage in openfb-angular module has different interface
            //       from localStorage so we look up by key
            return storage.fbtoken;
        },
        getAccessToken: function(){
            return storage.getItem(ACCESS_TOKEN);
        },
        getDeviceStatus: function(){
            return storage.getItem(DEVICE_STATUS) === 'true';
        },
        setDeviceStatus: function(value){
            storage.setItem(DEVICE_STATUS, value);
        },
        setNewMessages: function(value){
            storage.setItem(NEW_MESSAGES, value);
        },
        hasNewMessages: function(){
            storage.getItem(NEW_MESSAGES) === 'true';
        },
        setRecentContacts: function(obj){
            this.setObject(RECENT_CONTACTS, obj);
        },
        getRecentContacts: function(){
            return this.getObject(RECENT_CONTACTS);
        },
        setRecentFriends: function(obj){
            this.setObject(RECENT_FRIENDS, obj);
        },
        getRecentFriends: function(){
            return this.getObject(RECENT_FRIENDS);
        },
        clearAll: function(){
            storage.removeItem(ACCESS_TOKEN);
            storage.removeItem(REFRESH_TOKEN);
            storage.removeItem(FB_TOKEN);
            delete storage.fbtoken;
            storage.removeItem(DEVICE_STATUS);
            storage.removeItem(NEW_MESSAGES);
            storage.removeItem(RECENT_CONTACTS);
            storage.removeItem(RECENT_FRIENDS);
        },
        setObject: function(key, obj){
            storage.setItem(key, JSON.stringify(obj));
        },
        getObject: function(key){
            JSON.parse(storage.getItem(key));
        }
    };
 });
