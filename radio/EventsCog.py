from discord import utils
from discord.ext import commands


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Music Bot Ready')

    @commands.Cog.listener()
    async def on_guild_available(self, guild):
        channel = utils.getchannel = utils.get(guild.text_channels, name='bot-channel')
        if channel is None:
            await guild.create_text_channel('bot-channel')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is None:
            return

        if len(voice_state.channel.members) == 1:
            if self.bot.voice is not None:
                self.bot.voice.stop()
                self.bot.voice = None
                self.bot.station = None
            await voice_state.disconnect()
            voice_state.cleanup()

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        print(event)


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
