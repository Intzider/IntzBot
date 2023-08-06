import logging
from .playing import playing, channels

from discord import FFmpegOpusAudio
from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Music Bot Ready')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        async def reconnect(voice):
            logger.info("connect")
            # voice = await channels[guild.id].connect()
            await voice.move_to(channels[guild.id])
            logger.info("play")
            source = await FFmpegOpusAudio.from_probe(playing[guild.id], method='fallback')
            voice.play(source, after=lambda e: logger.error("It hath stopped: " + repr(e)))
            logger.info(f"{guild.name} | resumed play")

        voice_state = member.guild.voice_client
        guild = member.guild
        if voice_state is None:
            logger.info("is none")
            if guild.id in playing and guild.id in channels:
                logger.info("reconnect")
                await reconnect(voice_state)
            return

        logger.info(member.name)
        logger.info(member.id)
        logger.info("playing? " + str(voice_state.is_playing()))
        logger.info("connected? " + str(voice_state.is_connected()))
        logger.info(playing)
        logger.info(channels)
        if len(voice_state.channel.members) == 1:
            await voice_state.disconnect()
            voice_state.cleanup()
            del playing[guild.id]
            del channels[guild.id]
        else:
            if not voice_state.is_connected() and guild.id in channels:
                logger.info("stop")
                await reconnect(voice_state)

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        logger.error("error")
        logger.error(event)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        logger.error(repr(error))


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
