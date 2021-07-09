import logging
import feedparser
import click
import yaml
from tinydb import TinyDB
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# configure logging
logging.basicConfig(
    filename="prod.log",
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)


def generate_rss_endpoint(subreddit, terms):
    return f"https://www.reddit.com/search.rss?q={'%2B'.join(terms)}%2Bsubreddit:{subreddit}&sort=new"


@click.group()
def cli():
    """
    Poll a list of Reddit RSS feeds and push them to Telegram
    """
    pass


@cli.command()
@click.argument("subreddit", nargs=1)
@click.argument("terms", nargs=-1)
def add(subreddit, terms, to_stdout=True):
    """
    <subreddit> <terms>
    """
    # %2B is `+` url encoded
    # %3A is `:` url encoded

    db = TinyDB("db.json")
    doc_id = db.insert(
        {"feed": generate_rss_endpoint(subreddit, terms), "last_id": None, "subreddit": subreddit, "terms": terms}
    )
    if to_stdout:
        click.echo(f" ✅ added new entry with doc id: {doc_id}")
    logging.info(f" ✅ added new entry with doc id: {doc_id}")


@cli.command()
@click.argument("id", nargs=1)
def remove(id, to_stdout=True):
    """
    <doc_id> remove a particular entry
    """
    db = TinyDB("db.json")

    db.remove(doc_ids=[id])
    if to_stdout:
        click.echo(f"✅ removed doc id: {id}")
    logging.info(f"✅ removed doc id: {id}")


@cli.command()
def ls():
    """
    list all database entries
    """
    db = TinyDB("db.json")
    click.echo(f"|{'id':^4}|{'subreddit':^18}|{'term(s)':^36}|")
    for item in db:
        click.echo(f"|{item.doc_id:^4}|{item.get('subreddit'):^18}|{', '.join(item.get('terms')):^36}|")


@cli.command()
@click.pass_context
def poll(ctx):
    """
    poll the RSS feeds
    """
    with open("config.yml", 'r') as f:
        config = yaml.safe_load(f)

    if config is None or 'tg_bot_token' not in config:
        raise Exception("invalid configuration")

    updater = Updater(config.get('tg_bot_token'))
    dispatcher = updater.dispatcher
    # ctx.invoke(test, count=42)

    dispatcher.add_handler(CommandHandler("poll", poll))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("list", ls))
    dispatcher.add_handler(CommandHandler("remove", remove))

    updater.start_polling()
    
    updater.idle()


if __name__ == "__main__":
    cli()
