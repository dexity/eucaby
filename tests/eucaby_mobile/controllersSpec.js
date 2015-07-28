'use strict';

describe('main controller tests', function() {
    var $scope,
        $state,
        EucabyApi,
        $httpBackend,
        storageManager;
    var stateIsMock,
        contactsMock,
        friendsMock;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        $rootScope, _$state_, _$httpBackend_, _EucabyApi_, _storageManager_){
        $scope = $rootScope.$new();
        $state = _$state_;
        $httpBackend = _$httpBackend_;
        EucabyApi = _EucabyApi_;
        storageManager = _storageManager_;
    }));
    beforeEach(function(){
        spyOn(EucabyApi, 'logout');
        spyOn($state, 'go');
        stateIsMock = spyOn($state, 'is');
        contactsMock = spyOn(storageManager, 'getRecentContacts');
        friendsMock = spyOn(storageManager, 'getRecentFriends');
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        $controller('MainCtrl', {
            $scope: $scope, EucabyApi: EucabyApi
        });
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should define logout', function(){
        $scope.logout();
        expect(EucabyApi.logout).toHaveBeenCalled();
        expect($state.go).toHaveBeenCalledWith('app.login');
        $httpBackend.flush();
    });

    it('should set recent friends and contacts', inject(function($controller){
        // Initially there are no recent contacts or friends
        expect($scope.recentContacts).toEqual([]);
        expect($scope.recentFriends).toEqual({});

        var contacts = [{hello: 'world'}],
            friends = {user1: {user: 'user1'}};
        contactsMock.and.returnValue(contacts);
        friendsMock.and.returnValue(friends);
        $controller('MainCtrl',
                    {$scope: $scope, storageManager: storageManager});
        expect($scope.recentContacts).toEqual(contacts);
        expect($scope.recentFriends).toEqual(friends);
        $httpBackend.flush();
    }));

    it('should show header for map view', function(){
        stateIsMock.and.returnValue(true);
        expect($scope.showHeader()).toEqual(true);
        expect($state.is).toHaveBeenCalledWith('app.tab.map');
        $httpBackend.flush();
    });
});

describe('login controller tests', function(){

    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        $location,
        EucabyApi,
        notifications,
        utilsIonic,
        deferred;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _$location_,
        _EucabyApi_, _notifications_, _utilsIonic_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        $location = _$location_;
        EucabyApi = _EucabyApi_;
        notifications = _notifications_;
        utilsIonic = _utilsIonic_;
    }));
    beforeEach(function(){
        deferred = $q.defer();
        spyOn(EucabyApi, 'login').and.callFake(function(){
            return deferred.promise;
        });
        spyOn($ionicLoading, 'show');
        spyOn($ionicLoading, 'hide');
        spyOn($location, 'path');
        spyOn(notifications, 'init');
        spyOn(utilsIonic, 'alert');
    });
    beforeEach(inject(function($controller){
        $controller('LoginCtrl', {
            $scope: $scope, EucabyApi: EucabyApi, notifications: notifications
        })
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should go to map view after successful login', function(){
        deferred.resolve();
        $scope.facebookLogin();
        $scope.$apply();
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        expect($location.path).toHaveBeenCalledWith('/app/tab/map');
        expect(notifications.init).toHaveBeenCalledWith();
    });

    it('should display error after failed login', function(){
        deferred.reject('facebookLogin error');
        $scope.facebookLogin();
        $scope.$apply();
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        expect(utilsIonic.alert).toHaveBeenCalled();
    });
});

describe('map controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $window,
        $ionicLoading,
        $ionicModal,
        Friends,
        map,
        utilsIonic,
        mapIonic,
        deferred;
    var locMock,
        tmplMock,
        friendsMock;
    var mapMock = jasmine.createSpy(),
        markerMock = jasmine.createSpy();

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$window_, _$ionicLoading_,
        _$ionicModal_, _Friends_, _map_, _utilsIonic_, _mapIonic_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $window = _$window_;
        $ionicLoading = _$ionicLoading_;
        $ionicModal = _$ionicModal_;
        Friends = _Friends_;
        map = _map_;
        utilsIonic = _utilsIonic_;
        mapIonic = _mapIonic_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        locMock = spyOn(map, 'currentLocation');
        spyOn(map, 'createMap').and.returnValue(mapMock);
        spyOn(map, 'createMarker').and.returnValue(markerMock);
        // $ionicModal.fromTemplateUrl makes 2 http requests
        tmplMock = spyOn($ionicModal, 'fromTemplateUrl');
        tmplMock.and.callFake(function(){
            return deferred.promise;
        });
        friendsMock = spyOn(Friends, 'all');
        spyOn($ionicLoading, 'show');
        spyOn($ionicLoading, 'hide');
        spyOn(utilsIonic, 'alert');
        $window.google = {
            maps: {event: {addListener: jasmine.createSpy()}}
        };
    });
    beforeEach(inject(function($controller){
        $controller('MapCtrl', {
            $scope: $scope, map: map
        });
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should init', function(){
        // Note: Functions created in controller cannot be mocked
        //       so we test functions call by methods which they use inside
        expect($scope.markers).toEqual([]);
        expect($scope.friends).toEqual([]);
        expect(map.currentLocation).toHaveBeenCalled();
        // Register request and notification modals
        expect($ionicModal.fromTemplateUrl.calls.count()).toEqual(2);
    });

    it('should center on me and set current location', function(){
        locMock.and.callFake(function () {
            arguments[0](1.2, 3.4);
        });
        $scope.centerOnMe();
        $scope.$apply();
        expect($scope.map).toBeDefined();
        expect($scope.marker).toBeDefined();
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        expect(map.createMap).toHaveBeenCalled();
        expect(map.createMarker).toHaveBeenCalled();
    });

    it('should center on me and hide loading', function(){
        locMock.and.callFake(function () {
            arguments[0](1.2, 3.4);
        });
        $scope.centerOnMe(true);
        $scope.$apply();
        expect($ionicLoading.show.calls.any()).toEqual(false);
        expect($ionicLoading.hide.calls.any()).toEqual(false);
        expect($window.google.maps.event.addListener).toHaveBeenCalled();
    });

    it('should center on me and show error', function(){
        locMock.and.callFake(function () {
            arguments[1]('Some error');
        });
        $scope.centerOnMe();
        $scope.$apply();
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        expect(map.createMap).toHaveBeenCalled();
        expect(utilsIonic.alert).toHaveBeenCalled();
        expect(map.createMarker.calls.any()).toEqual(false);
    });

    it('should register model', function(){
        $ionicModal.fromTemplateUrl.calls.reset();
        deferred.resolve('some_modal');
        $scope.registerModal('template.html', 'notification');
        expect($ionicModal.fromTemplateUrl)
            .toHaveBeenCalledWith('template.html', {scope: $scope});
        $scope.$apply();
        expect($scope.notification).toBeDefined();
    });

    it('should load friends', function(){
        deferred = $q.defer();
        friendsMock.and.callFake(function(){
            return deferred.promise;
        });
        var recentFriends = {
            user1: {name: 'User 1', username: 'user1'},
            user2: {name: 'User 2', username: 'user2'}
        };
        var recentFriendsCopy = angular.copy(recentFriends);
        var friends = [
            {name: 'User X', username: 'userx'},
            {name: 'User 2', username: 'user2'}];
        $rootScope.recentFriends = recentFriends;
        deferred.resolve({data: friends});
        $scope.loadFriends();
        $scope.$apply();
        expect(Friends.all).toHaveBeenCalled();
        expect($rootScope.friends)
            .toEqual([{name: 'User X', username: 'userx'}]);
        expect($rootScope.recentFriends).toEqual(recentFriendsCopy);
    });

    it('should load friends with error', function(){
        deferred = $q.defer();
        friendsMock.and.callFake(function(){
            return deferred.promise;
        });
        deferred.reject('loadFriends error');
        $scope.loadFriends();
        $scope.$apply();
        expect(utilsIonic.alert).toHaveBeenCalled();
    });

    it('should refresh friends', function(){
        deferred = $q.defer();
        spyOn($scope, 'loadFriends').and.callFake(function(){
            return deferred.promise;
        });
        deferred.resolve({data: []});
        $scope.refreshFriends();
        expect($scope.loadFriends).toHaveBeenCalled();
        expect($ionicLoading.show).toHaveBeenCalled();
        // expect($ionicLoading.hide).toHaveBeenCalled();
    });

    it('should check if form is valid', function(){
        var form;
        // Empty form
        expect($scope.isFormValid({})).toEqual(false);
        expect(utilsIonic.alert).toHaveBeenCalled();
        // Invalid email
        form = {email: 'wrong'};
        expect($scope.isFormValid(form)).toEqual(false);
        expect(utilsIonic.alert).toHaveBeenCalled();
        // Valid email
        form = {email: 'some@email'};
        expect($scope.isFormValid(form)).toEqual(true);
        // Both email and user are set
        form = {email: 'some@email', user: 'user1'};
        expect($scope.isFormValid(form)).toEqual(false);
        expect(utilsIonic.alert).toHaveBeenCalled();
        // User is set
        form = {user: 'user1'};
        expect($scope.isFormValid(form)).toEqual(true);
    });

    it('should handle modal.shown event', function(){
        spyOn($scope, 'loadFriends');
        deferred = $q.defer();
        spyOn(mapIonic, 'getCurrentLocation').and.callFake(function(){
            return deferred.promise;
        });
        deferred.resolve({
             map: 'somemap', marker: 'somemarker', lat: 1.2, lng: 3.4});
        // Friends are not populated
        expect($scope.friends).toEqual([]);
        $scope.modalShownHandler(null, 'notification');
        expect($scope.loadFriends).toHaveBeenCalled();
        expect(mapIonic.getCurrentLocation.calls.any()).toEqual(false);

        // Friends is populated
        $scope.loadFriends.calls.reset();
        $scope.notifyModal = 'notification';
        $scope.friends = [{name: 'User 1', username: 'user1'}];
        expect($scope.map).toBeUndefined();
        expect($scope.marker).toBeUndefined();
        expect($scope.currentLatLng).toBeUndefined();

        $scope.modalShownHandler(null, 'notification');  // Run function
        $scope.$apply();
        expect($scope.loadFriends.calls.any()).toEqual(false);
        expect($scope.map).toEqual('somemap');
        expect($scope.marker).toEqual('somemarker');
        expect($scope.currentLatLng).toEqual({lat: 1.2, lng: 3.4});
    });
});

describe('message controller tests', function(){
    var $q,
        $rootScope,
        $mapScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        $ionicModal,
        Autocomplete,
        Request,
        Notification,
        ctrlUtils,
        utils,
        deferred;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _$ionicModal_,
        _Autocomplete_, _Request_, _Notification_, _ctrlUtils_, _utils_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $mapScope = $rootScope.$new();
        $scope = $mapScope.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        Autocomplete = _Autocomplete_;
        Request = _Request_;
        Notification = _Notification_;
        ctrlUtils = _ctrlUtils_;
        utils = _utils_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        spyOn(ctrlUtils, 'selectUser');
        spyOn(utils, 'manageRecent');
        spyOn($ionicLoading, 'show');
        spyOn($ionicLoading, 'hide');
        $scope.requestModal = {
            hide: jasmine.createSpy()
        };
        $scope.notifyModal = {
            hide: jasmine.createSpy()
        };
        spyOn(ctrlUtils, 'messageSuccess').and.callThrough();
        spyOn(ctrlUtils, 'messageError').and.callThrough();
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        // Hierarchy of controllers: MapCtrl <- MessageCtrl
        $controller('MapCtrl', {$scope: $mapScope});
        $controller('MessageCtrl', {
            $scope: $scope, ctrlUtils: ctrlUtils
        });
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should select user', function(){
        $scope.selectUser('Test User');
        expect(ctrlUtils.selectUser).toHaveBeenCalledWith($scope, 'Test User');
        $httpBackend.flush();
    });

    it('should auto type text', function(){
        spyOn(Autocomplete, 'query').and.callFake(function(){
            return deferred.promise;
        });
        $scope.form = {
            email: 'some'
        };
        deferred.resolve({data: ['some@email1', 'some@email2']})
        $scope.autoTyping();
        $scope.$apply();
        expect($scope.autoItems).toEqual(['some@email1', 'some@email2']);
        $httpBackend.flush();
    });

    it('should autocomplete text', function(){
        $scope.autoItems = ['some@email1', 'some@email2'];
        $scope.autoComplete('test@email');
        expect($scope.autoItems).toEqual([]);
        expect($scope.form.email).toEqual('test@email');
        $httpBackend.flush();
    });

    it('should handle sendRequest event with success', function(){
        $scope.form = {email: 'some@email'};
        spyOn(Request, 'post').and.callFake(function(){
            return deferred.promise;
        });
        deferred.resolve();
        $scope.sendRequestHandler();
        expect(ctrlUtils.messageSuccess).toHaveBeenCalledWith(
            $scope, $scope.requestModal, 'Request submitted');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        $httpBackend.flush();
    });

    it('should handle sendRequest event with error', function(){
        $scope.form = {email: 'some@email'};
        spyOn(Request, 'post').and.callFake(function(){
            return deferred.promise;
        });
        deferred.reject({});
        $scope.sendRequestHandler();
        expect(Request.post).toHaveBeenCalledWith({email: 'some@email'});
        expect(ctrlUtils.messageError).toHaveBeenCalledWith(
            'Failed to send request');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        $httpBackend.flush();
    });

    it('should handle sendLocation event with success', function(){
        $scope.form = {email: 'some@email'};
        $rootScope.currentLatLng = {lat: 1.2, lng: 3.4};
        spyOn(Notification, 'post').and.callFake(function(){
            return deferred.promise;
        });
        deferred.resolve();
        $scope.sendLocationHandler();
        expect(Notification.post).toHaveBeenCalledWith(
            {email: 'some@email'}, 1.2, 3.4);
        expect(ctrlUtils.messageSuccess).toHaveBeenCalledWith(
            $scope, $scope.notifyModal, 'Location submitted');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        $httpBackend.flush();
    });

    it('should handle sendRequest event with error', function(){
        $scope.form = {email: 'some@email'};
        $rootScope.currentLatLng = {lat: 1.2, lng: 3.4};
        spyOn(Notification, 'post').and.callFake(function(){
            return deferred.promise;
        });
        deferred.reject({});
        $scope.sendLocationHandler();
        expect(ctrlUtils.messageError).toHaveBeenCalledWith(
            'Failed to send location');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        $httpBackend.flush();
    });

});

describe('profile controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        utilsIonic,
        User,
        deferred;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _User_,
        _utilsIonic_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        User = _User_;
        utilsIonic = _utilsIonic_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        spyOn(utilsIonic, 'alert');
        spyOn($ionicLoading, 'show');
        spyOn($ionicLoading, 'hide');
        spyOn(User, 'profile').and.callFake(function(){
            return deferred.promise;
        });
        var tsDate = new Date(1437338776000);  // July 19, 2015
        jasmine.clock().mockDate(tsDate);  // Mock current date with tsDate
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        $controller('ProfileCtrl', {$scope: $scope})
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should load profile when success', function(){
        var data = {data: {name: 'UserA', username: 'user1',
            date_joined: '2015-07-17T22:43:19+00:00'}};
        deferred.resolve(data);
        $scope.$apply();
        expect($scope.profile).toEqual({name: 'UserA', username: 'user1',
            date_joined: 'Jul 17, 2015 3:43 pm'});
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
    });

    it('should show error when loading profile', function(){
        deferred.reject('Profile error');
        $scope.$apply();
        expect(utilsIonic.alert)
            .toHaveBeenCalledWith('Failed to load user profile');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
    });
});

describe('settings controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        Settings,
        utilsIonic,
        deferred,
        deferredPost;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _Settings_,
        _utilsIonic_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        Settings = _Settings_;
        utilsIonic = _utilsIonic_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        deferredPost = $q.defer();
        spyOn($ionicLoading, 'show');
        spyOn($ionicLoading, 'hide');
        spyOn(Settings, 'get').and.callFake(function(){
            return deferred.promise;
        });
        spyOn(Settings, 'post').and.callFake(function(){
            return deferredPost.promise;
        });
        spyOn(utilsIonic, 'alert');
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        $controller('SettingsCtrl', {$scope: $scope});
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should init settings controller with success', function(){
        // Success
        deferred.resolve({data: {email_subscription: true}});
        $scope.$apply();
        expect($scope.emailSubscription.checked).toEqual(true);
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
    });

    it('should init settings controller with error', function(){
        deferred.reject('Settings get error');
        $scope.$apply();
        expect($scope.emailSubscription.checked).toEqual(false);
        expect(utilsIonic.alert)
            .toHaveBeenCalledWith('Failed to load settings');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
    });

    it('should set email subscription', function(){
        // Parameter is not set, default is true
        var data = {data: {email_subscription: null}};
        $scope.setEmailSubscription(data);
        expect($scope.emailSubscription.checked).toEqual(true);
        // Parameter is true
        data = {data: {email_subscription: false}};
        $scope.setEmailSubscription(data);
        expect($scope.emailSubscription.checked).toEqual(false);
    });

    it('should email subscription change with success', function(){
        var data = {data: {email_subscription: true}};
        deferredPost.resolve(data);
        $scope.emailSubscriptionChange();
        $scope.$apply();
        expect(Settings.post).toHaveBeenCalledWith({email_subscription: false});
        expect($scope.emailSubscription.checked).toEqual(true);
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
    });

    it('should email subscription change with error', function(){
        deferredPost.reject('Settings post error');
        $scope.emailSubscriptionChange();
        $scope.$apply();
        expect(Settings.post).toHaveBeenCalledWith({email_subscription: false});
        expect($scope.emailSubscription.checked).toEqual(false);
        expect(utilsIonic.alert)
            .toHaveBeenCalledWith('Failed to update settings');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
    });
});

describe('messages list controller tests', function(){
    var $q,
        $state,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        Activity,
        utilsIonic,
        deferredInc,
        deferredOut,
        createController;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$state_, _$rootScope_, _$httpBackend_, _$ionicLoading_,
        _Activity_, _utilsIonic_){
        $q = _$q_;
        $state = _$state_;
        $rootScope = _$rootScope_;
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        Activity = _Activity_;
        utilsIonic = _utilsIonic_;
    }));
    beforeEach(function() {
        deferredInc = $q.defer();
        deferredOut = $q.defer();
        spyOn($ionicLoading, 'show');
        spyOn($ionicLoading, 'hide');
        spyOn(utilsIonic, 'alert');
        spyOn(Activity, 'incoming').and.callFake(function(){
            return deferredInc.promise;
        });
        spyOn(Activity, 'outgoing').and.callFake(function(){
            return deferredOut.promise;
        });
        jasmine.clock().mockDate(new Date(1437338776000));  // July 19, 2015
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        createController = function(){
            return $controller('MessagesListCtrl', {$scope: $scope});
        };
        createController();
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should init messages list controller', inject(function(){
        deferredInc.reject('Messages list error');
        $scope.$apply();
        expect($scope.type).toEqual('incoming');
        expect(Activity.incoming).toHaveBeenCalled();
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();

        spyOn($state, 'is').and.returnValue(true);
        createController();
        expect($scope.type).toEqual('outgoing');
        expect(Activity.outgoing).toHaveBeenCalled();
    }));

    it('should define outgoing formatter', function(){
        var item = {
            id: 123,
            created_date: '2015-07-17T22:43:19+00:00',
            recipient: {name: 'UserA', email: 'some@email'}
        },
        res = {
            description: 'received 1 d 22 hr ago',
            name: 'UserA',
            notification_url: '#/app/tab/outgoing_notification/123',
            request_url: '#/app/tab/outgoing_request/123'
        };
        expect($scope.outgoingFormatter(item)).toEqual(res);
    });

    it('should define incoming formatter', function(){
        var item = {
            id: 123,
            created_date: '2015-07-17T22:43:19+00:00',
            sender: {name: 'UserB'}
        },
        res = {
            description: 'sent 1 d 22 hr ago',
            name: 'UserB',
            notification_url: '#/app/tab/incoming_notification/123',
            request_url: '#/app/tab/incoming_request/123'
        };
        expect($scope.incomingFormatter(item)).toEqual(res);
    });

    it('should load incoming or outgoing messages with success', function(){
        // Outgoing messages (very similar to incoming messages)
        var data = {
            data: [
                {id: 123, type: 'notification', session: {complete: true},
                    recipient: {name: 'UserA'}, message: 'Some message',
                    created_date: '2015-07-17T22:43:19+00:00'}
            ]
        };
        var messages = [
            {item: data.data[0], complete: true, name: 'UserA',
                description: 'received 1 d 22 hr ago', message: 'Some message',
                url: '#/app/tab/outgoing_notification/123',
                icon: 'ion-ios-location'}
        ];
        $scope.type = 'outgoing';
        $scope.loadItems();
        deferredOut.resolve(data);
        $scope.$apply();
        expect($scope.messages).toEqual(messages);
        expect($scope.viewTitle).toEqual('Outgoing');
        expect(Activity.outgoing).toHaveBeenCalled();

        // Incoming messages
        Activity.incoming.calls.reset();
        $scope.type = 'incoming';
        $scope.loadItems();
        expect(Activity.incoming).toHaveBeenCalled();
    });

    it('should load incoming or outgoing messages with error', function() {
        // Outgoing messages
        $scope.type = 'outgoing';
        deferredOut.reject('Outgoing error');
        $scope.loadItems();
        $scope.$apply();
        expect(Activity.outgoing).toHaveBeenCalled();
        expect(utilsIonic.alert)
            .toHaveBeenCalledWith('Error', 'Error loading data');
    });

    it('should refresh messages and broadcast event', function(){
        var deferred = $q.defer();
        spyOn($scope, 'loadItems').and.callFake(function(){
            return deferred.promise;
        });
        spyOn($scope, '$broadcast');
        deferred.resolve();
        $scope.refresh();
        $scope.$apply();
        expect($scope.loadItems).toHaveBeenCalled();
        expect($scope.$broadcast)
            .toHaveBeenCalledWith('scroll.refreshComplete');
    });
});

describe('notification detail controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        map,
        Notification,
        deferred;
    var mapMock = jasmine.createSpy(),
        markerMock = jasmine.createSpy();

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _map_,
        _Notification_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        map = _map_;
        Notification = _Notification_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        spyOn($ionicLoading, 'show');
        spyOn($ionicLoading, 'hide');
        spyOn(map, 'createMap').and.returnValue(mapMock);
        spyOn(map, 'createMarker').and.returnValue(markerMock);
        spyOn(Notification, 'get').and.callFake(function(){
            return deferred.promise;
        });
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        $controller('NotificationDetailCtrl', {$scope: $scope});
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should get notification', function(){
        var data = {
            data: {
                session: {complete: true},
                location: {lat: 1.2, lng: 3.4},
                is_web: false
            }
        };
        deferred.resolve(data);
        $scope.$apply();
        expect($ionicLoading.show.calls.any()).toEqual(false);
        expect($ionicLoading.hide.calls.any()).toEqual(false);
        expect($scope.isOutgoing).toBeDefined();
        expect($scope.map).toEqual(mapMock);
        expect($scope.marker).toEqual(markerMock);
        expect($scope.item).toEqual(data.data);
        expect($scope.icon).toEqual('ion-ios-location');
        expect(map.createMap).toHaveBeenCalledWith('locmap', 1.2, 3.4);
        expect(map.createMarker)
            .toHaveBeenCalledWith($scope.map, 1.2, 3.4, -1, false);
    });
});

describe('request detail controller tests', function(){
    var $q,
        $window,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        map,
        Request,
        Notification,
        utilsIonic,
        mapIonic,
        deferredNotifPost,
        deferredReqGet,
        deferredLoc,
        reqData;
    var mapMock = jasmine.createSpyObj('map', ['setCenter']),
        markerMock = jasmine.createSpy('markerMock'),
        locMock = jasmine.createSpy('location');

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$window_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _map_,
        _Request_, _Notification_, _utilsIonic_, _mapIonic_){
        $q = _$q_;
        $window = _$window_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        map = _map_;
        Request = _Request_;
        Notification = _Notification_;
        utilsIonic = _utilsIonic_;
        mapIonic = _mapIonic_;
    }));
    beforeEach(function() {
        deferredNotifPost = $q.defer();
        deferredReqGet = $q.defer();
        deferredLoc = $q.defer();
        // Mock for angular ready
        spyOn(angular, 'element').and.callFake(function(){
            return {
                ready: function(){
                    arguments[0]();
                }
            }
        });
        spyOn($ionicLoading, 'show');
        spyOn($ionicLoading, 'hide');
        spyOn(utilsIonic, 'urlHasSubstring').and.returnValue(true);
        spyOn(map, 'createMap').and.returnValue(mapMock);
        spyOn(map, 'createMarker').and.returnValue(markerMock);
        spyOn(Notification, 'post').and.callFake(function(){
            return deferredNotifPost.promise;
        });
        spyOn(Request, 'get').and.callFake(function(){
            return deferredReqGet.promise;
        });
        spyOn(mapIonic, 'getCurrentLocation').and.callFake(function(){
            return deferredLoc.promise;
        });
        reqData = {
            data: {
                session: {complete: true, token: 'ABC'},
                notifications: [{
                        location: {lat: 1.2, lng: 3.4},
                        is_web: true}]
        }};
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        $controller('RequestDetailCtrl', {$scope: $scope});
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should init', function(){
        $rootScope.currentZoom = 5;
        deferredReqGet.resolve(reqData);
        $scope.$apply();
        expect($scope.map).toEqual(mapMock);
        expect($scope.marker).toEqual(markerMock);
        expect($scope.item).toEqual(reqData.data);
        expect($scope.icon).toEqual('ion-ios-bolt');
        expect($scope.form).toEqual({token: 'ABC'});
        expect($rootScope.currentLatLng).toEqual({lat: 1.2, lng: 3.4});
        expect($scope.isOutgoing).toEqual(true);
        expect($scope.showBrowserWarning).toEqual(true);
        expect(Request.get).toHaveBeenCalled();
        expect(map.createMap)
            .toHaveBeenCalledWith('locmap', 1.2, 3.4, {zoom: 5});
        expect(map.createMarker)
            .toHaveBeenCalledWith(mapMock, 1.2, 3.4, 0, true);
    });

    it('should populate markers', function(){
        // Only non-web notifications
        $scope.map = mapMock;
        var notifs = [
            {location: {lat: 1, lng: 2}, is_web: false}
        ];
        $scope.populateMarkers(notifs);
        expect($scope.showBrowserWarning).toEqual(false);
        expect($scope.markers.length).toEqual(1);

        // Mixed notifications
        notifs.push({location: {lat: 3, lng: 4}, is_web: true});
        $scope.populateMarkers(notifs);
        expect($scope.showBrowserWarning).toEqual(true);
        expect($scope.markers.length).toEqual(2);
    });

    it('should handle location', function(){
        // No notifications
        $scope.item = {notifications: []};
        $scope.locationHandler({map: mapMock});
        expect($scope.map).toEqual(mapMock);
        expect($scope.marker).toBeUndefined();
        expect($scope.markers).toEqual([]);
        expect($rootScope.currentLatLng)
            .toEqual({lat: undefined, lng: undefined});

        // Notifications are set
        $scope.map.setCenter.calls.reset();
        spyOn($scope, 'populateMarkers').and.callThrough();
        spyOn($scope, 'centerMarker').and.callThrough();
        $scope.item = {notifications: [
            {location: {lat: 1, lng: 2}, is_web: false},
            {location: {lat: 3, lng: 4}, is_web: true}
        ]};
        var data = {map: mapMock, marker: null, lat: 1.2, lng: 3.4};
        $scope.locationHandler(data);
        expect($scope.map).toEqual(mapMock);
        expect($scope.marker).toEqual($scope.markers[0]);
        expect($scope.markers.length).toEqual(2);
        expect($rootScope.currentLatLng)
            .toEqual({lat: 1.2, lng: 3.4});
        expect($scope.map.setCenter).toHaveBeenCalledWith({lat: 1.2, lng: 3.4});
        expect($scope.populateMarkers).toHaveBeenCalled();
        expect($scope.centerMarker).toHaveBeenCalled();
    });

    it('should handle request', function(){
        var dataMock = jasmine.createSpy('data');
        spyOn($scope, 'locationHandler');
        // Request is outgoing
        $scope.isOutgoing = true;
        $scope.requestHandler(reqData);
        expect($scope.item).toEqual(reqData.data);
        expect($scope.icon).toEqual('ion-ios-bolt');
        expect($scope.form).toEqual({token: 'ABC'});
        expect($scope.locationHandler)
            .toHaveBeenCalledWith({
                map: mapMock, marker: null, lat: 1.2, lng: 3.4});

        // Request is not outgoing
        $scope.locationHandler.calls.reset();
        $scope.isOutgoing = false;
        $scope.requestHandler(reqData);
        expect(mapIonic.getCurrentLocation).toHaveBeenCalledWith('locmap');
        deferredLoc.resolve(dataMock);
        $scope.$apply();
        expect($scope.locationHandler).toHaveBeenCalledWith(dataMock);
    });

    it('should send location with success', function(){
        $scope.form = {token: 'ABC'};
        $rootScope.currentLatLng = {lat: 1.2, lng: 3.4};
        var reqMock = jasmine.createSpy();
        Request.get.calls.reset();
        spyOn(utilsIonic, 'toast');
        spyOn($scope, 'requestHandler');
        deferredNotifPost.resolve(null);  // data don't matter
        deferredReqGet.resolve(reqData);
        $scope.sendLocation();
        expect(Notification.post)
            .toHaveBeenCalledWith({token: 'ABC'}, 1.2, 3.4);
        $scope.$apply();
        expect($scope.form).toEqual({});
        expect(Request.get).toHaveBeenCalled();
        expect($scope.requestHandler).toHaveBeenCalledWith(reqData);
        expect(utilsIonic.toast).toHaveBeenCalledWith('Location submitted');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
    });

    it('should send location with error', function(){
        $scope.form = {token: 'ABC'};
        $rootScope.currentLatLng = {lat: 1.2, lng: 3.4};
        spyOn(utilsIonic, 'alert');
        deferredNotifPost.reject({});
        $scope.sendLocation();
        expect(Notification.post)
            .toHaveBeenCalledWith({token: 'ABC'}, 1.2, 3.4);
        $scope.$apply();
        expect(utilsIonic.alert)
            .toHaveBeenCalledWith('Error ', 'Failed to send location');
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
    });

    it('should center marker', function(){
        $scope.map = map.createMap();
        $scope.centerMarker(locMock);
        expect($scope.map.setCenter).toHaveBeenCalledWith(locMock);
    });

    it('should center on me', function(){
        spyOn(map, 'currentLocation').and.callFake(function(){
            arguments[0](1.2, 3.4);
        });
        spyOn($scope, 'centerMarker').and.callThrough();
        $window.google = {
            maps: {LatLng: function(lat, lng){
                return locMock
            }}
        };
        // Map is not set
        $scope.centerOnMe();
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        expect($scope.centerMarker.calls.any()).toEqual(false);
        // Map is set
        $scope.map = mapMock;
        $ionicLoading.show.calls.reset();
        $ionicLoading.hide.calls.reset();
        $scope.centerOnMe();
        expect($ionicLoading.show).toHaveBeenCalled();
        expect($ionicLoading.hide).toHaveBeenCalled();
        expect($scope.map.setCenter).toHaveBeenCalledWith(locMock);
    });


});

describe('controller utils tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        utils,
        ctrlUtils,
        utilsIonic,
        deferred;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _utils_,
        _ctrlUtils_, _utilsIonic_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        utils = _utils_;
        ctrlUtils = _ctrlUtils_;
        utilsIonic = _utilsIonic_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        spyOn($ionicLoading, 'hide');
        spyOn(utilsIonic, 'toast');
        spyOn(utilsIonic, 'alert');
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });

    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should select user', function(){
        var scope = {
            selectedUser: undefined,
            selectedName: undefined,
            form: {
                username: undefined
            }
        };
        // No parameters defined
        ctrlUtils.selectUser(scope, 'Test User');
        expect(scope.form.username).toEqual(false);
        expect(scope.selectedUser).toEqual(false);
        expect(scope.selectedName).toEqual('Test User');
        // Username is selected
        scope.form.username = 'user';
        ctrlUtils.selectUser(scope, 'Test User');
        expect(scope.form.username).toEqual('user');
        expect(scope.selectedUser).toEqual('user');
        expect(scope.selectedName).toEqual('Test User');
        // Same username is selected again (toggle)
        ctrlUtils.selectUser(scope, 'Test User');
        expect(scope.form.username).toEqual(false);
        expect(scope.selectedUser).toEqual(false);
    });

    it('should handle message success', function(){
        var modal = {
            hide: jasmine.createSpy()
        };
        spyOn(utils, 'manageRecent');
        $scope.form = {email: 'some@email'};

        ctrlUtils.messageSuccess($scope, modal, 'Success status')();
        // Clean screen
        expect($ionicLoading.hide).toHaveBeenCalled();
        expect(modal.hide).toHaveBeenCalled();
        expect(utilsIonic.toast).toHaveBeenCalledWith('Success status');
        expect(utils.manageRecent).toHaveBeenCalled();
        expect($scope.form).toEqual({});  // Clean form
    });

    it('should handle message error', function(){
        ctrlUtils.messageError('Default error')({});
        expect($ionicLoading.hide).toHaveBeenCalled();
        expect(utilsIonic.alert)
            .toHaveBeenCalledWith('Error ', 'Default error');

        // Specific message
        utilsIonic.alert.calls.reset();
        ctrlUtils.messageError('Default error')({message: 'Specific error'});
        expect(utilsIonic.alert)
            .toHaveBeenCalledWith('Error ', 'Specific error');
    });
});