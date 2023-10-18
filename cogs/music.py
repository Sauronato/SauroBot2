import discord
from discord.ext import commands
from discord.ext.commands import Context
from youtube_search import YoutubeSearch 
import youtube_dlc as youtube_dl


# Crear una extensión separada para el reproductor de música
# Define una vista personalizada que contiene los botones
class MusicView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="", custom_id="button-start", style=discord.ButtonStyle.primary, emoji="▶️") # the button has a custom_id set
    async def start_button_callback(self, button, interaction):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", custom_id="button-skip", style=discord.ButtonStyle.primary, emoji="⏭️") # the button has a custom_id set
    async def skip_button_callback(self, button, interaction):
        await interaction.response.edit_message(view=self)

class MusicPlayer(commands.Cog, name="music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.bot.database
        self.voice = {}  # Diccionario para mantener el estado de los canales de voz por servidor
        self.queue = {}  # Diccionario para mantener listas de reproducción por servidor
        self.play_channel = {}  # Canal de texto para enviar mensajes de información de la canción
        self.play_message = {}  # Mensaje de información de la canción
        self.play_role = {}  # Rol para permitir a los usuarios pausar y reanudar la canción
        self.current_song = {}  # Información de la canción actual

    @commands.hybrid_command(
            name="update",
            description="Actualiza la base de datos.",
    )
    async def show_settings(self, context: Context):
        try:
            # Obtener valores de las listas
            music_channels = self.play_channel
            music_messages = self.play_message
            music_roles = self.play_role
            
            # Crear un mensaje con los contenidos de las listas
            message = "Configuración actual:\n"
            message += f"Canal de música: {music_channels}\n"
            message += f"Mensaje de música: {music_messages}\n"
            message += f"Rol de música: {music_roles}\n"
            
            await context.send(message)
        except Exception as e:
            print(f"Error al mostrar la configuración: {e}")
            await context.send("Ha ocurrido un error al mostrar la configuración.")
    async def getEmptySong(self):
        return {
            "title": "No hay canciones en la lista de reproducción",
            "description": "Agrega canciones a la lista de reproducción con el comando `/play`",
            "thumbnail_url": "",
            "song_url": "",
        }

    async def create_music_embed(self, current_song, playlist):
        # Crear un objeto Embed
        embed = discord.Embed(
            title=current_song["title"],
            description=current_song["description"],
            color=0x3498DB  # Color azul
        )

        # Agregar una imagen de la portada de la canción
        embed.set_thumbnail(url=current_song["thumbnail_url"])

        # Agregar un cuadro grande con la canción que está sonando
        embed.set_image(url=current_song["song_url"])

        # Crear una lista de canciones en la lista de reproducción
        playlist_text = "\n".join([f"{i + 1}. {song}" for i, song in enumerate(playlist)])
        embed.add_field(name="Lista de Reproducción", value=playlist_text, inline=False)
        # Agregar botones para pausa, play y skip
        embed.set_footer(text="Controles:")

        return embed

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        # Manejar la interacción de botón
        if interaction.custom_id == "pause_button":
            await interaction.respond(content="Has presionado el botón de pausa.")
        elif interaction.custom_id == "play_button":
            await interaction.respond(content="Has presionado el botón de play.")
        elif interaction.custom_id == "skip_button":
            await interaction.respond(content="Has presionado el botón de skip.")

    @commands.hybrid_command(
        name="setchannel",
        description="Asigna un canal para reproducir las canciones.",
    )
    async def setchannel(self, context: Context):
        if context.guild is None:
            await context.send("Este comando solo se puede utilizar en un servidor.")
            return
        server_id = context.guild.id

        # Verifica si el usuario que ejecutó el comando es un administrador
        if context.author.guild_permissions.administrator:
            self.play_channel[server_id] = context.channel.id  # Usar el ID del canal, no la mención
            await  self.bot.database.setMusicChannel(server_id, context.channel.id)
            await context.send(f'Canal de lista de reproducción establecido en {context.channel.mention}')

            # Obtener el canal de lista de reproducción
            playlist_channel = self.bot.get_channel(self.play_channel[server_id])

            if playlist_channel:
                messages = []
                # Obtiene todos los mensajes en el canal
                async for message in playlist_channel.history(limit=None):
                    messages.append(message)
                for message in messages:
                    await message.delete()
                song = await self.getEmptySong()
                music_embed = await self.create_music_embed(song, [])  # Sin información de la canción actual y una lista de reproducción vacía

                music_view = MusicView()  # Crea una instancia de tu vista

                # Agrega la vista al contenido del mensaje
                music_embed.add_field(name="Controles", value="\u200B", inline=False)
                await context.send(embed=music_embed, view=music_view)

                # Puedes guardar el ID del mensaje si es necesario
                self.play_message[server_id] = message.id
                await self.bot.database.setMusicMessage(server_id, message.id)

            else:
                await context.send('No se pudo encontrar el canal de lista de reproducción.')
        else:
            await context.send('Solo los administradores pueden configurar el canal de lista de reproducción.')

    @commands.Cog.listener()
    async def on_message(self, message):
        playlist_channel = None
        playlist_message = None
        if message.guild is None:
            return
        server_id = message.guild.id
        if server_id not in self.play_channel:
            return
        playlist_channel = self.bot.get_channel(self.play_channel[server_id])
        if playlist_channel is not None and message.channel == playlist_channel:
            if message.author.bot:
                if self.play_channel[server_id] is not None:
                    playlist_channel = self.bot.get_channel(self.play_channel[server_id])
                else:
                    return
                if playlist_channel is not None and message.channel == playlist_channel:
                    playlist_message = await message.channel.fetch_message(self.play_message[server_id])
                    if playlist_message is not None and message.reference is not None and message.reference.message_id == playlist_message.id:
                            return
                await message.delete()
            if message.content.startswith('/'):
                    await self.bot.process_commands(message)
                    await message.delete()
            else:    
                    playlist_message = await message.channel.fetch_message(self.play_message[server_id])
                    await playlist_message.edit(content=f"Nuevo mensaje de {message.author.mention}: {message.content}")
                    await message.delete()
        return

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
            views = video_info["views"]

            # Mensaje de información de la canción
            info_message = f"**Canción solicitada por {context.author.mention}**\n\n" \
                        f"**Título:** {title}\n" \
                        f"**Vistas:** {views}\n" \
                        f"**Enlace:** {video_url}"

            await context.send(info_message)

            # Descargar y agregar a la lista de reproducción
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'opus',
                    'preferredquality': '192',
                }],
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                url2 = info['url']

            source = discord.FFmpegPCMAudio(url2)
            self.queue[server_id].append(source)

            if not self.voice[server_id].is_playing() and len(self.queue[server_id]) == 1:
                self.play_next(server_id)

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



