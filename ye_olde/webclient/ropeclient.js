// Ropeclient web client
// See http://www.github.com/voneiden/ropeclient
// for license

// Autocomplete variables
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
    'spawn':[3,"Character name?","Short description? (Max 40 chars)","Long description"]
};

// Message edit variables
edit_history = [];
edit_index   = -1;
edit_mem     = ''; 
editing = 0;

// Special colors
color_timestamp = 'gray';

// separator line
update_separator = false;


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

// This function updates the green blocks left of entrybox
function displayAutocomplete() {
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
}

// This function handles all autocomplete related events
function AutoComplete(event) {
    // There are 3 stages
    // 1 - command autocomplete
    // 2 - argument 1 complete
    // 3 - argument 2 complete..
    // 4 - argument 3 complete..
    if (editing) { return }
    keyCode = event.keyCode
    if (autocomplete_stage == 0 && keyCode == 9) {
        //displayOfftopic("Enter stage 1");
        autocomplete_stage = 1;
    }
    
    if (autocomplete_stage == 1 && keyCode == 9) {
        if (autocomplete_cycle.length == 0) {
            autocomplete_base = $("#entrybox").val()
            //displayOfftopic("Search for command "+autocomplete_base);
            // Fill the cycle with results
            var pattern = new RegExp('^' + autocomplete_base + '.*',"i");
            for (var cmd in autocomplete_commands) {
                if (pattern.test(cmd)) {
                    autocomplete_cycle.push(cmd)
                }
            }
            
            if (autocomplete_cycle.length == 0) {
                // No results found, fall back to stage 0
                autocomplete_stage = 0;
            }
            
            else { 
                //displayOfftopic("Auto completing command");
                $("#entrybox").val("");
                autocomplete_buffer.push(autocomplete_cycle[autocomplete_index]);
                displayAutocomplete();
                //$("#entrybox").val(autocomplete_cycle[autocomplete_index] + " "); 
            }
        }
        else {
            autocomplete_index += 1;
            autocomplete_index %= autocomplete_cycle.length;
            //displayOfftopic("Auto completing command");
            //$("#entrybox").val(autocomplete_cycle[autocomplete_index] + " "); 
            autocomplete_buffer.pop();
            autocomplete_buffer.push(autocomplete_cycle[autocomplete_index]);
            displayAutocomplete();
        }
    }
    // Abort choosing autocomplete command
    else if (autocomplete_stage == 1 && keyCode == 8) {
        $("#entrybox").val(autocomplete_base );
        $("#autocomplete").text("");
        autocomplete_stage = 0;
        autocomplete_cycle = [];
        autocomplete_buffer = [];
        autocomplete_index = 0;
        autocomplete_base = "";
        if (event.preventDefault) { event.preventDefault(); }
    }
    
    // Accept autocomplete command by typing something else
    else if (autocomplete_stage == 1 && keyCode >= 48) {
        //displayOfftopic("Autocomplete accepted")
        $("#entrybox").val("");
        autocomplete_stage = 2;
        
    }
    
    else if (autocomplete_stage == 2 && keyCode == 8 && $("#entrybox").val().length == 0) {
        // If we have more than one command in the buffer, return the last command. 
        // Otherwise return the base text for autcomplete
        
        if (autocomplete_buffer.length > 1) {
            $("#entrybox").val(autocomplete_buffer.pop());
            displayAutocomplete();
            
        }
        else { // Return to normal mode
            autocomplete_stage = 0; 
            $("#autocomplete").text("");
            autocomplete_cycle = [];
            autocomplete_index = 0;
            autocomplete_buffer = [];
            $("#entrybox").val(autocomplete_base );
        }
        
        if (event.preventDefault) { event.preventDefault(); }
    }
    else if (autocomplete_stage == 2 && keyCode == 9) {
        autocomplete_buffer.push($("#entrybox").val());
        $("#entrybox").val("");
        displayAutocomplete();
        
        
    }
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
    $("#lefttop").append(text);
    document.getElementById("lefttop").scrollTop = document.getElementById("lefttop").scrollHeight;

}
function displayMain(text) {
    $("#leftbottom").append(text);
    document.getElementById("leftbottom").scrollTop = document.getElementById("leftbottom").scrollHeight;
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
function ws_init(url) {
    if ( $.browser.mozilla ) {
        ws = new MozWebSocket(url);
    } else {
        ws = new WebSocket(url);
    }
    
    displayOfftopic("Connecting to " + url + "... socket state "+ws.readyState+"<br>");
    
    ws.onopen = function() {
        displayOfftopic("Connection established.<br>");
    };
    
    ws.onmessage = function(e) {
        var message = $.trim(e.data);
        var tok = message.split(" ");
        var hdr = tok.shift();
        
        //message = message.replace(/\n/g,"<br />");

        if (hdr == "msg") {
            var everything = tok.join(" ");
            var lines = everything.split("\x1b");
            var output = [];
            
            while (lines.length) {
                var line = lines.shift();
                var linetok = line.split("\x1f");
                var timestamp = linetok.shift();
                //displayOfftopic(false,timestamp)
                var editable = linetok.shift();
                var message = linetok.shift();
                
                if (editable == "1") {
                    edit_history.push([timestamp,message])
                }
                while (edit_history.length > 10) {
                    edit_history.shift()
                }
                
                message = diceParse(message);
                message = nameParse(message);
                var spanid = '';
                if (timestamp && timestamp != "0") {
                    spanid = ' id="' + timestamp + '"';
                    timestamp = makeTimestamp(timestamp);
                }
                else {
                    timestamp = '';
                }
                output.push('<span class="msg"' + spanid + ">" + timestamp + message + "</span>");
            }
            displayMain(output.join(""));
        }
        else if (hdr == "oft") {
            //A lot faster method of displaying a lot of text at once.
            //Still needs improving, so lets try..
            
            var everything = tok.join(" ");
            var lines = everything.split("\x1b");
            var output = [];
            while (lines.length) {
                var line = lines.shift();
                var linetok = line.split(" ");
                var timestamp = linetok.shift();
                var message = linetok.join(" ");
                
                message = diceParse(message);
                var spanid = '';
                if (timestamp && timestamp != "0") {
                    spanid = ' id="' + timestamp + '"';
                    timestamp = makeTimestamp(timestamp);
                }
                else {
                    timestamp = '';
                }
                output.push('<span class="msg"' + spanid + ">" + timestamp + message + "</span>");
                //var timestamp = '';
                //var spanid = '';
                // if (id && id != "0") {
                //    spanid = ' id="' + id + '"';
                //    timestamp = makeTimestamp(id);
                //    
                //}
            }
            displayOfftopic(output.join(''));
            //displayOfftopic(false,output.join(""));
        }
        else if (hdr == 'pwd') {
            marker = $('<span />').insertBefore('#entrybox');
            $('#entrybox').detach().attr('type', 'password').insertAfter(marker);
            marker.remove();
            $("#entrybox").focus();
            //$("#entrybox").attr('type','password');
            isPassword = 1;
            //displayOfftopic('pwd toggle');
        }
        else if (hdr == 'clr') {
            var window = tok.shift();

            if (window == 'main') {
                //$('#leftbottom').innerHTML = "Cleared.<br />";
                document.getElementById('leftbottom').innerHTML = "";
            }
            else if (window == 'offtopic') {
                document.getElementById('lefttop').innerHTML = "";
            }
            else {
                displayOfftopic(false,"Unknown thingy");
            }
        }
        else if (hdr == 'png') {
            ws_send('png');
        }
        else if (hdr == 'ptu') {
            // player type update.. single player!!
            updatePlayer(tok.shift());
        }
        else if (hdr == 'plu') {
            // Player list update!
            updatePlayerList(tok.shift().split(';'));
        
        }
        else if (hdr == 'col') {
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
        else if (hdr == 'fnt') {
            
            font = tok.shift();
            size = tok.shift();
            $("#lefttop").css("font-family",font);
            $("#leftbottom").css("font-family",font);
            $("#lefttop").css("font-size",size);
            $("#leftbottom").css("font-size",size);
        }
        else if (hdr == 'edi') {
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
            displayOfftopic(false,'unknown header (len:'+hdr.length+': ' + hdr);
        }
    };
    
    ws.onclose = function() {
        displayMain('<font size="+2" color="red">Disconnected, hit F5 to reconnect</font>')
        displayOfftopic('<font size="+2" color="red">Disconnected, hit F5 to reconnect</font>')
    };
    
    ws.onerror = function (error) {
        //alert(error.toSource())
        displayOfftopic(false,"Error: "+error.data+" (Hit F5 to reconnect)");
    };
}

function updatePlayer(playerinfo) {
    var info = playerinfo.split(':');
    var name = info.shift()
    var typing = info.shift()
    if (typing == "1") { typing = "*" }
    else { typing = "" }
    var char = nameParse(info.shift());
    var pattern = new RegExp("<pre>"+name+'.*?</pre>');
    //var results = document.getElementById('righttop').innerHTML.match(pattern);
    var results = $("#righttop").html().match(pattern);

    while (results.length) {
        result = results.shift()
        $("#righttop").html( $("#righttop").html().replace(result,"<pre>"+name+typing+" ("+char+")</pre>"))
    }
}
function updatePlayerList(playerList) {
    document.getElementById('righttop').innerHTML = "";
    while (playerList.length) {
        var info = playerList.shift().split(':')
        var name = info.shift()
        var typing = info.shift()
        var char = nameParse(info.shift());
        if (typing == "1") { typing = "*" }
        else { typing = "" }
        document.getElementById('righttop').innerHTML += "<pre>"+name+typing+" ("+char+")</pre>";
        
        
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
    document.getElementById("leftbottom").scrollTop = document.getElementById("leftbottom").scrollHeight;
    document.getElementById("lefttop").scrollTop = document.getElementById("lefttop").scrollHeight;
});

$(window).blur(function(event){
    //displayOfftopic(0,"Lost focus");
    if (update_separator) {
        $("#bottomlw").remove();
        $("#toplw").remove();
        $("#leftbottom").append('<hr id="bottomlw">');
        $("#lefttop").append('<hr id="toplw">');
        document.getElementById("leftbottom").scrollTop = document.getElementById("leftbottom").scrollHeight;
        document.getElementById("lefttop").scrollTop = document.getElementById("lefttop").scrollHeight;
        update_separator = false;
    }
});

$(window).focus(function(event){
    //displayOfftopic(0,"Got focus");
    setTimeout(function() { $("#entrybox").focus(); }, 0);
});
$(document).ready(function(){
    isTyping = 0;
    isPassword = 0;
    playerList = new Array();
    
    $("#entrybox").focus();
    $("#entrybox").keydown(function(event){
        if (event.keyCode == 9) {
            AutoComplete(event);
            
            if (event.preventDefault) { event.preventDefault(); }
            return false;
            
        }
        else if (event.keyCode == 38 || event.keyCode == 40) // Up / Down
            {
                EditHistory(event);
            }
            
            
        else {
            AutoComplete(event);
        }
    });
    $("#entrybox").keyup(function(event){
        if(event.keyCode == 13){
            // Check if it's a command or message
            
            if (isPassword) {
                header = "msg";
                isPassword = 0;
                var content = $("#entrybox").val();
                $("#entrybox").val("");
                
                marker = $('<span />').insertBefore('#entrybox');
                $('#entrybox').detach().attr('type', 'text').insertAfter(marker);
                marker.remove();
                $("#entrybox").focus();
                
                var shaObj = new jsSHA(content+'r0p3s4lt');
                content = shaObj.getHash("SHA-256","HEX");
            }
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
        
    });
    
    $("#entrybox").focusout(function(event){
        //setTimeout(function() { $("#entrybox").focus(); }, 0);
    });
    //ws_init("ws://localhost:9091")
    ws_init("ws://ninjabox.sytes.net:9091")
});