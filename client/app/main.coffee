test_messages = [
  {
    raw: "This is a simple test message!"
    owner: "voneiden"
    stamp: 1435958925.9176872
  },
  {
    raw: "Another message. Testing <red>red<reset> color."
    owner: "player"
    stamp: 1435958985.9176872
  },
  {
    raw: "Dice test: I rolled {2d6;3,6}..."
    owner: "afkguy"
    stamp: 1435959022.9176872
  }
]


connection = require("connection")
ui = require("ui")


interval = 0


test = ->
  interval += 1
  ui.append_offtopic(render_message("Hello! #{interval}"))

###
  Called when browser window is resized
###
resize_event = (event) ->
  console.log("res", event)
  offtopic = $("#offtopic")
  ontopic = $("#ontopic")

  offtopic.scrollTop(offtopic[0].scrollHeight - offtopic.innerHeight())
  ontopic.scrollTop(ontopic[0].scrollHeight - ontopic.innerHeight())

###
  Initialize ropeclient
###
init = ->
  console.log("Ready!")
  console.log("Jquery", $)
  #append_offtopic(render_message("Hello!"))
  for i in [0..50]
    msg = test_messages[Math.floor(Math.random() * test_messages.length)]
    ui.append_offtopic(msg)
    ui.append_ontopic(msg)

  #window.setInterval(test, 1000)

  $(window).resize(resize_event)

  #connection.connect()
  $("button").click(->
    $(".connection-container").fadeOut()
  )


exports.init = init
