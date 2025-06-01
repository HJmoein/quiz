import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

QUESTIONS = [
    {
        "question": "در کدام یک از ترکیبات زیر، اتم مرکزی دارای بیشترین تعداد جفت‌الکترون ناپیوندی است؟",
        "options": ["NH3", "H2O", "SF6", "XeF4"],
        "answer": 3  # XeF4 (2 جفت ناپیوندی روی Xe)
    },
    {
        "question": "در واکنش زیر، چند مول الکترون منتقل می‌شود؟\n\nCr2O7^2- + 14H^+ + 6I^- → 2Cr^3+ + 7H2O + 3I2",
        "options": ["3", "6", "12", "18"],
        "answer": 2  # 6e- برای هر Cr2O7^2-، در کل 12e-
    },
    {
        "question": "کدام از ایزوتوپ‌های زیر بیشترین پایداری هسته‌ای را دارد؟",
        "options": ["U-235", "C-14", "Fe-56", "Pb-210"],
        "answer": 2  # Fe-56 پایدارترین هسته
    },
    {
        "question": "در کدام یک از موارد زیر، پیوند یونی برقرار است؟",
        "options": ["H2O", "NaCl", "CO2", "NH4Cl"],
        "answer": 1  # NaCl
    },
    {
        "question": "کدام عامل بیشترین تأثیر را در افزایش شعاع یونی یون Al^3+ نسبت به یون Mg^2+ دارد؟",
        "options": ["بار هسته", "سطح انرژی", "پیکربندی الکترونی", "نیروی دافعه الکترون‌ها"],
        "answer": 2  # پیکربندی الکترونی (Al^3+ و Mg^2+ ایزوالکترون‌اند ولی بار موثر فرق دارد)
    },
    {
        "question": "در واکنش تعادل زیر، افزایش دما چه اثری بر مقدار تعادلی NH3 دارد؟\nN2(g) + 3H2(g) ⇄ 2NH3(g) ΔH = -92 kJ/mol",
        "options": ["افزایش می‌یابد", "کاهش می‌یابد", "تغییری نمی‌کند", "ابتدا کاهش سپس افزایش"],
        "answer": 1  # واکنش گرمازا → افزایش دما تعادل را به سمت واکنش‌دهنده می‌برد
    },
    {
        "question": "کدام یک از ترکیبات زیر دارای بیشترین انرژی شبکه یونی است؟",
        "options": ["NaCl", "MgO", "KBr", "CaF2"],
        "answer": 1  # MgO به علت بار بیشتر و اندازه کوچکتر یون‌ها
    },
    {
        "question": "کدام یک از ترکیبات زیر آروماتیک نیست؟",
        "options": ["بنزن", "نفتالین", "سیکلوهگزن", "فوران"],
        "answer": 2  # سیکلوهگزن آروماتیک نیست
    },
    {
        "question": "در ساختار مولکولی SF4، زاویه پیوند F-S-F تقریباً چند درجه است؟",
        "options": ["90", "104.5", "120", "102"],
        "answer": 3  # ساختار تابیده (see-saw) زاویه حدود 102 دارد
    },
    {
        "question": "در محلول بافر CH3COOH و CH3COONa، افزودن مقدار کمی HCl چه اثری دارد؟",
        "options": [
            "pH به طور قابل توجهی کاهش می‌یابد",
            "pH تقریباً ثابت می‌ماند",
            "pH به طور قابل توجهی افزایش می‌یابد",
            "محلول کاملاً اسیدی می‌شود"
        ],
        "answer": 1  # pH تقریباً ثابت می‌ماند
    }
]
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # اگر قبلاً شرکت کرده باشد اجازه شروع ندارد
    if user_data.get(user_id, {}).get("participated", False):
        await update.message.reply_text("شما قبلاً در این آزمون شرکت کرده‌اید و فقط یک بار می‌توانید شرکت کنید")
        return
    user_data[user_id] = {
        "score": 0,
        "q_index": 0,
        "waiting_ready": True,
        "answer_lock": False,
        "participated": False  # بعداً True می‌شود
    }
    await update.message.reply_text(
        "به مسابقه اطلاعات عمومی سخت (چهارگزینه‌ای) خوش آمدید\n"
        "هر سؤال ۳۰ ثانیه فرصت دارد.\n"
        "آیا آماده‌ای؟ (لطفاً فقط تایپ کن: بله، آره، نه، خیر)"
    )

async def ready_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()
    if user_id not in user_data or not user_data[user_id].get("waiting_ready", False):
        return
    if text in ["بله", "اره", "آره"]:
        user_data[user_id]["waiting_ready"] = False
        user_data[user_id]["participated"] = True  # کاربر الان شرکت کرده!
        await update.message.reply_text("آزمون شروع شد")
        await asyncio.sleep(1)
        await ask_question(update, context)
    elif text in ["نه", "خیر"]:
        user_data[user_id]["waiting_ready"] = False
        await update.message.reply_text("باشه، هر وقت آماده بودی /start رو بزن")
    else:
        await update.message.reply_text("لطفاً فقط یکی از این‌ها را تایپ کن: بله، آره، نه، خیر")

async def ask_question(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update_or_query, 'effective_user'):
        user_id = update_or_query.effective_user.id
        chat_id = update_or_query.effective_chat.id
    else:
        user_id = update_or_query.from_user.id
        chat_id = update_or_query.message.chat.id

    idx = user_data[user_id]["q_index"]
    user_data[user_id]["answer_lock"] = False
    if idx < len(QUESTIONS):
        q = QUESTIONS[idx]
        keyboard = [
            [InlineKeyboardButton(opt, callback_data=f"answer_{i}")]
            for i, opt in enumerate(q["options"])
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"سؤال {idx+1}:\n{q['question']}",
            reply_markup=reply_markup
        )
        user_data[user_id]['current_msg_id'] = sent_msg.message_id

        # تایمر ۱۰ ثانیه‌ای برای هر سؤال
        asyncio.create_task(question_timeout(chat_id, user_id, idx, sent_msg.message_id, context))
    else:
        percent = int(user_data[user_id]["score"] * 100 / len(QUESTIONS))
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🔚 پایان آزمون!\n"
                f"درصد شما: {percent}%\n"
                f"تعداد پاسخ صحیح: {user_data[user_id]['score']} از {len(QUESTIONS)}"
            )
        )

async def question_timeout(chat_id, user_id, q_index, msg_id, context):
    await asyncio.sleep(30)
    if user_data[user_id]["q_index"] == q_index and not user_data[user_id]["answer_lock"]:
        user_data[user_id]["answer_lock"] = True
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=None
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏰ زمان تمام شد سوال بعدی:"
        )
        user_data[user_id]["q_index"] += 2
        await ask_question_dummy(chat_id, user_id, context)

async def ask_question_dummy(chat_id, user_id, context):
    class Dummy:
        pass
    dummy = Dummy()
    dummy.effective_user = type('User', (), {'id': user_id})
    dummy.effective_chat = type('Chat', (), {'id': chat_id})
    await ask_question(dummy, context)

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    q_index = user_data[user_id]["q_index"]

    if user_data[user_id].get("answer_lock", False):
        await query.answer(text="برای این سؤال دیگر نمی‌توان پاسخ داد", show_alert=True)
        return
    user_data[user_id]["answer_lock"] = True

    if q_index >= len(QUESTIONS):
        await query.answer()
        return

    correct_idx = QUESTIONS[q_index]["answer"]
    user_ans = int(query.data.replace("answer_", ""))
    await query.edit_message_reply_markup(reply_markup=None)
    if user_ans == correct_idx:
        user_data[user_id]["score"] += 2
        await query.message.reply_text("✅ درست بود")
    else:
        ans_text = QUESTIONS[q_index]["options"][correct_idx]
        await query.message.reply_text(f"❌ اشتباه جواب صحیح: {ans_text}")

    user_data[user_id]["q_index"] += 2
    await ask_question(query, context)

def main():
    TOKEN = "8149868544:AAFENL50P59AXdRtMk1ZujoCw_xidJWAvzw"  # توکن ربات خودت را اینجا بذار
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(answer_handler, pattern="^answer_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ready_message_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
