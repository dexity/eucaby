'use strict';

angular.module('eucaby.controllers',
               ['eucaby.services', 'eucaby.utils', 'eucaby.api', 'eucaby.push'])

.controller('MainCtrl',
    ['$scope', '$rootScope', '$state', '$ionicSideMenuDelegate',
      'storageManager', 'EucabyApi', 'push',
    function($scope, $rootScope, $state, $ionicSideMenuDelegate,
             storageManager, EucabyApi, push) {

    $rootScope.currentZoom = 13;
    $rootScope.contactsHistory = {};
    $rootScope.recentContacts = storageManager.getRecentContacts() || [];
    $rootScope.recentFriends = storageManager.getRecentFriends() || {};

//    $rootScope.setNoMessages = function(){
//        push.checkMessages(false);
//    };
//    $rootScope.hasMessages = push.checkMessages();

    $scope.showSideMenu = function(){
        return $scope.showHeader();
    };

    $scope.toggleRight = function(){
        $ionicSideMenuDelegate.toggleRight(!$ionicSideMenuDelegate.isOpenRight());
    };

    $scope.showHeader = function(){
        return $state.is('app.tab.map');
    };

    $scope.logout = function () {
        EucabyApi.logout();
        $state.go('app.login');
    };
}])

.controller('LoginCtrl',
    ['$scope', '$location', '$ionicLoading', 'EucabyApi', 'push', 'utils',
     function($scope, $location, $ionicLoading, EucabyApi, push, utils) {

    $scope.facebookLogin = function(){

        $ionicLoading.show();
        EucabyApi.login().then(function () {
                $location.path('/app/tab/map');
                push.initNotifications();
            }, function(data) {
                utils.alert('Error', 'Error during log in. ' +
                                     'Please try again in a moment.');
                console.error(data);
            })
            .finally(function(){
                $ionicLoading.hide();
            });
    };
}])

.controller('MapCtrl', ['$scope', '$rootScope',
    '$http', '$ionicModal', '$ionicLoading', 'map', 'utils', 'Friends',
    function($scope, $rootScope,
             $http, $ionicModal, $ionicLoading, map, utils, Friends) {

    // Center on me action
    $scope.centerOnMe = function() {
        $ionicLoading.show();

        map.currentLocation(function(lat, lng){
            $scope.map = map.createMap('map', lat, lng,
                                       {zoom: $scope.currentZoom});
            google.maps.event.addListener(
                $scope.map, 'zoom_changed', function() {
                $rootScope.currentZoom = $scope.map.getZoom();
            });
            $scope.marker = map.createMarker($scope.map, lat, lng);
            $ionicLoading.hide();
        },
        function(data){
            $scope.map = map.createMap('map');
            $ionicLoading.hide();
            utils.alert('Location Error',
                        'Unable to get location: ' + data.message);
        });
    };

    $scope.centerOnMe();
    $scope.markers = [];
    $rootScope.friends = [];

    var registerModal = function(template, modalName){
        $ionicModal.fromTemplateUrl(template, {
            scope: $scope
        }).then(function(modal) {
            $scope[modalName] = modal;
        });
    };

    registerModal('templates/request.html', 'requestModal');
    registerModal('templates/notify.html', 'notifyModal');

    $scope.loadFriends = function(){
        // Loads friends
        return Friends.all().then(function(data){
            $rootScope.friends = data.data;
            utils.syncFriendsWithRecent(
                $rootScope.recentFriends, $rootScope.friends);
        }, function(data){
            utils.alert('Error', 'Error loading friends');
            console.error(data);
        });
    };

    $scope.refreshFriends = function(){
        $ionicLoading.show();
        $scope.loadFriends().finally(function(){
            $ionicLoading.hide();
        });
    };

    // Modal shown event
    $scope.$on('modal.shown', function(event, modal) {
        // XXX: Update friends once a day
        if (angular.equals($scope.friends, [])){
            $scope.loadFriends();
        }

        if ($scope.notifyModal === modal) {
            map.getCurrentLocation('notifymap').then(function(data) {
                $scope.map = data.map;
                $scope.marker = data.marker;
                $rootScope.currentLatLng = {lat: data.lat, lng: data.lng};
            });
        }
    });

    $scope.isFormValid = function(form){
        // Main form validation
        var emailValue = form.email.$viewValue;
        var userValue = form.user.$viewValue;
        if ((!emailValue && !userValue) || (emailValue && userValue)){
            utils.alert(
                'Error', 'Please provide either an email or select a friend');
            return false;
        }

        // Note: We use type="text" for email instead of type="email" because
        //       email type triggers ng-change expression only when email is
        //       valid. This is not what we want. ng-change should trigger
        //       every type user types in the input field. So we explicitly
        //       validate email field instead of form.email.$invalid
        if (form.email.$dirty && !utils.validEmail(emailValue)) {
            utils.alert('Error', 'Please provide a valid email');
            return false;
        }
        return true;
    };

    /*
    // Socket.io
    socket.on('connect', function(){
        console.log("Connected");
    });

    socket.on('message', function(message) {
        var msg = JSON.parse(message);
        clearOverlays($scope.markers);
        var marker = markerFactory(
            $scope.map, msg.location.lat, msg.location.lng,
            msg.session.receiver_email);
        $scope.markers.push(marker);
    });
    */
}])

.controller('NotificationCtrl',
    ['$scope', '$rootScope', '$ionicLoading', 'utils', 'ctrlUtils', 'Notification',
    function($scope, $rootScope, $ionicLoading, utils, ctrlUtils, Notification) {

    $scope.form = {};
    $scope.selectUser = function(name){
        ctrlUtils.selectUser($scope, name);
    };

    $scope.$on('sendLocation', function(event){
        // Send location action
        // Warning: This is a hack to access child scope directly
        //          messageForm in ng-included template.
        if (!$scope.isFormValid($scope.$$childHead.messageForm)){
            return;
        }

        $ionicLoading.show();
        Notification.post($scope.form, $rootScope.currentLatLng.lat,
                          $rootScope.currentLatLng.lng).then(
            ctrlUtils.messageSuccess(
                $scope, $scope.notifyModal, 'Location submitted'),
            ctrlUtils.messageError('Failed to send location'));
    });
}])

.controller('RequestCtrl',
    ['$scope', '$rootScope', '$ionicLoading', 'utils', 'ctrlUtils', 'Request', 'Autocomplete',
    function($scope, $rootScope, $ionicLoading, utils, ctrlUtils, Request, Autocomplete) {

    $scope.form = {};
    $scope.selectUser = function(name){
        ctrlUtils.selectUser($scope, name);
    };

    // Autocomplete test
    $scope.autoTyping = function(){
        Autocomplete.query($scope.form.email).then(function(data){
            $scope.autoItems = data.data;
        });
    };

    $scope.autoComplete = function(item){
        $scope.autoItems = [];
        $scope.form.email = item;
    };

    $scope.$on('sendRequest', function(event){
        // Send request action
        // Warning: This is a hack to access child scope directly
        if (!$scope.isFormValid($scope.$$childHead.messageForm)){
            return;
        }

        $ionicLoading.show();
        Request.post($scope.form).then(
            ctrlUtils.messageSuccess(
                $scope, $scope.requestModal, 'Request submitted'),
            ctrlUtils.messageError('Failed to send request'));
    });
}])

.controller('ProfileCtrl',
    ['$scope', '$ionicLoading', 'utils', 'dateUtils', 'User',
    function($scope, $ionicLoading, utils, dateUtils, User) {

    $ionicLoading.show();
    User.profile().then(function(data){
        $scope.profile = data.data;
        $scope.profile.date_joined = dateUtils.ts2hd(
            Date.parse(data.data.date_joined), true);
    }, function(data){
        utils.alert('Failed to load user profile');
        console.error(data);
    }).finally(function(){
        $ionicLoading.hide();
    });
}])

.controller('SettingsCtrl',
    ['$scope', '$ionicLoading', 'utils', 'Settings',
     function($scope, $ionicLoading, utils, Settings) {

    $scope.emailSubscription = { checked: false };

    var setEmailSubscription = function(data){
        // Sets email subscription checkbox based from data
        var emailSub = data.data.email_subscription;
        if (emailSub === null){
            emailSub = true; // Default is true
        }
        $scope.emailSubscription.checked = emailSub;
    };

    $ionicLoading.show();
    Settings.get().then(function(data){
        setEmailSubscription(data);
    }, function(data){
        utils.alert('Failed to load settings');
    }).finally(function(){
        $ionicLoading.hide();
    });

    $scope.emailSubscriptionChange = function() {
        $ionicLoading.show();
        var postData = {email_subscription: $scope.emailSubscription.checked};
        Settings.post(postData).then(function(data){
            setEmailSubscription(data);
        }, function(data){
            utils.alert('Failed to update settings');
        }).finally(function(){
            $ionicLoading.hide();
        });
        console.log('Push Notification Change', $scope.emailSubscription.checked);
    };

}])

.controller('OutgoingCtrl',
    ['$scope', '$stateParams', '$ionicLoading', 'utils', 'dateUtils', 'Activity',
    function($scope, $stateParams, $ionicLoading, utils, dateUtils, Activity) {

    $ionicLoading.show();
    // Outgoing formatter
    var formatter = function(item){
        return {
            description: 'received ' + dateUtils.ts2h(
                Date.parse(item.created_date)),
            name: item.recipient.name || item.recipient.email,
            notification_url: '#/app/tab/outgoing_notification/' + item.id,
            request_url: '#/app/tab/outgoing_request/' + item.id
        };
    };
    var loadItems = function(){
        // Load outgoing items
        return Activity.outgoing().then(function(data){
            $scope.messages = utils.formatMessages(data.data, formatter);
            $scope.viewTitle = 'Outgoing';
        }, function(data){
            utils.alert('Error', 'Error loading data');
            console.error(data);
        });
    };

    loadItems().finally(function(){
        $ionicLoading.hide();
    });

    $scope.refresh = function(){
        loadItems().finally(function(){
            $scope.$broadcast('scroll.refreshComplete');
        });
    };
}])

.controller('IncomingCtrl',
    ['$scope', '$stateParams', '$ionicLoading', 'utils', 'dateUtils', 'Activity',
    function($scope, $stateParams, $ionicLoading, utils, dateUtils, Activity) {

    $ionicLoading.show();
    // Incoming formatter
    var formatter = function(item){
        return {
            description: 'sent ' + dateUtils.ts2h(
                Date.parse(item.created_date)),
            name: item.sender.name,
            notification_url: '#/app/tab/incoming_notification/' + item.id,
            request_url: '#/app/tab/incoming_request/' + item.id
        };
    };
    var loadItems = function() {
        // Load incoming items
        return Activity.incoming().then(function (data) {
            $scope.messages = utils.formatMessages(data.data, formatter);
            $scope.viewTitle = 'Incoming';
        }, function (data) {
            utils.alert('Error', 'Error loading data');
            console.error(data);
        }).finally(function () {
            $ionicLoading.hide();
        });
    };

    loadItems().finally(function(){
        $ionicLoading.hide();
    });

    $scope.refresh = function(){
        loadItems().finally(function(){
            $scope.$broadcast('scroll.refreshComplete');
        });
    };
}])

.controller('NotificationDetailCtrl',
            ['$scope', '$ionicHistory', '$ionicLoading', '$stateParams', 'map', 'Notification',
    function($scope, $ionicHistory, $ionicLoading, $stateParams, map, Notification) {

        var stateName = $ionicHistory.currentView().stateName;
        $scope.isOutgoing = stateName.indexOf('outgoing') > -1;

        // XXX: Add $ionicLoading feature
        Notification.get($stateParams.id).then(function(data){
            $scope.item = data.data;
            $scope.icon = $scope.item.session.complete ? 'ion-ios-location': 'ion-ios-location-outline';
            var loc = $scope.item.location;
            $scope.map = map.createMap('locmap', loc.lat, loc.lng);
            $scope.marker = map.createMarker($scope.map, loc.lat, loc.lng);
        });
    }
])

.controller('RequestDetailCtrl',
    ['$scope', '$rootScope', '$ionicLoading', '$ionicHistory', '$http', '$stateParams', 'map',
     'utils', 'Request', 'Notification',
    function($scope, $rootScope, $ionicLoading, $ionicHistory, $http, $stateParams, map, utils,
             Request, Notification) {

        var stateName = $ionicHistory.currentView().stateName;
        var showBrowserWarning = false;
        var populateMarkers = function(notifs){
            for (var i = 0; i < notifs.length; i++){
                var item = notifs[i];
                var loc = item.location;
                if (item.is_web){
                    showBrowserWarning = true;
                }
                if ($scope.map){
                    $scope.markers.push(
                        map.createMarker(
                            $scope.map, loc.lat, loc.lng, i, item.is_web));
                }
            }
        };
        var requestCallback = function(data){
            $scope.item = data.data;
            $scope.icon = $scope.item.session.complete ? 'ion-ios-bolt': 'ion-ios-bolt-outline';
            $scope.markers = [];
            $scope.form.token = $scope.item.session.token;
            // Load map
            map.getCurrentLocation('locmap').then(function(data) {
                $scope.map = data.map;
                $scope.marker = data.marker;
                $rootScope.currentLatLng = {lat: data.lat, lng: data.lng};
                populateMarkers($scope.item.notifications);
                $scope.showBrowserWarning = showBrowserWarning;
            });
        };
        $scope.isOutgoing = stateName.indexOf('outgoing') > -1;
        $scope.form = {};
        $scope.sendLocation = function(){
            $ionicLoading.show();
            Notification.post($scope.form, $rootScope.currentLatLng.lat,
                              $rootScope.currentLatLng.lng)
            .then(function(data){
                $ionicLoading.hide();
                // Reload request
                Request.get($stateParams.id).then(requestCallback);
                utils.toast('Location submitted');
            }, function(data){
                $ionicLoading.hide();
                utils.alert('Error', data.message || 'Failed to send request');
            });
        };

        Request.get($stateParams.id).then(requestCallback);
    }
])

.factory('ctrlUtils', ['$ionicLoading', 'utils', function($ionicLoading, utils) {
    return {
        selectUser: function ($scope, name) {
            // Hack for deselected radio button. This will avoid creating
            // a custom radio button directive.
            // Idea: http://jsfiddle.net/8s4m2e5e/3/
            if ($scope.selectedUser === $scope.form.username) {
                $scope.form.username = false;
            }
            $scope.selectedUser = $scope.form.username;
            $scope.selectedName = name;
        },
        messageSuccess: function($scope, modal, status){
            $ionicLoading.hide();
            modal.hide();
            utils.toast(status);
            // Update recent contacts
            utils.manageRecent(
                $rootScope.recentContacts, $rootScope.recentFriends,
                $rootScope.friends, $scope.form, $scope.selectedName);
            $scope.form = {};  // Clear form
            return function(data){};
        },
        messageError: function(default_error) {
            return function(data){
                $ionicLoading.hide();
                utils.alert('Error ', data.message || default_error);
            };
        }
    };
}]);
