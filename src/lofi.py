import yt_dlp as youtube_dl
import discord
import asyncio

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Take the first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class LofiMusicPlayer:
    def __init__(self, bot):
        self.bot = bot

    async def play(self, voice_client, url="https://www.youtube.com/watch?v=4xDzrJKXOOY"):
        """Plays the Lofi stream in the voice channel."""
        if voice_client.is_playing():
            voice_client.stop()

        await asyncio.sleep(0)
        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        print(f'Now playing: {player.title}')

    async def connect(self):
        """Connects to a specified voice channel and starts playing Lofi music."""
        channel_id = 1294909246860955691
        channel = self.bot.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.VoiceChannel):
            print(f"Channel with ID {channel_id} not found or is not a voice channel.")
            return

        if channel.guild.voice_client is None:
            voice_client = await channel.connect()
        else:
            voice_client = channel.guild.voice_client

        await self.play(voice_client)