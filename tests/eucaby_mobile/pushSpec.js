
describe('push notifications tests', function(){

    var $q,
        $scope,
        storageManager,
        storage,
        $window,
        $state,
        $httpBackend,
        $cordovaPush,
        notifications,
        EucabyApi,
        utilsIonic,
        deferred,
        deferredReg;
    var ANDROID_ID = 'some_android_id';

    beforeEach(module('eucaby.push'));
    beforeEach(function() {
        module(function($provide) {
            $provide.constant('ANDROID_ID', ANDROID_ID);
        });
    });
    beforeEach(inject(function(_$q_, $rootScope, _$httpBackend_, _$cordovaPush_,
        _notifications_, _storageManager_, _$window_, _$state_, _EucabyApi_,
        _utilsIonic_){
        $q = _$q_;
        $scope = $rootScope.$new();
        $httpBackend = _$httpBackend_;
        $cordovaPush = _$cordovaPush_;
        notifications = _notifications_;
        storageManager = _storageManager_;
        $window = _$window_;
        $state = _$state_;
        EucabyApi = _EucabyApi_;
        utilsIonic = _utilsIonic_;
    }));
    beforeEach(function() {
        storage = {};
        // LocalStorage mock.
        spyOn($window.localStorage, 'getItem').and.callFake(function (key) {
            return storage[key];
        });
        spyOn($window.localStorage, 'setItem').and.callFake(function(key, value) {
            storage[key] = value;
        });
    });
    beforeEach(function() {
        deferred = $q.defer();
        deferredReg = $q.defer();
        spyOn(EucabyApi, 'api').and.callFake(function(){
            return deferred.promise;
        });
        spyOn($cordovaPush, 'register').and.callFake(function(){
            return deferredReg.promise;
        });
        spyOn(storageManager, 'setDeviceStatus').and.callThrough();
        spyOn(console, 'log').and.callThrough();
        spyOn(utilsIonic, 'confirm').and.callFake(function(){
            arguments[4]();
        });
        $httpBackend.whenGET(/^templates\/.*/).respond('');
    });

    it('should init', function(){

    });

    it('should register device', function(){
        // No device key is set
        notifications.$registerDevice();
        expect(EucabyApi.api.calls.any()).toEqual(false);

        // Device key is set but user is not logged in
        notifications.$registerDevice('ABC');
        expect(EucabyApi.api.calls.any()).toEqual(false);

        // Invalid platform
        notifications.$registerDevice('ABC', 'wrong');
        expect(EucabyApi.api.calls.any()).toEqual(false);

        // Device key is set and user is logged in
        storage.ec_access_token = 'sometoken';
        deferred.resolve();
        notifications.$registerDevice('ABC', 'android');
        $scope.$apply();
        expect(EucabyApi.api).toHaveBeenCalledWith({
            method: 'POST', path: '/device/register',
            data: { device_key: 'ABC', platform: 'android'}});
        expect(storageManager.setDeviceStatus).toHaveBeenCalledWith('true');
        expect(storage.ec_device_registered).toEqual('true');

        // Device is registered, api request is not performed
        EucabyApi.api.calls.reset();
        notifications.$registerDevice('ABC', 'android');
        $scope.$apply();
        expect(EucabyApi.api.calls.any()).toEqual(false);
    });

    it('should register Android device', function(){
        notifications.$registerAndroid();
        expect($cordovaPush.register)
            .toHaveBeenCalledWith({senderID: ANDROID_ID});
        deferredReg.resolve();
        $scope.$apply();
        expect(console.log)
            .toHaveBeenCalledWith('Android registration accepted');
    });

    it('should redirect', function(){
        var data = {type: 'notification', id: 123};
        spyOn($state, 'go');
        // Don't redirect to detail view
        notifications.$redirect(data, false);
        expect($state.go).toHaveBeenCalledWith('app.tab.incoming');

        // Redirect to detail view
        $state.go.calls.reset();
        notifications.$redirect(data, true);
        expect($state.go)
            .toHaveBeenCalledWith('app.tab.notification', {id: 123});
    });

    it('should register iOS device', function(){
        spyOn(notifications, '$registerDevice');
        notifications.$registerIOS();
        expect($cordovaPush.register)
            .toHaveBeenCalledWith({badge: true, sound: true, alert: true});
        deferredReg.resolve('ABC');
        $scope.$apply();
        expect(notifications.$registerDevice)
            .toHaveBeenCalledWith('ABC', 'ios');
    });

    it('should handle message', function(){
        var payload = {type: 'notification', id: 123};
        spyOn(notifications, '$redirect');
        // Not foreground (background or cold start)
        notifications.$handleMessage(payload, false);
        expect(notifications.$redirect).toHaveBeenCalledWith(payload, true);

        // Foreground
        notifications.$redirect.calls.reset();
        notifications.$handleMessage(payload, true);
        expect(utilsIonic.confirm).toHaveBeenCalled();
        expect(notifications.$redirect).toHaveBeenCalledWith(payload, true);

        // Not foreground, wrong type
        payload.type = 'wrong';
        notifications.$redirect.calls.reset();
        notifications.$handleMessage(payload, false);
        expect(notifications.$redirect).toHaveBeenCalledWith(payload, false);

        // Foreground, wrong type
        notifications.$redirect.calls.reset();
        utilsIonic.confirm.calls.reset();
        notifications.$handleMessage(payload, true);
        expect(utilsIonic.confirm).toHaveBeenCalled();
        expect(notifications.$redirect).toHaveBeenCalledWith(payload, false);
    });

    it('should handle android message', function(){
        var event = jasmine.createSpy(),
            plMock = jasmine.createSpy('payload');
        spyOn(notifications, '$registerDevice');
        spyOn(notifications, '$handleMessage');
        spyOn(console, 'error');
        // Registration
        notifications.$receivedHandlerAndroid(
            event, {event: 'registered', regid: '123'});
        expect(notifications.$registerDevice)
            .toHaveBeenCalledWith('123', 'android');
        expect(notifications.$handleMessage.calls.any()).toEqual(false);

        // Message
        notifications.$registerDevice.calls.reset();
        notifications.$receivedHandlerAndroid(
            event, {event: 'message', regid: '123', payload: plMock,
                    foreground: true});
        expect(notifications.$registerDevice.calls.any()).toEqual(false);
        expect(notifications.$handleMessage).toHaveBeenCalledWith(plMock, true);

        // Error
        notifications.$registerDevice.calls.reset();
        notifications.$handleMessage.calls.reset();
        notifications.$receivedHandlerAndroid(event, {event: 'error'});
        expect(notifications.$registerDevice.calls.any()).toEqual(false);
        expect(notifications.$handleMessage.calls.any()).toEqual(false);
    });

    it('should handle ios message', function(){
        var event = jasmine.createSpy(),
            notifMock = jasmine.createSpy('notif');
        notifMock.foreground = '1';
        spyOn(notifications, '$handleMessage');
        notifications.$receivedHandlerIOS(event, notifMock);
        expect(notifications.$handleMessage)
            .toHaveBeenCalledWith(notifMock, true);
    });
});
