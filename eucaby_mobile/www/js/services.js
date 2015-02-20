'use strict';

angular.module('eucaby.services', ['ngResource', 'eucaby.api', 'eucaby.utils'])

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
.factory('Notification', ['EucabyApi', 'utils', function(EucabyApi, utils) {

    return {
        get: function(id){
            return EucabyApi.api({path: '/location/notification/' + id});
        },
        post: function(form, lat, lng){
            var params = utils.activityParams(form);
            params.latlng = lat + ',' + lng;
            return EucabyApi.api({method: 'POST', path: '/location/notification', params: params})
        }
    }
}])
.factory('Request', ['EucabyApi', 'utils', function(EucabyApi, utils) {

    return {
        get: function(id){
            return EucabyApi.api({path: '/location/request/' + id});
        },
        post: function(form){
            var params = utils.activityParams(form);
            return EucabyApi.api({method: 'POST', path: '/location/request', params: params})
        }
    }
}]);
