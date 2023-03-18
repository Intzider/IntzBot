import json
import os

from discord import FFmpegOpusAudio
from discord.ext import commands


def get_streams() -> dict:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "streams.json"), "r") as file:
        return json.load(file)


class RadioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.streams = get_streams()
        self.bot.voice = None
        self.bot.station = None

    async def is_in_channel(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel")
            self.bot.station = None
            return False
        if ctx.author.voice.channel is None:
            await ctx.send("You're not in a voice channel")
            self.bot.station = None
            return False
        return True

    async def is_valid_station(self, ctx, args):
        if len(args) != 1:
            message = "Missing radio station argument:\n"
            message += "\n".join(
                [f"    {os.getenv('PREFIX')}play {x}" for x, v in self.bot.streams.items() if v != self.bot.station])
            await ctx.send(message)
            return False

        if self.bot.streams.get(args[0], "") == self.bot.station:
            await ctx.send("This is already playing")
            return False
        else:
            self.bot.station = self.bot.streams.get(args[0], None)

        if self.bot.station is None:
            await ctx.send("You mistyped, I ain't playin nuffin")
            return False

        return True

    @commands.command(name="play")
    async def play(self, ctx, *args):
        def play_audio(err=None):
            if err is not None:
                print(err)
            if self.bot.voice is None:
                return
            self.bot.voice.play(FFmpegOpusAudio(self.bot.station, options="-filter:a volume=0.2"),
                                after=lambda e: play_audio(e))

        change = await self.is_valid_station(ctx, args)

        if await self.is_in_channel(ctx) and change:
            if self.bot.voice is not None and not change:
                return
            elif self.bot.voice is not None:
                await self.bot.voice.disconnect(force=False)

            voice_channel = ctx.author.voice.channel
            self.bot.voice = ctx.channel.guild.voice_client
            if self.bot.voice is None:
                self.bot.voice = await voice_channel.connect()
            elif self.bot.voice.channel != voice_channel:
                self.bot.voice.move_to(voice_channel)
            play_audio()

    @commands.command(name="pause")
    async def pause(self, ctx):
        if 'voice' in globals():
            if self.bot.voice.is_playing():
                self.bot.voice.pause()
            else:
                self.bot.voice.resume()

    @commands.command(name="resume")
    async def resume(self, ctx):
        await self.pause(ctx)

    @commands.command(name="stop")
    async def stop(self, ctx, change=False):
        if self.bot.voice is not None:
            self.bot.voice.stop()
        if not change:
            await self.disconnect(ctx)

    @commands.command(name="dc")
    async def disconnect(self, ctx):
        voice_state = ctx.guild.voice_client
        if voice_state is None:
            return

        await voice_state.disconnect()
        voice_state.cleanup()
        self.bot.voice = None
        self.bot.station = None

    @commands.command(name="reload_streams")
    async def reload_streams(self, ctx):
        self.bot.streams = get_streams()
        await ctx.send(f"Streams reloaded, I now have {len(self.bot.streams)} streams")


async def setup(bot):
    await bot.add_cog(RadioCog(bot))
