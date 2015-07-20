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
            $scope: $scope,
            EucabyApi: EucabyApi
        })
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

    var $scope,
        $httpBackend,
        EucabyApi,
        push;

    beforeEach(module('eucaby.push'));
    beforeEach(module('eucaby.controllers'));
    beforeEach(inject(function(
        $rootScope, _$httpBackend_, _EucabyApi_, _push_){
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        EucabyApi = _EucabyApi_;
        push = _push_;
    }));
    beforeEach(inject(function($controller){
        $controller('LoginCtrl', {
            $scope: $scope,
            EucabyApi: EucabyApi,
            push: push
        })
    }));
    afterEach(function(){
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    it('should go to map view after successful login', function(){

    });

//    it('should display error after failed login', function(){
//
//    });

});

describe('map controller tests', function(){

});

describe('message controller tests', function(){

});

describe('profile controller tests', function(){

});

describe('settings controller tests', function(){

});

describe('outgoing controller tests', function(){

});

describe('incoming controller tests', function(){

});

describe('notification detail controller tests', function(){

});


describe('request detail controller tests', function(){

});

describe('controller utils tests', function(){

});