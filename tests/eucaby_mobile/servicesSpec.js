'use strict';

describe('services tests', function(){
    var $scope, $window, $httpBackend, $q, EucabyApi;
    var successHandler, errorHandler;
    var storage = {};
    var defaultStorage = {
        ec_access_token: 'some_access_token',
        ec_refresh_token: 'some_refresh_token'
    };
    // Note: This is fake requests
    var FRIENDS_LIST = {
        data: [
            {name: 'UserA', username: '123'},
            {name: 'UserB', username: '456'}
        ]};
    var ACTIVITY_LIST = {
        data: [
            {recipient: 'UserA', sender: 'UserB', type: 'request'},
            {recipient: 'UserB', sender: 'UserA', type: 'notification'}
        ]};
    var REQUEST_POST = {
        data: {
            recipient: 'UserA', sender: 'UserB', session: 'S',
            type: 'request'}};
    var REQUEST_GET = {
        data: {
            recipient: 'UserA', sender: 'UserB', session: 'S',
            type: 'request', notifications: ['N1', 'N2']}};
    var NOTIFICATION_POST = {
        data: {
            recipient: 'UserA', sender: 'UserB', session: 'S',
            type: 'notification', location: '1,2'}};
    var NOTIFICATION_GET = {
        data: {
            recipient: 'UserA', sender: 'UserB', session: 'S', request: 'R',
            type: 'notification', location: '1,2'}};
    var ENDPOINT = 'http://api.eucaby-dev.appspot.com';

    beforeEach(module('eucaby.services'));
    beforeEach(module('eucaby.api'));
    beforeEach(inject(function($rootScope, _$window_, _$httpBackend_, _$q_,
                               _EucabyApi_){
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        $window = _$window_;
        $q = _$q_;
        EucabyApi = _EucabyApi_;
        EucabyApi.init($window.localStorage);
    }));
    beforeEach(function() {
        spyOn(EucabyApi, 'api').and.callThrough();
        // LocalStorage mock
        spyOn($window.localStorage, 'getItem').and.callFake(function (key) {
            return storage[key];
        });
        successHandler = jasmine.createSpy('success');
        errorHandler = jasmine.createSpy('error');
    });

    it('should return friends list', inject(function(_Friends_){
        storage = defaultStorage;
        $httpBackend.whenGET(ENDPOINT + '/friends').respond(FRIENDS_LIST);
        $httpBackend.expectGET(ENDPOINT + '/friends')
            .respond(200, FRIENDS_LIST);
        _Friends_.all().then(successHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(successHandler).toHaveBeenCalledWith(FRIENDS_LIST);
        expect(EucabyApi.api).toHaveBeenCalledWith({path: '/friends'});
    }));

    it('should return error for friends list', inject(function(_Friends_){
        storage = defaultStorage;
        $httpBackend.whenGET(ENDPOINT + '/friends').respond(500, 'Some error');
        $httpBackend.expectGET(ENDPOINT + '/friends')
            .respond(500, 'Some error');
        _Friends_.all().then(null, errorHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(errorHandler).toHaveBeenCalledWith('Some error');
        expect(EucabyApi.api).toHaveBeenCalledWith({path: '/friends'});
    }));

    it('should return outgoing and incoming activity lists',
       inject(function(_Activity_){
        var types = ['outgoing', 'incoming'];
        storage = defaultStorage;
        for (var i=0; i<types.length; i++){
            var _type = types[i];
            $httpBackend.whenGET(ENDPOINT + '/history?type=' + _type)
                .respond(ACTIVITY_LIST);
            $httpBackend.expectGET(ENDPOINT + '/history?type=' + _type)
                .respond(ACTIVITY_LIST);
            // Activity.outgoing(), Activity.incoming()
            _Activity_[_type]().then(successHandler);
            $scope.$digest();
            $httpBackend.flush();
            expect(successHandler).toHaveBeenCalledWith(ACTIVITY_LIST);
            expect(EucabyApi.api).toHaveBeenCalledWith(
                {path: '/history', params: {type: _type}});
        }
    }));

    it('should get notification details', inject(function(_Notification_){
        storage = defaultStorage;
        var id = '123';
        $httpBackend.whenGET(ENDPOINT + '/location/notification/' + id)
            .respond(NOTIFICATION_GET);
        $httpBackend.expectGET(ENDPOINT + '/location/notification/' + id)
            .respond(NOTIFICATION_GET);
        _Notification_.get(id).then(successHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(successHandler).toHaveBeenCalledWith(NOTIFICATION_GET);
        expect(EucabyApi.api).toHaveBeenCalledWith(
            {path: '/location/notification/' + id});
    }));

    it('should post notification', inject(function(_Notification_){
        storage = defaultStorage;
        var lat = 1, lng = 2, email = 'test@example.com';
        var form = {email: email};
        var data = {email: email, latlng: '1,2'};
        $httpBackend.whenPOST(ENDPOINT + '/location/notification')
            .respond(NOTIFICATION_POST);
        $httpBackend.expectPOST(ENDPOINT + '/location/notification')
            .respond(NOTIFICATION_POST);
        _Notification_.post(form, lat, lng).then(successHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(successHandler).toHaveBeenCalledWith(NOTIFICATION_POST);
        expect(EucabyApi.api).toHaveBeenCalledWith(
            {method: 'POST', path: '/location/notification', data: data});
    }));

    it('should get request details', inject(function(_Request_){
        storage = defaultStorage;
        var id = '123';
        $httpBackend.whenGET(ENDPOINT + '/location/request/' + id)
            .respond(REQUEST_GET);
        $httpBackend.expectGET(ENDPOINT + '/location/request/' + id)
            .respond(REQUEST_GET);
        _Request_.get(id).then(successHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(successHandler).toHaveBeenCalledWith(REQUEST_GET);
        expect(EucabyApi.api).toHaveBeenCalledWith(
            {path: '/location/request/' + id});
    }));

    it('should post request', inject(function(_Request_){
        storage = defaultStorage;
        var email = 'test@example.com';
        var form = {email: email};
        $httpBackend.whenPOST(ENDPOINT + '/location/request')
            .respond(REQUEST_POST);
        $httpBackend.expectPOST(ENDPOINT + '/location/request')
            .respond(REQUEST_POST);
        _Request_.post(form).then(successHandler);
        $scope.$digest();
        $httpBackend.flush();
        expect(successHandler).toHaveBeenCalledWith(REQUEST_POST);
        expect(EucabyApi.api).toHaveBeenCalledWith(
            {method: 'POST', path: '/location/request', data: form});
    }));
});