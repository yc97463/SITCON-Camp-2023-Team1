from datetime import datetime
from jsonIOHandler import JsonIOHandler
import time

def is_competition_matched(competition, profile) -> bool:
 
  with JsonIOHandler('profile_choices.json') as handler:
    profile_choices = handler.data
  now_date = datetime.now()

  # validate data in competition
  try:
    date = datetime.strptime(competition['date'], '%Y-%m-%d')
    exp = competition['exp']
    min_age = competition['min_age']
    max_age = competition['max_age']
    category = competition['category']
    
    assert exp in profile_choices['exp'] or exp is None
    assert category in profile_choices['category']

    # get user profile setting
    user_birth = datetime.strptime(profile['birth'], '%Y-%m-%d') if profile['birth'] else None
    user_exp = profile['exp']
    user_category = profile['category']
    user_age = None
    if user_birth:
      user_age = now_date.year - user_birth.year
      if now_date.month > user_birth.month:
        user_age -= 1
      elif now_date.month == user_birth.month and now_date.day > user_birth.day:
        user_age -= 1

    # filtering
    res = True
    res = (user_age is None or min_age <= user_age and user_age <= max_age) and res  # filter with user's age
    res = ((exp is None or user_exp is None) or profile_choices['exp'].index(user_exp) >= profile_choices['exp'].index(exp)) and res  # filter with user's exp
    res = ((len(user_category) == 0 or category is None) or category in user_category) and res  # filter with user's category preferences
    res = (now_date < date) and res # filter out competition that has ended
    return res
  
  except Exception as e:
    print(f'Something wrong in is_competition_matched()\ncompetition = {competition}\nerror: {e}')
    return False

def get_fav_competitions(fav, comps):
  res = []
  for comp in comps:
    if comp['id'] in fav:
      res.append(comp)
  return res

def generate_competition_info(comp, index, length):
  age_range = '無'
  if comp['min_age'] > 0 and comp['max_age'] == 999:
    age_range = f"{comp['min_age']}歲以上"
  elif comp['min_age'] == 0 and comp['max_age'] < 999:
    age_range = f"{comp['max_age']}歲以下"
  elif comp['min_age'] > 0 and comp['max_age'] < 999:
    age_range = f"{str(comp['min_age'])}'到'{str(comp['max_age'])}歲"

  return f''' \
                            {index+1}/{length}
  
*# {comp['title']}*

*開始日期:* {comp['date']}
*最高獎金:* {comp['prize'] if comp['prize'] else '無'}
*學歷要求:* {comp['exp'] if comp['exp'] else '無'}
*年齡限制:* {age_range}
*分類類別:* {comp['category'] if comp['category'] else '無'}
*相關連結:* {comp['url'] if comp['url'] else '暫無'}
'''

def crawl():
  time.sleep(.1)
  