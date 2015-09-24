'use strict';

angular.module('eucaby.services', [
    'eucaby.api',
    'eucaby.utils'
])

.factory('User', [
    'EucabyApi',
function(EucabyApi) {
    return {
        profile: function(){
            return EucabyApi.api({path: '/me'});
        }
    };
}])
.factory('Settings', [
    'EucabyApi',
function(EucabyApi) {
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
.factory('Friends', [
    'EucabyApi',
 function(EucabyApi) {
    return {
        all: function(params){
            var obj = {path: '/friends'};
            if (angular.isObject(params)){
                obj.params = params;
            }
            return EucabyApi.api(obj);
        }
    };
}])
.factory('Activity', [
    'EucabyApi',
function(EucabyApi) {
    return {
        outgoing: function(){
            return EucabyApi.api({path: '/history', params: {type: 'outgoing'}});
        },
        incoming: function(){
            return EucabyApi.api({path: '/history', params: {type: 'incoming'}});
        }
    };
}])
.factory('Notification', [
    'EucabyApi',
    'utils',
function(EucabyApi, utils) {
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
.factory('Request', [
    'EucabyApi',
    'utils',
function(EucabyApi, utils) {
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
}])

.factory('Autocomplete', [
    'EucabyApi',
function(EucabyApi) {
     return {
         // Note: You can optimize the query request: if starting substring
         //       returns no results the appending characters to the substring
         //       will make it less likely to return any result.
         query: function (query) {
             return EucabyApi.api(
                 {path: '/autocomplete?limit=5&query=' + query});
         }
     };
 }]);
