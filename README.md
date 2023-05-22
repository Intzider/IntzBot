# Discord radio bot with Shazam feature

Available commands:
* `/radio [station]`
    * change current station / connect to voice channel
* `/disconnect`
    * stop playing and disconnect from voice channel
* `/shazam`
    * identify current song (defaults to 10s)
* `/shazam [duration]`
    * identify current song with `duration` seconds of listening (between 10 and 20)

### Notes
* default prefix for non-slash commands set to `:`, can be changed in `.env` file (requires service restart)
* installation script located in `installation` folder
* there are other commands available but are set to `owner` which is hardcoded in `bot.py` (change requires service restart)