connection = require("connection")
ui = require("ui")

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
    password_element = $("#password")

    # Hash password
    static_salt = password_element.data("static_salt")
    dynamic_salt = password_element.data("dynamic_salt")
    v = sha256(password.val() + static_salt)
    if dynamic_salt?
      v = sha256(v + dynamic_salt)

    # Clear password
    password.val("")

    # Return to normal input mode
    ui.normal_mode()

    # Send login password
    connection.send_msg(v)

    return false




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