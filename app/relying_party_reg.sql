-- --------------------------------------------------------
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


CREATE DATABASE IF NOT EXISTS `relyingparty_reg` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `relyingparty_reg`;

CREATE TABLE IF NOT EXISTS `access_certificate` (
  `accessCertificate_id` int(11) NOT NULL AUTO_INCREMENT,
  `intended_use` varchar(255) DEFAULT NULL,
  `certificate` text NOT NULL,
  `certificate_issuer` varchar(255) DEFAULT NULL,
  `certificate_distinguished_name` varchar(255) DEFAULT NULL,
  `validity_from` date DEFAULT NULL,
  `validity_to` date DEFAULT NULL,
  `serial_number` varchar(100) DEFAULT NULL,
  `status` enum('active','revoke','expired') NOT NULL,
  `DNS_name` varchar(255) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `relyingParty_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`accessCertificate_id`),
  KEY `fk_user_accessCert` (`user_id`),
  KEY `fk_relyingParty_accessCert` (`relyingParty_id`),
  CONSTRAINT `fk_relyingParty_accessCert` FOREIGN KEY (`relyingParty_id`) REFERENCES `relying_party` (`relyingParty_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_user_accessCert` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `relying_party` (
  `relyingParty_id` int(11) NOT NULL AUTO_INCREMENT,
  `country` varchar(100) NOT NULL,
  `name` varchar(255) NOT NULL,
  `registration_number` varchar(100) DEFAULT NULL,
  `common_name` varchar(255) DEFAULT NULL,
  `contacts` text DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`relyingParty_id`),
  KEY `fk_user_relyingParty` (`user_id`),
  CONSTRAINT `fk_user_relyingParty` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `hash_pid` varchar(256) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
