import asyncio
import random
import json
import os
import warnings
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

warnings.filterwarnings("ignore")

# --- SOZLAMALAR ---
API_TOKEN = '8646139362:AAE7XOAWYM6C_T44JW_0ovFY5GwU41pwRiE'
ADMIN_ID = 5157985294 
ADMIN_USERNAME = "@inferno_zzz"
CHANNEL_ID = "@auraCCC7"
DATA_FILE = "data.json"

main_bot = Bot(token=API_TOKEN)
main_dp = Dispatcher()

# --- 📁 MA'LUMOTLARNI SAQLASH VA YUKLASH ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {"bots": {}}
    return {"bots": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Baza yuklanadi
db = load_data()

class QuizState(StatesGroup):
    waiting_question = State()
    waiting_options = State()
    waiting_correct = State()

# --- 🛠 MIJOZNING QUIZ BOT LOGIKASI (BOLA BOT) ---
async def run_quiz_bot(token):
    try:
        q_bot = Bot(token=token)
        q_dp = Dispatcher()
        
        # Agar token bazada bo'lmasa, yangi joy ochamiz
        if token not in db["bots"]:
            db["bots"][token] = []
            save_data(db)

        def q_bot_kb():
            return ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="➕ Test tuzish")],
                [KeyboardButton(text="🚀 Testni boshlash (Guruhda)")],
                [KeyboardButton(text="➕ Guruhga qo'shish")]
            ], resize_keyboard=True)

        @q_dp.message(Command("start"))
        async def q_start(message: types.Message):
            if message.chat.type == "private":
                await message.answer("👋 Xush kelibsiz! Test tuzishni boshlash uchun tugmani bosing.", reply_markup=q_bot_kb())
            else:
                await message.answer("🤖 Bot guruhda tayyor! /test buyrug'ini yuboring.")

        @q_dp.message(F.text == "➕ Test tuzish")
        async def start_make(message: types.Message, state: FSMContext):
            await message.answer("❓ Savolni yuboring:")
            await state.set_state(QuizState.waiting_question)

        @q_dp.message(QuizState.waiting_question)
        async def get_q(message: types.Message, state: FSMContext):
            await state.update_data(question=message.text)
            await message.answer("📝 Variantlarni vergul bilan ajratib yuboring (Masalan: A, B, C):")
            await state.set_state(QuizState.waiting_options)

        @q_dp.message(QuizState.waiting_options)
        async def get_opts(message: types.Message, state: FSMContext):
            options = [o.strip() for o in message.text.split(',')]
            await state.update_data(options=options)
            buttons = [[InlineKeyboardButton(text=opt, callback_data=f"correct_{i}")] for i, opt in enumerate(options)]
            await message.answer("✅ To'g'ri javobni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            await state.set_state(QuizState.waiting_correct)

        @q_dp.callback_query(F.data.startswith("correct_"))
        async def save_test(call: types.CallbackQuery, state: FSMContext):
            correct_id = int(call.data.split('_')[1])
            data = await state.get_data()
            
            # MA'LUMOTNI BAZAGA QO'SHISH
            db["bots"][token].append({'q': data['question'], 'options': data['options'], 'correct': correct_id})
            save_data(db) # FAYLGA YOZISH
            
            await call.message.answer(f"✅ Saqlandi! Jami: {len(db['bots'][token])}", reply_markup=q_bot_kb())
            await state.clear()
            await call.answer()

        @q_dp.message(F.text == "🚀 Testni boshlash (Guruhda)")
        @q_dp.message(Command("test"))
        async def launch_quiz(message: types.Message):
            tests = db["bots"].get(token, [])
            if not tests: return await message.answer("❌ Testlar yuklanmagan!")
            
            temp_tests = list(tests)
            random.shuffle(temp_tests)
            for t in temp_tests:
                try:
                    await q_bot.send_poll(message.chat.id, t['q'], t['options'], t['correct'], type="quiz", is_anonymous=False)
                    await asyncio.sleep(2)
                except: continue

        await q_dp.start_polling(q_bot)
    except: pass

# --- 🏠 ASOSIY BOT LOGIKASI ---

async def is_member(user_id):
    try:
        m = await main_bot.get_chat_member(CHANNEL_ID, user_id)
        return m.status in ["creator", "administrator", "member"]
    except: return False

@main_dp.message(Command("start"))
async def start_main(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🛠 Xizmatlar")], [KeyboardButton(text="👨‍💻 Admin")]], resize_keyboard=True)
    if await is_member(message.from_user.id):
        await message.answer("Assalomu alaykum! Xush kelibsiz!", reply_markup=kb)
    else:
        sub_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna", url=f"https://t.me/{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_sub")]
        ])
        await message.answer("❌ Botdan foydalanish uchun kanalimizga a'zo bo'ling!", reply_markup=sub_kb)

@main_dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await is_member(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Xush kelibsiz!", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🛠 Xizmatlar")], [KeyboardButton(text="👨‍💻 Admin")]], resize_keyboard=True))
    else: await call.answer("⚠️ Hali a'zo emassiz!", show_alert=True)

@main_dp.message(F.text == "🛠 Xizmatlar")
async def serv(message: types.Message):
    if not await is_member(message.from_user.id): return
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📝 Mustaqil ish tayyorlash")],
        [KeyboardButton(text="📢 Kanal va guruh boshqarish")],
        [KeyboardButton(text="🤖 Bot yaratish"), KeyboardButton(text="⬅️ Orqaga")]
    ], resize_keyboard=True)
    await message.answer("Xizmatni tanlang:", reply_markup=kb)

@main_dp.message(F.text == "🤖 Bot yaratish")
async def bot_t(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 Quiz Bot (25 000)")], [KeyboardButton(text="⬅️ Orqaga")]], resize_keyboard=True)
    await message.answer("🤖 Bot turini tanlang:", reply_markup=kb)

@main_dp.message(F.text.contains("Quiz Bot"))
async def q_order(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ To'lov qildim", callback_data=f"pay_{message.from_user.id}")]])
    await message.answer(f"💳 Narxi: 25 000 so'm.\nAdmin: {ADMIN_USERNAME}\nTo'lovdan so'ng tugmani bosing.", reply_markup=kb)

@main_dp.callback_query(F.data.startswith("pay_"))
async def pay_notify(call: types.CallbackQuery):
    uid = call.data.split('_')[1]
    photos = await main_bot.get_user_profile_photos(call.from_user.id, limit=1)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ok_{uid}")]])
    info = f"💰 **To'lov!**\n👤: {call.from_user.full_name}\n🆔: `{uid}`"
    
    if photos.total_count > 0:
        await main_bot.send_photo(ADMIN_ID, photos.photos[0][-1].file_id, caption=info, reply_markup=kb)
    else:
        await main_bot.send_message(ADMIN_ID, info, reply_markup=kb)
    await call.message.answer("⌛ To'lov tekshirilmoqda...")
    await call.answer()

@main_dp.callback_query(F.data.startswith("ok_"))
async def ok_confirm(call: types.CallbackQuery):
    uid = int(call.data.split('_')[1])
    await main_bot.send_message(uid, "✅ Tasdiqlandi! API Tokenni yuboring:")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()

@main_dp.message(F.text.contains(":"))
async def run_bot_start(message: types.Message):
    if not await is_member(message.from_user.id): return
    token = message.text.strip()
    await message.answer("🚀 Botingiz ishga tushmoqda...")
    asyncio.create_task(run_quiz_bot(token))

@main_dp.message(F.text == "⬅️ Orqaga")
async def back(message: types.Message):
    await message.answer("Bosh menyu", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🛠 Xizmatlar")], [KeyboardButton(text="👨‍💻 Admin")]], resize_keyboard=True))

@main_dp.message(F.text == "👨‍💻 Admin")
async def adm(message: types.Message):
    await message.answer(f"👨‍💻 Admin: {ADMIN_USERNAME}")

# --- 🚀 ASOSIY ISHGA TUSHIRISH ---
async def main():
    # Baza ichidagi barcha botlarni qayta yoqish
    for token in db["bots"].keys():
        if ":" in token:
            asyncio.create_task(run_quiz_bot(token))
            
    await main_dp.start_polling(main_bot)

if __name__ == '__main__':
    asyncio.run(main())0:52 29.03.2026