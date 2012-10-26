# utils
$ = (id) -> document.getElementById(id)

makeParam = (param) ->
  ("#{key}=#{value}" for own key, value of param).join('&')

get = (url, param, callback) ->
  xhr = new XMLHttpRequest()
  xhr.open('GET', url + '?' + makeParam(param), true)
  xhr.onload = -> callback?(xhr.responseText)
  xhr.send(null)

log = (text) ->
  div = document.createElement('div')
  div.textContent = text
  document.body.appendChild(div)

# main
main = ->
  { id, channelToken } = document.body.dataset
  channel = new goog.appengine.Channel(channelToken)
  socket = channel.open()
  # メッセージが来たら反応する
  socket.onopen = -> log 'open'
  socket.onmessage = (e) -> log e.data

  $('button').addEventListener 'click', ->
    x = $('x').value
    y = $('y').value
    get('/channel/put', { from: id, x, y })
  , false

main()