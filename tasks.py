#!.venv/bin/python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to send timed Telegram messages.

This Bot uses the Application class to handle the bot and the JobQueue to send
timed messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.

Note:
To use the JobQueue, you must install PTB via
`pip install python-telegram-bot[job-queue]`
"""

import logging
import json
import datetime

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
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

with open("config.json", "r") as config_file:
    config = json.load(config_file)
    config_file.close()

# Define a few command handlers. These usually take the two arguments update and
# context.
# Best practice would be to replace context with an underscore,
# since context is an unused local variable.
# This being an example and not having context present confusing beginners,
# we decided to have it present as context.

next_time = datetime.datetime.now()
state = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("Use /start_timer to start pomodoro and /stop_timer to stop pomodoro")


async def notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the notification."""
    now = datetime.datetime.now()
    job = context.job

    if state in [1,3,5,7] and now == next_time:
        await context.bot.send_message(job.chat_id, text=f"Session started")
        next_time += datetime.timedelta(1500)
        state += 1
    
    elif state == [2,4,6] and now == next_time:
        await context.bot.send_message(job.chat_id, text=f"Short break")
        next_time += datetime.timedelta(300)
        state += 1

    elif state == 8 and now == next_time:
        await context.bot.send_message(job.chat_id, text=f"Long break")
        next_time += datetime.timedelta(900)
        state = 1


def remove_job_if_exists(name: str, job_queue: JobQueue) -> bool:
    """Remove job with given name. Returns whether job was removed."""

    current_jobs = job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def start_timer(update: Update, job_queue: JobQueue) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id

    # job_removed = remove_job_if_exists(str(chat_id), context)

    # text = "Timer successfulmessagely set!"
    # if job_removed:
    #     text += " Old one was removed."
    # await update.effective_message.reply_text(text)

    try:
        job_queue.run_repeating(notification, 60, chat_id=chat_id, name=str(chat_id))
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /timer_start")


async def stop_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


def main() -> None:
    """Run bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config["API_TOKEN"]).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("start_timer", start_timer))
    application.add_handler(CommandHandler("stop_timer", stop_timer))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()