// Ropeclient web client
// See http://www.github.com/voneiden/ropeclient
// for license

// Customize default url
switch(window.location.protocol) {
    case 'file:':
        default_url = "ws://localhost:9091" // If client is accessed as file:/// default to localhost
        break;
    default:
        default_url = "ws://ninjabox.sytes.net:9091" // Else default to web
}

autocomplete_stage = 0;
autocomplete_base  = "";
autocomplete_cycle = [];
autocomplete_index = 0;
autocomplete_buffer = [];
autocomplete_commands = {
    'action':[1,"Message?"],
    'attach':[1,"Who?/To?","To?"],
    'calldice':[3,"Targets, sep. with comma","Roll request","Query"],
    'chars':[0],
    'create':[4,"Title?","Description?","Exit name (or blank)?", "Return exit name (or blank?"],
    'detach':[0],
    'editlocation':[2,'Choose attribute to edit: name/description','set to?'],
    'getlog':[3,'E-Mail','Mode (1=talk, 2=offtopic, 3=all)','Max age in hours'],
    'locs':[0],
    'look':[0,"Enter/At who?"],
    'kill':[1,"Who?"],
    'me':[1,"Message?"],
    'notify':[2,"Who?","Message?"],
    'players':[0],
    'tell':[2,"Who?","Message?"],
    'setcolor':[0,"Enter to list/Color name (from)?","Enter to erase definition/Color name (to)?"],
    'setfont':[2,"Font name?","Font size?"],
    'sethilight':[0,"Enter to list/Regex pattern/Index number to delete","Color to change matching patterns"],
    'settalk':[1,"To color?"],
    'spawn':[3,"Spawn a character - Character name?","One-line description (optional, short)","Long description"]
};

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

function initialize()
{
    $("#connect_button").click(function() { connect($("#connect_destination").val()) });
    $("#connect_destination").keypress(function (e) { if (e.which == 13) { connect($("#connect_destination").val()); } });
    $("#connect_destination").val( $.jStorage.get("last_url", default_url));
    $("#connect_destination").focus();
    
    $("#input").keyup(input_event_keyup);
    $("#input").keydown(input_event_keydown);
    $("#input-password").keydown(input_event_keydown);
}

/*
 * Handle keyup events (everything except tabs)
 */
function input_event_keyup(event)
{

    if (is_typing == false && $("#input").val().length > 0) { input_typing(true); }
    else if (is_typing == true && $("#input").val().length == 0) { input_typing(false); }
    else if (event.keyCode == 8) { handle_autocomplete(true); }
    else { console.log("PROOT", event.keyCode);}
}

/*
 * Handle keydown events (tabs)
 */
function input_event_keydown(event)
{
    if (event.keyCode == 13 && !event.shiftKey) { input_enter(event); }
    else if (event.keyCode == 9)  { input_tab(event); }
}

/*
 * Handle enter input event
 */
function input_enter(event)
{
    var message = {};
    if (is_password == true) 
    {
        message.key = "pwd";
            
		var shaObj = new jsSHA($("#input-password").val()+'r0p3s4lt'); // TODO: deal with this poor static salt
        message.value = shaObj.getHash("SHA-256","HEX");      // Though; does this service require such strong authentication?
		
		// Clear, detach, change mode to normal text and reattach the input block
        $("#input-password").val("");
        //var marker = $('<span />').insertBefore('#input');
        //$('#input').detach().attr('type', 'text').insertAfter(marker);
        //marker.remove();
        //$("#input").focus();
        $("#input-password").hide();
        $("#input").show();
        $("#input").focus();

        is_password = false;

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
        message.value = $("#input").val();
        if (message.value.length == 0) { return; }
        $("#input").val("");
        event.preventDefault();
    }
    else
    {
        // TODO
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

/*
 * Autocomplete function
 * Default mode is to react to the tab key
 * if backspace is true, react to backspace instead
 */
autocomplete_buffer = new Array();
autocomplete_choices = new Array();

function handle_autocomplete(backspace) {
    if (backspace == null) { backspace = false; }
    var input = $("#input").val();
    var autocomplete_command_keys = Object.keys(autocomplete_commands)

    // First call to autocomplete, choose matching command and fill choices
    if (autocomplete_buffer.length == 0 && !backspace) {
        console.log("Stage 1 autocomplete");
        var regex = new RegExp("\\b"+input, 'i')
        autocomplete_choices = new Array();

        for (var i=0; i < autocomplete_command_keys.length; i++) {
            if (autocomplete_command_keys[i].search(regex) > -1) {
                autocomplete_choices.push(autocomplete_command_keys[i])
            }
        }
        console.log(autocomplete_choices);
        if (autocomplete_choices.length > 0) {
            autocomplete_buffer.push(autocomplete_choices[0])
            $("#input").val("");
            autocomplete_display();
        }
        else {
            console.log("Nothing found");
        }
    }

    else {
        // Remove parameter
        if (backspace && input.length == 0) {
            autocomplete_buffer.pop();
            autocomplete_display();
        }

        else if (backspace) { return; }
        // Cycle through command choices
        else if (autocomplete_buffer.length == 1 && input.length == 0) {
            console.log("Cycle");
            var index = autocomplete_choices.indexOf(autocomplete_buffer[0]);
            index += 1;

            if (index+1 > autocomplete_choices.length) { index = 0; }
            autocomplete_buffer[0] = autocomplete_choices[index];
            console.log(autocomplete_choices);
            console.log(index)
            autocomplete_display();
        }
        // Add parameter
        else {
            autocomplete_buffer.push(input);
            $("#input").val("");
            autocomplete_display();
        }
    }
}

// This function updates the green blocks left of entrybox
function autocomplete_display() {
    var text = "";
    for (var i in autocomplete_buffer) {
        text += '<span style="color:lime;border-style:solid;border-width:1px;border-color:lime;">'+autocomplete_buffer[i]+'</span>';
    }
    if (autocomplete_buffer.length > 0) { // This is a neat feature!
        var cmd = autocomplete_buffer[0];
        var questions = autocomplete_commands[cmd]
        // -1 because of the required args number
        if (questions.length  - 1< autocomplete_buffer.length) {
            text += "Press Enter"
        }
        else {
            text += questions[autocomplete_buffer.length];
        }

    }
    $("#autocomplete").html(text);
    $("#autocomplete").focus();
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
    /*
		var message = {};
        if (input_password == true) { // Currently typing a password
            

			input_password = false;
        } // TODO: Continue here
        else if (editing) {
            var header = 'edi ' + edit_history[edit_history.length - 1 - edit_index][0]
            var content = $("#entrybox").val();
            //displayOfftopic(false,"Sending content: "+content)
            editing = 0
            $("#autocomplete").html("");
            edit_index = -1
            $("#entrybox").val("");
        }
        
        else if (autocomplete_buffer.length == 0) {
            var header = 'msg';
            var content = $("#entrybox").val();
            // Move the last write delimiter?
            if (content[0] == '(') {
                $("#toplw").remove();
                $("#lefttop").append('<hr id="toplw">');
                document.getElementById("lefttop").scrollTop = document.getElementById("lefttop").scrollHeight;
            }
            else {
                $("#bottomlw").remove();
                $("#leftbottom").append('<hr id="bottomlw">');
                document.getElementById("leftbottom").scrollTop = document.getElementById("leftbottom").scrollHeight;
            }
        }
        else {
            var header = "cmd";
            var content = autocomplete_buffer.join("\x1b")
            var temp = $("#entrybox").val();
            if (temp.length > 0) {
                content += "\x1b" + temp
            }
            autocomplete_buffer = [];
            autocomplete_stage = 0;
            autocomplete_index = 0;
            autocomplete_cycle = [];
            displayAutocomplete();
        }
        //displayOfftopic("Content: "+content);
        $("#entrybox").val("");
        ws_send(header + " " + content);
        isTyping = 0;
        
    }
    
    else {
        //if (event.keyCode == 8) {
            //AutoComplete(event.keyCode);
        //}
        
        
        if (isTyping == 0 && $("#entrybox").val().length > 0) {    
            isTyping = 1;
            update_separator = true;
            ws_send("pit")
        }
        else if (isTyping == 1 && $("#entrybox").val().length == 0) {
            isTyping = 0;
            ws_send("pnt")
        }
    }    
}*/


function connect(url) 
{
    $.jStorage.set("last_url", url);
    $("#connect_button").hide();
    $("#connect_destination").hide();
    
    $("#input").focus();
    
    if ( $.browser.mozilla ) { ws = new MozWebSocket(url); } // Mozilla compatibility
    else { ws = new WebSocket(url); }
    
    displayOfftopic("Connecting to " + url + "... socket state "+ws.readyState+"<br>");
    
    ws.onopen = function() { displayOfftopic("Connection established.<br>");};
    ws.onmessage = receiveMessage
    
    ws.onclose = function() { // TODO
        displayMain('<font size="+2" color="red">Disconnected, hit F5 to reconnect</font>')
        displayOfftopic('<font size="+2" color="red">Disconnected, hit F5 to reconnect</font>')
    };
    
    ws.onerror = function (error) {
        displayOfftopic(false,"Error: "+error.data+" (Hit F5 to reconnect)");
    };
}

/*
 * receiveMessage handles received messages which must be valid json strings
 */
function receiveMessage(e) {
    var message;
    try { message = JSON.parse(e.data); }
    catch (SyntaxError) {
        console.log("Parse error");
        console.log(e);
        return
    }
    var key = message.key;
    
    // msg is a single line in-topic message
    if (key == "msg") {
        displayMain(format_message_msg(message));
    }

    // msg_list consists of a list of multiple msg elements
    else if (key == "msg_list")
    {
        var buffer = [];
        for (var i = 0; i < message.value.length; i++) 
        {
            buffer.push(format_message_msg(message.value[i]));
        }
        displayMain(buffer.join(""));
    }

    // oft is a single line off-topic message
    else if (key == "oft") {
        displayOfftopic(format_message_oft(message));
    }

    // oft_list consists of a list of multiple oft elements
    else if (key == "oft_list") {
        var buffer =[];
        for (var i = 0; i < message.value.length; i++)
        {
            buffer.push(format_message_oft(message.value[i]));
        }
        displayOfftopic(buffer.join(""))
    }

    // pwd requests the client to go into password typing mode (hide input and hash output)
    // TODO: server based salt
    else if (key == 'pwd') {
        //marker = $('<span />').insertBefore('#input');
        //$('#input').detach().attr('type', 'password').insertAfter(marker);
        //marker.remove();
        //$("#input").focus();
        $("#input").hide();
        $("#input-password").show();
        $("#input-password").focus();
        is_password = 1;
    }
    else if (key == "clr") {
        var window = message.window || "both"

        if (window == "msg" || window == "both") {
            document.getElementById('root-left-bottomchat').innerHTML = "";
        }
        if (window == "oft" || window == "both") {
            document.getElementById('root-left-topchat').innerHTML = "";
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
        $("#root-left-topchat").css("font-family",font);
        $("#root-left-bottomchat").css("font-family",font);
        $("#root-left-topchat").css("font-size",size);
        $("#root-left-bottomchat").css("font-size",size);
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

function format_text_color(text) {
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

function format_text_timestamp(text, timestamp) {
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

function format_message_oft(message) {
    // TODO: Message ID
    var text = message.value;
    var timestamp;
    if (message.timestamp) {
        timestamp = new Date(message.timestamp * 1000);

    }
    else {
        timestamp = false;
    }
    text = format_text_timestamp(text, timestamp);
    text = format_text_color(text)
    return '<span class="msg">' + text + "</span>";
}

function format_message_msg(message) {
    var text = message.value;
    text = format_text_color(text)
    return '<span class="msg">' + text + "</span>";
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
function displayOfftopic(text) {
    $("#root-left-topchat").append(text);
    document.getElementById("root-left-topchat").scrollTop = document.getElementById("root-left-topchat").scrollHeight;

}
function displayMain(text) {
    $("#root-left-bottomchat").append(text);
    document.getElementById("root-left-bottomchat").scrollTop = document.getElementById("root-left-bottomchat").scrollHeight;
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
    var results = $("#righttop").html().match(pattern);

    while (results.length) {
        var result = results.shift()
        $("#righttop").html( $("#righttop").html().replace(result,"<pre>"+name+typing+character+"</pre>"))
    }
}
function updatePlayerList(message) {
    document.getElementById('righttop').innerHTML = "";
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
        document.getElementById('righttop').innerHTML += "<pre>"+name+typing+character+"</pre>";
        
        
    }
}
function ws_send(msg) {
    ws.send(msg);
}
 
function ws_close() {
    log("closing connection..");
    ws.close();
}
$(window).resize(function() {
    document.getElementById("root-left-bottomchat").scrollTop = document.getElementById("root-left-bottomchat").scrollHeight;
    document.getElementById("root-left-topchat").scrollTop = document.getElementById("root-left-topchat").scrollHeight;
});

$(window).blur(function(event){
    //displayOfftopic(0,"Lost focus");
    if (update_separator) {
        $("#bottomlw").remove();
        $("#toplw").remove();
        $("#root-left-bottomchat").append('<hr id="bottomlw">');
        $("#root-left-topchat").append('<hr id="toplw">');
        document.getElementById("root-left-bottomchat").scrollTop = document.getElementById("root-left-bottomchat").scrollHeight;
        document.getElementById("root-left-topchat").scrollTop = document.getElementById("root-left-topchat").scrollHeight;
        update_separator = false;
    }
});

$(window).focus(function(event){
    //displayOfftopic(0,"Got focus");
    setTimeout(function() { $("#entrybox").focus(); }, 0);
});



$(document).ready(function(){ initialize() });

