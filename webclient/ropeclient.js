function displayOfftopic(msg) {
    document.getElementById('lefttop').innerHTML += '<font color="#aaaaff">' + msg +  "</font>";  
    document.getElementById("lefttop").scrollTop = document.getElementById("lefttop").scrollHeight;

}
function displayMain(msg) {
    document.getElementById('leftbottom').innerHTML += '<font color="#aaaaff">' + msg + "</font>";  
    document.getElementById("leftbottom").scrollTop = document.getElementById("lefttop").scrollHeight;
}

function ws_init(url) {
    if ( $.browser.mozilla ) {
        ws = new MozWebSocket(url);
    } else {
        ws = new WebSocket(url);
    }
    
    displayOfftopic("Connecting to " + url + "... socket state "+ws.readyState)

    ws.onopen = function() {
        displayOfftopic("Connection established.");
    };
    
    ws.onmessage = function(e) {
        var message = $.trim(e.data);
        var tok = message.split(" ");
        var hdr = tok.shift();
        
        //message = message.replace(/\n/g,"<br />");

        if (hdr == "msg") {
            var timestamp = tok.shift();
            message = tok.join(" ");
            displayMain('<pre>'+message+'</pre>');
        }
        else if (hdr == "oft") {
            var timestamp = tok.shift();
            message = tok.join(" ");
            displayOfftopic('<pre>'+message+'</pre>');
        }
        else if (hdr == 'pwd') {
            marker = $('<span />').insertBefore('#entrybox');
            $('#entrybox').detach().attr('type', 'password').insertAfter(marker);
            marker.remove();
            $("#entrybox").focus();
            //$("#entrybox").attr('type','password');
            isPassword = 1;
            displayOfftopic('pwd toggle');
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
                displayOfftopic("Unknown thingy");
            }
        }
        else if (hdr == 'ptu') {
            // player type update.. single player!!
            updatePlayer(tok.shift());
        }
        else if (hdr == 'plu') {
            // Player list update!
            updatePlayerList(tok.shift().split(';'));
        
        }
        else {
            displayOfftopic('unknown header (len'+hdr.length+': ' + hdr);
        }
    };
    
    ws.onclose = function() {
        displayOfftopic("Connection closed.");
    };
    
    ws.onerror = function (error) {
        alert(error.toSource())
        displayOfftopic("Error: "+error.data);
    };
}

function updatePlayer(playerinfo) {
    var info = playerinfo.split(':');
    var name = info.shift()
    var typing = info.shift()
    if (typing == "1") { typing = "*" }
    else { typing = "" }
    var char = info.shift()
    var pattern = new RegExp("<pre>"+name+'.*</pre>');
    //var results = document.getElementById('righttop').innerHTML.match(pattern);
    var results = $("#righttop").html().match(pattern);

    while (results.length) {
        result = results.shift()
        $("#righttop").html( $("#righttop").html().replace(result,"<pre>"+name+typing+" ("+char+")<br>"))
    }
}
function updatePlayerList(playerList) {
    displayOfftopic("Updating full playerlist"+playerList.join(" "));
    document.getElementById('righttop').innerHTML = "";
    while (playerList.length) {
        var info = playerList.shift().split(':')
        var name = info.shift()
        var typing = info.shift()
        var char = info.shift()
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

$(document).ready(function(){
    isTyping = 0;
    isPassword = 0;
    playerList = new Array();
    
    $("#entrybox").focus();

    $("#entrybox").keyup(function(event){
        if(event.keyCode == 13){
            if (isPassword) {
                isPassword = 0;
                var msg = $("#entrybox").val();
                $("#entrybox").val("");
                
                marker = $('<span />').insertBefore('#entrybox');
                $('#entrybox').detach().attr('type', 'text').insertAfter(marker);
                marker.remove();
                $("#entrybox").focus();
                
                var shaObj = new jsSHA(msg+'r0p3s4lt');
                msg = shaObj.getHash("SHA-256","HEX");
            }
            else {
                var msg = $("#entrybox").val()
                $("#entrybox").val("");
            }
            ws_send('msg ' + msg);
            isTyping = 0;
            
        }
        else {
            if (isTyping == 0 && $("#entrybox").val().length > 0) {    
                isTyping = 1;
                ws_send("pit")
        }
            else if (isTyping == 1 && $("#entrybox").val().length == 0) {
                isTyping = 0;
                ws_send("pnt")
            }
        }
    });
    
    $("#entrybox").focusout(function(event){
        setTimeout(function() { $("#entrybox").focus(); }, 0);
    });

    ws_init("ws://ninjabox.sytes.net:9091")
});
