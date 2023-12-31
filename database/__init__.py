""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 6.1.0
"""


import aiosqlite
class DatabaseManager:
    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection
    
    async def get_info_servers(self) -> int:
        rows = await self.connection.execute(
            "SELECT COUNT(*) FROM servers",
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0
        
    async def get_info_server(self, server_id: int) -> {}:
        rows = await self.connection.execute(
            "SELECT * FROM servers WHERE id=?",
            (
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            for row in result:
                print (row)
                print (type(row))
            return result if result is not None else 0
        

    async def add_server(self, server_id: int) -> None:
        """
        This function will add a server to the database.

        :param server_id: The ID of the server.
        """
        rows = await self.connection.execute(
            "SELECT id FROM servers WHERE id=?",
            (
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            if result is None:
                print(f"Adding server {server_id} to the database.")
                await self.connection.execute(
                    "INSERT INTO servers VALUES (?,NULL,NULL,NULL)",
                    (
                        server_id,
                    ),
                )
                await self.connection.commit()
            else:
                print(f"Server {server_id} already exists in the database.")
    
    async def getMusicChannel(self, server_id: int) -> {int, int}:
        rows = await self.connection.execute(
            "SELECT id, music_channel FROM servers WHERE id=?",
            (
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result if result is not None else 0
    
    async def getMusicChannels(self) -> {int, int}:
        rows = await self.connection.execute(
            "SELECT id, music_channel FROM servers",
        )
        async with rows as cursor:
            results = await cursor.fetchall()
            music_channels = {}
            for result in results:
                server_id, channel_id = result
                server_id = int(server_id)
                music_channels[server_id] = int(channel_id)
            return music_channels
    
    async def setMusicChannel(self, server_id: int, channel_id: int) -> None:
            result = await self.connection.execute(
            "UPDATE servers SET music_channel = ? WHERE id = ?",
            (channel_id, server_id)
            )
            if result is None:
                print (f"Server {server_id} does not exist in the database.")
            else:
                print(f"Updating channel {channel_id} in {server_id} on the database.")
            await self.connection.commit()
    
    async def getMusicRole(self, server_id: int) -> int:
        rows = await self.connection.execute(
            "SELECT music_role FROM servers WHERE id=?",
            (
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result if result is not None else 0
    
    async def setMusicRole(self, server_id: int, role_id: int) -> None:
        await self.connection.execute(
            "UPDATE servers SET music_role=? WHERE id=?",
            (
                role_id,
                server_id,
            ),
        )
        await self.connection.commit()

    async def getMusicRoles(self) -> {int, int}:
        rows = await self.connection.execute(
            "SELECT id, music_role FROM servers",
        )
        async with rows as cursor:
            results = await cursor.fetchall()
            music_roles = {}
            for result in results:
                print (result)
                server_id, role_id = result
                music_roles[server_id] = role_id
            return music_roles
    
    async def getMusicMessage(self, server_id: int) -> int:
        rows = await self.connection.execute(
            "SELECT music_message FROM servers WHERE id=?",
            (
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result if result is not None else 0
    
    async def setMusicMessage(self, server_id: int, message_id: int) -> None:
        await self.connection.execute(
            "UPDATE servers SET music_message=? WHERE id=?",
            (
                message_id,
                server_id,
            ),
        )
        await self.connection.commit()

    async def getMusicMessages(self) -> {int, int}:
        rows = await self.connection.execute(
            "SELECT id, music_message FROM servers",
        )
        async with rows as cursor:
            results = await cursor.fetchall()
            music_messages = {}
            for result in results:
                server_id, message_id = result
                music_messages[server_id] = message_id
            return music_messages
        
    async def add_warn(
        self, user_id: int, server_id: int, moderator_id: int, reason: str
    ) -> int:
        """
        This function will add a warn to the database.

        :param user_id: The ID of the user that should be warned.
        :param reason: The reason why the user should be warned.
        """
        rows = await self.connection.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            warn_id = result[0] + 1 if result is not None else 1
            await self.connection.execute(
                "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",
                (
                    warn_id,
                    user_id,
                    server_id,
                    moderator_id,
                    reason,
                ),
            )
            await self.connection.commit()
            return warn_id

    async def remove_warn(self, warn_id: int, user_id: int, server_id: int) -> int:
        """
        This function will remove a warn from the database.

        :param warn_id: The ID of the warn.
        :param user_id: The ID of the user that was warned.
        :param server_id: The ID of the server where the user has been warned
        """
        await self.connection.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (
                warn_id,
                user_id,
                server_id,
            ),
        )
        await self.connection.commit()
        rows = await self.connection.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

    async def get_warnings(self, user_id: int, server_id: int) -> list:
        """
        This function will get all the warnings of a user.

        :param user_id: The ID of the user that should be checked.
        :param server_id: The ID of the server that should be checked.
        :return: A list of all the warnings of the user.
        """
        rows = await self.connection.execute(
            "SELECT user_id, server_id, moderator_id, reason, strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list
