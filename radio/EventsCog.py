import logging

from discord import app_commands, Interaction
from discord.ext import commands

logger = logging.getLogger('discord')


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self, i: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            message = f"Slow down, try again in {error.retry_after:.0f}s"
        else:
            logger.error(repr(error))
            message = "Something went wrong... ;_;"
        if i.response.is_done():
            await i.followup.send(message, ephemeral=True)
        else:
            await i.response.send_message(message, ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Music Bot Ready')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is None:
            return

        if len(voice_state.channel.members) == 1:
            await voice_state.disconnect()

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        logger.error(event)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        logger.error(repr(error))


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
