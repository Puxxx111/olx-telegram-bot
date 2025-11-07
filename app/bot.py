from __future__ import annotations

import asyncio
from typing import Dict, Optional
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery, BotCommand

# Support running both as module (python -m app.bot) and as script (python app/bot.py)
try:
    from .config import load_config
    from .filters_storage import FiltersStorage
    from .seen_storage import SeenStorage
    from .keyboards import main_menu, filters_menu, filters_delete_menu, tracking_choice_menu, tracking_start_menu
    from .parser import OlxAd
    from .tracker import Tracker
except Exception:  # noqa: E722
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from app.config import load_config
    from app.filters_storage import FiltersStorage
    from app.seen_storage import SeenStorage
    from app.keyboards import main_menu, filters_menu, filters_delete_menu, tracking_choice_menu, tracking_start_menu
    from app.parser import OlxAd
    from app.tracker import Tracker


class AppState:
    def __init__(self, filters_file: str, seen_file: str):
        self.filters = FiltersStorage(filters_file)
        self.seen = SeenStorage(seen_file)
        # parallel trackers per chat (limit globally)
        self.active_trackers: dict[int, Tracker] = {}
        self.active_filters: dict[int, str] = {}
        self.max_parallel: int = 3
        # simple per-chat create filter state
        self.awaiting_name: set[int] = set()
        self.awaiting_url_for_name: dict[int, str] = {}


def format_ad_caption(ad: OlxAd) -> str:
    parts = [
        f"📌 <b>{escape_html(ad.title)}</b>",
        f"💵 <b>Ціна:</b> {escape_html(ad.price)}",
        f"🧭<b>Локація/дата:</b> {escape_html(ad.location_date)}",
    ]
    if ad.size:
        parts.append(f"📐 <b>Площа:</b> {escape_html(ad.size)}")
    parts.append(f"🔗 <a href=\"{ad.url}\">Відкрити оголошення</a>")
    return "\n".join(parts)


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "<")
        .replace(">", ">")
    )


async def send_help(message: Message):
    help_text = """
<b>📚 Інструкція з використання бота:</b>

<b>Основні команди:</b>
/start - Запустити бота
/help - Показати це повідомлення

<b>Робота з фільтрами:</b>
1️⃣ <b>Створення фільтра:</b>
   • Натисніть "🗃️ Мої фільтри"
   • Виберіть "💾 Створити фільтр"
   • Введіть назву фільтра Наприклад "Київ-оренда"
   • Вставте посилання з OLX з налаштованими параметрами пошуку

2️⃣ <b>Відстеження оголошень:</b>
   • Натисніть "📡 Відстежити фільтр"
   • Виберіть створений фільтр
   • Натисніть "▶️ Запустити!"

3️⃣ <b>Керування фільтрами:</b>
   • Перегляд - "Мої фільтри"
   • Видалення - кнопка "Видалити" в меню фільтрів

❗️ <b>Важливо:</b>
• Можна відстежувати до 3 фільтрів одночасно
• Для зупинки відстеження натисніть "⏹ Зупинити!"
• Бот перевіряє нові оголошення кожну хвилину

🤗 Якщо бот вам сподобався і став у нагоді, ₿ підтримайте автора 🇺🇦\n
🟣 <b>ETH:</b> <code>0xf4acece1ac6270cad690c8b0edfccccf640290ab</code>\n
🔵 <b>TON:</b> <code>UQBdwmdnD9jx9h_SaOUrcEV-89G3o9RR16TPG_7WYyQ0jopu</code>\n
📧 <code>corvi11@proton.me</code>
"""
    await message.answer(help_text)
    logging.info("Help command used by chat %s", message.chat.id)


async def run_bot():
    # logging setup
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.info("Starting OLX bot...")

    cfg = load_config()
    bot = Bot(token=cfg.bot_token,
              default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    state = AppState(filters_file=cfg.filters_file, seen_file=cfg.seen_file)

    # Регистрация команд бота
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Показать инструкцию")
    ])

    @dp.message(CommandStart())
    async def start(message: Message):
        logging.info("Bot started. Chat %s used /start", message.chat.id)
        is_running = message.chat.id in state.active_trackers and state.active_trackers[message.chat.id].is_running(
        )
        await message.answer(
            "Привіт 🤗! Я бот для відстеження оголошень OLX. Виберіть дію:",
            reply_markup=main_menu(tracking_running=is_running),
        )

    @dp.message(F.text == "🗃️ Мої фiльтри")
    async def show_filters(message: Message):
        names = state.filters.list_names()
        logging.info("Show filters to chat %s", message.chat.id)
        await message.answer(
            "Ваші фільтри:",
            reply_markup=filters_menu(names),
        )

    @dp.callback_query(F.data.startswith("filter:"))
    async def filters_click(callback: CallbackQuery):
        name = callback.data.split(":", 1)[1]
        url = state.filters.read().get(name, "")
        if url:
            await callback.message.answer(f"<b>{escape_html(name)}</b>\n{escape_html(url)}")
        logging.info("Filter clicked: %s (chat %s)",
                     name, callback.message.chat.id)
        await callback.answer()

    @dp.callback_query(F.data == "filters:create")
    async def filters_create(callback: CallbackQuery):
        chat_id = callback.message.chat.id
        state.awaiting_name.add(chat_id)
        state.awaiting_url_for_name.pop(chat_id, None)
        await callback.message.answer("Введіть назву фільтра (наприклад, Київ_квартири):")
        logging.info("Create filter initiated by chat %s", chat_id)
        await callback.answer()

    @dp.message(lambda m: m.chat.id in state.awaiting_name)
    async def receive_filter_name(message: Message):
        chat_id = message.chat.id
        text = (message.text or "").strip()
        if not text:
            await message.answer("Назва не може бути пустою. Спробуйте ще раз.")
            return
        state.awaiting_name.discard(chat_id)
        state.awaiting_url_for_name[chat_id] = text
        await message.answer("Надішліть посилання OLX з налаштованими параметрами пошуку:")
        logging.info("Filter name received from chat %s: %s", chat_id, text)

    @dp.message(lambda m: m.chat.id in state.awaiting_url_for_name)
    async def receive_filter_url(message: Message):
        chat_id = message.chat.id
        text = (message.text or "").strip()
        name = state.awaiting_url_for_name[chat_id]
        url = text
        if not (url.startswith("http://") or url.startswith("https://")):
            await message.answer("Потрібно коректне посилання (http/https). Спробуйте ще раз або /start")
            return
        state.awaiting_url_for_name.pop(chat_id, None)
        state.filters.upsert(name, url)
        await message.answer(f"✅ Збережено фільтр <b>{escape_html(name)}</b>")
        await message.answer("Ваші фільтри:", reply_markup=filters_menu(state.filters.list_names()))
        logging.info("Filter saved (chat %s): %s -> %s", chat_id, name, url)

    @dp.callback_query(F.data == "filters:delete")
    async def filters_delete(callback: CallbackQuery):
        names = state.filters.list_names()
        await callback.message.answer("Оберіть фільтр для видалення:", reply_markup=filters_delete_menu(names))
        await callback.answer()

    @dp.callback_query(F.data.startswith("filters:delete:"))
    async def filters_do_delete(callback: CallbackQuery):
        name = callback.data.split(":", 2)[2]
        existed = state.filters.delete(name)
        if existed:
            await callback.message.answer(f"🗑 Видалено фільтр <b>{escape_html(name)}</b>")
        else:
            await callback.message.answer("Не знайдено такого фільтра")
        await callback.answer()

    @dp.message(F.text == "Отследить объявления")
    @dp.message(F.text == "📡 Відстежити фільтр")
    @dp.message(F.text.regexp(r"(?i)отследить"))
    @dp.message(F.text == "/track")
    async def track_choose(message: Message):
        names = state.filters.list_names()
        if names:
            await message.answer("Оберіть фільтр для відстеження нових оголошень:", reply_markup=tracking_choice_menu(names))
            logging.info(
                "Tracking menu shown to chat %s with %d filters", message.chat.id, len(names))
        else:
            await message.answer("Фільтрів ще немає. Створити новий?", reply_markup=tracking_choice_menu(names))
            logging.info(
                "No filters available for chat %s; suggested creating one", message.chat.id)

    @dp.callback_query(F.data.startswith("track:"))
    async def track_callbacks(callback: CallbackQuery):
        parts = callback.data.split(":")
        if parts[1] == "start":
            filter_name = parts[2]
            url = state.filters.read().get(filter_name)
            if not url:
                await callback.message.answer("Фільтр не знайдено")
                await callback.answer()
                return

            chat_id = callback.message.chat.id
            if chat_id not in state.active_trackers and len(state.active_trackers) >= state.max_parallel:
                await callback.message.answer("🚦 Перевищено ліміт одночасних відстежень. Спробуйте пізніше або зупиніть інше відстеження.")
                await callback.answer()
                return

            if chat_id in state.active_trackers and state.active_trackers[chat_id].is_running():
                await state.active_trackers[chat_id].stop()

            tracker = Tracker(interval_sec=60)
            state.active_trackers[chat_id] = tracker
            state.active_filters[chat_id] = filter_name
            logging.info("Tracking started for chat %s, filter '%s' -> %s",
                         callback.message.chat.id, filter_name, url)

            async def on_new_ads(ads: list[OlxAd]):
                ad_ids = {a.ad_id for a in ads}
                new_ids = state.seen.unseen_only(filter_name, ad_ids)
                new_ads = [a for a in ads if a.ad_id in new_ids]
                if not new_ads:
                    logging.info("No new ads for chat %s, filter '%s'",
                                 callback.message.chat.id, filter_name)
                    return None
                state.seen.add_many(filter_name, new_ids)
                logging.info("Found %d new ads for chat %s, filter '%s'", len(
                    new_ads), callback.message.chat.id, filter_name)
                for ad in new_ads:
                    caption = format_ad_caption(ad)
                    try:
                        if ad.image_url:
                            await callback.message.answer_photo(photo=ad.image_url, caption=caption)
                        else:
                            await callback.message.answer(caption)
                    except Exception:
                        await callback.message.answer(caption)
                logging.info("Sent %d new ads to chat %s", len(
                    new_ads), callback.message.chat.id)
                await callback.message.answer(
                    f"""Відстеження запущено для <b>{escape_html(filter_name)}</b>

    🤗 Якщо бот вам сподобався і став у нагоді, ₿ підтримайте автора 🇺🇦\n
    🟣 <b>ETH:</b> <code>0xf4acece1ac6270cad690c8b0edfccccf640290ab</code>\n
    🔵 <b>TON:</b> <code>UQBdwmdnD9jx9h_SaOUrcEV-89G3o9RR16TPG_7WYyQ0jopu</code>\n
    📧 <code>corvi11@proton.me</code>
    """,
                    reply_markup=main_menu(tracking_running=True),
                )

            await tracker.start(url, on_new_ads)

            await callback.message.answer(
                f"Відстеження запущено для <b>{escape_html(filter_name)}</b>",
                reply_markup=main_menu(tracking_running=True),
                parse_mode="HTML"
            )
            await callback.answer("Старт")
        else:
            filter_name = parts[1]
            state.active_filters[callback.message.chat.id] = filter_name
            await callback.message.answer(
                f"Фільтр: <b>{escape_html(filter_name)}</b>",
                reply_markup=tracking_start_menu(filter_name),
            )
            await callback.answer()

    @dp.message(F.text == "⏹ Зупинити!")
    async def stop_tracking(message: Message):
        chat_id = message.chat.id
        tracker = state.active_trackers.get(chat_id)
        if tracker and tracker.is_running():
            await tracker.stop()
            state.active_trackers.pop(chat_id, None)
            state.active_filters.pop(chat_id, None)
            await message.answer("⏹ Зупинено відстеження", reply_markup=main_menu(tracking_running=False))
            logging.info("Tracking stopped for chat %s", chat_id)
        else:
            await message.answer("Зараз нічого не відстежується", reply_markup=main_menu(tracking_running=False))
            logging.info(
                "Stop requested but nothing running for chat %s", message.chat.id)

    # === ИСПРАВЛЕННЫЕ ОБРАБОТЧИКИ ДЛЯ /help ===
    @dp.message(Command(commands=["help"]))
    async def help_command(message: Message):
        await send_help(message)

    @dp.message(F.text == "/help")
    async def help_text_fallback(message: Message):
        await send_help(message)
    # ==========================================

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
