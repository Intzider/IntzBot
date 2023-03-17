import json
import os

from discord import FFmpegPCMAudio, FFmpegOpusAudio, Intents
from discord.ext import commands

from dotenv import load_dotenv

from Events import Events

load_dotenv()


def get_streams():
    with open("streams.json", "r") as file:
        return json.load(file)


class Bot(commands.Bot):
    def __init__(self, command_prefix, *, self_bot):
        super().__init__(command_prefix, intents=Intents().all(), self_bot=self_bot)
        self.voice = None
        self.current_station = None
        self.streams = get_streams()

        @self.command(name="play")
        async def play(ctx, *args):
            def play_audio(err):
                print(err)
                self.voice.play(FFmpegOpusAudio(self.current_station), after=lambda e: play_audio(e))

            change = False
            if len(args) != 1:
                message = "Missing radio station argument:\n"
                message += "\n".join([f"    /play {x}" for x, v in self.streams.items() if v != self.current_station])
                await ctx.send(message)
                return
            if self.streams.get(args[0], "") == self.current_station:
                await ctx.send("This is already playing")
                return
            else:
                self.current_station = self.streams.get(args[0], None)
                change = True
            if self.current_station is None:
                await ctx.send("Fuck you, you mistyped\nI ain't playin nuffin")
                return

            channel = ctx.author.voice
            if channel is None:
                await ctx.send("You're not in a voice channel")
                self.current_station = None
                return
            if channel.channel is None:
                await ctx.send("You're not in a voice channel")
                self.current_station = None
                return

            if self.voice is not None and not change:
                return
            elif change:
                await stop(ctx, change)

            voice_channel = ctx.author.voice.channel
            self.voice = ctx.channel.guild.voice_client
            if self.voice is None:
                self.voice = await voice_channel.connect()
            elif self.voice.channel != voice_channel:
                self.voice.move_to(voice_channel)
            play_audio("")

        @self.command(name="pause")
        async def pause(ctx):
            if 'voice' in globals():
                if self.voice.is_playing():
                    self.voice.pause()
                else:
                    self.voice.resume()

        @self.command(name="resume")
        async def resume(ctx):
            await pause(ctx)

        @self.command(name="stop")
        async def stop(ctx, change=False):
            if self.voice is not None:
                self.voice.stop()
            if not change:
                await disconnect(ctx)

        @self.command(name="dc")
        async def disconnect(ctx):
            for x in bot.voice_clients:
                if x.channel == ctx.author.voice.channel:
                    self.voice = None
                    self.current_station = None
                    await x.disconnect(force=False)
                    x.cleanup()

    async def setup_hook(self) -> None:
        await self.add_cog(Events(self))

    async def on_message(self, message, /) -> None:
        await self.process_commands(message)


if __name__ == "__main__":
    bot = Bot(command_prefix="/", self_bot=False)
    bot.run(os.getenv('TOKEN'))
