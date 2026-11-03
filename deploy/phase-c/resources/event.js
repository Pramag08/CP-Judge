/* CPJudge: authenticated same-origin polling; native result widgets do the rendering. */
function EventReceiver(websocket, poller, channels, last_msg, onmessage) {
    var receiver = this;
    this.onwsclose = null;
    this.websocket = null;
    var stopped = false;
    function poll() {
        if (stopped) return;
        $.ajax({url: '/cpjudge/events/' + encodeURIComponent(channels.join('|')),
                cache: false, dataType: 'json'})
            .done(function(data) {
                data.messages.forEach(function(message) { if (onmessage) onmessage(message); });
            })
            .fail(function(response) {
                if ([401,403,404].indexOf(response.status) !== -1) stopped = true;
            })
            .always(function() { if (!stopped) setTimeout(poll, 1000); });
    }
    poll();
}
