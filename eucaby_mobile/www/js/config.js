'use strict';

// Configuration module

angular.module('eucaby.config', [])

.factory('config', function(){

    var isProd = true;
    var config;

    if (!isProd){
        config = {  // Development
            ANDROID_ID: '376614047301',
            EUCABY_API_ENDPOINT: 'https://api.eucaby-dev.appspot.com',  // 'http://localhost:8888'
            FB_APP_ID: '809426419123624'
        };
    } else {
        config = {  // Production
            ANDROID_ID: '1013390921672',
            EUCABY_API_ENDPOINT: 'https://api.eucaby.com',
            FB_APP_ID: '1622022934714935'
        };
    }
    return config;
});
