-- --------------------------------------------------------
-- Anfitrião:                    127.0.0.1
-- Versão do servidor:           11.4.2-MariaDB - mariadb.org binary distribution
-- SO do servidor:               Win64
-- HeidiSQL Versão:              12.6.0.6765
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- A despejar estrutura da base de dados para relyingparty_reg
CREATE DATABASE IF NOT EXISTS `relyingparty_reg` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `relyingparty_reg`;

-- A despejar estrutura para tabela relyingparty_reg.credential
CREATE TABLE IF NOT EXISTS `credential` (
  `credential_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `format` varchar(50) NOT NULL,
  `meta` text DEFAULT NULL,
  `path` varchar(255) DEFAULT NULL,
  `credentialValues` text DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`credential_id`),
  KEY `fk_cred_user` (`user_id`),
  CONSTRAINT `fk_cred_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela relyingparty_reg.intendeduse
CREATE TABLE IF NOT EXISTS `intendeduse` (
  `intendeduse_id` int(11) NOT NULL AUTO_INCREMENT,
  `createdAt` datetime NOT NULL,
  `revokedAt` datetime DEFAULT NULL,
  `intendedUseIdentifier` varchar(255) DEFAULT NULL,
  `type_policy` varchar(255) DEFAULT NULL,
  `policy_uri` varchar(255) DEFAULT NULL,
  `purpose` text DEFAULT NULL,
  `credential_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `wrp` int(11) DEFAULT NULL,
  PRIMARY KEY (`intendeduse_id`),
  KEY `fk_iu_cred` (`credential_id`),
  KEY `fk_iu_user` (`user_id`),
  KEY `fk_iu_wrp` (`wrp`),
  CONSTRAINT `fk_iu_cred` FOREIGN KEY (`credential_id`) REFERENCES `credential` (`credential_id`),
  CONSTRAINT `fk_iu_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`),
  CONSTRAINT `fk_iu_wrp` FOREIGN KEY (`wrp`) REFERENCES `walletrelyingparty` (`wrp_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela relyingparty_reg.legalentity
CREATE TABLE IF NOT EXISTS `legalentity` (
  `legalentity_id` int(11) NOT NULL AUTO_INCREMENT,
  `legalperson_id` int(11) DEFAULT NULL,
  `naturalperson_id` int(11) DEFAULT NULL,
  `postalAddress` varchar(255) DEFAULT NULL,
  `country` varchar(100) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `infoURI` varchar(255) DEFAULT NULL,
  `identifier` varchar(255) DEFAULT NULL,
  `identifierType` varchar(255) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`legalentity_id`),
  KEY `fk_le_legalperson` (`legalperson_id`),
  KEY `fk_le_naturalperson` (`naturalperson_id`),
  KEY `fk_le_user` (`user_id`),
  CONSTRAINT `fk_le_legalperson` FOREIGN KEY (`legalperson_id`) REFERENCES `legalperson` (`legalperson_id`),
  CONSTRAINT `fk_le_naturalperson` FOREIGN KEY (`naturalperson_id`) REFERENCES `naturalperson` (`naturalperson_id`),
  CONSTRAINT `fk_le_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela relyingparty_reg.legalperson
CREATE TABLE IF NOT EXISTS `legalperson` (
  `legalperson_id` int(11) NOT NULL AUTO_INCREMENT,
  `legalBasis` text NOT NULL,
  `legalName` varchar(255) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`legalperson_id`),
  KEY `fk_legalperson_user` (`user_id`),
  CONSTRAINT `fk_legalperson_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela relyingparty_reg.naturalperson
CREATE TABLE IF NOT EXISTS `naturalperson` (
  `naturalperson_id` int(11) NOT NULL AUTO_INCREMENT,
  `givenName` varchar(100) NOT NULL,
  `familyName` varchar(100) NOT NULL,
  `dateOfBirth` date DEFAULT NULL,
  `placeOfBirth` varchar(255) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`naturalperson_id`),
  KEY `np_user_id` (`user_id`),
  CONSTRAINT `np_user_id` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela relyingparty_reg.user
CREATE TABLE IF NOT EXISTS `user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `hash_pid` varchar(256) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela relyingparty_reg.walletrelyingparty
CREATE TABLE IF NOT EXISTS `walletrelyingparty` (
  `wrp_id` int(11) NOT NULL AUTO_INCREMENT,
  `tradeName` varchar(255) DEFAULT NULL,
  `supportURI` varchar(255) DEFAULT NULL,
  `srvDescription` text DEFAULT NULL,
  `intended_use` int(11) DEFAULT NULL,
  `isPSB` tinyint(1) DEFAULT 0,
  `entitlement` varchar(255) DEFAULT NULL,
  `providesAttestations` int(11) DEFAULT NULL,
  `supervisorAuthority` int(11) DEFAULT NULL,
  `isIntermediary` tinyint(1) DEFAULT NULL,
  `registryURI` varchar(255) DEFAULT NULL,
  `usesIntermediary` int(11) DEFAULT NULL,
  `providerType` varchar(100) DEFAULT NULL,
  `x5c` varchar(255) DEFAULT NULL,
  `typePolicy` varchar(255) DEFAULT NULL,
  `policyURI` varchar(255) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `legalEntity` int(11) DEFAULT NULL,
  PRIMARY KEY (`wrp_id`),
  KEY `fk_wrp_supervisor` (`supervisorAuthority`),
  KEY `fk_wrp_intermediary` (`usesIntermediary`),
  KEY `fk_wrp_user` (`user_id`),
  KEY `fk_wrp_iu` (`intended_use`),
  KEY `fk_wrp_cred` (`providesAttestations`),
  KEY `fk_wrp_le` (`legalEntity`),
  CONSTRAINT `fk_wrp_cred` FOREIGN KEY (`providesAttestations`) REFERENCES `credential` (`credential_id`),
  CONSTRAINT `fk_wrp_intermediary` FOREIGN KEY (`usesIntermediary`) REFERENCES `walletrelyingparty` (`wrp_id`),
  CONSTRAINT `fk_wrp_iu` FOREIGN KEY (`intended_use`) REFERENCES `intendeduse` (`intendeduse_id`),
  CONSTRAINT `fk_wrp_le` FOREIGN KEY (`legalEntity`) REFERENCES `legalentity` (`legalentity_id`),
  CONSTRAINT `fk_wrp_supervisor` FOREIGN KEY (`supervisorAuthority`) REFERENCES `legalentity` (`legalentity_id`),
  CONSTRAINT `fk_wrp_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
