import logging
import feedparser
import click
import yaml
from tinydb import TinyDB
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
from telegram import ParseMode

# configure logging
logging.basicConfig(
    filename="prod.log",
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)


def generate_rss_endpoint(subreddit, terms):
    # %2B is `+` url encoded
    # %3A is `:` url encoded
    return f"https://www.reddit.com/search.rss?q={'%2B'.join(terms)}%2Bsubreddit:{subreddit}&sort=new"


@click.group()
def cli():
    """
    Poll a list of Reddit RSS feeds and push them to Telegram
    """
    pass


def add(subreddit, terms):
    db = TinyDB("data.json")
    doc_id = db.insert(
        {
            "feed": generate_rss_endpoint(subreddit, terms),
            "last_id": None,
            "subreddit": subreddit,
            "terms": terms,
        }
    )
    logging.info(f"✅ added doc with id {doc_id}")
    return doc_id


@cli.command(name="add")
@click.argument("subreddit", nargs=1)
@click.argument("terms", nargs=-1)
def add_cli(subreddit, terms):
    """
    <subreddit> <terms>
    """
    doc_id = add(subreddit, terms)
    click.echo(f"✅ added doc with id {doc_id}")


def add_tg(update, context):
    if len(context.args) < 1:
        update.message.reply_text("👎 must specify a subreddit")
        return
    elif len(context.args) < 2:
        update.message.reply_text("👎 must specify at least one search term")
        return

    doc_id = add(context.args[0], context.args[1:])
    update.message.reply_text(f"✅ added doc with id {doc_id}")


def remove(id):
    db = TinyDB("data.json")
    db.remove(doc_ids=[id])
    logging.info(f"✅ removed doc with id {id}")


@cli.command(name="remove")
@click.argument("id", nargs=1)
def remove_cli(id):
    """
    <doc_id> remove a particular entry
    """
    remove(id)
    click.echo(f"✅ removed doc with id {id}")


def remove_tg(update, context):
    if len(context.args) < 1:
        update.message.reply_text("👎 must specify a doc id")
        return

    remove(int(context.args[0]))
    update.message.reply_text(f"✅ removed doc with id {id}")


@cli.command(name="ls")
def ls_cli():
    """
    list all database entries
    """
    click.echo(f"|{'id':^4}|{'subreddit':^18}|{'term(s)':^36}|")
    for item in ls():
        click.echo(
            f"|{item.doc_id:^4}|{item.get('subreddit'):^18}|{', '.join(item.get('terms')):^36}|"
        )


def ls_tg(update, context):
    results = ""
    for item in ls():
        results.append(
            f"id: {item.doc_id}, sub: {item.get('subreddit')}, terms: ({', '.join(item.get('terms'))})\n"
        )
        results.pop()  # remove last newline
    update.message.reply_text(results)


def ls():
    db = TinyDB("data.json")
    return db.all()


def add_chat_tg(update, context):
    if update.my_chat_member:
        db = TinyDB("chats.json")
        db.insert({'chat_id': update.effective_chat.id})
        logging.info("🙋‍♂️ added new chat id, yay!")


def poll_tg(update, context):
    poll_job(context)


def poll_job(context):
    db = TinyDB("data.json")
    for item in db:
        d = feedparser.parse(item.get('feed'))
        # sorted by new
        last_index = None
        for i in range(len(d.entries)):
            entry = d.entries[i]
            if entry.id == item.get("last_id"):
                last_index = i
        new_entries = d.entries[:last_index]
        # push all new entries per feed to chat
        for e in new_entries:
            context.bot.send_message(context.job.context, text=f'[{e.title}]({e.link})', parse_mode=ParseMode.MARKDOWN_V2)

        if len(new_entries) > 0:
            db.update({'last_id': new_entries[0].id}, doc_ids=[item.doc_id])


@cli.command(name="poll")
def poll_cli():
    """
    poll the RSS feeds
    """
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    if config is None or "tg_bot_token" not in config:
        raise Exception("invalid configuration")

    BOT_TOKEN = config.get("tg_bot_token")
    POLL_INTERVAL = config.get("poll_interval") or 0.5

    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    dispatcher.add_handler(CommandHandler("refresh", poll_tg))
    dispatcher.add_handler(CommandHandler("help", help_tg))
    dispatcher.add_handler(CommandHandler("add", add_tg))
    dispatcher.add_handler(CommandHandler("list", ls_tg))
    dispatcher.add_handler(CommandHandler("remove", remove_tg))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, add_chat_tg))

    chat_id = TinyDB("chats.json").all()[0]
    job_queue.run_repeating(poll_job, interval=POLL_INTERVAL, name="poller", context=chat_id)

    updater.start_polling()
    logging.info("⭐ Started polling")
    updater.idle()


def help_tg(update, context):
    update.message.reply_text(
        """commands available:\n
        /add <subreddit> <search terms>: add a new entry\n
        /remove <id>: remove an entry\n
        /list: list all entries\n
        /refresh: force poll all entries\n
        /help: view this message again cause I'm a forgetful idiot"""
    )


if __name__ == "__main__":
    cli()
