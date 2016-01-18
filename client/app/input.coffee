connection = require("connection")

textarea = null;
password = null;
typing = false;

keypress = (e) ->
  console.log("Keypress", e)
  if e.which == 13
    v = textarea.val()
    textarea.val("")
    if v.length > 0
      connection.send_msg(v)
    e.stopPropagation()
    return false;

keypress_password = (e) ->
  if e.which == 13
    v = password.val()
    password.val("")
    $("#password").hide()
    $("#input").show().focus()
    connection.send_msg(v)



keyup = (e) ->
  length = textarea.val().length
  if length > 0 and !typing
    typing = true;
    connection.send_pit()

  if length == 0 and typing
    typing = false;
    connection.send_pnt()

init = ->
  textarea = $("#input > textarea")
  textarea.keypress(keypress)
  textarea.keyup(keyup)

  password = $("#password > input")
  password.keypress(keypress_password)



exports.init = init