import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import Context
from youtube_search import YoutubeSearch 
import youtube_dlc as youtube_dl


# Crear una extensión separada para el reproductor de música
# Define una vista personalizada que contiene los botones
class MusicView(discord.ui.View):
    def __init__(self,cog):
        super().__init__()
        self.cog = cog

    @discord.ui.button(label="", custom_id="button-start", style=discord.ButtonStyle.primary, emoji="▶️") # the button has a custom_id set
    async def start_button_callback(self, interaction, button):
        server_id = interaction.guild_id
        await self.cog.start_stop(server_id)
        try:
            await interaction.response.defer()
        except:
            pass

    @discord.ui.button(label="", custom_id="button-skip", style=discord.ButtonStyle.primary, emoji="⏭️") # the button has a custom_id set
    async def skip_button_callback(self, interaction, button):
        server_id = interaction.guild_id
        #Añadir la comprobación de permisos
        await self.cog.skip(server_id)
        try:
            await interaction.response.defer()
        except:
            pass

    @discord.ui.button(label="", custom_id="button-exit", style=discord.ButtonStyle.primary, emoji="⏏️") # the button has a custom_id set
    async def exit_button_callback(self, interaction, button):
        server_id = interaction.guild_id
        #Añadir la comprobación de permisos
        await self.cog.exit(server_id)
        try:
            await interaction.response.defer()
        except:
            pass

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
        self.music_view = {} #Vista de los botones de musica
        self.play_channel[721752348443017237] = 1164259244904824862
        self.play_message[721752348443017237] = 1164722172636450927 
        self.queue[721752348443017237] = []
        self.voice[721752348443017237] = None

    async def start_stop(self, server_id):
        if server_id in self.voice:
            if self.voice[server_id].is_playing():
                self.voice[server_id].pause()
                #self.is_running = not self.is_running
            else:
                self.voice[server_id].resume()
                #self.is_running = not self.is_running
        else:
            if server_id in self.queue and self.queue[server_id] is not None and len(self.queue[server_id]) > 0:
                self.play_next(server_id)
                #self.is_running = not self.is_running
            else:
                play_channel = self.bot.get_channel(self.play_channel[server_id])
                await self.bot.autodeleteMessage(play_channel, "No hay canciones en la lista de reproducción. Agrega canciones con el comando `/play`")
        

    async def skip(self, server_id):
        if server_id in self.voice:
            self.voice[server_id].stop()
            if len(self.queue[server_id]) > 0:
                self.play_next(server_id)
                #self.is_running = not self.is_running
            else:
                return
    async def exit(self, server_id):
        if server_id in self.voice:
            await self.voice[server_id].disconnect()
            self.voice[server_id] = None
            self.queue[server_id].clear()
            self.current_song[server_id] = None
            await self.updateSong(server_id)
        else:
            return


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
            "title": "No hay canciones en la lista de reproducción",
            "thumbnail_url": "",
            "views": "",
            "author": "",
            "author_url": "",
            "duration": "",
            "song_url": "",
            "requested_by": "",
            "source": None,
        }
    async def createSong(self,title, thumbnail_url, views, author, author_url, duration, video_url, requested_by, source):
        return {
            "title": title,
            "thumbnail_url": thumbnail_url,
            "views": views,
            "author": author,
            "author_url": author_url,
            "duration": duration,
            "song_url": video_url,
            "requested_by": requested_by,
            "source": source,
        }

    async def create_music_embed(self, current_song, playlist):
        # Crear un objeto Embed
        if current_song["title"] == "No hay canciones en la lista de reproducción":
            description = "Agrega canciones a la lista de reproducción con el comando `/play`"
        else:
            description = f"De **[{current_song['author']}]({current_song['author_url'].replace(' ', '')})** dura `{current_song['duration']}`\n"
            description += f"Pedida por <@{current_song['requested_by']}>\n"
            description += f"Vistas: `{current_song['views']}`\n"
            description += f"[Ver en YouTube]({current_song['song_url']})"
        embed = discord.Embed(
            title=current_song["title"],
            description=description,
            color=0x3498DB  # Color azul
        )

        # Agregar un cuadro grande con la canción que está sonando
        embed.set_image(url=current_song["thumbnail_url"])

        # Crear una lista de canciones en la lista de reproducción
        playlist_text = "\n".join([f"{i + 1}. {song['title']}" for i, song in enumerate(playlist)])
        embed.add_field(name="Lista de Reproducción", value=playlist_text, inline=False)

        return embed

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        # Manejar la interacción de botón
        if interaction.custom_id == "pause_button":
            await interaction.respond(content="Has presionado el botón de pausa.")
        elif interaction.custom_id == "button-start":
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

                music_view = MusicView(self)  # Crea una instancia de tu vista
                self.music_view[server_id] = music_view
                # Agrega la vista al contenido del mensaje
                music_embed.add_field(name="Controles", value="\u200B", inline=False)
                await context.send(embed=music_embed, view=self.music_view[server_id])

                # Puedes guardar el ID del mensaje si es necesario
                self.play_message[server_id] = message.id
                self.queue[server_id] = []
                self.voice[server_id] = None
                await self.bot.database.setMusicMessage(server_id, message.id)

            else:
                await context.send('No se pudo encontrar el canal de lista de reproducción.')
        else:
            await context.send('Solo los administradores pueden configurar el canal de lista de reproducción.')

    @commands.Cog.listener()
    async def on_message(self, message):
        playlist_channel = None
        playlist_message = None
        # Verifica si el mensaje es de un servidor
        if message.guild is not None:
            server_id = message.guild.id
            # Verifica si el servidor tiene un canal de lista de reproducción configurado
            if server_id in self.play_channel:
                playlist_channel = self.bot.get_channel(self.play_channel[server_id])

                # Verifica si el mensaje proviene del canal de lista de reproducción
                if playlist_channel is not None and message.channel == playlist_channel:
                    # Verifica si el mensaje proviene de un bot
                    if not message.author.bot:
                        # Verifica si el mensaje comienza con un comando
                        if message.content.startswith('/'):
                            await self.bot.process_commands(message)
                            await message.delete()
                        else:
                            # Aquí puedes realizar otras acciones personalizadas si no es un comando
                            await message.delete()

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

    async def check_voice(self,ctx, bot):
        server_id = ctx.guild.id

        if server_id in bot.voice_clients:
            voice_client = bot.voice_clients[server_id]
            if voice_client.is_connected():
                voice_client.disconnect()
                self.initializated = True



    @commands.hybrid_command(
        name="playe",
        description="Play a YouTube video in the voice channel.",
    )
    async def play(self, context: Context, query: str):
        if context.guild is None:
            await self.bot.autodeleteMessage(context, "Este comando solo se puede utilizar en un servidor.")
        else:
            server_id = context.guild.id
            if server_id in self.play_channel:
                play_channel = self.bot.get_channel(self.play_channel[server_id])
            else:
                await self.bot.autodeleteMessage(context, "No se ha configurado ningún canal de lista de reproducción. 😢")
                return
            if context.channel != play_channel:
                await self.bot.autodeleteMessage(context, "Este comando solo se puede utilizar en el canal de lista de reproducción. 💡")
                return
            elif context.author.voice is None:
                await self.bot.autodeleteMessage(context, "No estás en un canal de voz. 👹")
                return
            elif query == "":
                await self.bot.autodeleteMessage(context, "Si no me das una canción, mal vamos 👹")
                return
            elif server_id in self.voice:
                    if self.voice[server_id] is not None and self.voice[server_id].is_connected() and context.author.voice.channel.id != self.voice[server_id].channel.id:
                        await self.bot.autodeleteMessage(context, "🎉 ¡Estamos de fiesta en otro canal! ¿No vienes o no puedes? 🤨")
                        return
                    else:
                        if self.voice[server_id] == None:
                            self.voice[server_id] = await context.author.voice.channel.connect()

    
                
        send_message = await context.send("Buscando canción...")

    # Utilizar youtube-search-python para buscar el video
        results = YoutubeSearch(query, max_results=1).to_dict()
        id = -1
        if results:
            #Se queda con el primer id que tenga mas de 0 de duración
            
            for i, result in enumerate(results):
                duration = result["duration"]

                if isinstance(duration, str):
                    if duration != "0":
                        id = i
                        break
                elif isinstance(duration, int):
                    # Si ya es un entero (int), puedes usarlo directamente
                    if duration > 0:
                        id = i
                        break
            if id == -1:
                await self.bot.autodeleteMessage(context, "No se ha encontrado ninguna canción repoducible. 😢")
                await send_message.delete()
                return

            video_id = results[id]["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Obtener información del video
            video_info = results[id]
            title = video_info["title"]
            duration = video_info["duration"]
            await send_message.edit(content=f"Reproduciendo '{title}'...")
            views = video_info["views"]
            author = video_info["channel"]
            author_url = f"https://www.youtube.com/@{video_info['channel']}"

            requested_by = context.author.id

            # Obtener la imagen de la portada del video
            thumbnail_url = video_info["thumbnails"][0]

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
            song = await self.createSong(title, thumbnail_url, views, author, author_url, duration, video_url, requested_by, source)
            self.queue[server_id].append(song)
            await send_message.delete()
            if not self.voice[server_id].is_playing() and len(self.queue[server_id]) == 1:
                await self.play_next(server_id)
            else:
                await self.updateSong(server_id)
            #await send_message.delete()

    async def play_next(self, server_id):
        if len(self.queue[server_id]) > 0:
            song = self.queue[server_id][0]
            source = song["source"]
            self.current_song[server_id] = song
            await self.updateSong(server_id)
            self.queue[server_id].pop(0)
            if self.voice[server_id] is not None:
                self.voice[server_id].play(source, after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(server_id), self.bot.loop))
        else:
            await self.updateSong(server_id)
            if self.voice[server_id] is not None:
                await self.voice[server_id].disconnect()
                self.voice[server_id] = None


    async def updateSong(self, server_id):
        if (self.play_channel[server_id] is not None and self.play_message[server_id] is not None):

            #Obetener siguiente canción
            if len(self.queue[server_id]) > 0:
                song = self.current_song[server_id]
            else:
                song = await self.getEmptySong()
            # Crear un objeto Embed
            music_embed = await self.create_music_embed(song, self.queue[server_id])
            # Crear una instancia de tu vista
            music_view = MusicView(self)
            if server_id in self.music_view:
                self.music_view[server_id].clear_items()
                self.music_view[server_id] = music_view
                # Edita el mensaje con la nueva información
                playlist_channel = self.bot.get_channel(self.play_channel[server_id])
                playlist_message = await playlist_channel.fetch_message(self.play_message[server_id])
                await playlist_message.edit(embed=music_embed, view = self.music_view[server_id])
                return
            else:
                self.music_view[server_id] = music_view
                playlist_channel = self.bot.get_channel(self.play_channel[server_id])
                playlist_message = await playlist_channel.fetch_message(self.play_message[server_id])
                await playlist_message.delete()
                playlist_message = await playlist_channel.send(embed=music_embed, view = self.music_view[server_id])
                self.play_message[server_id] = playlist_message.id
                await self.bot.database.setMusicMessage(server_id, playlist_message.id)              


    @commands.hybrid_command(
        name="leave",
        description="Leave the voice channel.",
    )
    async def leave(self, context: Context):
        server_id = context.guild.id
        if server_id in self.voice:
            if self.voice[server_id].is_connected():
                await self.voice[server_id].disconnect()
                self.voice[server_id] = None
                self.queue[server_id] = []
            else:
                await context.send("I'm not in a voice channel.")
        else:
            await context.send("I'm not in a voice channel.")


# Agrega la extensión al bot
async def setup(bot) -> None:
    await bot.add_cog(MusicPlayer(bot))



