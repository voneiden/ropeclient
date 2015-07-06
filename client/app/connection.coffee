main = require("main")
ui = require("ui")
websocket = null


handle = (data) ->
  if !data.k?
    console.warn("Invalid data packet, key is missing. Ignoring")
    return

  # Offtopic message
  if data.k == "oft"
    ui.append_offtopic(data.v)

  else
    console.warn("Unimplemented key:", data.key)

onopen = (event) ->
  if websocket?
    websocket.send("Testing! Stuff!")


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