$(document).ready(function(){
    // start up the SocketIO connection to the server
    let socket = io.connect(`http://${document.domain}:${location.port}`);
    let $ticker = $("#cea-worker-ticker");
    // this is a callback that triggers when the "my response" event is emitted by the server.
    socket.on('cea-worker-message', function(data) {
        let lines = data.message.split(/\r?\n/);
        let last_line = lines[lines.length - 1];

        $ticker.text(`${data.jobid}: ${last_line.substr(0, 80)}`);
    });
    
    socket.on('cea-worker-success', function(data) {
        $ticker.text(`${data.jobid}: completed`);
    });

    socket.on('cea-worker-error', function(data) {
        alert(data.error);
        $ticker.text(`${data.jobid}: error`);
    });
});