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
