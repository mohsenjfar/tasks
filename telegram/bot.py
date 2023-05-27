import logging
import json
from datetime import date, time, datetime, timedelta
import pytz
import pandas as pd
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

# from asgiref.sync import async_to_sync
import sys, os, django
sys.path.append('/root/taskerbot')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from tasks.models import Task

# Enable logging
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )


with open("config.json", "r") as config_file:
    config = json.load(config_file)
    config_file.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation"""

    await update.message.reply_text(
        "Need help? use /help button"
    )


def return_time():
    start_time = datetime.combine(date.today(), time(7,0))
    end_time = datetime.combine(date.today(), time(22,0))
    periods = [25,5,25,5,25,5,25,15]
    states = {
        25:"Session started", 
        5:"Short break", 
        15:"Long break\nDon't forget to drink water"
    }
    times = {}
    while start_time < end_time:
        for p in periods:
            times[start_time.strftime('%H:%M')] = states[p]
            start_time += timedelta(minutes=p)
    return times


async def notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job

    now  = datetime.now(pytz.timezone('Asia/Tehran')).strftime('%H:%M')

    if now in job.data:
        await context.bot.send_message(job.chat_id, text=job.data[now])


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""

    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def timer_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    data = return_time()

    chat_id = update.effective_message.chat_id

    job_removed = remove_job_if_exists(str(chat_id), context)

    context.job_queue.run_repeating(notification, 60, chat_id=chat_id, name=str(chat_id), data=data, first=1)

    text = "Timer successfully set!"
    if job_removed:
        text += " Old one was removed."

    await update.message.reply_text(text)


async def timer_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)

SUMMARY, DESCRIPTION, DATE, FREQ, CONFIRM = range(5)

async def insert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    context.user_data['values'] = {}

    await update.message.reply_text(
        "Task summary:"
    )

    return SUMMARY


async def task_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    context.user_data['values']['summary'] = update.message.text

    reply_keyboard = [
        ["/no_description"]
    ]

    await update.message.reply_text(
        "Task description:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True
        ),
    )

    return DESCRIPTION

async def task_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    context.user_data['values']['description'] = update.message.text

    await update.message.reply_text(
        "Task due time (yyyy-mm-dd hh:mm):",
    )

    return DATE

async def description_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    await update.message.reply_text(
        "Task due time (yyyy-mm-dd hh:mm):"
    )

    return DATE


async def task_due(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    context.user_data['values']['date'] = update.message.text

    reply_keyboard = [
        ["/no_frequency"]
    ]

    await update.message.reply_text(
        "Task frequency",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    return FREQ

async def task_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    """Stores the info about the user and ends the conversation."""
    
    context.user_data['values']['freq'] = update.message.text

    text = ""

    for value in context.user_data['values']:
        text += f"{value}: {context.user_data['values'][value]}\n"

    reply_keyboard = [
        ["/confirm"]
    ]

    await update.message.reply_text(
        "Confirm data:\n\n" + text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True
        ),
    )

    return CONFIRM

async def frequency_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the location and asks for info about the user."""

    text = ""

    for value in context.user_data['values']:
        text += f"{value}: {context.user_data['values'][value]}\n"

    reply_keyboard = [
        ["/confirm"]
    ]

    await update.message.reply_text(
        "Confirm data:\n\n" + text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True
        ),
    )

    return CONFIRM


async def data_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    # Create the tuple "params" with all the parameters inserted by the user
    values = context.user_data['values']

    Task.objects.create(
        summary = values['summary'],
        due = datetime.strptime(values['date'], '%Y-%m-%d %H:%M'),
        freq = values['freq'] if 'freq' in values else None,
        description = values['description'] if 'description' in values else None
    )

    await update.message.reply_text(
        f"{values['summary']} successfully inserted.",
        reply_markup=ReplyKeyboardRemove()
    )

    del context.user_data['values']

    return ConversationHandler.END

QUERY = range(1)


def return_task_values(task):
    id = task.id
    summary = task.summary
    dt = datetime.strftime(task.due, '%Y-%m-%d %H:%M')
    description = f'\nDescription: {task.description}'
    text = f"Summary: {summary}\nDate: {dt}" + description
    return text


async def select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    reply_keyboard = [
        ["/overdue", "/today"],
        ["/tommorrow", "/all"]
    ]

    await update.message.reply_text(
        "Type query statement or use keyboard shortcuts:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True
        ),
    )

    return QUERY

async def tasks_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    statement = f"SELECT * FROM 'tasks_task' WHERE {update.message.text}" 

    try:
        tasks = Task.objects.raw(statement)
        if tasks:
            for task in tasks:
                text = return_task_values(task)
                await update.effective_message.reply_text(text,reply_markup=ReplyKeyboardRemove())
        else:
            await update.effective_message.reply_text("No task", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await update.message.reply_text("Statement not correct use /help", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

async def overdue_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job
    
    context.user_data['message_id'] = update.message.message_id
    
    tasks = Task.objects.filter(due__lte = datetime.now()).order_by('due')

    if tasks:
        for task in tasks:
            text = return_task_values(task)
            await update.effective_message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    else:
        await update.effective_message.reply_text("All done!", reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END


async def today_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job
    
    context.user_data['message_id'] = update.message.message_id

    start_time = datetime.combine(date.today(), time(0,0))
    end_time = datetime.combine(date.today() + timedelta(days=1), time(0,0))
    tasks = Task.objects.filter(due__gte = start_time, due__lte = end_time).order_by('due')

    if tasks:
        for task in tasks:
            text = return_task_values(task)
            await update.effective_message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    else:
        await update.effective_message.reply_text("All done!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


async def tommorrow_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job
    
    context.user_data['message_id'] = update.message.message_id

    start_time = datetime.combine(date.today() + timedelta(days=1), time(0,0))
    end_time = datetime.combine(date.today() + timedelta(days=2), time(0,0))
    tasks = Task.objects.filter(due__gte = start_time, due__lte = end_time).order_by('due')

    if tasks:
        for task in tasks:
            text = return_task_values(task)
            await update.effective_message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    else:
        await update.effective_message.reply_text("All done!", reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END

async def all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    tasks = Task.objects.all()

    if tasks:
        for task in tasks:
            text = return_task_values(task)
            await update.effective_message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    else:
        await update.effective_message.reply_text("All done!", reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    current_id = update.message.message_id + 1

    for message_id in range(context.user_data['message_id'],current_id):
        await context.bot.deleteMessage(message_id = message_id, chat_id = update.message.chat_id)


async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the photo and asks for a location."""

    await update.message.reply_text(
        "Request cancelled",
        reply_markup=ReplyKeyboardRemove()
    )

    del context.user_data['values']

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config["TEST_TOKEN"]).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    insert_handler = ConversationHandler(
        entry_points=[CommandHandler("insert", insert)],
        states={
            SUMMARY : [MessageHandler(filters.TEXT & ~filters.COMMAND, task_summary)],
            DESCRIPTION : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, task_description),
                CommandHandler("no_description", description_skip),
            ],
            DATE : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, task_due),
            ],
            FREQ : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, task_frequency),
                CommandHandler("no_frequency", frequency_skip),
            ],
            CONFIRM : [CommandHandler("confirm", data_confirm),],
        },
        fallbacks=[CommandHandler("c", cancel_request)],
    )

    select_handler = ConversationHandler(
        entry_points=[CommandHandler("select", select)],
        states={
            QUERY : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tasks_query),
                CommandHandler("today", today_tasks),
                CommandHandler("overdue", overdue_tasks),
                CommandHandler("tommorrow", tommorrow_tasks),
                CommandHandler("all", all_tasks)
            ]
        },
        fallbacks=[CommandHandler("c", cancel_request)],
    )

    application.add_handler(insert_handler)
    application.add_handler(select_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("timer_start", timer_start))
    application.add_handler(CommandHandler("timer_stop", timer_stop))


    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()