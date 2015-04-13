'use strict';

angular.module('eucaby.services', ['eucaby.api', 'eucaby.utils'])

.factory('User', ['EucabyApi', function(EucabyApi) {

    return {
        profile: function(){
            return EucabyApi.api({path: '/me'});
        }
    };
}])
.factory('Settings', ['EucabyApi', function(EucabyApi) {

    return {
        get: function(){
            return EucabyApi.api({path: '/settings'});
        },
        post: function(data){
            return EucabyApi.api(
                {method: 'POST', path: '/settings', data: data});
        }
    };
}])
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
    };
}])
.factory('Notification', ['EucabyApi', 'utils', function(EucabyApi, utils) {

    return {
        get: function(id){
            return EucabyApi.api({path: '/location/notification/' + id});
        },
        post: function(form, lat, lng){
            var data = utils.activityParams(form);
            data.latlng = lat + ',' + lng;
            return EucabyApi.api(
                {method: 'POST', path: '/location/notification', data: data});
        }
    };
}])
.factory('Request', ['EucabyApi', 'utils', function(EucabyApi, utils) {

    return {
        get: function(id){
            return EucabyApi.api({path: '/location/request/' + id});
        },
        post: function(form){
            var data = utils.activityParams(form);
            return EucabyApi.api({method: 'POST', path: '/location/request',
                                  data: data});
        }
    };
}]);
