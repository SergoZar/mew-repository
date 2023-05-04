#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.types import ParseMode, ContentType

import links_manager
import logging
import textwrap
import re
from pylingva import pylingva
trans = pylingva()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
with open("token", "r", encoding="utf-8") as f:
    bot = Bot(token=f.read().strip())
dp = Dispatcher(bot)


async def edit(text):
    tr = trans.translate('auto', 'en', text)
    links = await links_manager.get_links()
    links = ' | '.join([f"[{link[1]}]({link[0]})" for link in links])
    return f"""
{text}
---
{tr}
---
{links}"""


@dp.channel_post_handler(content_types=ContentType.all())
@dp.edited_channel_post_handler(content_types=ContentType.all())
async def edit_message(message: types.Message):
    try:
        msg = message.text.split("\n---")[0]
        await message.edit_text(
            await edit(msg),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    except:
        media = (
            message.audio or
            message.animation or
            message.document or
            (message.photo[-1] if message.photo else None) or
            message.video
        )
        if message.caption:
            msg = message.caption.split("\n---")[0]
            media = types.InputMedia(
                media=media.file_id,
                type=await message.content_type,
                caption=await edit(msg),
                parse_mode=ParseMode.MARKDOWN
            )
            await message.edit_media(media)



async def list_links(message,text=""):
    text += "\n"
    links = await links_manager.get_links(True)
    for i, data in links:
        text += f"`**{i}**. {data[0]} {data[1]}`\n"
    if not links:
        await message.answer("Список посилань порожній",parse_mode=ParseMode.MARKDOWN)
        return
    await message.answer(text.strip(),parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(
    commands=['fuck']
    # filters.builtin.IDFilter(user_id=), commands=['fuck']
)
async def set_data(message: types.Message):
    msg = message.text.replace("/fuck", "").strip().replace("—","--")
    # msg =  --add https://a.com my link text"
    add_ = re.search("^--add (\S+) (.+)$", msg)
    # msg =  --mov 5 2"
    mov_ = re.search("^--mov (\d+) (\d+)$", msg)
    # msg =  --upd 1 https://dgg.gg ddg link"
    upd_ = re.search("^--upd (\d+) (\S+) (.+)$", msg)
    # msg =  --del 5"
    # msg =  --del all"
    del_ = re.search("^--del (\d+|all)", msg)
    links = await links_manager.get_links(True)
    if msg[:6] == "--help" or msg == "":
        await message.answer(textwrap.dedent("""
            `--help` - інфа
            `--list` - список усіх посилань
            `--add url text` - додати
            `--mov id1 id2` - поміняти місцями
            `--upd id url text` - змінити
            `--del id/all` - видалити по id або всі(all)
            """), 
            parse_mode=ParseMode.MARKDOWN, 
            disable_web_page_preview=True
        )
    if msg[:6] == "--list":
        await list_links(message, "Список посилань:")
    if add_:
        link = add_[1]
        text = add_[2].strip()
        await links_manager.add_link(link, text)
        await list_links(message, "Оновлений список посилань:")
    if mov_:
        id1 = int(mov_[1])
        id2 = int(mov_[2])
        if len(links)-1 < id1 or len(links)-1 < id2 or id1 < 0 or id2 < 0:
            await message.answer(f"id {id1} або id {id2} нема")
            return
        await links_manager.mov_links(id1, id2)
        await list_links(message, "Оновлений список посилань:")
    if upd_:
        id_ = int(upd_[1])
        if len(links)-1 < id_ or id_ < 0:
            await message.answer(f"id {id_} нема")
            return
        link = upd_[2]
        text = upd_[3].strip()
        await links_manager.upd_link(id_, link, text)
        await list_links(message, "Оновлений список посилань:")
    if del_:
        try:
            id_ = int(del_[1])
            if len(links)-1 < id_ or id_ < 0:
                await message.answer(f"id {id_} нема")
                return
            await links_manager.del_link(id_)
        except:
            await links_manager.del_link(id_, True)
        await list_links(message, "Оновлений список посилань:")
        
        

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
