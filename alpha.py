# Standard Library
import os
import sys
import re
import time
import math
import asyncio
import logging
import secrets
import mimetypes
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, quote_plus
from typing import Any, Optional, Dict, Union

# Third-Party Libraries
import aiohttp
from aiohttp import web
import aiofiles
from aiohttp.http_exceptions import BadStatusLine

import pyromod.listen
from pyrogram import Client, filters, utils, raw, idle
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.errors import (
    AuthBytesInvalid,
    FloodWait,
)
from pyrogram.file_id import FileId, FileType, ThumbnailSource
from pyrogram.session import Session, Auth

from motor.motor_asyncio import AsyncIOMotorClient

# -- Logging --
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

StartTime = time.time()

# -- Config / Vars --
API_ID = 20360765
API_HASH = "c4191fa3677e8e872bac8f21578cbb8a"
BOT_TOKEN = "7887919396:AAEbDiBh_LkD0GLEuzHekxcgCFdphlCTUuU"

MULTI_CLIENT = False
name = 'filetolinkbot'

DATABASE_URL = "mongodb+srv://biklriplit:efaXfv2Ps9MRfner@cluster0.4hfu8zj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

UPDATES_CHANNEL = "TestMeWithLove"  # (not enforced anymore)
OWNER_ID = ()
OWNER_USERNAME = ""

SLEEP_THRESHOLD = '60'
WORKERS = 4
BIN_CHANNEL = "TestMeWithLove"

PORT = 80
BIND_ADRESS = 'alphronix.live'
FQDN = "64.227.136.200" # why we use?
PING_INTERVAL = "1200"  # 20 minutes
NO_PORT = True
APP_NAME = None
MY_PASS = False  # not used anymore
URL = f"http://{BIND_ADRESS}/"
ON_HEROKU = False
TERMUX = False


# -- Bot instance
StreamBot = Client(
    name='Streamer',
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,
    workers=4
)

multi_clients = {}
work_loads = {0: "StreamBot"}

# -- Database
class Database:
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db["users"]

    def new_user(self, id: int):
        return {
            "id": id,
            "join_date": datetime.utcnow().date().isoformat()
        }

    async def add_user(self, id: int):
        user = self.new_user(id)
        await self.col.insert_one(user)

    async def is_user_exist(self, id: int):
        user = await self.col.find_one({"id": int(id)})
        return True if user else False

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id: int):
        await self.col.delete_many({"id": int(user_id)})

# -- Optional handler (Termux DNS fix)
if TERMUX:
    import dns.asyncresolver
    async_resolver = dns.asyncresolver.Resolver(configure=False)
    async_resolver.nameservers = ["8.8.8.8", "8.8.4.4", "1.1.1.1"]
    dns.asyncresolver.default_resolver = async_resolver

# -- Web App / Routes
routes = web.RouteTableDef()
loop = asyncio.get_event_loop()

StreamBot.start() # Bot starts

db = Database(DATABASE_URL, name) # Database

# -- Utils --
class InvalidHash(Exception):
    message = "Invalid hash"

class FIleNotFound(Exception):
    message = "File not found"


def get_media_from_message(message: "Message") -> Any:
    media_types = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
    )
    for attr in media_types:
        media = getattr(message, attr, None)
        if media:
            return media


def get_hash(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    return getattr(media, "file_unique_id", "")[:6]

def get_name(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    file_name = getattr(media, "file_name", "")
    return file_name if file_name else ""

def get_media_file_size(m):
    media = get_media_from_message(m)
    return getattr(media, "file_size", 0)

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


async def start_services():
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = BIND_ADRESS
    await web.TCPSite(app, bind_address, PORT).start()
    print('----------------------- Service Started -----------------------------------------------------------------')
    print('                        bot =>> {}'.format((await StreamBot.get_me()).first_name))
    print('                        server ip =>> {}:{}'.format(bind_address, PORT))
    print('                        Owner =>> {}'.format((OWNER_USERNAME)))
    print('---------------------------------------------------------------------------------------------------------')
    await idle()

# /start
@StreamBot.on_message(filters.command('start') & filters.private)
async def start(b, m):
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id)
        await b.send_message(
            BIN_CHANNEL,
            f"#NEW_USER: \n\nNew User [{m.from_user.first_name}](tg://user?id={m.from_user.id}) Started !!"
        )

    usr_cmd = m.text.split("_")[-1]
    if usr_cmd == "/start":
        await m.reply_photo(
            photo="https://graph.org/file/c329bc326c2100e513d95.jpg",
            caption=(
                "**ʜᴇʟʟᴏ...⚡\n\nɪᴀᴍ ᴀ sɪᴍᴘʟᴇ ᴛᴇʟᴇɢʀᴀᴍ ғɪʟᴇ/ᴠɪᴅᴇᴏ ᴛᴏ "
                "ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋ ᴀɴᴅ sᴛʀᴇᴀᴍ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴏʀ ʙᴏᴛ.**\n\n"
                "**ᴜsᴇ /help ғᴏʀ ᴍᴏʀᴇ ᴅᴇᴛsɪʟs\n\nsᴇɴᴅ ᴍᴇ ᴀɴʏ ᴠɪᴅᴇᴏ / ғɪʟᴇ "
                "ᴛᴏ sᴇᴇ ᴍʏ ᴘᴏᴡᴇʀᴢ...**"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("⚡ ᴜᴘᴅᴀᴛᴇᴢ ⚡", url="https://t.me/akborana"),
                     InlineKeyboardButton("⚡ sᴜᴘᴘᴏʀᴛ ⚡", url="https://t.me/j0kes199")],
                    [InlineKeyboardButton("💸 ᴅᴏɴᴀᴛᴇ 💸", url="https://t.me/J0KES199/10638"),
                     InlineKeyboardButton("💠 WEBSITE 💠", url="https://akborana.me")],
                    [InlineKeyboardButton("💌 PORTFOLIO 💌", url="https://akay.is-a.dev")]
                ]
            ),
        )
    else:
        # Deep-link start payload -> generate links from BIN_CHANNEL message id
        get_msg = await b.get_messages(chat_id=BIN_CHANNEL, ids=int(usr_cmd))

        file_size = None
        if get_msg.video:
            file_size = f"{humanbytes(get_msg.video.file_size)}"
        elif get_msg.document:
            file_size = f"{humanbytes(get_msg.document.file_size)}"
        elif get_msg.audio:
            file_size = f"{humanbytes(get_msg.audio.file_size)}"

        file_name = None
        if get_msg.video:
            file_name = f"{get_msg.video.file_name}"
        elif get_msg.document:
            file_name = f"{get_msg.document.file_name}"
        elif get_msg.audio:
            file_name = f"{get_msg.audio.file_name}"

        stream_link = f"{URL}stream/{str(get_msg.id)}?hash={get_hash(get_msg)}"

        msg_text = (
            "**ᴛᴏᴜʀ ʟɪɴᴋ ɪs ɢᴇɴᴇʀᴀᴛᴇᴅ...⚡\n\n📧 ғɪʟᴇ ɴᴀᴍᴇ :-\n{}\n {}\n\n"
            "💌 ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ :- {}\n\n♻️ ᴛʜɪs ʟɪɴᴋ ɪs ᴘᴇʀᴍᴀɴᴇɴᴛ ᴀɴᴅ ᴡᴏɴ'ᴛ "
            "ɢᴇᴛ ᴇxᴘɪʀᴇᴅ ♻️\n\n<b>❖ https://m.youtube.com/@akborana</b>**"
        )
        await m.reply_text(
            text=msg_text.format(file_name, file_size, stream_link),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⚡ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ⚡", url=stream_link)]]
            )
        )

# Handle media from private chats
@StreamBot.on_message(
    (filters.private) & (filters.document | filters.video | filters.audio | filters.photo),
    group=4
)
async def private_receive_handler(c: Client, m: Message):
    # No login/password gating, no force-sub
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id)
        await c.send_message(
            BIN_CHANNEL,
            f"Nᴇᴡ Usᴇʀ Jᴏɪɴᴇᴅ : \n\n Nᴀᴍᴇ : [{m.from_user.first_name}](tg://user?id={m.from_user.id}) Sᴛᴀʀᴛᴇᴅ Yᴏᴜʀ Bᴏᴛ !!"
        )

    try:
        log_msg = await m.forward(chat_id=BIN_CHANNEL)

        stream_link = f"{URL}stream/{str(log_msg.id)}?hash={get_hash(log_msg)}"
        online_link = f"{URL}download/{str(log_msg.id)}?hash={get_hash(log_msg)}"
        #logging.info(f"Log msg: {log_msg}")
        msg_text = """
<b>ʏᴏᴜʀ ʟɪɴᴋ ɪs ɢᴇɴᴇʀᴀᴛᴇᴅ...⚡

<b>📧 ғɪʟᴇ ɴᴀᴍᴇ :- </b> <i><b>{}</b></i>

<b>📦 ғɪʟᴇ sɪᴢᴇ :- </b> <i><b>{}</b></i>

<b>💌 ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ :- </b> <i><b>{}</b></i>

<b>🖥 ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ :- </b> <i><b>{}</b></i>

<b>♻️ ᴛʜɪs ʟɪɴᴋ ɪs ᴘᴇʀᴍᴀɴᴇɴᴛ ᴀɴᴅ ᴡᴏɴ'ᴛ ɢᴇᴛs ᴇxᴘɪʀᴇᴅ ♻️\n\n❖ YouTube.com/OpusTechz</b>"""

        await log_msg.reply_text(
            text=f"**RᴇQᴜᴇꜱᴛᴇᴅ ʙʏ :** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n"
                 f"**Uꜱᴇʀ ɪᴅ :** `{m.from_user.id}`\n"
                 f"**Stream ʟɪɴᴋ :** {stream_link}",
            disable_web_page_preview=True,
            quote=True
        )

        await m.reply_text(
            text=msg_text.format(
                get_name(log_msg),
                humanbytes(get_media_file_size(m)),
                online_link,
                stream_link
            ),
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⚡ ᴡᴀᴛᴄʜ ⚡", url=stream_link),
                  InlineKeyboardButton('⚡ ᴅᴏᴡɴʟᴏᴀᴅ ⚡', url=online_link)]]
            )
        )
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await c.send_message(
            chat_id=BIN_CHANNEL,
            text=(f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {str(e.x)}s from "
                  f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n"
                  f"**𝚄𝚜𝚎𝚛 𝙸𝙳 :** `{str(m.from_user.id)}`"),
            disable_web_page_preview=True
        )

# Handle media from channels (no banned-channel checks)
@StreamBot.on_message(filters.channel & ~filters.group & (filters.document | filters.video | filters.photo) & ~filters.forwarded, group=-1)
async def channel_receive_handler(bot, broadcast):
    try:
        log_msg = await broadcast.forward(chat_id=BIN_CHANNEL)

        stream_link = f"{URL}stream/{str(log_msg.id)}?hash={get_hash(log_msg)}"
        online_link = f"{URL}download/{str(log_msg.id)}?hash={get_hash(log_msg)}"

        await log_msg.reply_text(
            text=(f"**Cʜᴀɴɴᴇʟ Nᴀᴍᴇ:** `{broadcast.chat.title}`\n"
                  f"**Cʜᴀɴɴᴇʟ ID:** `{broadcast.chat.id}`\n"
                  f"**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** {stream_link}"),
            quote=True
        )

        await bot.edit_message_reply_markup(
            chat_id=broadcast.chat.id,
            id=broadcast.id,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⚡ ᴡᴀᴛᴄʜ ⚡", url=stream_link),
                  InlineKeyboardButton('⚡ ᴅᴏᴡɴʟᴏᴀᴅ ⚡', url=online_link)]]
            )
        )
    except FloodWait as w:
        await asyncio.sleep(w.x)
        await bot.send_message(
            chat_id=BIN_CHANNEL,
            text=(f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {str(w.x)}s from {broadcast.chat.title}\n\n"
                  f"**Cʜᴀɴɴᴇʟ ID:** `{str(broadcast.chat.id)}`"),
            disable_web_page_preview=True
        )
    except Exception as e:
        await bot.send_message(
            chat_id=BIN_CHANNEL,
            text=f"**#ᴇʀʀᴏʀ_ᴛʀᴀᴄᴇʙᴀᴄᴋ:** `{e}`",
            disable_web_page_preview=True
        )
        print(f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\nEʀʀᴏʀ:  **Give me edit permission in updates and bin Chanell{e}**")

# ----- Web server & helpers
async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

# -- Ping (optional keep-alive)
async def ping_server():
    sleep_time = 3600
    while True:
        await asyncio.sleep(sleep_time)
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(URL) as resp:
                    logging.info("Pinged server with response: {}".format(resp.status))
        except TimeoutError:
            logging.warning("Couldn't connect to the site URL..!")
        except Exception:
            traceback.print_exc()


@routes.get("/", allow_head=True)
async def root_route_handler(_):
    # return web.json_response(
        # {
            # "server_status": "running",
            # "uptime": get_readable_time(time.time() - StartTime),
            # "telegram_bot": "@" + (await StreamBot.get_me()).username,
            # "connected_bots": len(multi_clients),
            # "loads": dict(
                # ("bot" + str(c + 1), l)
                # for c, (_, l) in enumerate(
                    # sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
                # )
            # ),
            # "version": "v1.0[t1]",
        # }
    # )
    
    # -- Cute HTML for root (/)
    try:
        bot_info = await StreamBot.get_me()
        uptime = get_readable_time(time.time() - StartTime)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Server Status</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #0f172a;
                    color: #e2e8f0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .card {{
                    background: #1e293b;
                    padding: 20px 30px;
                    border-radius: 12px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.5);
                    width: 400px;
                }}
                h1 {{
                    margin-top: 0;
                    color: #38bdf8;
                    text-align: center;
                }}
                .info {{
                    margin: 10px 0;
                    padding: 10px;
                    background: #334155;
                    border-radius: 8px;
                }}
                .key {{ font-weight: bold; color: #fbbf24; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>📡 Server Status</h1>
                <div class="info"><span class="key">Server:</span> Running ✅</div>
                <div class="info"><span class="key">Uptime:</span> {uptime}</div>
                <div class="info"><span class="key">Telegram Bot:</span> @{bot_info.username}</div>
                <div class="info"><span class="key">Connected Bots:</span> {len(multi_clients)}</div>
                <div class="info"><span class="key">Version:</span> v1.0[t1]</div>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")
    except Exception as e:
        return web.Response(status=500, text=f"Error: {e}")



@routes.get(r"/stream/{id:\d+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        id = int(request.match_info["id"])
        secure_hash = request.rel_url.query.get("hash")

        if not secure_hash:
            raise web.HTTPForbidden(text="Missing hash parameter")

        if "Range" in request.headers:
            return await media_streamer(request, id, secure_hash)

        return web.Response(
            text=await render_page(id, secure_hash),
            content_type="text/html"
        )

    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FileNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except Exception as e:
        logging.critical(e.with_traceback(None))
        return web.Response(status=500, text=f"Internal Server Error: {e}")



@routes.get(r"/download/{id:\d+}", allow_head=True)
async def media_stream_handler(request: web.Request):
    try:
        id = int(request.match_info["id"])
        secure_hash = request.rel_url.query.get("hash")
        if not secure_hash:
            raise web.HTTPForbidden(text="Missing hash")
        return await media_streamer(request, id, secure_hash)
    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)
    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)
    except (AttributeError, BadStatusLine, ConnectionResetError):
        return web.Response(status=400, text="Invalid request or connection closed.")
    except Exception as e:
        logging.critical(e.with_traceback(None))
        return web.Response(status=500, text=f"Internal Server Error: {e}")


class_cache = {}

# ----- Media Streamer
async def media_streamer(request: web.Request, id: int, secure_hash: str):
    range_header = request.headers.get("Range", 0)
    #logging.info(f"Incoming stream request: id={id}, hash={secure_hash}")
    #logging.info(f"Request headers: {dict(request.headers)}")
    #logging.info(f"Range header: {range_header}")
    index = 0
    faster_client = StreamBot
    if MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logging.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logging.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect

    file_id = await tg_connect.get_file_properties(id)

    if file_id.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with ID {id}")
        raise InvalidHash

    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = request.http_range.stop or file_size - 1

    req_length = until_bytes - from_bytes
    new_chunk_size = await chunk_size(req_length)
    offset = await offset_fix(from_bytes, new_chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = (until_bytes % new_chunk_size) + 1
    part_count = math.ceil(req_length / new_chunk_size)
    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, new_chunk_size
    )

    mime_type = file_id.mime_type
    file_name = file_id.file_name
    disposition = "inline" if "stream" in str(request.rel_url.path) else "attachment"
    if mime_type:
        if not file_name:
            try:
                file_name = f"{secrets.token_hex(2)}.{mime_type.split('/')[1]}"
            except (IndexError, AttributeError):
                file_name = f"{secrets.token_hex(2)}.unknown"
    else:
        if file_name:
            mime_type = mimetypes.guess_type(file_id.file_name)
        else:
            mime_type = "application/octet-stream"
            file_name = f"{secrets.token_hex(2)}.unknown"

    return_resp = web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Range": f"bytes={from_bytes}-{until_bytes}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Disposition": f'{disposition}; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        },
    )

    if return_resp.status == 200:
        return_resp.headers.add("Content-Length", str(file_size))

    return return_resp

# ------- Render html page
async def render_page(id, secure_hash):
    file_data = await get_file_ids(StreamBot, str(BIN_CHANNEL), int(id))

    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f"link hash: {secure_hash} - {file_data.unique_id[:6]}")
        logging.debug(f"Invalid hash for message with - ID {id}")
        raise InvalidHash

    src = urljoin(URL, f"stream/{id}?hash={secure_hash}")
    # -- Download button fixed (lol)
    dll = urljoin(URL, f"download/{id}?hash={secure_hash}")
    file_type = str(file_data.mime_type.split('/')[0].strip())
    if file_type == "video":
        async with aiofiles.open("req.html") as r:
            heading = f"Watch {file_data.file_name}"
            html = (await r.read()) % (heading, file_data.file_name, dll)

    elif file_type == "audio":
        async with aiofiles.open("req.html") as r:
            heading = f"Listen {file_data.file_name}"
            html = (await r.read()) % (heading, file_data.file_name, dll)

    else:
        async with aiofiles.open("dl.html") as r:
            async with aiohttp.ClientSession() as s:
                async with s.get(src) as u:
                    heading = f"Download {file_data.file_name}"
                    file_size = humanbytes(int(u.headers.get("Content-Length")))
                    html = (await r.read()) % (heading, file_data.file_name, src, file_size)

    return html



async def chunk_size(length):
    return 2 ** max(min(math.ceil(math.log2(length / 1024)), 10), 2) * 1024

async def offset_fix(offset, chunksize):
    offset -= offset % chunksize
    return offset

# ----- ByteStreamer
class ByteStreamer:
    def __init__(self, client: Client):
        """Holds cache & methods to stream files from Telegram."""
        self.clean_timer = 30 * 60
        self.client: Client = client
        self.cached_file_ids: Dict[int, FileId] = {}
        asyncio.create_task(self.clean_cache())

    async def get_file_properties(self, id: int) -> FileId:
        if id not in self.cached_file_ids:
            await self.generate_file_properties(id)
            logging.debug(f"Cached file properties for message with ID {id}")
        return self.cached_file_ids[id]

    async def generate_file_properties(self, id: int) -> FileId:
        file_id = await get_file_ids(self.client, BIN_CHANNEL, id)
        logging.debug(f"Generated file ID and Unique ID for message with ID {id}")
        if not file_id:
            logging.debug(f"Message with ID {id} not found")
            raise FIleNotFound
        self.cached_file_ids[id] = file_id
        logging.debug(f"Cached media message with ID {id}")
        return self.cached_file_ids[id]

    async def generate_media_session(self, client: Client, file_id: FileId) -> Session:
        media_session = client.media_sessions.get(file_id.dc_id, None)

        if media_session is None:
            if file_id.dc_id != await client.storage.dc_id():
                media_session = Session(
                    client,
                    file_id.dc_id,
                    await Auth(
                        client, file_id.dc_id, await client.storage.test_mode()
                    ).create(),
                    await client.storage.test_mode(),
                    is_media=True,
                )
                await media_session.start()

                for _ in range(6):
                    exported_auth = await client.invoke(
                        raw.functions.auth.ExportAuthorization(dc_id=file_id.dc_id)
                    )

                    try:
                        await media_session.send(
                            raw.functions.auth.ImportAuthorization(
                                id=exported_auth.id, bytes=exported_auth.bytes
                            )
                        )
                        break
                    except AuthBytesInvalid:
                        logging.debug(
                            f"Invalid authorization bytes for DC {file_id.dc_id}"
                        )
                        continue
                else:
                    await media_session.stop()
                    raise AuthBytesInvalid
            else:
                media_session = Session(
                    client,
                    file_id.dc_id,
                    await client.storage.auth_key(),
                    await client.storage.test_mode(),
                    is_media=True,
                )
                await media_session.start()
            logging.debug(f"Created media session for DC {file_id.dc_id}")
            client.media_sessions[file_id.dc_id] = media_session
        else:
            logging.debug(f"Using cached media session for DC {file_id.dc_id}")
        return media_session

    @staticmethod
    async def get_location(file_id: FileId) -> Union[
        raw.types.InputPhotoFileLocation,
        raw.types.InputDocumentFileLocation,
        raw.types.InputPeerPhotoFileLocation,
    ]:
        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id, access_hash=file_id.chat_access_hash
                )
            else:
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash,
                    )

            location = raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
            )
        elif file_type == FileType.PHOTO:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )
        return location

    async def yield_file(
        self,
        file_id: FileId,
        index: int,
        offset: int,
        first_part_cut: int,
        last_part_cut: int,
        part_count: int,
        chunk_size: int,
    ) -> Union[str, None]:
        client = self.client
        work_loads[index]
        logging.debug(f"Starting to yielding file with client {index}.")
        media_session = await self.generate_media_session(client, file_id)

        current_part = 1
        location = await self.get_location(file_id)

        try:
            r = await media_session.send(
                raw.functions.upload.GetFile(
                    location=location, offset=offset, limit=chunk_size
                ),
            )
            if isinstance(r, raw.types.upload.File):
                while current_part <= part_count:
                    chunk = r.bytes
                    if not chunk:
                        break
                    offset += chunk_size
                    if part_count == 1:
                        yield chunk[first_part_cut:last_part_cut]
                        break
                    if current_part == 1:
                        yield chunk[first_part_cut:]
                    if 1 < current_part <= part_count:
                        yield chunk

                    r = await media_session.send(
                        raw.functions.upload.GetFile(
                            location=location, offset=offset, limit=chunk_size
                        ),
                    )

                    current_part += 1
        except (TimeoutError, AttributeError):
            pass
        finally:
            logging.debug("Finished yielding file with {current_part} parts.")
            work_loads[index]

    async def clean_cache(self) -> None:
        while True:
            await asyncio.sleep(self.clean_timer)
            self.cached_file_ids.clear()
            logging.debug("Cleaned the cache")

def get_readable_time(seconds: int) -> str:
    count = 0
    readable_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", " days"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        readable_time += time_list.pop() + ", "
    time_list.reverse()
    readable_time += ": ".join(time_list)
    return readable_time

async def parse_file_id(message: "Message") -> Optional[FileId]:
    media = get_media_from_message(message)
    if media:
        return FileId.decode(media.file_id)

async def parse_file_unique_id(message: "Message") -> Optional[str]:
    media = get_media_from_message(message)
    if media:
        return media.file_unique_id

async def get_file_ids(client: Client, chat_id: int, id: int) -> Optional[FileId]:
    message = await client.get_messages(chat_id, id)
    if message.empty:
        raise FIleNotFound
    media = get_media_from_message(message)
    file_unique_id = await parse_file_unique_id(message)
    file_id = await parse_file_id(message)
    setattr(file_id, "file_size", getattr(media, "file_size", 0))
    setattr(file_id, "mime_type", getattr(media, "mime_type", ""))
    setattr(file_id, "file_name", getattr(media, "file_name", ""))
    setattr(file_id, "unique_id", file_unique_id)
    return file_id



if __name__ == '__main__':
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        logging.info('----------------------- Service Stopped -----------------------')
