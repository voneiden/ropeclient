// Ropeclient web client
// See http://www.github.com/voneiden/ropeclient
// for license information and documentation

// If you're currently playing and reading this: don't cheat. It's not nice.

// Customize default url

// TODO TODO TODO
/*
 * Error causes page to lose flow
 * Unique hash not implemented
 */

function Ropeclient() {}

Ropeclient.prototype.init =  function() {
    var default_url = ""
    switch(window.location.protocol) {
    case 'file:':
        default_url = "ws://localhost:9091" // If client is accessed as file:/// default to localhost
        break;
    default:
        default_url = "ws://ninjabox.sytes.net:9091" // Else default to web
    }

    // Define elements
    var self = this;
    this.input_destination = $("#input-destination");
    this.input_destination_connect = $("#input-destination-connect");
    this.input_plain = $("#input-plain");
    this.input_password = $("#input-password");
    this.output_1 = $("#output-1");
    this.output_2 = $("#output-2");
    this.output_3 = $("#output-3");



    // Define events
    this.input_destination_connect.click(function() { self.connect(self.input_destination.val()) });
    this.input_destination.keypress(function (e) { if (e.which == 13) { self.connect(self.input_destination.val()); } });
    this.input_destination.val( $.jStorage.get("last_url", default_url));
    this.input_destination.focus();

    this.input_plain.keyup(function (event) { self.event_key(0, event);});
    this.input_plain.keydown(function (event) { self.event_key(1, event);});
    this.input_password.keydown(function (event) { self.event_key(1, event);});

    // Define variables
}






// Define constants
// Message edit variables
edit_history = [];
edit_index   = -1;
edit_mem     = ''; 
is_editing = false;

// Special colors
color_timestamp = 'gray';

// separator line
update_separator = false;

is_typing = false; 
is_password = false;

player_list = new Array();
ws = null;




Ropeclient.prototype.connect = function (url) {

    // Todo, enable these buttons if disconnected
    this.input_destination.hide();
    this.input_destination_connect.hide();
    
    this.input_plain.focus();

    // Do we need this still?
    //if ( $.browser.mozilla ) { ws = new MozWebSocket(url); } // Mozilla compatibility
    //else { ws = new WebSocket(url); }
    ws = new WebSocket(url);
    var self = this;
    this.print_2("Connecting to " + url + "... socket state "+ws.readyState+"<br>");
    
    ws.onopen = function() {
        $.jStorage.set("last_url", url);
        self.print_2("Connection established.<br>");
    };
    ws.onmessage = function(event) {
        self.receive_message(event);
    }
    
    ws.onclose = function() {
        self.print_1('<span style="font-size: large; color: red;">Disconnected, hit F5 to reconnect</font>')
        self.print_2('<span style="font-size: large; color: red;">Disconnected, hit F5 to reconnect</font>')
    };
    
    ws.onerror = function (error) {
        self.print_2(false,"Error: "+error.data+" (Hit F5 to reconnect)");
    };
}


// This function handles the up and down arrow key presses
// To allow users to browse and edit history of their previous writings
function EditHistory(event) {
    if (autocomplete_stage != 0 || isPassword) {
        if (event.preventDefault) { event.preventDefault(); }
        return false
    }
    
    // Adjust index depending on key event
    if (event.keyCode == 38) { edit_index += 1 }
    else if (event.keyCode == 40) { edit_index -= 1 }
    
    
    // Make sure the index is within acceptable bounds
    if (edit_index >= edit_history.length) {
        edit_index = edit_history.length -1 
    }
    
    if (edit_index < -1) { edit_index = -1 }
    
    // Resolve action
    if (edit_index == -1 && editing == 0) {
        }
    else if (edit_index == -1 && editing == 1) {
        editing = 0;
        $("#autocomplete").html("");
        $("#entrybox").val(edit_mem);
        edit_mem = '';
    }  
    else if (edit_index > -1 && editing == 0) {
        edit_mem = $("#entrybox").val();
        $("#autocomplete").html("Editing");
        editing = 1;
        var msg = edit_history[edit_history.length - 1 - edit_index][1]
        $("#entrybox").val(EditHistoryName(msg));
    }
    
    else if (edit_index > -1 && editing == 1) {
        var msg = edit_history[edit_history.length - 1 - edit_index][1]
        $("#entrybox").val(EditHistoryName(msg));
    }
    //displayOfftopic(false,editing+" "+edit_index+"  - ")
}



// Generates a visual timestamp from unix time
function  makeTimestamp(id) {
    var d = new Date(parseFloat(id)*1000);
    var hours = d.getHours();
    var minutes = d.getMinutes();
    var seconds = d.getSeconds();
    
    if (hours < 10) { hours = "0" + hours; }
    if (minutes < 10) { minutes = "0" + minutes;}
    if (seconds < 10) { seconds = "0" + seconds;}
    
    
    return '<font color="' + color_timestamp + '">[' + hours + ":" + minutes + ":" + seconds + "]</font> "
    
}
Ropeclient.prototype.print_2 = function(text) {
    this.output_2.append(text);
    console.log(this.output_2);
    this.output_2.scrollTop(this.output_2[0].scrollHeight);
    //document.getElementById("root-chat-ooc").scrollTop = document.getElementById("root-chat-ooc").scrollHeight;
}
Ropeclient.prototype.print_1 = function(text) {
    this.output_1.append(text);
    this.output_1.scrollTop(this.output_1[0].scrollHeight);
}

function nameParse(msg) {
    var pattern = /\$\(disp\=(.*?)\)/;
    var match = pattern.exec(msg);
    while (match != null) {
        var name = match[1];
        msg = msg.replace('$(disp='+name+')',name);
        
        match = pattern.exec(msg);
    }
    return msg;
}

function diceParse(msg) {
    var results = msg.match(/\$\{dice\|.*?\}/g);
    if (results) { 
        while (results.length) {
            var result = results.shift();
            //var tok = result.split('=').pop().split(';');
            var tok = result.split('|');
            tok.shift();
            var d1 = tok.shift();
            var d2 = tok.shift().slice(0,-1);
            var id = 'dice-'+Math.random() 
                          
            msg = msg.replace(result,'<span id="'+id+'" onclick="swapDice(\''+id+'\',\''+d1+'\',\''+d2+'\')" class="dice">'+d1+'</span>');
            //msg.replace('voneiden','aasdufihiuahshafsud');
        }
        return msg; 
    }
    else { 
        return msg; 
    }
   
}
function swapDice(id,from,to) {
    var pattern = new RegExp('<span.*?onclick="swapDice.'+id+'.*?</span>');
    if (document.getElementById(id).innerHTML == from) {
        document.getElementById(id).innerHTML = to
    }
    else {
        document.getElementById(id).innerHTML = from
    }

}


function updatePlayer(message) {

    var name = message.name;
    var typing = message.typing;
    if (typing == "1") { typing = "*" }
    else { typing = "" }
    var character = message.character;
    if (character) {
        character = " ("+ character + ")";
    }
    else {
        character = "";
    }

    var pattern = new RegExp("<pre>"+name+'.*?</pre>');
    //var results = document.getElementById('righttop').innerHTML.match(pattern);
    var results = $("#root-right").html().match(pattern);

    while (results.length) {
        var result = results.shift()
        $("#root-right").html( $("#root-right").html().replace(result,"<pre>"+name+typing+character+"</pre>"))
    }
}
function updatePlayerList(message) {
    document.getElementById('root-right').innerHTML = "";
    while (message.value.length) {
        var player = message.value.shift()
        var name = player.name;
        var typing = player.typing;
        var character = player.character; // TODO: nameparse

        if (typing == "1") {
            typing = "*"
        }
        else {
            typing = ""
        }
        if (character) {
            character = " ("+ character + ")";
        }
        else {
            character = "";
        }
        document.getElementById('root-right').innerHTML += "<pre>"+name+typing+character+"</pre>";
        
        
    }
}
function ws_send(msg) {
    ws.send(msg);
}
 
function ws_close() {
    log("closing connection..");
    ws.close();
}
/*
$(window).resize(function() {
    document.getElementById("root-chat-ic").scrollTop = document.getElementById("root-chat-ic").scrollHeight;
    document.getElementById("root-chat-ooc").scrollTop = document.getElementById("root-chat-ooc").scrollHeight;
});
*/

$(window).blur(function(event){
    //displayOfftopic(0,"Lost focus");
    if (update_separator) {
        $("#bottomlw").remove();
        $("#toplw").remove();
        $("#root-chat-ic").append('<hr id="bottomlw">');
        $("#root-chat-ooc").append('<hr id="toplw">');
        document.getElementById("root-chat-ic").scrollTop = document.getElementById("root-chat-ic").scrollHeight;
        document.getElementById("root-chat-ooc").scrollTop = document.getElementById("root-chat-ooc").scrollHeight;
        update_separator = false;
    }
});

$(window).focus(function(event){
    //displayOfftopic(0,"Got focus");
    setTimeout(function() { $("#entrybox").focus(); }, 0);
});


var ropeclient = null;
$(document).ready(function(){
    ropeclient = new Ropeclient();
    ropeclient.init()
});

