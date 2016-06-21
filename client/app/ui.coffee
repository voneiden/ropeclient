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
render_message = (message) ->
  if message instanceof Array
    return (render_message(msg) for msg in message).join("")
  else
    if !message? || !message.k? || !message.v?
      console.error("Invalid message:", message)
      return null

    # Add colors
    value = parse_colors(message.v)
    value = parse_dice(value)

    html = ""

    # Display three col
    if message.k == "oft" && (message.a? || message.t?)
      timestamp = "[hh:mm]"
      account = if message.a? then message.a else "Unknown"
      html = "<tr><td>#{timestamp}</td><td>#{account}</td><td>#{value}</td>"

    # Display full width
    else
      html = "<tr><td colspan=\"3\">#{value}</td></tr>"
    return $.parseHTML(html)

###
  Append HTML into offtopic
###
append_offtopic = (message) ->
  if !message?
    console.error("Invalid element")
    return
  html = render_message(message, true)
  offtopic = $("#offtopic-table")
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


password_mode = (static_salt, dynamic_salt) ->
  $("#input").hide().blur()
  password = $("#password")
  password
    .show()
    .data("static_salt", static_salt)
    .data("dynamic_salt", dynamic_salt)
    .find("input")
      .focus()



normal_mode = () ->
  $("#password").hide().blur()
  $("#input")
    .show()
    .find("textarea")
      .focus()

show_connect = ->

clear_offtopic = () ->
  offtopic = $("#offtopic-table").html("")


exports.append_offtopic = append_offtopic
exports.append_ontopic = append_ontopic
exports.clear_offtopic = clear_offtopic
exports.password_mode = password_mode
exports.normal_mode = normal_mode