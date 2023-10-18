CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `servers` (
  `id` VARCHAR(20) NOT NULL PRIMARY KEY,
  `music_channel` VARCHAR(20) NOT NULL,
  `music_message` VARCHAR(20) NOT NULL,
  `music_role` VARCHAR(20) NOT NULL
);