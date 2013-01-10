# utils
$ = (id) -> document.getElementById(id)

xhrsend = (url, param, method='GET', callback) ->
  xhr = new XMLHttpRequest
  if method.toUpperCase() is 'GET'
    params = ("#{key}=#{value}" for own key, value of param).join '&'
    url += '?' + params
    param = null
  xhr.open(method, url, true)
  xhr.onload = -> calback?(xhr.responseText)
  xhr.send(param)

uuid = do ->
  re = /[xy]/g
  replacer = (c) ->
    r = Math.random() * 16 |0
    (if c is 'x' then r else (r & 3 | 8)).toString 16
  ->
    'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(re, replacer).toUpperCase()


class Model
  constructor: ->
    @id = uuid()

  change: ->
    eve "#{@id}.change", null, @

class View
  render: (model) ->
  
  watch: (model) =>
    if @_model
      eve.off "#{@_model.id}.change"
    @_model = model
    eve.on "#{model.id}.change", @render.bind(@)


# --- main ---

class Game extends Model
  BASE_URL: '/channel/'
  SIZE: 3

  constructor: ->
    super()
    @reset()
    
  reset: ->
    @field = ('_' for i in [1..@SIZE*@SIZE])

  setup: (@userId, @mark) ->
    @isMyTurn = @mark is 'o'

  canPutPieceAt: (index) ->
    # 置けるかどうか判定
    @isMyTurn and @field[index] is '_'

  putPieceAt: (index) ->
    return if not @canPutPieceAt(index)
    @field[index] = @mark
    @change()
    xhrsend(@BASE_URL + 'put',
      from: @userId, x: index % @SIZE, y: index / @SIZE |0)

  update: (data) ->
    if data
      @field = data.split('')
      @isMyTurn = not @isMyTurn
    @change()


class Reversi extends Game
  SIZE: 8

  _at: (x, y) ->
    return if x < 0 or x >= @SIZE or y < 0 or y >= @SIZE
    @field[x + y * @SIZE]

  canPutPieceAt: (index) ->
    return false unless @isMyTurn and @field[index] is '_'
    x = index % @SIZE
    y = index / @SIZE |0
    for [dx, dy] in [[-1,0],[-1,-1],[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1]]
      mark = @_at(x + dx, y + dy)
      continue if mark is @mark or mark is '_' or !mark
      for i in [2..7]
        mark = @_at(x + dx * i, y + dy * i)
        break if mark is '_' or !mark
        return true if mark is @mark
    false


class GameView extends View
  constructor: ->
    super()
    @parent = $('field')

  watch: (model) ->
    super model
    
    # create elements
    size = model.SIZE
    fragment = document.createDocumentFragment()
    for i in [0...size * size]
      button = document.createElement 'div'
      button.classList.add 'button'
      button.dataset.index = i
      fragment.appendChild button
    @parent.appendChild fragment

    # add event listeners
    @parent.addEventListener 'mouseup', (e) =>
      model.putPieceAt(e.target.dataset.index |0)
    , false

  render: (model) ->
    button = @parent.firstChild
    for mark in model.field
      button.textContent = if mark is '_' then '' else mark
      button = button.nextSibling


class ReversiView extends GameView
  render: (model) ->
    button = @parent.firstChild
    for mark in model.field
      clist = button.classList
      clist.remove 'piece-o'
      clist.remove 'piece-x'
      if mark is 'o' then clist.add 'piece-o'
      else if mark is 'x' then clist.add 'piece-x'
      button = button.nextSibling

     
class InfoBox extends View
  constructor: ->
    super()
    @elem = $('info')
    
  watch: (model) ->
    super model
    
    # create elements
    for name in ['left', 'right', 'black', 'white']
      div = document.createElement 'div'
      div.className = name
      @elem.appendChild div
      @[name] = div
    
  render: (model) ->
    mark = model.mark
    data = model.field.join ''
    black = data.split('x').length - 1
    white = data.split('o').length - 1

    @left.innerText  = "#{if mark is 'x' then 'あなた' else 'あいて'}/黒: #{black}"
    @right.innerText = "#{if mark is 'o' then 'あなた' else 'あいて'}/白: #{white}"
    @black.style.width = black * 100 / 64 + '%'
    @white.style.width = white * 100 / 64 + '%'
    if model.isMyTurn ^ (mark is 'o')
      @left.classList.add 'on-turn'
      @right.classList.remove 'on-turn'
    else
      @right.classList.add 'on-turn'
      @left.classList.remove 'on-turn'

    # バグを回避
    @left.style.maxWidth = @right.style.maxWidth = '400px'

  show: (message) ->
    @left.classList.remove 'on-turn'
    @right.classList.remove 'on-turn'
    @left.innerText = message
    @right.innerText = ' '

    
class Overlay
  constructor: ->
    @elem = $('overlay')

  show: (text) ->
    @elem.textContent = text
    @elem.className = 'show'
    setTimeout =>
      @elem.className = ''
    , 2000

class Logger
  constructor: ->
    @elem = $('logger')

  log: (text) ->
    div = document.createElement('div')
    div.textContent = text
    @elem.insertBefore div, @elem.firstChild


main = ->
  { id, channelToken, type } = document.body.dataset
  if type is 'reversi'
    [game, gameView, info] = [new Reversi, new ReversiView, new InfoBox]
    gameView.watch game
    info.watch game
    info.show '相手のユーザーを待っています……'
  else if type is 'tictactoe'
    [game, gameView] = [new Game, new GameView]
    gameView.watch game
  
  overlay = new Overlay
  logger = new Logger
  channel = new goog.appengine.Channel(channelToken)
  socket = channel.open()
  
  # メッセージが来たら反応する
  socket.onopen = -> logger.log 'open'
  socket.onmessage = (e) ->
    data = e.data
    logger.log data
    if data is 'please try again'
      info.show 'やり直してください'
    else if m = data.match(/found opponent (\w+) you are (o|x)/)
      [dummy, opponentID, mark] = m
      game.setup(id, mark)
    else if data is 'Not Your Turn!' or data is 'Wrong Place'
      game.update()
    else if m = data.match(/(\w+) has Won/)
      [dummy, winner] = m
      if winner is id
        overlay.show 'おめでとう、あなたの勝ちです'
      else
        overlay.show '残念、あなたの負けです...'
    else if data is 'Match Drawn'
      overlay.show 'ひきわけになりました'
    else if data.match(/^[_ox]+$/)
      game.update(data)
    else if data is 'connection lost with opponent'
      info?.show '相手のユーザーが切断されました'
      game.reset()

main()