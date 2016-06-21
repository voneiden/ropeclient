main = require("main")
ui = require("ui")
websocket = null

# From Coffeescript cookbook - to determine if an incoming message is an array
typeIsArray = Array.isArray || ( value ) -> return {}.toString.call( value ) is '[object Array]'

message_pit = JSON.stringify({'k':'pit'})
message_pnt = JSON.stringify({'k':'pnt'})
message_msg = {'k': 'msg', 'v': ''}

send_pit = ->
  if websocket?
    websocket.send(message_pit)
send_pnt = ->
  if websocket?
    websocket.send(message_pnt)

send_msg = (value)->
  if websocket?
    message_msg.v = value
    websocket.send(JSON.stringify(message_msg))

handle = (data) ->
  console.warn("Handle data", data)
  if typeIsArray(data)
    for message in data
      process(message)
  else
    process(data)

process = (message) ->
  if !message.k?
    console.warn("Invalid data packet, key is missing. Ignoring")
    return

  # Offtopic message
  if message.k == "oft"
    ui.append_offtopic(message)

  # Ontopic message
  else if message.k == "ont"
    ui.append_ontopic(message)

  # Password request
  else if message.k == "pwd"
    ui.password_mode(message.ss, message.ds)

  # Clear view
  else if message.k == "clr"
    if message.v == "oft"
      ui.clear_offtopic()

    else if message.v == "ont"
      ui.clear_ontopic()

    else if message.v == "all"
      ui.clear_offtopic()
      ui.clear_ontopic()

    else
      console.error("Unknown value for clear")
  else
    console.warn("Unimplemented key:", message.k)


onopen = (event) ->
  console.warn("Open")
  if websocket?
    console.warn("Sending test")
    #websocket.send("Testing! Stuff!")
  else
    console.warn("No websocket")

onmessage = (event) ->
  try
    data = JSON.parse(event.data)
  catch
    console.warn("Received invalid JSON object, ignoring")
    return

  handle(data)

onerror = (event) ->
  ui.append_offtopic("<red>Connection failed!")

connect = ->
  websocket = new WebSocket("ws://localhost:8090")
  websocket.onopen = onopen
  websocket.onmessage = onmessage
  websocket.onerror = onerror


exports.connect = connect
exports.send_pit = send_pit
exports.send_pnt = send_pnt
exports.send_msg = send_msg