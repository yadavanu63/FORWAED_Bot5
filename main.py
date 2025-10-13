import re    
import os 
import sys
import time      
import pymongo
import asyncio
import tgcrypto
import requests
import datetime
import random
import math
from pyromod import listen
from pyrogram import enums 
from Crypto.Cipher import AES
from pymongo import MongoClient
from aiohttp import ClientSession    
from pyrogram.types import Message, BotCommand  
from pyrogram import Client, filters
from base64 import b64encode, b64decode
from pyrogram.errors import *
from pyrogram.types import User, Message        
from pyrogram.types.messages_and_media import message
from config import *
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid

#========================= Initaited bot ===========================
# Initialize bot and MongoDB
app = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo = MongoClient(MONGO_URI)
db = mongo["forward_bot"]
users = db["users"]
users_collection = db["busers"]
auth_col = db["auth_users"]
cancel_flags = {}
OWNER_LOG_GROUP = -1003133514394
FORCE_CHANNEL = -1002630069470
#===================== Random Choose Image =======================
image_list = [
    "https://www.pixelstalk.net/wp-content/uploads/2025/03/A-breathtaking-image-of-a-lion-roaring-proudly-atop-a-rocky-outcrop-with-dramatic-clouds-and-rays-of-sunlight-breaking-through-2.webp"
    ]
#======================== Force Subscribe =======================
async def force_subscribe(client, message):
    try:
        user = await client.get_chat_member(FORCE_CHANNEL, message.from_user.id)
        if user.status in ("left", "kicked"):
            raise UserNotParticipant
    except UserNotParticipant:
        try:
            invite_link = await client.create_chat_invite_link(FORCE_CHANNEL)
            channel_info = await client.get_chat(FORCE_CHANNEL)
            channel_name = f"{channel_info.title}"
        except ChatAdminRequired:
            return await message.reply("❌ Bot is not admin in the force channel.")

        random_image = random.choice(image_list)
        return await client.send_photo(
            chat_id=message.chat.id,
            photo=random_image,
            caption=(
               f"🔒 𝗛𝗲𝘆 {message.from_user.mention} !\n\n"
                f"🔔 𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝗼𝘂𝗿 𝗼𝗳𝗳𝗶𝗰𝗶𝗮𝗹 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗼 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗲 𝘂𝘀𝗶𝗻𝗴 𝘁𝗵𝗶𝘀 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝗯𝗼𝘁.\n\n"
                f"📢 𝗜𝗻𝘀𝗶𝗱𝗲: 𝗧𝗶𝗽𝘀, 𝗨𝗽𝗱𝗮𝘁𝗲𝘀, 𝗔𝗻𝗻𝗼𝘂𝗻𝗰𝗲𝗺𝗲𝗻𝘁𝘀 & 𝗠𝗼𝗿𝗲\n\n"
                f"📢 𝗝𝗼𝗶𝗻 <u>**{channel_name}**</u> 𝗮𝗻𝗱 𝗰𝗹𝗶𝗰𝗸 𝘁𝗵𝗲 𝗯𝘂𝘁𝘁𝗼𝗻 𝗯𝗲𝗹𝗼𝘄!"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f'📢 Join {channel_name}', url=invite_link.invite_link),
                InlineKeyboardButton("✅ I've Joined", callback_data="checksub")
            ]])
        )
    except Exception as e:
        print(f"[ForceSubscribe Error] {e}")
        return await message.reply(f"[ForceSubscribe Error] {e}")
        #return await message.reply("⚠️ An error occurred while checking subscription.")
    return True

@app.on_callback_query(filters.regex("checksub"))
async def recheck_subscription(client, callback_query):
    message = callback_query.message
    result = await force_subscribe(client, callback_query)

    if result is True:
        try:
            await callback_query.message.edit(
                "✅ 𝗬𝗼𝘂'𝘃𝗲 𝗯𝗲𝗲𝗻 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝘃𝗲𝗿𝗶𝗳𝗶𝗲𝗱!\n\n✨ You can now enjoy full access to this premium bot."
            )
        except Exception as e:
            print(f"[ForceSubscribe Error] {e}")
    else:
        # Don't use await callback_query.message.edit and answer together
        await callback_query.answer(
            "❌ You still haven't joined the required channel!", show_alert=True
        )
#======================= Set bot commands ========================

@app.on_message(filters.command("set") & filters.user(OWNER_ID))
async def set_bot_commands(client, message):
    result = await force_subscribe(client, message)
    if result is not True:
        return
    commands = [
        BotCommand("start", "🚀 Start the bot"),
        BotCommand("stop", "🛑 Stop forwarding"),
        BotCommand("id", "🆔 Show your Telegram ID"),
        BotCommand("forward", "📤 Forward messages"),
        BotCommand("settings", "🔍 Change settings"),
         BotCommand("manage", "👤 Premium User Management Panel"),
        BotCommand("broadcast", "📢 Broadcast a message to users"),
    ]

    await client.set_bot_commands(commands)
    await message.reply("<blockquote>✅ Bot commands set successfully.</blockquote>")

#======================= Check premium users ====================
def is_authorized(user_id):
    return auth_col.find_one({"_id": user_id}) or user_id == OWNER_ID

#======================== Premium Users Auth system  =======================
from pyromod.listen import Client as ListenClient

@app.on_message(filters.command("manage") & filters.user(OWNER_ID))
async def manage_users(client: ListenClient, message):
    result = await force_subscribe(client, message)
    if result is not True:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add User", callback_data="add_user"),
         InlineKeyboardButton("➖ Remove User", callback_data="remove_user")],
        [InlineKeyboardButton("🧹 Clear All", callback_data="clear_users"),
         InlineKeyboardButton("👥 Show All", callback_data="show_users")]
    ])
    await message.reply(
        "<b>👤 Premium User Management Panel</b>\n\n"
        "Use the buttons below to manage your authorized users.\n"
        "All actions are real-time and logged. 🛡️",
        reply_markup=kb
    )

# =================== ADD USER ======================
@app.on_callback_query(filters.regex("^add_user$"))
async def add_user(client: ListenClient, query: CallbackQuery):
    await query.message.edit("📝 Send the <b>User ID</b> to add.\nType /cancel to abort.")
    try:
        msg = await client.listen(query.message.chat.id, timeout=60)
        await msg.delete()

        if msg.text.lower() == "/cancel":
            return await query.message.edit("❌ Cancelled.")

        uid = int(msg.text.strip())

        if not auth_col.find_one({"_id": uid}):
            auth_col.insert_one({"_id": uid})
            await query.message.edit(f"✅ User <code>{uid}</code> added successfully.")
            try:
                await client.send_message(uid, "🎉 You have been added as a premium user!")
            except: pass
        else:
            await query.message.edit("ℹ️ User already exists.")
    except ValueError:
        await query.message.edit("❌ Invalid ID format.")
    except Exception as e:
        await query.message.edit(f"⚠️ Error: {e}")

# =================== REMOVE USER ======================
@app.on_callback_query(filters.regex("^remove_user$"))
async def remove_user(client: ListenClient, query: CallbackQuery):
    await query.message.edit("📝 Send the <b>User ID</b> to remove.\nType /cancel to abort.")
    try:
        msg = await client.listen(query.message.chat.id, timeout=60)
        await msg.delete()

        if msg.text.lower() == "/cancel":
            return await query.message.edit("❌ Cancelled.")

        uid = int(msg.text.strip())

        result = auth_col.delete_one({"_id": uid})
        if result.deleted_count:
            await query.message.edit(f"✅ User <code>{uid}</code> removed successfully.")
            try:
                await client.send_message(uid, "⚠️ You have been removed from premium access.")
            except: pass
        else:
            await query.message.edit("🚫 User not found.")
    except ValueError:
        await query.message.edit("❌ Invalid ID format.")
    except Exception as e:
        await query.message.edit(f"⚠️ Error: {e}")

# =================== CLEAR USERS ======================
@app.on_callback_query(filters.regex("^clear_users$"))
async def clear_users(client, query: CallbackQuery):
    result = auth_col.delete_many({})
    await query.message.edit(f"🧹 Cleared <b>{result.deleted_count}</b> users from the premium list.")

# =================== SHOW USERS ======================
@app.on_callback_query(filters.regex("^show_users$"))
async def show_users(client, query: CallbackQuery):
    users = list(auth_col.find())
    if not users:
        return await query.message.edit("🚫 No authorized users found.")
    user_list = "\n".join(f"🔹 <code>{u['_id']}</code>" for u in users)
    await query.message.edit(f"<b>👥 Premium Users:</b>\n\n{user_list}")
    
    
#========================== For broadcast ====================================
def add_user(user_id):
    if not users_collection.find_one({"_id": user_id}):
        users_collection.insert_one({"_id": user_id})

def remove_user(user_id):
    users_collection.delete_one({"_id": user_id})
    
def get_all_users():
    return [doc["_id"] for doc in users_collection.find()]

# Global store to keep track of broadcast requests
broadcast_requests = {}

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_handler(bot, message: Message):
    result = await force_subscribe(bot, message)
    if result is not True:
        return
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to broadcast it.")

    # Save the message ID and user ID
    broadcast_requests[message.from_user.id] = {
        "chat_id": message.chat.id,
        "message_id": message.reply_to_message.id
    }

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_broadcast"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")
        ]
    ])

    await message.reply_text(
        "Are you sure you want to broadcast this message?",
        reply_markup=buttons
    )


@app.on_callback_query(filters.regex("^(confirm_broadcast|cancel_broadcast)$"))
async def handle_broadcast_decision(bot, query: CallbackQuery):
    user_id = query.from_user.id
    action = query.data

    if user_id not in broadcast_requests:
        return await query.answer("No broadcast request found.", show_alert=True)

    data = broadcast_requests.pop(user_id)
    chat_id = data["chat_id"]
    message_id = data["message_id"]

    if action == "cancel_broadcast":
        await query.message.edit_text("❌ Broadcast canceled.")
        return

    await query.message.edit_text("📣 Broadcasting...")

    # Start broadcasting
    sent = 0
    failed = 0
    total = 0
    failed_users = []

    users = get_all_users()

    for uid in users:
        total += 1
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=chat_id,
                message_id=message_id
            )
            sent += 1
        except Exception as e:
            print(f"Failed to send to {uid}: {e}")
            failed += 1
            # Immediately delete the failed user from DB
            remove_user(uid)

    # Report
    report_text = (
        f"<blockquote>📢 <b>Broadcast Complete</b></blockquote>\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed to Send: {failed}\n"
        f"📊 Total Users: {total}"
    )
    await bot.send_message(chat_id, report_text)

#================= Reactiom & add users in database ======================
 #yaha pe reation wala part tha jo ki mene delet kar diya hai.
#=================== ID ============================
@app.on_message(filters.command("id"))
async def send_user_id(bot, message):
    result = await force_subscribe(bot, message)
    if result is not True:
        return
    user_id = message.from_user.id
    text = f"<blockquote>👤 Your Telegram ID is :</blockquote>\n\n{user_id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📨 Send to Owner", callback_data=f"send_id:{user_id}")]
    ])

    await message.reply_text(text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"send_id:(\d+)"))
async def handle_send_to_owner(bot, query):
    user_id = int(query.matches[0].group(1))

    await bot.send_message(
        OWNER_ID,
        f"📬 USER_ID : 👤 `{user_id}`"
    )

    await query.answer("✅ Sent to owner!", show_alert=True)

#===================== Detect chat id from message link ===================
def extract_ids_from_link(link):
    match = re.search(r"https://t.me/(c/)?([\w_]+)/?(\d+)?", link)
    if not match:
        return None, None
    if match.group(1):  # private group/channel
        chat_id = int(f"-100{match.group(2)}")
    else:
        username = match.group(2)
        chat_id = username if not username.isdigit() else int(username)
    msg_id = int(match.group(3)) if match.group(3) else None
    return chat_id, msg_id

#================================ Start command to start bot ============================
class Data:
    START = (
        "🌟 𝐇𝐞𝐲  {0} , 𝐖𝐄𝐋𝐂𝐎𝐌𝐄  !\n\n"
    )
# Define the start command handler
@app.on_message(filters.command("start"))
async def start(client: Client, msg: Message):
    result = await force_subscribe(client, msg)
    if result is not True:
        return
    user = await client.get_me()
    mention = user.mention
    random_image = random.choice(image_list)
    
    start_message = await client.send_photo(
        chat_id=msg.chat.id,
        photo=random_image,
        caption=Data.START.format(msg.from_user.mention)
    )
    
    await asyncio.sleep(1)
    user_id = msg.from_user.id
    
    if is_authorized(user_id):
        await start_message.edit_text(
            Data.START.format(msg.from_user.mention) +
            "🎉 <b>Welcome to</b> <u><b>Forward ProBot</b></u> 🎉\n\n"
            "<blockquote>🔓 Premium Access Confirmed</blockquote>\n"
            "✨ You're now ready to enjoy all <b>advanced forwarding features</b> :\n\n"
            "• ✏️ Smart Caption Replacement\n"
            "• 🧹 Text Deletion & Filters\n"
            "• 📌 Auto Pin & Media Control\n\n"
            "<b>🚀 Commands:</b>\n"
            "<blockquote>• /settings – Customize filters & features\n"
            "• /forward – Start message forwarding\n"
            "• /stop – Cancel active tasks</blockquote>\n\n"
            "📍 <i>Tip: Use message links to select range.</i>\n\n"
            "<b>⚡ Power meets simplicity – Enjoy seamless forwarding!</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Contact Admin", url="https://t.me/taporibot_bot")]
            ])
        )
    
    else:
        await asyncio.sleep(2)
        await start_message.edit_text(
            Data.START.format(msg.from_user.mention) +
            "<blockquote>🚫 Premium membership is required to use this bot.</blockquote>\n\n"
            "💎 <b>Features you'll unlock with access:</b>\n\n"
            "• 📤 Superfast message forwarding\n"
            "• ✨ Caption & link editing tools\n"
            "• 📌 Auto-pinning + media type filters\n"
            "• 🛠️ Custom word replacement & deletion\n\n"
            "<b>🤝 Want access?</b>\n"
            "<b> Use /id & Send to owner</b>\n"
            "<blockquote>Contact the admin to request your premium slot:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/taporibot_bot")]
            ])
        )
#================================ Set filters =============================
from pyromod.listen import Client as ListenClient

DEFAULT_TYPES = {
    "text": True, "photo": True, "video": True, "document": True,
    "audio": True, "voice": True, "sticker": True, "poll": True, "animation": True
}
ALLOWED_TYPES = list(DEFAULT_TYPES.keys())

def get_type_buttons(types):
    return [
        InlineKeyboardButton(
            f"{'✅' if types[t] else '❌'} {t.capitalize()}",
            callback_data=f"type_{t}"
        ) for t in ALLOWED_TYPES
    ]

def get_main_filter_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Replace Words", callback_data="edit_replace"),
         InlineKeyboardButton("❌ Delete Words", callback_data="edit_delete")],
        [InlineKeyboardButton("📌 Auto Pin", callback_data="toggle_autopin"),
         InlineKeyboardButton("🧪 Filters", callback_data="edit_types")],
        [InlineKeyboardButton("🎯 Set Target", callback_data="set_target"),
         InlineKeyboardButton("ℹ️ View Settings", callback_data="view_info")],
        [InlineKeyboardButton("♻️ Reset Settings", callback_data="reset_settings"),
         InlineKeyboardButton("📖 Help", callback_data="filters_help")],
        [InlineKeyboardButton("🖼 Change Thumbnail", callback_data="change_thumb")],  # 👈 New Feature
        [InlineKeyboardButton("✅ Save Settings", callback_data="done")]
    ])

caption = (
    "🛠️ **Customize Your Forwarding Filters**\n\n"
    "✨ Make the bot behave exactly how you want!\n\n"
    "🔹 Replace Words\n"
    "🔹 Delete Specific Text\n"
    "🔹 Filter by Media Types\n"
    "🔹 Change Video Thumbnail\n\n"
    "🔹 Auto Pin Messages\n\n"
    "🎯 Tap the buttons below to modify settings as per your style."
)

@app.on_message(filters.command("settings") & filters.private)
async def show_filter_menu(client: ListenClient, message):
    result = await force_subscribe(client, message)
    if result is not True:
        return
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return await message.reply("❌ 𝚈𝚘𝚞 𝚊𝚛𝚎 𝚗𝚘𝚝 𝚊𝚞𝚝𝚑𝚘𝚛𝚒𝚣𝚎𝚍.\n\n💎 𝙱𝚞𝚢 𝙿𝚛𝚎𝚖𝚒𝚞𝚖  [𝗧𝗮𝗽𝗼𝗿𝗶 𝟮.𝟬🥷](https://t.me/taporibot_bot) !")

    users.update_one({"user_id": user_id}, {
        "$setOnInsert": {
            "filters": {
                "replace": {},
                "delete": [],
                "types": DEFAULT_TYPES.copy()
            },
            "auto_pin": False,
            "thumbnail": None  # 👈 Thumbnail added
        }
    }, upsert=True)

    await message.reply(caption, reply_markup=get_main_filter_buttons())

#==================== Change Thumbnail Feature ====================
@app.on_callback_query(filters.regex("^change_thumb$"))
async def change_thumb_callback(client, query: CallbackQuery):
    await query.message.edit(
        "🖼 Please send me the image you want to use as video thumbnail.\n\n"
        "Or type /cancel to abort."
    )
    try:
        response = await client.listen(query.message.chat.id, timeout=120)
        if response.text and response.text.lower() == "/cancel":
            return await query.message.edit("❌ Cancelled.", reply_markup=get_main_filter_buttons())

        if not response.photo:
            return await query.message.edit("⚠️ Please send a photo file.", reply_markup=get_main_filter_buttons())

        file_path = await client.download_media(response.photo.file_id)
        users.update_one(
            {"user_id": query.from_user.id},
            {"$set": {"filters.thumbnail": file_path}},
            upsert=True
        )
        await query.message.edit("✅ Thumbnail saved successfully!", reply_markup=get_main_filter_buttons())
    except asyncio.TimeoutError:
        await query.message.edit("⏰ Timeout. Please try again.", reply_markup=get_main_filter_buttons())

@app.on_callback_query(filters.regex("^edit_types$"))
async def edit_types(_, query: CallbackQuery):
    user_id = query.from_user.id
    user = users.find_one({"user_id": user_id})
    types = user.get("filters", {}).get("types", DEFAULT_TYPES.copy())
    rows = [get_type_buttons(types)[i:i+3] for i in range(0, len(ALLOWED_TYPES), 3)]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
    await query.message.edit("📨 Toggle Message Types", reply_markup=InlineKeyboardMarkup(rows))

@app.on_callback_query(filters.regex("^type_"))
async def toggle_type(_, query: CallbackQuery):
    type_name = query.data.split("_")[1]
    user_id = query.from_user.id
    user = users.find_one({"user_id": user_id})
    filters_data = user.get("filters", {})
    types = filters_data.get("types", DEFAULT_TYPES.copy())
    types[type_name] = not types.get(type_name, True)
    users.update_one({"user_id": user_id}, {"$set": {"filters.types": types}})
    await edit_types(_, query)

@app.on_callback_query(filters.regex("^edit_replace$"))
async def edit_replace(client: ListenClient, query: CallbackQuery):
    await query.message.edit("🔁 Send replace in format: `old => new`\nType /cancel to abort.")
    try:
        response = await client.listen(query.message.chat.id, timeout=120)
        await response.delete()
        if response.text.lower() == "/cancel":
            return await query.message.edit("❌ Cancelled.", reply_markup=get_main_filter_buttons())
        old, new = [t.strip() for t in response.text.split("=>", 1)]
        users.update_one({"user_id": query.from_user.id}, {"$set": {f"filters.replace.{old}": new}})
        await query.message.edit(f"✅ Replacing `{old}` with `{new}`", reply_markup=get_main_filter_buttons())
    except Exception:
        await query.message.edit("❌ Invalid format. Try again.", reply_markup=get_main_filter_buttons())

@app.on_callback_query(filters.regex("^edit_delete$"))
async def edit_delete(client: ListenClient, query: CallbackQuery):
    await query.message.edit("❌ Send a word to delete\nType /cancel to abort.")
    try:
        response = await client.listen(query.message.chat.id, timeout=120)
        await response.delete()
        word = response.text.strip()
        if word.lower() == "/cancel":
            return await query.message.edit("❌ Cancelled.", reply_markup=get_main_filter_buttons())
        user = users.find_one({"user_id": query.from_user.id})
        delete_list = user.get("filters", {}).get("delete", [])
        if word not in delete_list:
            delete_list.append(word)
            users.update_one({"user_id": query.from_user.id}, {"$set": {"filters.delete": delete_list}})
        await query.message.edit(f"✅ Will delete: `{word}`", reply_markup=get_main_filter_buttons())
    except Exception:
        await query.message.edit("❌ Failed. Try again.", reply_markup=get_main_filter_buttons())

@app.on_callback_query(filters.regex("^toggle_autopin$"))
async def toggle_autopin(_, query: CallbackQuery):
    user_id = query.from_user.id
    user = users.find_one({"user_id": user_id})
    filters_data = user.get("filters", {})
    current = filters_data.get("auto_pin", False)

    # Toggle the value inside filters.auto_pin
    filters_data["auto_pin"] = not current
    users.update_one({"user_id": user_id}, {"$set": {"filters.auto_pin": not current}})

    status = "✅ Enabled" if not current else "❌ Disabled"
    await query.answer(f"Auto Pin: {status}", show_alert=True)

@app.on_callback_query(filters.regex("^back_to_menu$"))
async def back_to_main(_, query: CallbackQuery):
    await query.message.edit(caption, reply_markup=get_main_filter_buttons())

@app.on_callback_query(filters.regex("^set_target$"))
async def set_target_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    await query.message.edit("<blockquote>📩 Send a message link from the target channel</blockquote>")
    try:
        link_msg = await client.listen(query.message.chat.id, timeout=120)
        await link_msg.delete()
        link = link_msg.text.strip()
        chat_id, _ = extract_ids_from_link(link)
        if not chat_id:
            return await query.message.edit("<blockquote>❌ Invalid link</blockquote>", reply_markup=get_main_filter_buttons())
        users.update_one({"user_id": user_id}, {"$set": {"target_chat": chat_id}}, upsert=True)
        await query.message.edit(f"<blockquote>✅ Target set to `{chat_id}`</blockquote>", reply_markup=get_main_filter_buttons())
    except asyncio.TimeoutError:
        await query.message.edit("<blockquote>⏰ Timed out. Please try again</blockquote>", reply_markup=get_main_filter_buttons())

@app.on_callback_query(filters.regex("^view_info$"))
async def view_info_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    user = users.find_one({"user_id": user_id})
    if not user:
        return await query.message.reply("<blockquote>❌ No data found for this user.</blockquote>", reply_markup=get_main_filter_buttons())

    filters_data = user.get("filters", {})
    replace = filters_data.get("replace", {})
    delete = filters_data.get("delete", [])
    types = filters_data.get("types", {})
    auto_pin = filters_data.get("auto_pin", False)

    allowed_types = [
        "text", "photo", "video", "document", "audio",
        "voice", "sticker", "poll", "animation"
    ]
    type_status = "\n".join([
        f"▪️ `{t.capitalize()}`   :   {'✅' if types.get(t, False) else '❌'}"
        for t in allowed_types
    ])

    target_chat_id = user.get("target_chat")
    if target_chat_id:
        try:
            chat = await client.get_chat(target_chat_id)
            target_info_text = (
                f"<u>**Current Target**</u>\n\n"
                f"• Title  : <b>{chat.title}</b>\n"
                f"• ID  : <code>{target_chat_id}</code>\n"
            )
        except Exception:
            target_info_text = (
                f"<u>**Current Target**</u>\n\n"
                f"• ID  : <code>{target_chat_id}</code>\n"
                f"(⚠️ Bot may not have access to retrieve the title)\n"
            )
    else:
        target_info_text = "<u>**Current Target**</u>\n\n❌ No target is currently set.\nUse 🎯 Set Target button to set one.\n"

    await query.message.edit(
        f"<blockquote>⚙️ Settings Information  :</blockquote>\n\n"
        f"{target_info_text}\n"
        f"<u>**Filter Settings**</u>\n\n"
        f"🔁 Replace: {replace}\n"
        f"❌ Delete: {delete}\n"
        f"📌 Auto Pin: {auto_pin}\n\n"
        f"🖼 Thumbnail: {'✅ Set' if user.get('filters', {}).get('thumbnail') else '❌ Not Set'}\n\n"
        f"<u>**Message Types**</u>\n\n{type_status}",
        reply_markup=get_main_filter_buttons()
)

@app.on_callback_query(filters.regex("^reset_settings$"))
async def reset_settings_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    default_types = {
        "text": True,
        "photo": True,
        "video": True,
        "document": True,
        "audio": True,
        "voice": True,
        "sticker": True,
        "poll": True,
        "animation": True
    }

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "target_chat": None,
                "filters.replace": {},
                "filters.delete": [],
                "filters.types": default_types,
                "filters.auto_pin": True,
                "filters.thumbnail": None  # 👈 reset thumbnail too
            }
        },
        upsert=True
    )

    await query.message.edit(
        "<blockquote>♻️ <b>Settings Reset Successfully:</b></blockquote>\n\n"
        "• 🎯 Target Channel  :  Cleared\n"
        "• 🔁 Replace Words  :  Cleared\n"
        "• ❌ Delete Words  :  Cleared\n"
        "• 🔘 Message Types  :  Set to Default\n"
        "• 📌 Auto Pin  :  Enabled"
        "• 🖼 Thumbnail  :  Cleared",
        reply_markup=get_main_filter_buttons()
    )

@app.on_callback_query(filters.regex("^filters_help$"))
async def filters_help_callback(client, query: CallbackQuery):
    await query.message.edit(
        "<blockquote>📖 Help Guide – How to Use the Bot</blockquote>\n\n"

        "<blockquote>🔁 Forwarding Process</blockquote>\n\n"
        "1️⃣ Use <b>🎯 Set Target button</b> to set your target.\n"
        "   • Send any message link from your <b>target channel</b>.\n\n"
        "2️⃣ Use /forward command.\n"
        "   • First, send the link of the <b>first message</b> to forward (from source).\n"
        "   • Then, send the link of the <b>last message</b> to forward.\n"
        "   • Forwarding will begin with real-time progress.\n\n"
        "⚠️ Make sure bot is <b>admin</b> in both source & target channels.\n\n"

        "<blockquote>🛠 Filter Settings Overview</blockquote>\n\n"
        "🎯 <b>Set Target</b>\n"
        "• Select where messages will be forwarded to.\n\n"
        "🔁 <b>Replace Words</b>\n"
        "• Automatically change words in captions/text.\n"
        "• Example: Replace 'offer' ➡️ 'discount'.\n\n"
        "❌ <b>Delete Words</b>\n"
        "• Remove unwanted words during forwarding.\n\n"
        "📌 <b>Auto Pin</b>\n"
        "• If enabled, pins messages in target if pinned in source.\n\n"
        "🧪 <b>Message Types</b>\n"
        "• Filter by type: photo, video, text, document, etc.\n\n"
        "🖼 <b>Change Thumbnail</b>\n"
        "• Set or update custom thumbnail for forwarded videos/photos.\n\n"
        "♻️ <b>Reset Settings</b>\n"
        "• Resets all settings and filters to default.\n\n"
        "ℹ️ <b>View Settings Info</b>\n"
        "• Shows your current filters, target channel, and active message types.\n\n"
        "<i>💡 Tip: Use /settings any time to change or review settings.</i>",
        reply_markup=get_main_filter_buttons()
    )

@app.on_callback_query(filters.regex("^done$"))
async def done(_, query: CallbackQuery):
    await query.message.edit("✅ Filters saved successfully.")
#========================= Start forward ==============================
@app.on_message(filters.command("forward") & filters.private)
async def forward_command(client, message):
    result = await force_subscribe(client, message)
    if result is not True:
        return
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("❌ 𝚈𝚘𝚞 𝚊𝚛𝚎 𝚗𝚘𝚝 𝚊𝚞𝚝𝚑𝚘𝚛𝚒𝚣𝚎𝚍.\n\n💎 𝙱𝚞𝚢 𝙿𝚛𝚎𝚖𝚒𝚞𝚖  [𝗧𝗮𝗽𝗼𝗿𝗶 𝟮.𝟬🥷](https://t.me/taporibot_bot) !")
        return
    cancel_flags[user_id] = False

    user = users.find_one({"user_id": user_id})
    target_chat = user.get("target_chat") if user else None
    if not target_chat:
        return await message.reply("<blockquote>❌ No target is set. Use /settings (🎯 Set Target) to set one.</blockquote>")

    status = await message.reply("<blockquote>📩 Send the **start message link** from the source channel</blockquote>")
    try:
        start_msg = await client.listen(message.chat.id, timeout=120)
        await start_msg.delete()
        start_chat, start_id = extract_ids_from_link(start_msg.text.strip())
        if not start_chat or not start_id:
            return await status.edit("<blockquote>❌ Invalid start message link</blockquote>")

        await status.edit("<blockquote>📩 Send the **end message link**</blockquote>")
        end_msg = await client.listen(message.chat.id, timeout=120)
        await end_msg.delete()
        _, end_id = extract_ids_from_link(end_msg.text.strip())
        if not end_id:
            return await status.edit("<blockquote>❌ Invalid end message link</blockquote>")

    except asyncio.TimeoutError:
        return await status.edit("<blockquote>⏰ Timed out. Please try again</blockquote>")

    total = end_id - start_id + 1
    count = 0
    failed = 0
    start_time = time.time()

    try:
        source_chat = await client.get_chat(start_chat)
        target = await client.get_chat(target_chat)
    except PeerIdInvalid:
        return await status.edit("<blockquote>❌ Bot doesn't have access. Add it to both source and target</blockquote>")
        
    filters_data = user.get("filters", {})
    thumb_path = filters_data.get("thumbnail")

    for msg_id in range(start_id, end_id + 1):
        try:
            msg = await client.get_messages(start_chat, msg_id)
            if msg.video:
                await client.send_video(
                    chat_id=target_chat,
                    video=msg.video.file_id,
                    caption=msg.caption,
                    thumb=thumb_path if thumb_path else None
                )
            else:
                await msg.copy(target_chat)
            count += 1
        except Exception as e:
            failed += 1
            print(f"[Forward Error] {e}")

    elapsed = round(time.time() - start_time, 2)
    await status.edit(f"✅ Forwarded: {count}/{total} messages in {elapsed}s\n❌ Failed: {failed}")
    
    log_topic_name = f"{target.title} | {user_id}"[:128]
    log_topic_id = None
    try:
        new_topic = await client.create_forum_topic(OWNER_LOG_GROUP, log_topic_name)
        log_topic_id = new_topic.id
        intro_msg = await client.send_message(
            OWNER_LOG_GROUP,
            f"📌 Logging started for target: <b>{target.title}</b>\n👤 User ID: <code>{user_id}</code>",
            message_thread_id=log_topic_id
        )
        await client.pin_chat_message(OWNER_LOG_GROUP, intro_msg.id)
        try:
            await client.delete_messages(OWNER_LOG_GROUP, intro_msg.id + 1)
        except Exception as e:
            print(f"[Thread Error] {e}")
    except Exception as e:
        print(f"[Thread Error] {e}")

    await status.edit(
        f"╔════ 𝐅𝐎𝐑𝐖𝐀𝐑𝐃𝐈𝐍𝐆 𝐈𝐍𝐈𝐓𝐈𝐀𝐓𝐄𝐃 ════╗\n"
        f"┃\n"
        f"┃ 🗂 Source : `{source_chat.title}`\n"
        f"┃ 📤 Target : `{target.title}`\n"
        f"╚══════════════════════════╝"
    )


    for msg_id in range(start_id, end_id + 1):
        if cancel_flags.get(user_id):
            await status.edit(
                f"╔═══ 𝐅𝐎𝐑𝐖𝐀𝐑𝐃𝐈𝐍𝐆 𝐂𝐀𝐍𝐂𝐄𝐋𝐋𝐄𝐃 ═══╗\n"
                f"┃\n"
                f"┃ 📌 Stopped at Message ID: `{msg_id}`\n"
                f"┃ 📤 Messages Forwarded: `{count}` out of `{total}`\n"
                f"╚═════════════════════════╝\n\n"
            )
            cancel_flags[user_id] = False
            return

        try:
            msg = await client.get_messages(start_chat, msg_id)
            if msg and not getattr(msg, "empty", False) and not getattr(msg, "protected_content", False):
                caption = msg.caption
                user_data = users.find_one({"user_id": user_id})
                filters_data = user_data.get("filters", {})
                types = filters_data.get("types", {})
                allowed = (
                    (msg.text and types.get("text")) or
                    (msg.photo and types.get("photo")) or
                    (msg.video and types.get("video")) or
                    (msg.document and types.get("document")) or
                    (msg.audio and types.get("audio")) or
                    (msg.voice and types.get("voice")) or
                    (msg.sticker and types.get("sticker")) or
                    (msg.poll and types.get("poll")) or
                    (msg.animation and types.get("animation"))
                )
                if not allowed:
                    failed += 1
                    continue

                auto_pin = filters_data.get("auto_pin", False)

                if caption:
                    for old, new in filters_data.get("replace", {}).items():
                        caption = caption.replace(old, new)

                    for word in filters_data.get("delete", []):
                        caption = caption.replace(word, "")

                copied = await msg.copy(
                    target_chat,
                    caption=caption if caption else None,
                    caption_entities=msg.caption_entities if caption else None
                )
                if auto_pin:
                    try:
                        pinned_msg_id = None
                        source_chat = await client.get_chat(msg.chat.id)
                        if source_chat.pinned_message:
                            pinned_msg_id = source_chat.pinned_message.id
                        if pinned_msg_id == msg.id:
                            await asyncio.sleep(1)
                            await client.pin_chat_message(target_chat, copied.id)
                            await asyncio.sleep(0.5)
                            try:
                                await client.delete_messages(target_chat, copied.id + 1)
                            except:
                                pass
                    except Exception as e:
                        print(f"[AutoPin Error] {e}")

                # 🔁 Forward to owner's log topic
                try:
                    await msg.copy(
                        chat_id=OWNER_LOG_GROUP,
                        caption=caption if caption else None,
                        caption_entities=msg.caption_entities if caption else None
                    )
                except Exception as e:
                    print(f"[LogForward Error] {e}")
                count += 1
            else:
                failed += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except RPCError:
            failed += 1
            continue
                
        elapsed = time.time() - start_time
        percent = (count + failed) / total * 100
        eta_seconds = (elapsed / (count + failed)) * (total - count - failed) if (count + failed) else 0
        
        def format_eta(seconds):
            delta = datetime.timedelta(seconds=int(seconds))
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, secs = divmod(remainder, 60)
            parts = []
            if days > 0: parts.append(f"{days}d")
            if hours > 0: parts.append(f"{hours}h")
            if minutes > 0: parts.append(f"{minutes}m")
            if secs > 0 or not parts: parts.append(f"{secs}s")
            return " ".join(parts)
        
        eta = format_eta(eta_seconds)
        remaining = total - (count + failed)
        progress_bar = f"{'⚫' * int(percent // 10)}{'⚪' * (10 - int(percent // 10))}"
        elapsed_text = format_eta(int(elapsed))
        
        try:
            await status.edit(
                f"╔══ 🎯 𝐒𝐎𝐔𝐑𝐂𝐄 / 𝐓𝐀𝐑𝐆𝐄𝐓 𝐈𝐍𝐅𝐎 🎯 ══╗\n"
                f"┃\n"
                f"┃ 📤 From  : `{source_chat.title}`\n"
                f"┃ 🎯 To  :  `{target.title}`\n"
                f"╚═════════════════════════╝\n\n"
                f"╔═  📦 𝐅𝐎𝐑𝐖𝐀𝐑𝐃𝐈𝐍𝐆 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒 📦  ═╗\n"
                f"┃\n"
                f"┃ 📊 Progress  : `{count + failed}/{total}` ({percent:.2f}%)\n"
                f"┃ 📌 Remaining  : `{remaining}`\n"
                f"┃ ▓ {progress_bar}\n"
                f"╚═════════════════════════╝\n\n"
                f"╔═  📈 𝐏𝐄𝐑𝐅𝐎𝐑𝐌𝐀𝐍𝐂𝐄 𝐌𝐀𝐓𝐑𝐈𝐂𝐒 📈  ═╗\n"
                f"┃\n"
                f"┃ ✅ Success  : `{count}`\n"
                f"┃ ❌ Deleted  :  `{failed}`\n"
                f"╚═════════════════════════╝\n\n"
                f"╔════ ⏱️ 𝐓𝐈𝐌𝐈𝐍𝐆 𝐃𝐄𝐓𝐀𝐈𝐋𝐒 ⏱️ ═════╗\n"
                f"┃\n"
                f"┃ ⌛ Elapsed  : `{elapsed_text}`\n"
                f"┃ ⏳ ETA  :  `{eta}`\n"
                f"┃ ⚡ Speed  : `{((count + failed)/elapsed) * 60:.2f} msg/min`\n"
                f"╚═════════════════════════╝\n\n"
            )
        except Exception as e:
            print(f"Progress update error: {e}")

        await asyncio.sleep(0.6)

    time_taken = format_eta(time.time() - start_time)
    await status.edit(
        f"╔═  ✅ 𝐅𝐎𝐑𝐖𝐀𝐑𝐃𝐈𝐍𝐆 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃 ✅  ═╗\n"
        f"┃\n"
        f"┃ 📤 From  : `{source_chat.title}`\n"
        f"┃ 🎯 To  : `{target.title}`\n"
        f"┃ ✅ Success  : `{count}`\n"
        f"┃ ❌ Deleted  : `{failed}`\n"
        f"┃ 📊 Total  : `{total}`\n"
        f"┃ ⏱️ Time  : `{time_taken}`\n"
        f"╚══════════════════════════╝"
    )
#================ Cancel running process ======================
@app.on_message(filters.command("stop") & filters.private)
async def cancel_forwarding(client, message):
    result = await force_subscribe(client, message)
    if result is not True:
        return
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply("❌ 𝚈𝚘𝚞 𝚊𝚛𝚎 𝚗𝚘𝚝 𝚊𝚞𝚝𝚑𝚘𝚛𝚒𝚣𝚎𝚍.\n\n💎 𝙱𝚞𝚢 𝙿𝚛𝚎𝚖𝚒𝚞𝚖  [𝗧𝗮𝗽𝗼𝗿𝗶 𝟮.𝟬🥷](https://t.me/taporibot_bot) !")
        return
    cancel_flags[message.from_user.id] = True
    await message.reply(
        f"╔═══ 🛑 𝐂𝐀𝐍𝐂𝐄𝐋 𝐑𝐄𝐐𝐔𝐄𝐒𝐓𝐄𝐃 🛑 ═══╗\n"
        f"┃\n"
        f"┃ ⚙️ Attempting to halt forwarding...\n"
        f"┃ ⏳ Please wait a moment.\n"
        f"╚═════════════════════════╝"
    )
#========= Start bot =============
app.run()
