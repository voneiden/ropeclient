test_messages = [
  {
    k: "oft"
    v: "This is a simple test message!"
    a: "voneiden"
    t: 1435958925.9176872
  },
  {
    k: "oft"
    v: "Another message. Testing <red>red<reset> color."
    a: "player"
    t: 1435958985.9176872
  },
  {
    k: "oft"
    v: "Dice test: I rolled {2d6;3,6}..."
    a: "afkguy"
    t: 1435959022.9176872
  }
]


connection = require("connection")
ui = require("ui")
input = require("input")


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
  input.init()
  $(window).resize(resize_event)



  connection.connect()
  $("#connect").click(->
    $(".connection-container").fadeOut()
  )
  $("#connect").click()


exports.init = init
