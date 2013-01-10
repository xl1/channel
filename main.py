#coding: utf-8

from google.appengine.api import channel
from google.appengine.ext import db
import uuid, json, os
import webapp2, jinja2


  
jinja_env = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)
class Game(db.Model):
  user1 = db.StringProperty()
  user2 = db.StringProperty()
  board = db.StringProperty()
  lastUser = db.StringProperty()
  # o x
  # xo 
  #  xo

class User(db.Model):
  id = db.StringProperty()
  state = db.StringProperty()
  game = db.ReferenceProperty(Game)
  

  


class MainHandler(webapp2.RequestHandler):
  def get(self):
    # ユーザーをつくる
    id = 'user' + uuid.uuid4().hex
    user = User(key_name=id, id=id, state='waiting')
    user.put()
    # ページを生成して返す
    token = channel.create_channel(id)
    html = jinja_env.get_template('main_reversi.html').render({
      'id': id,
      'token': token
    })
    self.response.out.write(html)


class RoomHandler(webapp2.RequestHandler):
  # ユーザを部屋に入れたり出したりする
  def post(self, type):
    id = self.request.get('from')
    user = User.get_by_key_name(id)

    if user is None:
      channel.send_message(id, 'please try again')
      return

    if type == 'connected':
      opponent =\
        User.all().filter('state', 'waiting').filter('id !=', id).get()
      if opponent is None:
        channel.send_message(id, 'no other user in lobby. please wait')
        return
      # ゲームを作る
      game = Game(user1=id, user2=opponent.id,
        board='___________________________ox______xo___________________________'
      )
      game.put()
      user.game = opponent.game = game.key()
      user.state = opponent.state = 'active'
      user.put()
      opponent.put()
      # メッセージを送る
      oid = opponent.id
      channel.send_message(id, 'found opponent ' + oid + ' you are o')
      channel.send_message(oid, 'found opponent ' + id + ' you are x')
      channel.send_message(game.user1, game.board)
      channel.send_message(game.user2, game.board)
      
    elif type == 'disconnected':
      # ユーザーをけす
      try:
        game = user.game
      except:
        game = None
      if game:
        oid = game.user1
        if oid == id:
          oid = game.user2
        opponent = User.get_by_key_name(oid)
        opponent.state = 'waiting' 
        opponent.put()
        channel.send_message(oid, 'connection lost with opponent')
        game.delete()
      user.delete()


class GameHandler(webapp2.RequestHandler):
  def get(self, type):
    id = self.request.get('from')
    user = User.get_by_key_name(id)
    
    game=user.game
    board = list(game.board)
    def getBoard(x, y):
      return board[x + y * 8 ] if x in range(8) and y in range(8) else None
    
    if type == 'put':
      x = int(self.request.get('x'))
      y = int(self.request.get('y'))
      game = user.game
      
      mymark = 'o' if user.id == game.user1 else 'x'
      isgood = False
      #flag = True
      
      dxlist = [ 0, -1, -1, -1, 0, 1, 1,  1]
      dylist = [-1, -1,  0,  1, 1, 1, 0, -1]
      
      for i in range(0, 8):
        dx = dxlist[i]
        dy = dylist[i]
       
        mark = getBoard(x + dx, y + dy)
        if mark == None or mark == mymark or mark == '_':
          continue
          
        for j in range(2, 8):
          mark = getBoard(x + dx*j, y + dy*j )
          #channel.send_message(user.id, str(mark) + mymark + str(dx)+str(dy))
          if mark == '_' or mark is None:
            break
          if mark == mymark:
            for k in range(0,j):
              board[x+dx*k+(y+dy*k)*8] = mymark
            isgood = True
            break
            
            
      if isgood:
        if game.lastUser==user.id:
          channel.send_message(user.id,'Not Your Turn!')
        else:
          game.lastUser=user.id
          game.board = ''.join(board)
          game.put()
      else:
        channel.send_message(user.id, "Wrong Place")
        
      channel.send_message(game.user1, game.board)
      channel.send_message(game.user2, game.board)
      
      
      
      # かったかまけたか
      if '_' not in board:
        shiro,kuro=0,0
        for i in board:
          if i == 'o':
            shiro += 1 
          if i == 'x':
            kuro+=1
        if shiro>kuro:    
          channel.send_message(game.user1,'White Wins')
          channel.send_message(game.user2,'White Wins')
        elif kuro>shiro:
          channel.send_message(game.user1,'Black Wins')
          channel.send_message(game.user2,'Black Wins')
        else:
          channel.send_message(game.user1,'Match Drawn')
          channel.send_message(game.user2,'Match Drawn')
         

app = webapp2.WSGIApplication([
  ('/_ah/channel/(connected|disconnected)/', RoomHandler),
  ('/channel/(.*)', GameHandler),
  ('/', MainHandler)
], debug=True)