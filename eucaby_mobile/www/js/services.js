'use strict';

angular.module('eucaby.services', ['ngResource'])

.factory('Friends', ['$resource', function($resource) {

    return $resource('http://api.eucaby-dev.appspot.com/friends', {}, {
        query: {method: 'GET',
            headers: {'Authorization': 'Bearer Dvhn5yO4E6EMtJnJ0PQDI0fpROMqN2'}
        }
    });
}]);
