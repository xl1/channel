﻿#coding: utf-8

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
    html = jinja_env.get_template('main.html').render({
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
      game = Game(user1=id, user2=opponent.id, board='_________')
      game.put()
      user.game = opponent.game = game.key()
      user.state = opponent.state = 'active'
      user.put()
      opponent.put()
      # メッセージを送る
      oid = opponent.id
      channel.send_message(id, 'found opponent ' + oid)
      channel.send_message(oid, 'found opponent ' + id)

    elif type == 'disconnected':
      # ユーザーをけす
      user.delete()


class GameHandler(webapp2.RequestHandler):
  def get(self, type):
    id = self.request.get('from')
    user = User.get_by_key_name(id)

    if type == 'put':
      x = int(self.request.get('x'))
      y = int(self.request.get('y'))
      game = user.game
      
      if user.id == game.user1:
        board = list(game.board)
        board[x + y * 3] = 'o'
        game.board = ''.join(board)
      else:
        board = list(game.board)
        board[x + y * 3] = 'x'
        game.board = ''.join(board)
      channel.send_message(game.user1, game.board)
      channel.send_message(game.user2, game.board)
      # かったかまけたか
      game.put()
      


app = webapp2.WSGIApplication([
  ('/_ah/channel/(connected|disconnected)/', RoomHandler),
  ('/channel/(.*)', GameHandler),
  ('/', MainHandler)
], debug=True)