###
  Parse colors from raw messages. Colors are
  reprensented by html-like tags and may contain
  any alphanumeric character and #.
###
parse_colors = (text) ->
  color_pattern = /<[\w\d#]+>/g
  color_regex = new RegExp(color_pattern)
  stack = 0

  search_text = text
  while (match = color_regex.exec(search_text))?
    value = match[0].toLowerCase()
    if value == "<reset>" or value == "<r>"
      if stack == 0
        continue
      else
        stack -= 1
        text = text.replace(match[0], "</span>")
    else
      stack += 1
      color = match[0].substring(1, match[0].length - 1)
      text = text.replace(match[0], "<span style=\"color: #{color};\">")

    console.log("got match", match)

  for i in [0..stack]
    text += "</span>"

  return text

###
  Parses the dice commands in raw messages to html.
  Dice commands are enclosed in curly brackets and contain two parameters
  separated by a semicolon
###
parse_dice = (text) ->
  dice_pattern = /\{[\w\d]+;[\w\d,]+\}/g
  dice_regex = new RegExp(dice_pattern)

  search_text = text
  while (match = dice_regex.exec(search_text))?
    console.log("dice match", match)

    sub = match[0].substring(1, match[0].length - 1)
    params = sub.split(";")

    if params.length != 2
      console.error("Parse dice encountered invalid params")
      continue

    key = params[0]
    values = (parseInt(value) for value in params[1].split(','))

    sum = 0
    sum += value for value in values

    html = ["<span class=\"dice\" onclick=\"$(this).children().toggle()\">#{key}: #{value}",
            "<span class=\"dice-details\"> (#{params[1]})</span></span>"].join("")

    text = text.replace(match[0], html)

  return text


###
  Render a message received from server. The message can be a valid message object
  or it can be a string. Also, additional formatting (timestamp) is applied if offtopic is set to true.
###
render_message = (message, offtopic) ->
  if message instanceof Array
    return (render_message(msg, offtopic) for msg in message).join("")
  else
    if !message?
      console.error("Invalid message")
      return null

    if !offtopic?
      offtopic = false

    if message.raw
      html = message.raw
      if offtopic
        pad = (" " for i in [1..10-message.owner.length]).join("")
        html = "[hh:mm] #{pad}#{message.owner}: #{html}"
    else
      html = message

    # Add colors
    html = parse_colors(html)
    html = parse_dice(html)

    html = "<div>#{html}</div>"
    return $.parseHTML(html)

###
  Append HTML into offtopic
###
append_offtopic = (message) ->
  if !message?
    console.error("Invalid element")
    return
  html = render_message(message, true)
  offtopic = $("#offtopic")
  append(offtopic, html)

###
  Append HTML into ontopic
###
append_ontopic = (message) ->
  if !message?
    console.error("Invalid element")
    return

  html = render_message(message)
  ontopic = $("#ontopic")
  append(ontopic, html)

###
  Append HTML (element) to parent and scroll the element
  if necessary
###
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


show_connect = ->


exports.append_offtopic = append_offtopic
exports.append_ontopic = append_ontopic