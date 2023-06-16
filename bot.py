"""
Bot created by Kym_Andriy
"""
import asyncio
import collections
from email.mime import application
import logging
from multiprocessing.dummy import Process
import requests
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import telegram
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler
import json
import os
from telegram.ext import Updater, CommandHandler, MessageHandler
import threading
from telegram.ext import filters
from fake_useragent import UserAgent

##################
# HEROKU_UNCOMMENT
# PORT = int(os.environ.get('PORT', '8443'))
##################

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

################ CHANGE TO 'bot_congig.json'
user_agent = UserAgent()
session = requests.Session()
session.headers.update({'User-Agent': str(user_agent.chrome)})

temp_str = ""
with open("temp.json","r") as f:
    temp_str = f.read()
config_js = json.loads(temp_str)
temp_str = ""

final_image_regex = re.compile(config_js["FINAL_IMAGE_URL_REGEX"])
hash_artwork_regex = re.compile(config_js["HASH_IMAGE_URL_REGEX"])
user_profile_regex = re.compile(config_js["USER_PROFILE_URL_REGEX"])

def get_hash_urls(url, header=None):
    str_url = str(session.get(url, headers=header).content)
    content = [i.group() for i in hash_artwork_regex.finditer(str_url)]
    content = [i[(i.rfind("/")+1):] for i in content]
    return content

def get_artwork_image_url(hash):
    response = None
    full_url = str("https://www.artstation.com/projects/" + hash + ".json")
    try:
        response = session.get(full_url)
    except:
        logger.warning("Get artwork image URL did not return any content, response status code - ")
        return
    match_iterator = final_image_regex.finditer(str(response.content))
    image_urls = set([url_group.group().replace("medium", "large") for url_group in match_iterator])
    for i in image_urls:
        if i.find('small') != -1:
            image_urls.remove(i)
    js = json.loads(response.content)
    return {"username": str(js["user"]["username"]),"images": image_urls}

def prepare_keyboard():
    keyboard = []
    counter = 0
    row = []
    pattern = config_js["KEYBOARD_NEW_LINE_PATTERN"]
    js_map = collections.OrderedDict(sorted(config_js["KEYBOARD_MAP"].items()))
    for k, v in js_map.items():
        callback_str = str(k)
        callback_str = callback_str.replace('&', "and").replace("'","").replace('-','').lower()
        key = InlineKeyboardButton((str(k).replace('_'," ")), callback_data=callback_str)
        
        row.append(key)
        if pattern[counter] == 1:
            keyboard.append(row)
            row = []
        counter += 1
    return keyboard

keyboard = prepare_keyboard()
mn = InlineKeyboardMarkup([[InlineKeyboardButton("Menu", callback_data="menu")]])

async def getUserFirstFourtyArtworks(update: Update, context: CallbackContext.DEFAULT_TYPE):
    urls_hash =[] 
    user_profile = update.message.text
    profile_index = user_profile.rfind("/") + 1
    user_profile = "https://www.artstation.com/users/" + user_profile[profile_index:] + "/projects.json" 
    try:
        urls_hash = get_hash_urls(user_profile, {'user-agent': 'my-app/0.0.1'})
    except:
        return
    #urls_hash = urls_hash[:40] if len(urls_hash) > 40 else urls_hash
    counter = -1
    #await update.get_bot().sendChatAction(chat_id=update.message.chat_id, action = 'upload_photo')
    for i in urls_hash:
        counter = counter + 1
        if counter > 40:
            break
        try:
            photoes = get_artwork_image_url(i)
            for photo in photoes["images"]:
                try:
                    temp = photo.copy()
                    temp.replace("large", "4k")
                    await update.message.reply_document(temp, disable_notification=True)
                except:
                    try:
                        await update.message.reply_document(photo, disable_notification=True)
                    except:
                        pass
        except:
            pass
    if counter != -1:
        await update.message.reply_text("Please choose:", reply_markup=mn, disable_notification=True)

async def getImagesByURL(update: Update, context: CallbackContext.DEFAULT_TYPE):
    art_url = str(hash_artwork_regex.match(update.message.text).group())
    art_url = art_url[(art_url.rfind("/") + 1):]
    try:
        photoes = get_artwork_image_url(art_url)
        for photo in photoes["images"]:
            try:
                temp = photo.copy()
                temp.replace("large", "4k")
                await update.message.reply_document(temp, disable_notification=True)
            except:
                try:
                    await update.message.reply_document(photo, disable_notification=True)
                except:
                    pass
    except:
        pass
    await update.message.reply_html("\u2191 <a href=\"https://www.artstation.com/"+photoes["username"] + " \">"+photoes["username"]+"</a>", reply_markup=mn, disable_notification=True, disable_web_page_preview=True)


async def menu(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Please choose:", reply_markup=reply_markup)


async def start(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose:", reply_markup=reply_markup)

async def callback(update: Update, context: CallbackContext.DEFAULT_TYPE, artwokr_name, art_url):
    qu = update.callback_query
    art_name =  str(artwokr_name).replace("_"," ")
    await qu.answer()
    await qu.edit_message_text("Chosen theme: " + art_name)
    await update.callback_query.get_bot().sendChatAction(chat_id=update.callback_query.message.chat_id, action = 'upload_photo')
    urls_hash = get_hash_urls(art_url)
    photoes = None 
    for i in urls_hash:
        try:
            photoes = get_artwork_image_url(i)
            for photo in photoes["images"]:
                try:
                    temp = photo.copy()
                    temp.replace("large", "4k")
                    await update.callback_query.message.reply_document(temp, disable_notification=True)
                except:
                    try:
                        await update.callback_query.message.reply_document(photo, disable_notification=True)
                    except:
                        pass
        except:
            logger.error("loop exception")
        if photoes != None:
            await update.callback_query.message.reply_html("\u2191 <a href=\"https://www.artstation.com/"+photoes["username"] + " \">"+photoes["username"]+"</a>",disable_notification=True, disable_web_page_preview=True)
    await update.callback_query.message.reply_text(art_name, reply_markup=mn, disable_notification=True)

def main() -> None:
    token = config_js["BOT_TOKEN"]
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    for k, v in config_js["KEYBOARD_MAP"].items():
        cb_str = str(k).replace('&', "and").replace("'","").replace('-','').lower()
        pointer = (lambda update, context, kk=k, vv=v:  callback(update, context, kk, vv))
        application.add_handler(CallbackQueryHandler(pointer, pattern=cb_str))
    application.add_handler(CallbackQueryHandler(menu, pattern="menu"))
    application.add_handler(MessageHandler(filters=filters.Regex(hash_artwork_regex), callback=getImagesByURL))
    application.add_handler(MessageHandler(filters=filters.Regex(user_profile_regex), callback=getUserFirstFourtyArtworks))
    application.run_polling()
    ##################
    # HEROKU_UNCOMMENT
    #application.updater.start_webhook(
    #    listen='0.0.0.0',
    #    port=PORT,
    #    url_path=token,
    #    webhook_url='https://artstation-tg-bot.herokuapp.com/'+token,
    #)
    ##################

if __name__ == "__main__":
    main()

