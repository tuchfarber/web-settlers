from bottle import route, response, request, get, post, TEMPLATE_PATH, template, static_file, redirect, abort
import redis
from passlib.hash import bcrypt
import uuid

red = redis.StrictRedis(host='127.0.0.1',port=6379,db=0)
TEMPLATE_PATH.insert(0,'/var/www/html/templates')

@get('/')
def index():
  if checkIfLoggedIn():
    redirect('/lobby')
  return template('login')

@get('/static/<path:path>')
def static_callback(path):
  return static_file(path,root='/var/www/html/static/')

@get('/allusers')
def alluser_callback():
  user_list = red.lrange('sfb:user:list',0,-1)
  user_list_dec = [i.decode('utf-8') for i in user_list]
  all_users = {'all_users': user_list_dec}
  return all_users

@post('/login')
def login_callback():
  username = request.forms.get('username')
  password = request.forms.get('password')
  return login(username,password)

@post('/signup')
def signup_callback():
  username = request.forms.get('username')
  password = request.forms.get('password')
  return signup(username,password)

@get('/lobby')
def lobby():
  if checkIfLoggedIn():
    return template('lobby')
  abort(401, error401())

@get('/allgames')
def allgames():
  return {'allgames':[1,2,3,4,5]}

def error401():
  return "Sorry, access is denied. Please log in on the home page"

def userExist(un):
  return red.hget('sfb:user:' + un, 'password')

def signup(un,pw):
  if userExist(un):
    return 'Username already in use'
  if not un.isalnum():
    return "Username must be alpha-numeric"
  hash_pass = bcrypt.encrypt(pw)
  red.hset('sfb:user:' + un,'password',hash_pass)
  red.lpush('sfb:user:list',un)
  return 'Added account'

def login(un,pw):
  hash_pass = bcrypt.encrypt(pw)
  if userExist(un) is None:
    return {'loginStatus':'User does not exist'}
  if bcrypt.verify(pw, red.hget('sfb:user:' + un,'password')):
    cookie_hash = str(uuid.uuid4())
    response.set_cookie('sfb_token',un + ":" + cookie_hash)
    red.hset('sfb:user:' + un, 'token', cookie_hash)
    return {'loginStatus':'Success'}
  else:
    return {'loginStatus':'Password incorrect'}

def checkIfLoggedIn():
  cookie = request.get_cookie('sfb_token')
  if cookie:
    user = str(cookie).split(':')[0]
    token = str(cookie).split(':')[1]
    if token == red.hget('sfb:user:' + user, 'token').decode('utf-8'):
      return user
  return False
