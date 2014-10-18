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
};

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
};

Ropeclient.prototype.format_msg = function(message) {
    var text = message.value;
    text = this.format_color(text)
    //text = this.format_span(text, message);
    return '<span class="msg">' + text + "</span>";
};

Ropeclient.prototype.format_message = function(message, stack) {
    var root = false;
    if (!stack) {
        root = $('<span class="msg" />');
        stack = [root];
        console.log("root created");
        console.log(root);
        // Customize for output 1
        if (message.key == "msg") {

        }

        // Customize for output 2
        else if (message.key == "oft") {

        }
    }
    console.log("fm() called", message);
    var active = stack[stack.length - 1];
    if (message.style) {
        active.css(message.style);
        console.log("Set active", active, " CSS", message.style);
    };

    // TODO: handle specials
    if (message.special) {}
    else {
        for (var sub_i=0; sub_i < message.sub.length; sub_i++) {

            var sub = message.sub[sub_i]
            if ($.type(sub) === "string") {
                active.append(sub);
                continue;
            }
            else {
                console.log("SUB NOT INSTANCE OF STRING");
                console.log(typeof sub);
                var new_span = $('<span />');
                active.append(new_span);
                stack.push(new_span);
                stack = this.format_message(sub, stack);
            }
        }
    }
    if (stack.length > 1) {
        stack.pop();
    }

    if (root) {
        console.log("root terminated")
        console.log(stack[0]);
        return stack[0];
    }
    else {
        console.log("non root terminated");
        return stack;
    }
};

Ropeclient.prototype.format_message_subs = function(message, stack) {
    if (!stack) {
        var root = $('<span />');
        stack = [root];
    }
    else {
        var new_span = $('<span />');

    }
};

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