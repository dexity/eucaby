'use strict';

var EUCABY_ENDPOINT = 'http://api.eucaby-dev.appspot.com';
var TEMP_TOKEN = 'Dvhn5yO4E6EMtJnJ0PQDI0fpROMqN2';

angular.module('eucaby.services', ['ngResource', 'eucaby.api'])

.factory('Friends', ['EucabyApi', function(EucabyApi) {

    return {
        all: function(){
            return EucabyApi.api({path: '/friends'});
        }
    };
}])

.factory('Activity', ['EucabyApi', function(EucabyApi) {
    return {
        outgoing: function(){
            return EucabyApi.api({path: '/history', params: {type: 'outgoing'}});
        },
        incoming: function(){
            return EucabyApi.api({path: '/history', params: {type: 'incoming'}});
        }
    }
}])
.factory('NotificationDetail', ['EucabyApi', function(EucabyApi) {

    return {
        get: function(id){
            return EucabyApi.api({path: '/location/notification/' + id});
        }
    }
}])
.factory('RequestDetail', ['EucabyApi', function(EucabyApi) {

    return {
        get: function(id){
            return EucabyApi.api({path: '/location/request/' + id});
        }
    }
}]);
