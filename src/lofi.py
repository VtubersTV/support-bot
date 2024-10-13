import os
import random
import yt_dlp as youtube_dl
import discord
import asyncio
import shutil

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

    @classmethod
    async def get_info(cls, url):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        return data
    
    @classmethod
    async def download(cls, url):
        loop = asyncio.get_event_loop()
        music_folder = os.path.join(os.path.expanduser('~'), 'Music', 'Lofi')
        if not os.path.exists(music_folder):
            os.makedirs(music_folder, exist_ok=True)

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))

        if 'entries' in data:
            data = data['entries'][0]

        filename = os.path.join(music_folder, ytdl.prepare_filename(data))
    
        if not os.path.exists(filename):
            original_filename = ytdl.prepare_filename(data)
            if os.path.exists(original_filename):
                shutil.copy(original_filename, filename)
                os.remove(original_filename)
                print(f'Downloaded: {filename}')
            else:
                print('Download failed.')
                return None
        else:
            print(f'File already exists: {filename}')

        return os.path.basename(filename)

class LofiMusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.reaction_threshold = 5

    async def play_random_local(self, voice_client, cursor, channel, retryCount=0):
        cursor.execute("SELECT filename, title, video_id, thumbnail FROM LofiMusic ORDER BY RANDOM() LIMIT 1")
        rows = cursor.fetchall()

        if not rows:
            if retryCount == 0:
                print("No music found in the database.")
            else:
                print(f"No music found in the database. Retry count: {retryCount}")
            await asyncio.sleep(10)
            await self.play_random_local(voice_client, cursor, channel, retryCount + 1)
            return

        row = rows[0]
        filename = row[0]
        title = row[1]
        video_id = row[2]
        thumbnail = row[3]

        music_folder = os.path.join(os.path.expanduser('~'), 'Music', 'Lofi')

        if not os.path.exists(music_folder):
            print("Music folder not found.")
            return

        file_path = os.path.join(music_folder, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        # Play the music
        player = discord.FFmpegPCMAudio(file_path, **ffmpeg_options)
        voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        embed = discord.Embed(title=f"Now playing: {title} :musical_note:", color=0x3498DB)
        embed.url = f"https://www.youtube.com/watch?v={video_id}"
        embed.set_image(url=thumbnail)
        embed.description=f"To skip this song, react with the '👎'. It must have {self.reaction_threshold} reactions"
        embed.set_footer(text="View the source code: https://github.com/VtubersTV/support-bot/blob/master/src/lofi.py")
        message = await channel.send(embed=embed)
        
        # React to the message
        await message.add_reaction('👍')
        await message.add_reaction('👎')

        thumbs_down_count = 0

        def check(reaction, user):
            return user != self.bot.user and str(reaction.emoji) in ['👍', '👎'] and reaction.message.id == message.id

        while voice_client.is_playing():
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                if str(reaction.emoji) == '👎':
                    thumbs_down_count += 1
                    if thumbs_down_count >= self.reaction_threshold:
                        print("Song skipped due to too many thumbs down.")
                        voice_client.stop()
                        break
            except asyncio.TimeoutError:
                continue  # Just ignore timeout and keep playing

        # If song finished playing naturally, check if we need to skip
        if thumbs_down_count >= self.reaction_threshold:
            await self.play_random_local(voice_client, cursor, channel)

    async def connect(self, cursor):
        channel_id = 1294909246860955691
        channel = self.bot.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.VoiceChannel):
            print(f"Channel with ID {channel_id} not found or is not a voice channel.")
            return
        
        if channel.guild.voice_client is None:
            voice_client = await channel.connect()
        else:
            voice_client = channel.guild.voice_client

        await self.play_random_local(voice_client, cursor, channel)
