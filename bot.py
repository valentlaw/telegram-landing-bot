import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, SUPPORT_USERNAME, ADMIN_IDS
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()

class ProblemReport(StatesGroup):
    waiting_for_text = State()

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Роспись", callback_data="category_роспись")],
        [InlineKeyboardButton(text="📚 Обучение", callback_data="category_обучение")],
        [InlineKeyboardButton(text="📦 Шаблоны/Гайды", callback_data="category_шаблоны")],
        [InlineKeyboardButton(text="🔧 Другое", callback_data="category_другое")],
        [InlineKeyboardButton(text="📢 Сообщить о проблеме", callback_data="report_problem")],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="support")]
    ])
    return keyboard

def get_buy_keyboard(category: str):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить за Stars", callback_data=f"buy_stars_{category}")],
        [InlineKeyboardButton(text="👤 Связаться с продавцом", url=f"https://t.me/{SUPPORT_USERNAME}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await db.add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "👋 Добро пожаловать!\n\nВыберите категорию услуг:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "👋 Добро пожаловать!\n\nВыберите категорию услуг:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("category_"))
async def show_category(callback: CallbackQuery):
    category = callback.data.replace("category_", "")
    category_names = {
        "роспись": "🎨 Роспись",
        "обучение": "📚 Обучение",
        "шаблоны": "📦 Шаблоны/Гайды",
        "другое": "🔧 Другое"
    }
    
    category_info = await db.get_category_info(category)
    
    text = f"*{category_names.get(category, category)}*\n\n"
    if category_info:
        text += f"{category_info['description']}\n\n"
        text += f"💰 Цена: {category_info['price']} Stars"
    else:
        text += "Информация о категории временно недоступна.\nСвяжитесь с нами для получения деталей."
    
    await callback.message.edit_text(
        text,
        reply_markup=get_buy_keyboard(category),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_stars_"))
async def buy_with_stars(callback: CallbackQuery):
    category = callback.data.replace("buy_stars_", "")
    category_info = await db.get_category_info(category)
    
    if not category_info:
        await callback.answer("Информация о категории недоступна", show_alert=True)
        return
    
    price = category_info.get("price", 100)
    
    await callback.answer()
    await callback.message.answer(
        f"💎 Оплата за '{category}'\n\n"
        f"Сумма: {price} Stars\n\n"
        f"После оплаты свяжитесь с @{SUPPORT_USERNAME} для получения услуги."
    )

@dp.callback_query(F.data == "report_problem")
async def report_problem(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📢 Опишите проблему:\n\nНапишите текст сообщения или отправьте /cancel для отмены."
    )
    await state.set_state(ProblemReport.waiting_for_text)
    await callback.answer()

@dp.message(ProblemReport.waiting_for_text)
async def process_problem_report(message: types.Message, state: FSMContext):
    await db.add_problem_report(message.from_user.id, message.text)
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🚨 *Новое сообщение о проблеме*\n\n"
                f"От: @{message.from_user.username or message.from_user.id}\n"
                f"Текст: {message.text}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send to admin {admin_id}: {e}")
    
    await message.answer(
        "✅ Сообщение отправлено! Мы свяжемся с вами в ближайшее время.",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await callback.message.edit_text(
        f"💬 Поддержка\n\nСвяжитесь с нами: @{SUPPORT_USERNAME}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
            [InlineKeyboardButton(text="💬 Написать", url=f"https://t.me/{SUPPORT_USERNAME}")]
        ])
    )
    await callback.answer()

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_keyboard()
    )

async def main():
    await db.init()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
