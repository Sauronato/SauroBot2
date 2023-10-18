import discord
from discord.ext import commands
from discord.ext.commands import Context
from youtube_search import YoutubeSearch  

# Crear una extensión separada para el reproductor de música
class MusicPlayer(commands.Cog, name="music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.voice = {}  # Diccionario para mantener el estado de los canales de voz por servidor
        self.queue = {}  # Diccionario para mantener listas de reproducción por servidor


    @commands.hybrid_command(
        name="join",
        description="Join a voice channel.",
    )
    async def join(self, context: Context):
        server_id = context.guild.id
        if context.author.voice is not None:
            if server_id in self.voice:
                # Verificar si ya está conectado a un canal en el servidor
                await context.send("I'm already in a voice channel in this server.")
            else:
                self.voice[server_id] = await context.author.voice.channel.connect()
                self.queue[server_id] = []
        else:
            await context.send("You are not in a voice channel!")

    @commands.hybrid_command(
        name="playe",
        description="Play a YouTube video in the voice channel.",
    )
    async def play(self, context: Context, query: str):
        if context.guild is None:
            await context.send("Este comando solo se puede utilizar en un servidor.")
            return

        server_id = context.guild.id
        if server_id in self.voice:
            if not self.voice[server_id].is_connected():
                if context.author.voice is not None:
                    self.voice[server_id] = await context.author.voice.channel.connect()
                else:
                    await context.send("You are not in a voice channel!")
                    return
        else:
             if context.author.voice is not None:
                if server_id in self.voice:
                    # Verificar si ya está conectado a un canal en el servidor
                    await context.send("I'm already in a voice channel in this server.")
                else:
                    self.voice[server_id] = await context.author.voice.channel.connect()
                    self.queue[server_id] = []
             else:
                await context.send("You are not in a voice channel!")
                return


        # Utilizar youtube-search-python para buscar el video
        results = YoutubeSearch(query, max_results=1).to_dict()
        if results:
            video_id = results[0]["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Obtener información del video
            video_info = results[0]
            title = video_info["title"]
            uploader = video_info["channel"]
            views = video_info["views"]
            description = video_info["long_desc"]

            # Mensaje de información de la canción
            info_message = f"**Canción solicitada por {context.author.mention}**\n\n" \
                        f"**Título:** {title}\n" \
                        f"**Uploader:** {uploader}\n" \
                        f"**Vistas:** {views}\n" \
                        f"**Descripción:** {description}\n" \
                        f"**Enlace:** {video_url}"

            await context.send(info_message)

            # Agregar a la lista de reproducción
            self.queue[server_id].append(video_url)

            if not self.voice[server_id].is_playing() and len(self.queue[server_id]) == 1:
                source = discord.FFmpegPCMAudio(self.queue[server_id][0])
                self.voice[server_id].play(source, after=lambda e: self.play_next(server_id))

    def play_next(self, server_id):
        if len(self.queue[server_id]) > 0:
            source = self.queue[server_id].pop(0)
            self.voice[server_id].play(source, after=lambda e: self.play_next(server_id))

    @commands.hybrid_command(
        name="leave",
        description="Leave the voice channel.",
    )
    async def leave(self, context: Context):
        server_id = context.guild.id
        if server_id in self.voice:
            if self.voice[server_id].is_connected():
                await self.voice[server_id].disconnect()
                self.voice.pop(server_id)
                self.queue.pop(server_id)
            else:
                await context.send("I'm not in a voice channel.")
        else:
            await context.send("I'm not in a voice channel.")

# Agrega la extensión al bot
async def setup(bot) -> None:
    await bot.add_cog(MusicPlayer(bot))
