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
        expect($scope.showHeader()).toBeTruthy();
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
        expect(notifications.init).toHaveBeenCalledWith($rootScope);
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
        deferred;
    var locMock,
        tmplMock,
        friendsMock;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$window_, _$ionicLoading_,
        _$ionicModal_, _Friends_, _map_, _utilsIonic_){
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
    }));
    beforeEach(function() {
        deferred = $q.defer();
        locMock = spyOn(map, 'currentLocation');
        spyOn(map, 'createMap').and.returnValue('map');
        spyOn(map, 'createMarker').and.returnValue('marker');
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
        //$httpBackend.whenGET(/^templates\/.*/).respond('');
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

    it('should init map controller', function(){
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
        expect($ionicLoading.show.calls.any()).toBeFalsy();
        expect($ionicLoading.hide.calls.any()).toBeFalsy();
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
        expect(map.createMarker.calls.any()).toBeFalsy();
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

//    if('should register modal.shown event', function(){
//        tmplMock.and.andCallThrough();
//        createController();
//        $scope.registerModal('templates/request.html', 'requestModal');
//        $scope.requestModal.show();
//        $rootScope.$broadcast('modal.shown');
//    });

    it('should check if form is valid', function(){
        var form = {
            email: {$viewValue: undefined},
            user: {$viewValue: undefined}
        };
        // Empty form
        expect(function(){
            $scope.isFormValid({})
        }).toThrowError(TypeError);
        // No parameter is set
        expect($scope.isFormValid(form)).toBeFalsy();
        expect(utilsIonic.alert).toHaveBeenCalled();
        // Invalid email
        form.email.$viewValue = 'wrong';
        expect($scope.isFormValid(form)).toBeFalsy();
        expect(utilsIonic.alert).toHaveBeenCalled();
        // Valid email
        form.email.$viewValue = 'some@email';
        expect($scope.isFormValid(form)).toBeTruthy();
        // Both email and user are set
        form.user.$viewValue = 'user';
        expect($scope.isFormValid(form)).toBeFalsy();
        expect(utilsIonic.alert).toHaveBeenCalled();
        // User is set
        form.email.$viewValue = undefined;
        expect($scope.isFormValid(form)).toBeTruthy();
    });
});

describe('message controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        ctrlUtils,
        deferred;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _ctrlUtils_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        ctrlUtils = _ctrlUtils_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        spyOn(ctrlUtils, 'selectUser');
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
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
    });
});

describe('profile controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        deferred,
        createController;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        createController = function(){
            return $controller('ProfileCtrl', {
                $scope: $scope
            })
        }
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });
});

describe('settings controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        deferred,
        createController;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        createController = function(){
            return $controller('SettingsCtrl', {
                $scope: $scope
            })
        }
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });
});

describe('outgoing controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        deferred,
        createController;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        createController = function(){
            return $controller('OutgoingCtrl', {
                $scope: $scope
            })
        }
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });
});

describe('incoming controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        deferred,
        createController;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        createController = function(){
            return $controller('IncomingCtrl', {
                $scope: $scope
            })
        }
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });
});

describe('notification detail controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        deferred,
        createController;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        createController = function(){
            return $controller('NotificationDetailCtrl', {
                $scope: $scope
            })
        }
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });
});


describe('request detail controller tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        deferred,
        createController;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });
    beforeEach(inject(function($controller){
        createController = function(){
            return $controller('RequestDetailCtrl', {
                $scope: $scope
            })
        }
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });
});

describe('controller utils tests', function(){
    var $q,
        $rootScope,
        $scope,
        $httpBackend,
        $ionicLoading,
        ctrlUtils,
        deferred;

    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        _$q_, _$rootScope_, _$httpBackend_, _$ionicLoading_, _ctrlUtils_){
        $q = _$q_;
        $rootScope = _$rootScope_;
        $scope = _$rootScope_.$new();
        $httpBackend = _$httpBackend_;
        $ionicLoading = _$ionicLoading_;
        ctrlUtils = _ctrlUtils_;
    }));
    beforeEach(function() {
        deferred = $q.defer();
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
});