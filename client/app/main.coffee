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
  parent.append(element)



init = ->
  console.log("Ready!")
  console.log("Jquery", $)
  append_offtopic(render_message("Hello!"))
  for i in [0..50]
    append_offtopic(render_message("Hello! #{i}"))

  append_offtopic(render_message("Hello!"))


exports.init = init

