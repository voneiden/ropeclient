main = require("main")
websocket = null


handle = (data) ->
  if !data.k?
    console.warn("Invalid data packet, key is missing. Ignoring")
    return

  # Offtopic message
  if data.k == "oft"
    main.append_offtopic(data.v)

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

connect = ->
  websocket = new WebSocket("ws://localhost:8090")
  websocket.onopen = onopen
  websocket.onmessage = onmessage



exports.connect = connect