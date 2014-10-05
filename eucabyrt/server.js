var http = require('http');
var server = http.createServer().listen(4000);
var io = require('socket.io').listen(server);
var cookie_reader = require('cookie');
var querystring = require('querystring');

var redis = require('redis');
var sub = redis.createClient();

// Subscribe to the Redis location channel
sub.subscribe('eucabyrt');

// Configure socket.io to store cookie set by Django
/*
io.configure(function(){
    io.set('origins', '*:*');
    io.set('authorization', function(data, accept){
        if(data.headers.cookie){
            data.cookie = cookie_reader.parse(data.headers.cookie);
            return accept(null, true);
        }
        return accept('error', false);
    });
    io.set('log level', 1);
});
*/

var enableCORS = function(req, res, next) {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Content-Length, X-Requested-With, *');

        // intercept OPTIONS method
    if ('OPTIONS' == req.method) {
        res.send(200);
    } else {
        next();
    };
};
io.use(enableCORS);

io.sockets.on('connection', function (socket) {

    // Grab message from Redis and send to client
    sub.on('message', function(channel, message){
        console.log(message);
        socket.send(message);
    });

    // TODO: Notify Django app
    /*
    // Client is sending message through socket.io
    socket.on('send_message', function (message) {
        values = querystring.stringify({
            sessionid: socket.handshake.cookie['sessionid']
        });

        var options = {
            host: 'localhost',
            port: 3000,
            path: '/node_location',
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': values.length
            }
        };

        // Send message to Django server
        var req = http.request(options, function(res){
            res.setEncoding('utf8');

            //Print out error message
            res.on('data', function(message){
                if(message != 'ok'){
                    console.log('Message: ' + message);
                }
            });
        });

        req.write(values);
        req.end();
    });
    */
});
