Ropeclient.prototype.event_key = function(mode, event) {
    // mode = 1 down
    // mode = 0 up
    if (mode == 0) {
        if (is_typing == false && this.input_plain.val().length > 0) { input_typing(true); }
        else if (is_typing == true &&this.input_plain.val().length == 0) { input_typing(false); }
        else if (event.keyCode == 8) { handle_autocomplete(true); }
        else { console.log("PROOT", event.keyCode);}
    }
    else { // TAB
        if (event.keyCode == 13 && !event.shiftKey) { this.event_key_enter(event); }
        else if (event.keyCode == 9)  { input_tab(event); }
    }
}
/*
 * Handle enter input event
 */
Ropeclient.prototype.event_key_enter = function (event)
{
    var message = {};
    if (this.input_password_mode == true)
    {
        message.key = "pwd";
        //message.server_salt = this.password_server_salt;

        // Generate client salt. If available, use more secure functions, otherwise fall back
        var random_array;
        if (window.crypto && window.crypto.getRandomValues && window.Uint8Array) {
            random_array = new Uint8Array(32);
            crypto.getRandomValues(random_array);
        }
        else {
            this.print_2("Warning: your browser does not support a relatively \
                         new pseudo-random number generator function (crypto.getRandomValues). \
                         Your password will be salted using a less secure method. In reality, this \
                         is probably not a big problem. Consider upgrading your browser anyway. \
                         <a href=\"http://caniuse.com/#feat=getrandomvalues\">Check here for supported browsers</a>");
            random_array = new Array();
            for (var i=0; i < 32; i++) {
                random_array.push(Math.round(Math.random()*255))
            }
        }
        var client_salt = "";
        for (var i=0; i < random_array.length; i++) {
            var hex = random_array[i].toString(16);
            if (hex.length == 1) { hex = "0" + hex; }
            client_salt += hex;
        }

        // If this is a handshake, we gotta create just a preshared key from the password, random server salt and random client salt
        if (this.password_handshake) {
            console.log("HANDSHAKE")
            message.value = new jsSHA(this.input_password.val() + this.password_server_salt + client_salt).getHash("SHA-256","HEX");
            message.client_salt =  this.password_server_salt + client_salt
        }
        // Otherwise we hash the preshared key with random client salt
        else {
            console.log("NO HANDSHAKE")
            console.log("Server salt:", this.password_server_salt)
            var h1 = new jsSHA(this.input_password.val() + this.password_server_salt).getHash("SHA-256","HEX");
            message.value = new jsSHA(h1 + client_salt).getHash("SHA-256","HEX");
            message.client_salt = client_salt;
        }


        this.input_password.val("");
        this.input_password.hide();
        this.input_plain.show();
        this.input_plain.focus();

        this.input_password_mode = false;

        event.preventDefault();
    }
    else if (is_editing == true)
    {
        // TODO
    }
    else if (autocomplete_buffer.length == 0)
    {
        // Normal message
        message.key = "msg";
        message.value = this.input_plain.val();
        if (message.value.length == 0) { return; }
        this.input_plain.val("");
        event.preventDefault();
    }
    else if (autocomplete_buffer.length > 0) {
        message.key = autocomplete_buffer[0];
        message.value = autocomplete_buffer.slice(1);
        var input = $("#input").val();
        if (input.length > 0) {
            message.value.push(input);
        }
        $("#input").val("");
        autocomplete_buffer = new Array();
        $("#autocomplete").html("");
        event.preventDefault();
    }
    else
    {
        // Todo
        console.error("UNABLE TO SEND MESSAGE")
    }
    if (is_typing) {
        input_typing(false);
    }
    ws_send(JSON.stringify(message));
}

/*
 * Handle TAB events
 * Block focus change & forward to autocomplete function
 */
function input_tab(event) {
    console.log("TAB");
    handle_autocomplete();
    event.preventDefault();
}




function input_typing(typing) {
    var message = {}
    is_typing = typing;
    if (typing){
        message.key = "pit"
        console.log("pit")
    }
    else {
        message.key = "pnt"
        console.log("pnt")
    }
    ws_send(JSON.stringify(message))
}

Ropeclient.prototype.receive_message = function(event) {
    var message;

    // Parse the data if possible
    try {
        message = JSON.parse(event.data);
    }

    catch (SyntaxError) {
        console.error("Parse error");
        console.error(event);
        return
    }

    var key = message.key;

    // msg is a single line in-topic message
    if (key == "msg") {
        this.print_1(this.format_msg(message));
    }

    // msg_list consists of a list of multiple msg elements
    else if (key == "msg_list")
    {
        var buffer = [];
        for (var i = 0; i < message.value.length; i++)
        {
            console.log(this);
            var test2 = message.value[i];
            var test = this.format_msg(test2);
            buffer.push(this.format_msg(message.value[i]));
        }
        this.print_1(buffer.join(""));
    }

    // oft is a single line off-topic message
    else if (key == "oft") {
        this.print_2(this.format_oft(message));
    }

    // oft_list consists of a list of multiple oft elements
    else if (key == "oft_list") {
        var buffer =[];
        for (var i = 0; i < message.value.length; i++)
        {
            buffer.push(this.format_oft(message.value[i]));
        }
        this.print_2(buffer.join(""))
    }

    // pwd requests the client to go into password typing mode (hide input and hash output)
    // TODO: server based salt
    else if (key == 'pwd') {
        this.input_plain.hide();
        this.input_password.show();
        this.input_password.focus();
        this.input_password_mode = true;

        // Store server hash
        this.password_server_salt = message.server_salt;
        this.password_handshake = message.handshake;

    }
    else if (key == "clr") {
        var window = message.window || "both"

        if (window == "msg" || window == "both") {
            this.output_1.html("");
        }
        if (window == "oft" || window == "both") {
            this.output_2.html("");
        }
    }
    else if (key == 'ping') {
        ws_send(JSON.stringify({"key": "pong"}));
    }
    else if (key == 'ptu') {
        // player type update.. single player!!
        updatePlayer(message);
    }
    else if (key == 'plu') {
        // Player list update!
        updatePlayerList(message);

    }
    else if (key == 'col') {
        c1 = tok.shift();
        c2 = tok.shift();
        if (c1 == 'background') {
            $("#lefttop").css("background-color",c2);
            $("#leftbottom").css("background-color",c2);
            $("#righttop").css("background-color",c2);
            $("#rightbottom").css("background-color",c2);
            $("#leftentry").css("background-color",c2);
            $("#entrybox").css("background-color",c2);

        }
        else if (c1 == 'input') {
            $("#entrybox").css("color",c2);
        }
        else if (c1 == 'timestamp') {
            color_timestamp = c2;
        }
        else { displayOfftopic(false,"Unknown color received.. bug?"); }
    }
    else if (key == 'font') {

        font = message.font;
        size = message.size;
        $("#root-chat-ooc").css("font-family",font);
        $("#root-chat-ic").css("font-family",font);
        $("#root-chat-ooc").css("font-size",size);
        $("#root-chat-ic").css("font-size",size);
    }
    else if (key == 'edi') {
        timestamp = tok.shift();
        message = tok.join(" ");

        // Update history
        for (var i in edit_history) {
            if (edit_history[i][0] == timestamp) {
                edit_history[i] = [timestamp,message]
            }
        }
        // Update text
        message = nameParse(message);
        //displayOfftopic(false,"Updating id "+timestamp);
        //$("#"+timestamp).html(message);
        var element = document.getElementById(timestamp);
        if (element != null) { element.innerHTML = "[EDITED  ] " + message }
    }
    else {
        displayOfftopic('unknown header msg: ' + message.toString());
    }
};