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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

temp_str = ""
with open("bot_configs.json","r") as f:
    temp_str = f.read()
config_js = json.loads(temp_str)
temp_str = ""

final_image_regex = re.compile(config_js["FINAL_IMAGE_URL_REGEX"])
#final_image_regex = re.compile(r"https://\w+\.artstation\.com/p/assets/images([\w\d/-])+(\.jpg)")

hash_artwork_regex = re.compile(config_js["HASH_IMAGE_URL_REGEX"])
#hash_artwork_regex = re.compile(r"https://www\.artstation\.com/artwork/([\w\d])+")

def get_hash_urls(url):
    content = [i.group() for i in hash_artwork_regex.finditer(str(requests.get(url).content))]
    content = [i[(i.rfind("/")+1):] for i in content]
    return content

def get_artwork_image_url(hash):
    response = requests.get(("https://www.artstation.com/projects/"+hash+".json"))
    match_iterator = final_image_regex.finditer(str(response.content))
    image_urls = set([url_group.group().replace("medium", "large") for url_group in match_iterator])
    # image_urls = set(i if (i.find("small") is not -1) else "" for i in image_urls)
    for i in image_urls:
        if i.find('small') != -1:
            image_urls.remove(i)
    js = json.loads(response.content)
    return {"username": str(js["user"]["username"]),"images": image_urls}

def prepare_keyboard():
    
    keyboard = []
    counter = 0
    row = []
    js_map = collections.OrderedDict(sorted(config_js["KEYBOARD_MAP"].items()))#{k:v for k,v in config_js["KEYBOARD_MAP"].items()}
    for k, v in js_map.items():
        callback_str = str(k)
        callback_str = callback_str.replace('&', "and").replace("'","").replace('-','').lower()
        key = InlineKeyboardButton((str(k).replace('_'," ")), callback_data=callback_str)
        if (counter != 0) and ((counter % 3) == 0) and  (len(row) != 0):
            # row.append(key)
            keyboard.append(row)
            row = []
            # continue
        row.append(key)
        if (len(k) > 14) and len(row) != 0:
            # row.append(key)
            keyboard.append(row)
            row = []
        counter += 1
    return keyboard

keyboard = prepare_keyboard()
mn = InlineKeyboardMarkup([[InlineKeyboardButton("Menu", callback_data="menu")]])

async def menu(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Show:", reply_markup=reply_markup)


async def start(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please choose:", reply_markup=reply_markup)

async def callback(update: Update, context: CallbackContext.DEFAULT_TYPE, artwokr_name, art_url):

    qu = update.callback_query
    await qu.answer()
    await qu.edit_message_text("You chose: " + artwokr_name)
    await update.callback_query.get_bot().sendChatAction(chat_id=update.callback_query.message.chat_id, action = 'upload_photo')
    urls_hash = get_hash_urls(art_url)
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
            pass
        await update.callback_query.message.reply_html("\u2191 <a href=\"https://www.artstation.com/"+photoes["username"] + " \">"+photoes["username"]+"</a>",disable_notification=True, disable_web_page_preview=True)
    await update.callback_query.message.reply_text(artwokr_name, reply_markup=mn, disable_notification=True)

def main() -> None:
    token = config_js["BOT_TOKEN"]
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    for k, v in config_js["KEYBOARD_MAP"].items():
        cb_str = str(k).replace('&', "and").replace("'","").replace('-','').lower()
        pointer = (lambda update, context, kk=k, vv=v:  callback(update, context, kk, vv))
        application.add_handler(CallbackQueryHandler(pointer, pattern=cb_str))
    application.add_handler(CallbackQueryHandler(menu, pattern="menu"))
    application.run_polling()

if __name__ == "__main__":
    main()

