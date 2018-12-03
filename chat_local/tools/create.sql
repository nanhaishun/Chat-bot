DROP TABLE IF EXISTS `dialogue`;

CREATE TABLE `dialogue` (
  `id` int(4) unsigned NOT NULL AUTO_INCREMENT,
  `msgId` varchar(256) NOT NULL COMMENT 'msgId',
  `partyNo` varchar(256) NOT NULL COMMENT 'partyNo',
  `question` text NOT NULL COMMENT 'question',
  `responses` text NOT NULL COMMENT 'responses',
  `time_stamp` TIMESTAMP(6) NOT NULL COMMENT 'TIMESTAMP',
  PRIMARY KEY (`id`)
  -- UNIQUE KEY `name_UNIQUE` (`msgId`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
-- INSERT INTO `dialogue` VALUES (1,'no.1','lu2345678','爱理财','hello',NOW());