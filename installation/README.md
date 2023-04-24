### `install.sh`
* currently used as separate installation script (subject to change)
  * requires Discord bot token as 1st argument
  * no need to clone repository (cloning done in script)
  * run script under `su`
  * installs dependencies, creates python venv, copies systemd unit file; enables and starts service

### `discordbot.service`
* systemd unit file

### `reset_restore.sh`
* a quick project hard reset/pull and backup