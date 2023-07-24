# This is a simple echo bot using the decorator mechanism.
# It echoes any incoming text messages.

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot.types import InlineQueryResultArticle, InputTextMessageContent
from telebot.util import quick_markup

import json
import time
from datetime import datetime
import threading
import hashlib

from jsonIOHandler import JsonIOHandler
from crawl_skyline import crawl_skyline
from crawl_prizehunter import crawl_prizehunter
import utils

with open("secret.json", "r", encoding="utf8") as jfile:
  secret = json.load(jfile)

API_TOKEN = secret['TOKEN']
PROFILES_INIT = {'birth': None, 'exp': None, 'category': [], 'fav': []}
BROWSER_TRACKING_INIT = {'competition_ids': [], "index": 0}
COMPETITIONS_INIT = []

bot = telebot.TeleBot(API_TOKEN)
infav_markup = quick_markup({
  '⬅️': {'callback_data': 'prev'},
  '🤍': {'callback_data': 'fav_add'},
  '➡️': {'callback_data': 'next'}
}, row_width=3)
fav_markup = quick_markup({
  '⬅️': {'callback_data': 'prev'},
  '❤️': {'callback_data': 'fav_rm'},
  '➡️': {'callback_data': 'next'}
}, row_width=3)

with JsonIOHandler('profile_choices.json') as handler:
  profile_choices = handler.data

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
  bot.send_message(message.chat.id, '''
This is Competition bot, newest competition information for you.

/help /start - 查看指令說明
/profile - 設定篩選用的個人資訊
/clear - 清除個人資料設定
/search - 查詢活動資訊
/fav - 查詢加入收藏的活動資訊
''')


@bot.message_handler(commands=['profile'])
def set_profile(message):
  user = message.from_user
  chat = message.chat
  pf_identifier = str(chat.id) + str(user.id)
  content = message.text.split()
  data = None

  try:
    if len(content) == 1 or content[1] == 'help':
      with JsonIOHandler("database/profiles.json", PROFILES_INIT) as handler:
        p = handler.data[pf_identifier]
        current_profile = f'''\
目前的profile設定為:
生日: {p["birth"] if p["birth"] else "未設定"},
學歷: {p["exp"] if p["exp"] else "未設定"},
篩選類別: {"、".join(p["category"]) if len(p["category"]) else "未設定"}
'''
      bot.reply_to(message, f'''\
{current_profile}
/profile birth <year> <month> <date> - 設定生日
/profile exp <exp> - 設定學經歷
 - 從 {'、'.join(profile_choices['exp'])} 中擇一
/profile category add <category> - 新增領域類別
/profile category rm <category> - 移除領域類別
 - 從 {'、'.join(profile_choices['category'])} 中擇一''')
      return
    elif content[1] == 'birth':
      data = [int(content[2]), int(content[3]), int(content[4])]
      data = datetime(year=data[0], month=data[1], day=data[2])
      assert data < datetime.now()
      data = datetime.strftime(data, '%Y-%m-%d')
    elif content[1] == 'exp':
      data = content[2]
      with JsonIOHandler('profile_choices.json') as handler:
        assert data in handler.data['exp']
    elif content[1] == 'category' and content[2] == 'add':
      data = content[3]
      with JsonIOHandler('profile_choices.json') as handler:
        assert data in handler.data['category']
      with JsonIOHandler('database/profiles.json', PROFILES_INIT) as handler:
        assert data not in handler.data[pf_identifier]['category']
    elif content[1] == 'category' and content[2] == 'rm':
      data = content[3]
      with JsonIOHandler('database/profiles.json', PROFILES_INIT) as handler:
        assert data in handler.data[pf_identifier]['category']
    else:
      raise Exception("Wrong command format")
    
  except Exception as e :
    print(e)
    bot.reply_to(message, '格式有誤\n請用/profile help查看使用方法')
    return
  
  with JsonIOHandler("database/profiles.json", PROFILES_INIT) as handler:
    if content[1] == 'category':
      if content[2] == 'add':
        handler.data[pf_identifier]['category'].append(data)
      else:
        handler.data[pf_identifier]['category'].remove(data)

    else:
      handler.data[pf_identifier][content[1]] = data
  bot.reply_to(message, '已成功設定！')

@bot.message_handler(commands=['clear'])
def clear_profile(message):
  user = message.from_user
  chat = message.chat
  pf_identifier = str(chat.id) + str(user.id)
  with JsonIOHandler("database/profiles.json", PROFILES_INIT) as handler:
    handler.data[pf_identifier] = PROFILES_INIT
  bot.reply_to(message, '成功清除個人資訊')

@bot.message_handler(commands=['search'])
def search(message):
  user = message.from_user
  chat = message.chat
  pf_identifier = str(chat.id) + str(user.id)
  with JsonIOHandler("database/profiles.json", PROFILES_INIT) as handler:
    profile = handler.data[pf_identifier]
  with JsonIOHandler("database/competitions.json", COMPETITIONS_INIT) as handler:
    competitions = handler.data['competitions']
  
  filtered_competitions = list(filter(lambda com: utils.is_competition_matched(com, profile), handler.data['competitions']))
  filtered_competitions.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))

  if len(filtered_competitions) == 0:
    bot.reply_to(message, '沒有查詢到符合篩選條件的活動')
    return
  
  msg = bot.reply_to(message, 'Loading...')
  chat = msg.chat
  identifier = str(chat.id) + str(msg.message_id)
  with JsonIOHandler('database/browser_tracking.json', BROWSER_TRACKING_INIT) as handler:
    ids = [c['id'] for c in filtered_competitions]
    handler.data[identifier]['competition_ids'] = ids
    bsr_state = handler.data[identifier]

  index = bsr_state['index']
  cur_competition_id = bsr_state['competition_ids'][index]
  cur_competition = list(filter(lambda com: com['id'] == cur_competition_id, competitions))[0]
  is_fav = cur_competition_id in profile['fav']
  text = utils.generate_competition_info(cur_competition, index, len(bsr_state['competition_ids']))

  bot.edit_message_text(text=text,
                        chat_id=msg.chat.id,
                        message_id=msg.message_id,
                        reply_markup=fav_markup if is_fav else infav_markup,
                        parse_mode='markdown')

  
@bot.callback_query_handler(lambda call: call.data in ['fav_add', 'fav_rm', 'prev', 'next'])
def browser_callback(call):
  user = call.from_user
  msg = call.message
  chat = msg.chat
  pf_identifier = str(chat.id) + str(user.id)
  bsr_identifier = str(chat.id) + str(msg.id)
  with JsonIOHandler("database/profiles.json", PROFILES_INIT) as handler:
    profile = handler.data[pf_identifier]
  with JsonIOHandler('database/browser_tracking.json', BROWSER_TRACKING_INIT) as handler:
    bsr_state = handler.data[bsr_identifier]
  with JsonIOHandler("database/competitions.json", COMPETITIONS_INIT) as handler:
    competitions = handler.data['competitions']

  update_flag = True
  if call.data.startswith('fav'):
    comp_id = bsr_state['competition_ids'][bsr_state['index']]
    if call.data == 'fav_add' and comp_id not in profile['fav']:
      profile['fav'].append(comp_id)
    elif call.data == 'fav_rm' and comp_id in profile['fav']:
      profile['fav'].remove(comp_id)
  elif call.data == 'prev':
    if bsr_state['index'] > 0:
      bsr_state['index'] -= 1
    else:
      update_flag = False
  elif call.data == 'next':
    if bsr_state['index'] < len(bsr_state['competition_ids']) - 1:
      bsr_state['index'] += 1
    else:
      update_flag = False
  with JsonIOHandler("database/profiles.json", PROFILES_INIT) as handler:
    handler.data[pf_identifier] = profile 
  with JsonIOHandler('database/browser_tracking.json', BROWSER_TRACKING_INIT) as handler:
    handler.data[bsr_identifier] = bsr_state

  if update_flag:
    index = bsr_state['index']
    cur_competition_id = bsr_state['competition_ids'][index]
    cur_competition = list(filter(lambda com: com['id'] == cur_competition_id, competitions))[0]
    is_fav = cur_competition_id in profile['fav']
    text = utils.generate_competition_info(cur_competition, index, len(bsr_state['competition_ids']))

    bot.edit_message_text(text=text,
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=fav_markup if is_fav else infav_markup,
                          parse_mode='markdown')
  else:
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['fav'])
def show_favorite(message):
  user = message.from_user
  chat = message.chat
  pf_identifier = str(chat.id) + str(user.id)
  with JsonIOHandler("database/profiles.json", PROFILES_INIT) as handler:
    profile = handler.data[pf_identifier]
  with JsonIOHandler("database/competitions.json", COMPETITIONS_INIT) as handler:
    competitions = handler.data['competitions']
  
  filtered_competitions = utils.get_fav_competitions(profile['fav'], competitions)
  filtered_competitions.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))

  if len(filtered_competitions) == 0:
    bot.reply_to(message, '你目前有沒有加入收藏的活動')
    return
  
  msg = bot.reply_to(message, 'Loading...')
  chat = msg.chat
  bsr_identifier = str(chat.id) + str(msg.message_id) 
  with JsonIOHandler('database/browser_tracking.json', BROWSER_TRACKING_INIT) as handler:
    ids = [c['id'] for c in filtered_competitions]
    handler.data[bsr_identifier]['competition_ids'] = ids
    bsr_state = handler.data[bsr_identifier]

  index = bsr_state['index']
  cur_competition_id = bsr_state['competition_ids'][index]
  cur_competition = list(filter(lambda com: com['id'] == cur_competition_id, competitions))[0]
  is_fav = cur_competition_id in profile['fav']
  text = utils.generate_competition_info(cur_competition, index, len(bsr_state['competition_ids']))

  bot.edit_message_text(text=text,
                        chat_id=msg.chat.id,
                        message_id=msg.message_id,
                        reply_markup=fav_markup if is_fav else infav_markup,
                        parse_mode='markdown')




def run_crawler(terminal_event):
  while True:
    
    try:
      print('Try running crawl_skyline...')
      data = crawl_skyline()
      print('Data fetch success')
      print(f'data = {data}')
      to_hash = (data['title'] + data['date'] + data['category']).encode('utf-8')
      fingerprint = hashlib.sha256(to_hash).hexdigest()
      data['id'] = fingerprint

      add_flag = True

      if not utils.is_competition_matched(data, PROFILES_INIT):
        add_flag = False
      with JsonIOHandler('database/competitions.json', COMPETITIONS_INIT) as handler:
        for competition in handler.data['competitions']:
          if fingerprint == competition['id']:
            add_flag = False

        if add_flag:
          handler.data['competitions'].append(data)
        else:
          print('Data from crawl_skyline already exist or does not match the test, discarded.')
        
    except Exception as e:
      print(f"Something went wrong in crawl_skyline\nerror: {e}")

    try:
      print('Try running crawl_prizehunter...')
      data = crawl_prizehunter()
      print('Data fetch success')
      print(f'data = {data}')
      to_hash = (data['title'] + data['date'] + data['category']).encode('utf-8')
      fingerprint = hashlib.sha256(to_hash).hexdigest()
      data['id'] = fingerprint

      add_flag = True

      if not utils.is_competition_matched(data, PROFILES_INIT):
        add_flag = False
      with JsonIOHandler('database/competitions.json', COMPETITIONS_INIT) as handler:
        for competition in handler.data['competitions']:
          if fingerprint == competition['id']:
            add_flag = False

        if add_flag:
          handler.data['competitions'].append(data)
        else:
          print('Data from crawl_prizehunter already exist or does not match the test, discarded.')
        
    except Exception as e:
      print(f"Something went wrong in crawl_prizehunter\nerror: {e}")


    for _ in range(200):
      time.sleep(.1)
      if terminal_event.is_set():
        break

    if terminal_event.is_set():
      break

def run_crawler_fake(terminal_event):
  while True:
    print('run_crawler_fake')
    with JsonIOHandler('database/competitions.json', COMPETITIONS_INIT) as handler:
      pass
    for _ in range(50):
      time.sleep(.1)
      if terminal_event.is_set():
        break
    if terminal_event.is_set():
      break

terminal_event = threading.Event()
t = threading.Thread(target=run_crawler, args=(terminal_event,))
t.start()

print(">> Bot Is Online <<" )
bot.infinity_polling()
terminal_event.set()
print("Set terminal event")
t.join()
print("Exit successfully")