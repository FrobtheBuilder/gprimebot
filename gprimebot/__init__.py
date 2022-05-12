from ctypes import Union
import random
import time
from typing import Any, Dict
import tweepy, configparser, os, json
import pickle
import hashlib
from botstate import BotState
import io
from PIL import Image
import glob
import re

from rect_detect import detect_rects


DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
IMG_DIR = os.path.join(DATA_DIR, "img")

config = configparser.ConfigParser()
config.read_file(open(os.path.join(os.path.dirname(__file__), "../config.cfg"), "r"))

CHECK_INTERVAL = config.getint("options", "CheckInterval")
CONSUMER_KEY: str = config.get("authentication", "ConsumerKey")
CONSUMER_SECRET: str = config.get("authentication", "ConsumerSecret")
ACCESS_TOKEN: str = config.get("authentication", "AccessToken")
ACCESS_TOKEN_SECRET: str = config.get("authentication", "AccessTokenSecret")
TWEET: bool = config.getboolean("options", "Tweet")


auth = tweepy.OAuth1UserHandler(
   CONSUMER_KEY, 
   CONSUMER_SECRET, 
   ACCESS_TOKEN, 
   ACCESS_TOKEN_SECRET
)


FILENAME_PATTERN = re.compile("\d+")
def load_filenames():
    filenames = next(os.walk(os.path.join(DATA_DIR, "img")), (None, None, []))[2]
    filenames.sort(key=lambda el : int(re.search(FILENAME_PATTERN, el).group()))
    return filenames

def load_botstate() -> BotState:
    if os.path.isfile(os.path.join(DATA_DIR, "state.pkl")):
        with open(os.path.join(DATA_DIR, "state.pkl"), "rb") as trickstate_file:
            return pickle.load(trickstate_file)
    else:
        filenames = load_filenames()
        return BotState(
            next_filename = filenames[0], 
            next_post_time = time.time(),
            mode = "sequential",
            count = len(filenames)
        )

def save_botstate(state: BotState):
    with open(os.path.join(DATA_DIR, "state.pkl"), "wb+") as trickstate_file:
        pickle.dump(state, trickstate_file)

def slice_image(im: Image.Image) -> list[io.BytesIO]:
    rects = detect_rects(im)
    imgs = []
    bytes = io.BytesIO()
    im.save(bytes, "PNG")
    bytes.seek(0)
    imgs.append(bytes)
    for rect in rects:
        bytes = io.BytesIO()
        cropped = im.crop(rect)
        cropped.resize((cropped.size[0] * 2, cropped.size[1] * 2)).save(bytes, "PNG")
        bytes.seek(0)
        imgs.append(bytes)
    return imgs

api = tweepy.API(auth)


def post():
    state = load_botstate()
    filenames = load_filenames()
    if state.mode == "random" and state.count < len(filenames):
        state.mode = "sequential"
        state.next_filename = filenames[filenames.index(state.next_filename) + 1]

    filename = state.next_filename
    print(f"Posting:")
    print(filename)
    print(filenames)
    imgs: list[io.BytesIO]
    with Image.open(os.path.join(DATA_DIR, "img", filename)) as img:
        imgs = slice_image(img)
    print(imgs)
    if TWEET:
        try:
            media_ids = [api.simple_upload(file = img, filename = str(random.randint(0, 60000))).media_id for img in imgs]
            print(media_ids)
            api.update_status("", media_ids = media_ids)
        except Exception as err:
            print(err)

    

    if state.mode == "sequential" and filenames.index(state.next_filename) + 1 >= len(filenames):
        state.mode = "random"
    
    if state.mode == "random":
        state.next_filename = filenames[random.randint(0, len(filenames) - 1)]
        print(f"Out of posts, picking next post at random")
    else:
        state.next_filename = filenames[filenames.index(state.next_filename) + 1]
        posts_left = len(filenames) - filenames.index(state.next_filename)
        print(f"{posts_left} {'post' if posts_left == 1 else 'posts'} left")
    
    state.count = len(filenames)
    state.next_post_time = time.time() + (60 * 60 * 2)
    save_botstate(state)

while True:
    state = load_botstate()
    time.sleep(CHECK_INTERVAL)
    if time.time() > state.next_post_time:
        post()
        
