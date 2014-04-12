
var realtaxiMap;
var sbLat	= "34.4281937";
var sbLng	= "-119.702067";
var markersArray = [];

var mapFactory    = function(lat, lng){
    // Creates map
    var location = new google.maps.LatLng(lat, lng);
    var mapOptions = {
        center: location,
        zoom: 13,
        scrollwheel: false,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
    };
    return new google.maps.Map(document.getElementById("realtaxi-map"), mapOptions);
}

var markerFactory = function(map, lat, lng, username){

    return new google.maps.Marker({
            position:  	new google.maps.LatLng(lat, lng),
            title:      username,
            map:        map
        });
}

var clearOverlays = function(markers) {
    // Clears markers from the map
    if (markers) {
        for (var i = 0; i < markers.length; i++) {
            markers[i].setMap(null);
        }
    }
    markers = [];
}

$(function(){
    realtaxiMap = mapFactory(sbLat, sbLng);
    var socket = io.connect('localhost', {port: 4000});

    socket.on('connect', function(){
        console.log("Connected");
    });

    socket.on('message', function(message) {
        var msg = JSON.parse(message);
        clearOverlays(markersArray);
        var marker = markerFactory(realtaxiMap, msg.lat, msg.lng, msg.username);
        markersArray.push(marker);
    });

    $("#move").click(function(){
        socket.emit('send_message', function(data){
            console.log(data);
        });
    });


});