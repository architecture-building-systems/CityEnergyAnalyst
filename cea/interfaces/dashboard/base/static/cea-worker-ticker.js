$(document).ready(function () {
    // start up the SocketIO connection to the server
    let socket = io.connect(`http://${document.domain}:${location.port}`);
    let $ticker = $("#cea-worker-ticker");
    // this is a callback that triggers when the "my response" event is emitted by the server.
    socket.on("cea-worker-message", function (data) {
        let lines = data.message.split(/\r?\n/).map(x => x.trim()).filter(x => x.length > 0);
        let last_line = lines[lines.length - 1];

        $ticker.text(`${data.jobid}: ${last_line.substr(0, 80)}`);
    });

    socket.on("cea-worker-success", function (data) {
        $ticker.text(`${data.jobid}: completed`);
    });

    socket.on("cea-worker-error", function (job_info) {
        console.log("cea-worker-error: job_info:", job_info);
        alert(`ERROR running ${job_info.script} (${job_info.id})

${job_info.error}`);
        $ticker.text(`${job_info.id}: error`);
    });
});