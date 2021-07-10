# tele-rss-gram

Polls a list of RSS feeds and pushes any new items to a Telegram group

## Developing

Use Python >= 3.4

1. Install dependencies

## Deployment

1. Create a venv & install dependencies

    ```python
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2. Set your Telegram token & polling interval

    ```bash
    nano src/config.yml
    ```

    ```yaml
    tg_bot_token:
    poll_interval: 0.5
    ```

3. Add entries via CLI if desired

    ```python
    python3 src/main add upliftingnews cats
    ```

4. Set the bot going!

    ```bash
    tmux
    python3 src/main poll
    ```

Note: on first start, the bot will wait for you to add it to a group, and the chat ID will be stored. restart the bot to access its full functionality.

## Credits

Created by Matias Silva in 2021 to get vaccinated!
