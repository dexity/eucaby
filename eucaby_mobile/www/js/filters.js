'use strict'

angular.module('eucaby.filters', [])

.filter('capitalize', function() {
    return function(input, all) {
        return (!!input) ? input.replace(/([^\W_]+[^\s-]*) */g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();}) : '';
    }
})

.filter('userName', function(){
    return function(input){
        return (!!input) ? (input.name || input.email) : '';
    }
});
