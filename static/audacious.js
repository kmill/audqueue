function rpc(method, args) {
    return new Promise(function (onSuccess, onError) {
        var data = {method : method,
                    kwargs : args || {}};
        $.ajax({url : "/ajax/rpc",
                type : "POST",
                data : {message : JSON.stringify(data)},
                dataType : "json",
                timeout : 5000,
                success : function (res) {
                    if ("result" in res) {
                        if ("error" in res.result) {
                            onError(res.result.error);
                        } else {
                            onSuccess(res.result.result);
                        }
                    } else if ("error" in res) {
                        onError({type : "exception", args : res.error});
                    } else {
                        onError({type : "malformed"});
                    }
                },
                error : function (hjXHR, textStatus, errorThrown) {
                    onError({type : textStatus});
                }
               });
    });
}

var playlist_re = /^(.*?)\|(.*)\|(.*)$/;

function update() {
    rpc("playlist").then(function (playlist) {
        var $current = $("#current").empty();
        var $playpause = $('<a href="#">Play/pause</a>').appendTo($current);
        $playpause.click(function (e) {
            e.preventDefault();
            rpc("playpause").then(update);
        });
        $current.append(" ");
        $current.append($("<span>").text("(" + playlist.status + ")"));
        $current.append(" &mdash; ");
        $current.append($('<a href="#" title="Previous">&laquo;</a>').click(function (e) {
            e.preventDefault();
            rpc("reverse").then(update);
        }));
        $current.append(" | ");
        $current.append($('<a href="#" title="Next">&raquo;</a>').click(function (e) {
            e.preventDefault();
            rpc("advance").then(update);
        }));
        $current.append(" &mdash; Volume: " + playlist.volume + " ( ");
        $current.append($('<a href="#">-</a>').click(function (e) {
            e.preventDefault();
            rpc("setvolume", {v : playlist.volume - 5}).then(update);
        }));
        $current.append(" | ");
        $current.append($('<a href="#">+</a>').click(function (e) {
            e.preventDefault();
            rpc("setvolume", {v : playlist.volume + 5}).then(update);
        }));
        $current.append(" )");
        $current.append(" &mdash; ");
        $current.append($('<a href="#">Refresh</a>').click(function (e) { e.preventDefault(); update(); }));
        
        var $main = $("#main").empty();

        var $table = $('<table class="database_view">').appendTo($main);
        for (var i = 1; i in playlist.playlist; i++) {
            var row = playlist.playlist[i];
            var columns = playlist_re.exec(row);
            var $tr = $('<tr class="song_view">');
            if (i == playlist.position) {
                $tr.addClass("current");
            }
            (function (i, name, time) {
                var $commands = $('<td class="song_view_action">').appendTo($tr);
                $('<a href="#" title="Play">P</a>').appendTo($commands).click(function (e) {
                    e.preventDefault();
                    rpc("jump", {pos : i}).then(update);
                });
                $('<a href="#" title="Queue">Q</a>').appendTo($commands).click(function (e) {
                    e.preventDefault();
                    rpc("queue", {pos : i}).then(update);
                });
                $('<a href="#" title="Remove">R</a>').appendTo($commands).click(function (e) {
                    e.preventDefault();
                    rpc("remove", {pos : i}).then(update);
                });

                var $q = $('<td class="song_view_queue">').appendTo($tr);
                var idx = playlist.queue.indexOf(i);
                if (idx >= 0) {
                    $('<a href="#" title="dequeue">').text('#' + (idx + 1)).appendTo($q).click(function (e) {
                        e.preventDefault();
                        rpc("dequeue", {pos : i}).then(update);
                    });
                }
                $tr.append($("<td>").text(name).attr("title", name));
                $tr.append($('<td class="song_view_time">').text(time));
            })(i, columns[2], columns[3]);
            $tr.appendTo($table);
        }

        $('<p class="database_view_playall">').appendTo($main).append(
            $('<a href="#">Clear</a>').click(function (e) {
                e.preventDefault();
                rpc("clear").then(update);
            })
        );
        
        console.log(playlist);
    }, function (err) { console.log(err); });
}

$(function () {
    update();
});
