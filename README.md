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

### Docker
* compose service: `build: { context: ./discord-bot/IntzBot }` (build context is the repo root)
* `.env` is passed through `env_file`, it is not copied into the image
* streams are stored in `/data/streams.json` (seeded from `radio/streams.json` on first start), mount `/data` to keep them
* run `:sync` after first start or when slash commands change

### Dependencies
Direct dependencies go in `requirements.in`; `requirements.txt` is generated with hashes (use Python 3.12, same as the image):

```sh
pip install pip-tools
pip-compile --generate-hashes --strip-extras requirements.in            # after editing requirements.in
pip-compile --generate-hashes --strip-extras --upgrade requirements.in  # upgrade everything
```

Dependabot opens a weekly PR that does the upgrade for you (plus the Docker base image). CI builds the image and checks that ffmpeg and all modules import, so a green PR is safe to merge.
