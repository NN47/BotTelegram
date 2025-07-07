from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from collections import defaultdict, Counter
import sqlite3

# Список всех животных
animal_data = {
    "АЗИАТСКИЙ СЛОН": "Азиатский слон — крупное млекопитающее с выдающимся интеллектом и социальной структурой.",
    "АКСОЛОТЛЬ": "Аксолотль — удивительная амфибия, способная к регенерации конечностей.",
    "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ": "Александрийский попугай — умная и социальная птица с ярким оперением.",
    "АМУРСКИЙ ТИГР": "Амурский тигр — самый северный представитель тигров, символ силы и выносливости.",
    "АНДСКИЙ КОНДОР": "Андский кондор — одна из крупнейших летающих птиц, символ свободы и наблюдательности."
}

original_quiz_questions = [
    {"question": "1. Выходной день. Как вы его проведёте?", "options": {
        "Разлягусь на диване с книгой": "АКСОЛОТЛЬ",
        "Пойду гулять с друзьями": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ",
        "Устрою пикник на природе": "АНДСКИЙ КОНДОР",
        "Посижу в тишине с чаем": "АЗИАТСКИЙ СЛОН"
    }},
    {"question": "2. Ваш способ справиться со стрессом?", "options": {
        "Поговорить с кем-то": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ",
        "Уединиться в тишине": "АМУРСКИЙ ТИГР",
        "Съесть что-то вкусное": "АКСОЛОТЛЬ",
        "Пойти на тренировку": "АНДСКИЙ КОНДОР"
    }},
    {"question": "3. Какой стиль одежды вам ближе?", "options": {
        "Комфорт превыше всего": "АКСОЛОТЛЬ",
        "Ярко и смело": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ",
        "Строго и сдержанно": "АМУРСКИЙ ТИГР",
        "Спортивно и удобно": "АНДСКИЙ КОНДОР"
    }},
    {"question": "4. Любимая погода?", "options": {
        "Тёплый дождик и плед": "АКСОЛОТЛЬ",
        "Яркое солнце и ветер": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ",
        "Морозный воздух и снег": "АМУРСКИЙ ТИГР",
        "Прохладная тень летом": "АНДСКИЙ КОНДОР"
    }},
    {"question": "5. Что вы обычно выбираете на вечеринке?", "options": {
        "Я душа компании!": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ",
        "Танцую до упаду": "АНДСКИЙ КОНДОР",
        "Сижу в уголке и наблюдаю": "АМУРСКИЙ ТИГР",
        "Вообще не хожу на вечеринки": "АКСОЛОТЛЬ"
    }},
    {"question": "6. Как вы относитесь к приключениям?", "options": {
        "Люблю неожиданности": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ",
        "Планирую всё заранее": "АЗИАТСКИЙ СЛОН",
        "Не люблю менять привычки": "АКСОЛОТЛЬ",
        "Готов на всё ради эмоций": "АНДСКИЙ КОНДОР"
    }},
    {"question": "7. Утро понедельника. Что первое в голове?", "options": {
        "Где кофе?": "АКСОЛОТЛЬ",
        "Нужно всех собрать и организовать": "АЗИАТСКИЙ СЛОН",
        "Уже бегу на тренировку": "АНДСКИЙ КОНДОР",
        "С кем бы поболтать?": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ"
    }},
    {"question": "8. Что приносит вам больше радости?", "options": {
        "Тепло и уют": "АКСОЛОТЛЬ",
        "Свобода и ветер в лицо": "АНДСКИЙ КОНДОР",
        "Семья и традиции": "АЗИАТСКИЙ СЛОН",
        "Общение и юмор": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ"
    }},
    {"question": "9. Что вы сделаете, если вдруг сломался интернет?", "options": {
        "Полежу и отдохну — даже хорошо!": "АКСОЛОТЛЬ",
        "Позвоню друзьям": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ",
        "Пойду на улицу, столько дел!": "АНДСКИЙ КОНДОР",
        "Сделаю уборку и пересортирую книги": "АЗИАТСКИЙ СЛОН"
    }},
    {"question": "10. Какой ваш идеальный вечер?", "options": {
        "В одиночестве под одеялом": "АКСОЛОТЛЬ",
        "На сцене в центре внимания": "АЛЕКСАНДРИЙСКИЙ ПОПУГАЙ",
        "За ужином с близкими": "АЗИАТСКИЙ СЛОН",
        "На пробежке под луной": "АНДСКИЙ КОНДОР"
    }}
]

user_quiz_data = defaultdict(lambda: {"current": 0, "answers": []})

conn = sqlite3.connect("results.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS results (
        user_id INTEGER,
        animals TEXT
    )
""")
conn.commit()

def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("🎯 Пройти викторину", callback_data="start_quiz")]]
    update.message.reply_text(
        "Привет! Готовы узнать, какое вы тотемное животное?", reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_question(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    state = user_quiz_data[user_id]

    current = state["current"]
    if current >= len(original_quiz_questions):
        return show_result(update, context)

    question_data = original_quiz_questions[current]
    options = list(question_data["options"].items())

    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"answer:{i}")]
        for i, (text, _) in enumerate(options)
    ]
    if current > 0:
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])

    query.edit_message_text(question_data["question"], reply_markup=InlineKeyboardMarkup(keyboard))

def handle_answer(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    state = user_quiz_data[user_id]
    current = state["current"]

    if current >= len(original_quiz_questions):
        return

    try:
        index = int(query.data.split(":", 1)[1])
        question = original_quiz_questions[current]
        option_text, animal = list(question["options"].items())[index]
    except (IndexError, ValueError):
        query.answer("Ошибка при обработке ответа.")
        return

    if len(state["answers"]) > current:
        state["answers"][current] = animal
    else:
        state["answers"].append(animal)
    state["current"] += 1

    show_question(update, context)

def handle_back(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    state = user_quiz_data[user_id]

    if state["current"] > 0:
        state["current"] -= 1
        show_question(update, context)

def show_result(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    answers = user_quiz_data[user_id]["answers"]
    counter = Counter(answers)
    max_count = max(counter.values())
    top_animals = [animal for animal, count in counter.items() if count == max_count]

    # Сохраняем результат в базу
    c.execute("INSERT INTO results (user_id, animals) VALUES (?, ?)", (user_id, ", ".join(top_animals)))
    conn.commit()

    result_text = "Ваши тотемные животные:\n\n"
    for animal in top_animals:
        desc = animal_data.get(animal, "Описание недоступно.")
        result_text += f"🐾 {animal}: {desc}\n\n"

    keyboard = [[
        InlineKeyboardButton("🔁 Пройти снова", callback_data="start_quiz"),
        InlineKeyboardButton("🐾 Оформить опеку", url="https://example.com/adopt")
    ]]
    query.edit_message_text(result_text.strip(), reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == "start_quiz":
        user_quiz_data[user_id] = {"current": 0, "answers": []}
        show_question(update, context)
    elif query.data.startswith("answer:"):
        handle_answer(update, context)
    elif query.data == "back":
        handle_back(update, context)

def main():
    updater = Updater("You_Token", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
