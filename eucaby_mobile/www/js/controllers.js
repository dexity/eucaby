'use strict';

angular.module('eucaby.controllers', [
    'eucaby.services',
    'eucaby.utils',
    'eucaby.api',
    'eucaby.push'
])
.controller('MainCtrl', [
    '$scope',
    '$rootScope',
    '$state',
    '$ionicSideMenuDelegate',
    'storageManager',
    'EucabyApi',
    'utils',
    'utilsIonic',
function($scope, $rootScope, $state, $ionicSideMenuDelegate, storageManager,
         EucabyApi, utils, utilsIonic) {

    $scope.alignedTitle = function(){
        return utilsIonic.urlHasSubstring('request');
    };

    $scope.showSideMenu = function(){
        return $scope.showHeader();
    };

    $scope.toggleRight = function(){
        $ionicSideMenuDelegate
            .toggleRight(!$ionicSideMenuDelegate.isOpenRight());
    };

    $scope.showHeader = function(){
        return $state.is('app.tab.map');
    };

    $rootScope.hasBackButton = function(){
        return utilsIonic.hasBackButton();
    };

    $scope.logout = function () {
        EucabyApi.logout();
        $state.go('app.login');
    };

    // Init controller
    $rootScope.currentZoom = 13;
    $rootScope.contactsHistory = {};
    $rootScope.recentContacts = storageManager.getRecentContacts() || [];
    $rootScope.recentFriends = storageManager.getRecentFriends() || {};
}])

.controller('LoginCtrl', [
    '$scope',
    '$rootScope',
    '$location',
    '$ionicLoading',
    'EucabyApi',
    'notifications',
    'utils',
    'utilsIonic',
function($scope, $rootScope, $location, $ionicLoading, EucabyApi,
         notifications, utils, utilsIonic) {

    $scope.facebookLogin = function(){
        $ionicLoading.show();
        EucabyApi.login().then(function() {
                $location.path('/app/tab/map');
                notifications.init($rootScope);
            }, function(data) {
                utilsIonic.alert('Error', 'Error during log in. ' +
                                     'Please try again in a moment.');
                console.error(data);
        })
        .finally(function(){
            $ionicLoading.hide();
        });
    };
}])

.controller('MapCtrl', [
    '$scope',
    '$rootScope',
    '$http',
    '$ionicModal',
    '$ionicLoading',
    'map',
    'utils',
    'utilsIonic',
    'mapIonic',
    'Friends',
function($scope, $rootScope, $http, $ionicModal, $ionicLoading, map, utils,
         utilsIonic, mapIonic, Friends) {

    // Center on me action
    $scope.centerOnMe = function(hideLoading) {
        if (!hideLoading){
            $ionicLoading.show();
        }
        map.currentLocation(function(lat, lng){
            // Create a new map
            // Note: There might be performance issues when creating
            //       map for every current location click
            $scope.map = map.createMap('map', lat, lng,
                                       {zoom: $scope.currentZoom});
            $scope.marker = map.createMarker($scope.map, lat, lng);
            google.maps.event.addListener(
                $scope.map, 'zoom_changed', function() {
                $rootScope.currentZoom = $scope.map.getZoom();
            });
            if (!hideLoading) {
                $ionicLoading.hide();
            }
        },
        function(data){
            $scope.map = map.createMap('map');
            if (!hideLoading) {
                $ionicLoading.hide();
            }
            utilsIonic.alert('Location Error',
                        'Unable to get location: ' + data.message);
        });
    };

    $scope.registerModal = function(template, modalName){
        $ionicModal.fromTemplateUrl(template, {
            scope: $scope
        }).then(function(modal) {
            $scope[modalName] = modal;
        });
    };

    $scope.loadFriends = function(){
        // Loads friends
        return Friends.all().then(function(data){
            $rootScope.friends = data.data;
            utils.syncFriendsWithRecent(
                $rootScope.recentFriends, $rootScope.friends);
        }, function(data){
            utilsIonic.alert('Error', 'Error loading friends');
            console.error(data);
        });
    };

    $scope.refreshFriends = function(){
        $ionicLoading.show();
        $scope.loadFriends().finally(function(){
            $ionicLoading.hide();
        });
    };

    $scope.isFormValid = function(form){
        // Main form validation
        var emailValue = form.email.$viewValue;
        var userValue = form.user.$viewValue;
        if ((!emailValue && !userValue) || (emailValue && userValue)){
            utilsIonic.alert(
                'Error', 'Please provide either an email or select a friend');
            return false;
        }

        // Note: We use type="text" for email instead of type="email" because
        //       email type triggers ng-change expression only when email is
        //       valid. This is not what we want. ng-change should trigger
        //       every type user types in the input field. So we explicitly
        //       validate email field instead of form.email.$invalid
        if (emailValue && !utils.validEmail(emailValue)) {
            utilsIonic.alert('Error', 'Please provide a valid email');
            return false;
        }
        return true;
    };

    $scope.modalShownHandler = function(event, modal) {
        // Modal shown event handler
        if (angular.equals($scope.friends, [])){
            $scope.loadFriends();
        }
        if ($scope.notifyModal === modal) {
            mapIonic.getCurrentLocation('notifymap').then(function(data) {
                $scope.map = data.map;
                $scope.marker = data.marker;
                $rootScope.currentLatLng = {lat: data.lat, lng: data.lng};
            });
        }
    };

    // Init controller
    $scope.centerOnMe(true);
    $scope.markers = [];
    $rootScope.friends = [];
    $scope.registerModal('templates/request.html', 'requestModal');
    $scope.registerModal('templates/notify.html', 'notifyModal');
    $scope.$on('modal.shown', $scope.modalShownHandler);
}])

.controller('MessageCtrl', [
    '$scope',
    '$rootScope',
    '$ionicLoading',
    'utils',
    'ctrlUtils',
    'Request',
    'Notification',
    'Autocomplete',
function($scope, $rootScope, $ionicLoading, utils, ctrlUtils, Request,
         Notification, Autocomplete) {

    $scope.selectUser = function(name){
        ctrlUtils.selectUser($scope, name);
    };

    // Autocomplete
    $scope.autoTyping = function(){
        // On change input value function
        Autocomplete.query($scope.form.email).then(function(data){
            $scope.autoItems = data.data;
        });
    };

    $scope.autoComplete = function(item){
        // On click autocompleted item function
        $scope.autoItems = [];
        $scope.form.email = item;
    };

    $scope.sendRequestHandler = function(event){
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
    };

    $scope.sendLocationHandler = function(event){
        // Send location action
        // Note: We you here signal because form is triggered outside controller
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
    };

    // Init controller
    $scope.form = {};
    $scope.$on('sendRequest', $scope.sendRequestHandler);
    $scope.$on('sendLocation', $scope.sendLocationHandler);
}])

.controller('ProfileCtrl', [
    '$scope',
    '$ionicLoading',
    'utils',
    'dateUtils',
    'utilsIonic',
    'User',
function($scope, $ionicLoading, utils, dateUtils, utilsIonic, User) {

    $ionicLoading.show();
    User.profile().then(function(data){
        $scope.profile = data.data;
        $scope.profile.date_joined = dateUtils.ts2hd(
            Date.parse(data.data.date_joined), true);
    }, function(data){
        utilsIonic.alert('Failed to load user profile');
        console.error(data);
    }).finally(function(){
        $ionicLoading.hide();
    });
}])

.controller('SettingsCtrl', [
    '$scope',
    '$ionicLoading',
    'utils',
    'utilsIonic',
    'Settings',
function($scope, $ionicLoading, utils, utilsIonic, Settings) {

    var setEmailSubscription = function(data){
        // Sets email subscription checkbox based from data
        var emailSub = data.data.email_subscription;
        if (emailSub === null){
            emailSub = true; // Default is true
        }
        $scope.emailSubscription.checked = emailSub;
    };

    $scope.emailSubscriptionChange = function() {
        $ionicLoading.show();
        var postData = {email_subscription: $scope.emailSubscription.checked};
        Settings.post(postData).then(function(data){
            setEmailSubscription(data);
        }, function(data){
            utilsIonic.alert('Failed to update settings');
        }).finally(function(){
            $ionicLoading.hide();
        });
        console.log('Push Notification Change', $scope.emailSubscription.checked);
    };

    // Init controller
    $scope.emailSubscription = { checked: false };
    $ionicLoading.show();
    Settings.get().then(function(data){
        setEmailSubscription(data);
    }, function(data){
        utilsIonic.alert('Failed to load settings');
    }).finally(function(){
        $ionicLoading.hide();
    });
}])

.controller('OutgoingCtrl', [
    '$scope',
    '$stateParams',
    '$ionicLoading',
    'utils',
    'dateUtils',
    'utilsIonic',
    'Activity',
function($scope, $stateParams, $ionicLoading, utils, dateUtils, utilsIonic,
         Activity) {

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
            utilsIonic.alert('Error', 'Error loading data');
            console.error(data);
        });
    };

    $scope.refresh = function(){
        loadItems().finally(function(){
            $scope.$broadcast('scroll.refreshComplete');
        });
    };

    // Init controller
    $ionicLoading.show();
    loadItems().finally(function(){
        $ionicLoading.hide();
    });
}])

.controller('IncomingCtrl', [
    '$scope',
    '$ionicLoading',
    'utils',
    'dateUtils',
    'utilsIonic',
    'Activity',
function($scope, $ionicLoading, utils, dateUtils, utilsIonic, Activity) {

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
            utilsIonic.alert('Error', 'Error loading data');
            console.error(data);
        }).finally(function () {
            $ionicLoading.hide();
        });
    };

    $scope.refresh = function(){
        loadItems().finally(function(){
            $scope.$broadcast('scroll.refreshComplete');
        });
    };

    // Init controller
    $ionicLoading.show();
    loadItems().finally(function(){
        $ionicLoading.hide();
    });
}])

.controller('NotificationDetailCtrl', [
    '$scope',
    '$ionicLoading',
    '$stateParams',
    'map',
    'utils',
    'utilsIonic',
    'Notification',
function($scope, $ionicLoading, $stateParams, map, utils, utilsIonic,
         Notification) {

    // Init controller
    $scope.isOutgoing = utilsIonic.urlHasSubstring('outgoing');
    // XXX: Add $ionicLoading feature
    Notification.get($stateParams.id).then(function(data){
        $scope.item = data.data;
        $scope.icon = $scope.item.session.complete ? 'ion-ios-location': 'ion-ios-location-outline';
        var loc = $scope.item.location;
        $scope.map = map.createMap('locmap', loc.lat, loc.lng);
        $scope.marker = map.createMarker(
            $scope.map, loc.lat, loc.lng, -1, $scope.item.is_web);
    });
}])

.controller('RequestDetailCtrl', [
    '$scope',
    '$rootScope',
    '$ionicLoading',
    '$http',
    '$stateParams',
    'map',
    'utils',
    'mapIonic',
    'utilsIonic',
    'ctrlUtils',
    'Request',
    'Notification',
function($scope, $rootScope, $ionicLoading, $http, $stateParams, map, utils,
         mapIonic, utilsIonic, ctrlUtils, Request, Notification) {

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
        mapIonic.getCurrentLocation('locmap').then(function(data) {
            $scope.map = data.map;
            $scope.marker = data.marker;
            $rootScope.currentLatLng = {lat: data.lat, lng: data.lng};
            populateMarkers($scope.item.notifications);
            $scope.centerMarker($rootScope.currentLatLng);
            $scope.showBrowserWarning = showBrowserWarning;
        });
    };

    $scope.sendLocation = function(event) {
        // Send request action
        $ionicLoading.show();
        Notification.post($scope.form, $rootScope.currentLatLng.lat,
                          $rootScope.currentLatLng.lng)
        .then(function(data){
            $ionicLoading.hide();
            // Reload request
            Request.get($stateParams.id).then(requestCallback);
            utilsIonic.toast('Location submitted');
            $scope.form = {};
        }, ctrlUtils.messageError('Failed to send request'));
    };

    $scope.centerMarker = function(loc) {
        // Centers map at marker's location
        $scope.map.setCenter(loc);
    };

    $scope.centerOnMe = function() {
        // Centers map at the current location
        // Note: Location is obtain again in case if user is moving.
        //       Other option is to use stale $rootScope.currentLatLng
        $ionicLoading.show();
        map.currentLocation(function(lat, lng){
            if ($scope.map){
                var position = new google.maps.LatLng(lat, lng);
                $scope.centerMarker(position);
            }
            $ionicLoading.hide();
        });
    };

    // Init controller
    var showBrowserWarning = false;
    $scope.isOutgoing = utilsIonic.urlHasSubstring('outgoing');
    $scope.form = {};
    Request.get($stateParams.id).then(requestCallback);
}])

.factory('ctrlUtils', [
    '$rootScope',
    '$ionicLoading',
    'utils',
    'utilsIonic',
function($rootScope, $ionicLoading, utils, utilsIonic) {
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
            utilsIonic.toast(status);
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
                utilsIonic.alert('Error ', data.message || default_error);
            };
        }
    };
}]);
