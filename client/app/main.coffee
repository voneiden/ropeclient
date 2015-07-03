render_message = (message) ->
  if !message?
    console.error("Invalid message")
    return null

  if message.raw
    html = message.raw
  else
    html = message

  html = "<div>#{html}</div>"
  return $.parseHTML(html)

append_offtopic = (element) ->
  if !element?
    console.error("Invalid element")
    return

  offtopic = $("#offtopic")
  append(offtopic, element)


append = (parent, element) ->
  if !parent? or !element?
    console.error("Invalid parent or element")
    return
  console.log(parent)
  console.log(parent.scrollTop(), parent[0].scrollHeight)

  bottom = parent.innerHeight() + parent.scrollTop()
  console.log("Bottom", bottom)
  console.log("scrollHeight", parent[0].scrollHeight)
  if bottom >= parent[0].scrollHeight - 1
    autoscroll = true
  else
    autoscroll = false

  parent.append(element)
  if autoscroll
    parent.scrollTop(parent[0].scrollHeight - parent.innerHeight())

interval = 0
test = ->
  interval += 1
  append_offtopic(render_message("Hello! #{interval}"))

resize_event = (event) ->
  console.log("res", event)
  offtopic = $("#offtopic")
  ontopic = $("#ontopic")

  offtopic.scrollTop(offtopic[0].scrollHeight - offtopic.innerHeight())
  ontopic.scrollTop(ontopic[0].scrollHeight - ontopic.innerHeight())

init = ->
  console.log("Ready!")
  console.log("Jquery", $)
  append_offtopic(render_message("Hello!"))
  for i in [0..50]
    append_offtopic(render_message("Hello! #{i}"))

  window.setInterval(test, 1000)

  $(window).resize(resize_event)



exports.init = init

