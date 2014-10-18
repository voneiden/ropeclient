Ropeclient.prototype.format_color = function(text) {
    //Regex pattern $(c: HEX or TEXT )
    var pattern = /\$\(c\:(\#[\da-f]{6}|[a-z]+)\)/
    while (true)
    {
        var match = pattern.exec(text);
        if (match == null) { break; }

        if (match[1] == "default") { match[1] = "white" }
        // TODO deal with resets
        text = text.replace(match[0], '<font color="' + match[1] + '">')
    }

    return text;
}

Ropeclient.prototype.format_timestamp = function(text, timestamp) {
    if (!timestamp) {
        text = "        " + text
    }
    else {
        var pattern = /\$\(time\)/
        var match = pattern.exec(text)
        if (match) {
            text = text.replace(match[0], ("0" + timestamp.getHours().toString()).slice(-2) + ":" + ("0" + timestamp.getMinutes().toString()).slice(-2));
        }
        else {
            text = "        " + text
        }
    }
    return text;
}

Ropeclient.prototype.format_oft = function(message) {
    // TODO: Message ID
    var text = message.value;
    var timestamp;
    if (message.timestamp) {
        timestamp = new Date(message.timestamp * 1000);

    }
    else {
        timestamp = false;
    }
    text = this.format_timestamp(text, timestamp);
    text = this.format_color(text)
    return '<span class="msg">' + text + "</span>";
}

Ropeclient.prototype.format_msg = function(message) {
    var text = message.value;
    text = this.format_color(text)
    text = this.format_span(text, message);
    return '<span class="msg">' + text + "</span>";
}

Ropeclient.prototype.format_span = function(text, message) {
    var style = [];
    console.log(message);
    if (message["font-family"]) {
        style.push(["font-family", message["font-family"]]);
    }
    var span = '<span class="msg"';
    if (style.length > 0) {
        span += ' style="'
        for (var i=0; i < style.length; i++) {
            span += style[i][0] + ": " + style[i][1];
        }
        span += '"'
    }

    span += '>' + text + '</span>';
    return span;
}

function EditHistoryName(msg){
    var pattern = /\$\(disp\=(.*?)\)/;
    var match = pattern.exec(msg);
    while (match != null) {
        var name = match[1];
        msg = msg.replace('$(disp='+name+')','$(name)');

        match = pattern.exec(msg);
    }

    var pattern2 = /\<font color\=\"(.*?)\"\>/;
    var match = pattern2.exec(msg);
    while (match != null) {
        var color = match[1];
        msg = msg.replace('<font color="'+color+'">','<'+color+'>');

        match = pattern2.exec(msg);
    }

    var pattern3 = /\<\/font\>/;
    var match = pattern3.exec(msg);
    while (match != null) {
        var color = match[1];
        msg = msg.replace('</font>','<reset>');

        match = pattern3.exec(msg);
    }

    return msg;
}