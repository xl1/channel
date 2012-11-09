# utils
$ = (id) -> document.getElementById(id)
$$ = (q) -> [].slice.call document.querySelectorAll(q)
  
log = (text) ->
  div = document.createElement('div')
  div.textContent = text
  document.body.appendChild(div)
  

#
class Game
  # constants
  BASE_URL: '/channel/'

  constructor: ->
    @field = $('field')
    @buttons = $$('#field > .button')
    
  send: (type, param, callback) ->
    paramString = ("#{key}=#{value}" for own key, value of param).join('&')
    xhr = new XMLHttpRequest()
    xhr.open('GET', @BASE_URL + type + '?' + paramString, true)
    xhr.onload = -> callback?(xhr.responseText)
    xhr.send(null)
    
  addMark: (data) ->
    for mark, i in data.split('')
      @buttons[i].innerText = mark if mark isnt '_'
      


  
# main
main = ->
  game = new Game()

  { id, channelToken } = document.body.dataset
  channel = new goog.appengine.Channel(channelToken)
  socket = channel.open()
  # メッセージが来たら反応する
  socket.onopen = -> log 'open'
  socket.onmessage = (e) ->
    data = e.data
    if data.match(/^[_ox]{9}$/)
      log data
      game.addMark(data)
    else
      log data
        
  game.field.addEventListener 'mouseup', (e) ->
    for button, i in game.buttons
      if button is e.target
        game.send('put', { from: id, x: i % 3, y: i / 3 |0 })
        return
  , false

main()