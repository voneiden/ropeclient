main = require("main")
ui = require("ui")
websocket = null
typeIsArray = Array.isArray || ( value ) -> return {}.toString.call( value ) is '[object Array]'

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
    console.warn("APpending")
    ui.append_offtopic(message.v)

  else
    console.warn("Unimplemented key:", message.key)


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