#coding: utf-8

from google.appengine.api import channel
from google.appengine.ext import db
import uuid, json, os
import webapp2, jinja2

jinja_env = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)

class User(db.Model):
  id = db.StringProperty()
  state = db.StringProperty()


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

    if type == '???':
      # なんかする
      pass


app = webapp2.WSGIApplication([
  ('/_ah/channel/(connected|disconnected)/', RoomHandler),
  ('/channel/(.*)', GameHandler),
  ('/', MainHandler)
], debug=True)