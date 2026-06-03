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


-- A despejar estrutura da base de dados para wrp
CREATE DATABASE IF NOT EXISTS `wrp` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `wrp`;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.user
CREATE TABLE IF NOT EXISTS `user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `hash_pid` varchar(256) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.law
CREATE TABLE IF NOT EXISTS `law` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legislative_identifier` varchar(255) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `law_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.law_legal_basis
CREATE TABLE IF NOT EXISTS `law_legal_basis` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `law_id` int(11) DEFAULT NULL,
  `legal_basis` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `law_id` (`law_id`),
  CONSTRAINT `law_legal_basis_ibfk_1` FOREIGN KEY (`law_id`) REFERENCES `law` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_person
CREATE TABLE IF NOT EXISTS `legal_person` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `legal_person_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_person_law
CREATE TABLE IF NOT EXISTS `legal_person_law` (
  `legal_person_id` int(11) NOT NULL,
  `law_id` int(11) NOT NULL,
  PRIMARY KEY (`legal_person_id`,`law_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_person_name
CREATE TABLE IF NOT EXISTS `legal_person_name` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legal_person_id` int(11) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `legal_person_id` (`legal_person_id`),
  CONSTRAINT `legal_person_name_ibfk_1` FOREIGN KEY (`legal_person_id`) REFERENCES `legal_person` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.natural_person
CREATE TABLE IF NOT EXISTS `natural_person` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `family_name` varchar(255) NOT NULL,
  `given_name` varchar(255) NOT NULL,
  `date_of_birth` date DEFAULT NULL,
  `place_of_birth` varchar(255) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `natural_person_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.identifier
CREATE TABLE IF NOT EXISTS `identifier` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `identifier` varchar(255) NOT NULL,
  `type` varchar(100) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `identifier_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_entity
CREATE TABLE IF NOT EXISTS `legal_entity` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legal_person_id` int(11) DEFAULT NULL,
  `natural_person_id` int(11) DEFAULT NULL,
  `country` varchar(10) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `legal_person_id` (`legal_person_id`),
  KEY `natural_person_id` (`natural_person_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `legal_entity_ibfk_1` FOREIGN KEY (`legal_person_id`) REFERENCES `legal_person` (`id`),
  CONSTRAINT `legal_entity_ibfk_2` FOREIGN KEY (`natural_person_id`) REFERENCES `natural_person` (`id`),
  CONSTRAINT `legal_entity_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_entity_identifier
CREATE TABLE IF NOT EXISTS `legal_entity_identifier` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legal_entity_id` int(11) DEFAULT NULL,
  `identifier_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `legal_entity_id` (`legal_entity_id`),
  KEY `identifier_id` (`identifier_id`),
  CONSTRAINT `legal_entity_identifier_ibfk_1` FOREIGN KEY (`legal_entity_id`) REFERENCES `legal_entity` (`id`),
  CONSTRAINT `legal_entity_identifier_ibfk_2` FOREIGN KEY (`identifier_id`) REFERENCES `identifier` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_entity_email
CREATE TABLE IF NOT EXISTS `legal_entity_email` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legal_entity_id` int(11) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `legal_entity_id` (`legal_entity_id`),
  CONSTRAINT `legal_entity_email_ibfk_1` FOREIGN KEY (`legal_entity_id`) REFERENCES `legal_entity` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_entity_info_uri
CREATE TABLE IF NOT EXISTS `legal_entity_info_uri` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legal_entity_id` int(11) DEFAULT NULL,
  `uri` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `legal_entity_id` (`legal_entity_id`),
  CONSTRAINT `legal_entity_info_uri_ibfk_1` FOREIGN KEY (`legal_entity_id`) REFERENCES `legal_entity` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_entity_phone
CREATE TABLE IF NOT EXISTS `legal_entity_phone` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legal_entity_id` int(11) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `legal_entity_id` (`legal_entity_id`),
  CONSTRAINT `legal_entity_phone_ibfk_1` FOREIGN KEY (`legal_entity_id`) REFERENCES `legal_entity` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.legal_entity_postal_address
CREATE TABLE IF NOT EXISTS `legal_entity_postal_address` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legal_entity_id` int(11) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `legal_entity_id` (`legal_entity_id`),
  CONSTRAINT `legal_entity_postal_address_ibfk_1` FOREIGN KEY (`legal_entity_id`) REFERENCES `legal_entity` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.provider
CREATE TABLE IF NOT EXISTS `provider` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `legal_entity_id` int(11) NOT NULL,
  `provider_type` varchar(100) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `legal_entity_id` (`legal_entity_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `provider_ibfk_1` FOREIGN KEY (`legal_entity_id`) REFERENCES `legal_entity` (`id`),
  CONSTRAINT `provider_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.provider_x5c
CREATE TABLE IF NOT EXISTS `provider_x5c` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `provider_id` int(11) DEFAULT NULL,
  `certificate` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `provider_id` (`provider_id`),
  CONSTRAINT `provider_x5c_ibfk_1` FOREIGN KEY (`provider_id`) REFERENCES `provider` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.policy
CREATE TABLE IF NOT EXISTS `policy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `policy_uri` text DEFAULT NULL,
  `type` varchar(100) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `policy_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.provider_policy
CREATE TABLE IF NOT EXISTS `provider_policy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `provider_id` int(11) DEFAULT NULL,
  `policy_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `provider_id` (`provider_id`),
  KEY `policy_id` (`policy_id`),
  CONSTRAINT `provider_policy_ibfk_1` FOREIGN KEY (`provider_id`) REFERENCES `provider` (`id`),
  CONSTRAINT `provider_policy_ibfk_2` FOREIGN KEY (`policy_id`) REFERENCES `policy` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.credential
CREATE TABLE IF NOT EXISTS `credential` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `format` varchar(100) NOT NULL,
  `meta` text NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `credential_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- A despejar estrutura para tabela wrp.claim
CREATE TABLE IF NOT EXISTS `claim` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `credential_id` int(11) NOT NULL,
  `path` longtext DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_claim_credential` (`credential_id`),
  CONSTRAINT `FK_claim_credential` FOREIGN KEY (`credential_id`) REFERENCES `credential` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.intended_use
CREATE TABLE IF NOT EXISTS `intended_use` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `intended_use_identifier` varchar(255) NOT NULL,
  `created_at` date NOT NULL,
  `revoked_at` date DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `intended_use_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.intended_use_credential
CREATE TABLE IF NOT EXISTS `intended_use_credential` (
  `intended_use_id` int(11) NOT NULL,
  `credential_id` int(11) NOT NULL,
  PRIMARY KEY (`intended_use_id`,`credential_id`),
  KEY `credential_id` (`credential_id`),
  CONSTRAINT `intended_use_credential_ibfk_1` FOREIGN KEY (`intended_use_id`) REFERENCES `intended_use` (`id`),
  CONSTRAINT `intended_use_credential_ibfk_2` FOREIGN KEY (`credential_id`) REFERENCES `credential` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.intended_use_policy
CREATE TABLE IF NOT EXISTS `intended_use_policy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `intended_use_id` int(11) DEFAULT NULL,
  `policy_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `intended_use_id` (`intended_use_id`),
  KEY `policy_id` (`policy_id`),
  CONSTRAINT `intended_use_policy_ibfk_1` FOREIGN KEY (`intended_use_id`) REFERENCES `intended_use` (`id`),
  CONSTRAINT `intended_use_policy_ibfk_2` FOREIGN KEY (`policy_id`) REFERENCES `policy` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.multilanguage_string
CREATE TABLE IF NOT EXISTS `multilanguage_string` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lang` varchar(10) DEFAULT NULL,
  `content` text DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `multilanguage_string_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.intended_use_purpose
CREATE TABLE IF NOT EXISTS `intended_use_purpose` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `intended_use_id` int(11) DEFAULT NULL,
  `mls_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `intended_use_id` (`intended_use_id`),
  KEY `mls_id` (`mls_id`),
  CONSTRAINT `intended_use_purpose_ibfk_1` FOREIGN KEY (`intended_use_id`) REFERENCES `intended_use` (`id`),
  CONSTRAINT `intended_use_purpose_ibfk_2` FOREIGN KEY (`mls_id`) REFERENCES `multilanguage_string` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.provided_attestation
CREATE TABLE IF NOT EXISTS `provided_attestation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `format` varchar(100) NOT NULL,
  `meta` text NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `provided_attestation_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.supervisory_authority
CREATE TABLE IF NOT EXISTS `supervisory_authority` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `country` varchar(10) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `supervisory_authority_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.supervisory_authority_email
CREATE TABLE IF NOT EXISTS `supervisory_authority_email` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `authority_id` int(11) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `authority_id` (`authority_id`),
  CONSTRAINT `supervisory_authority_email_ibfk_1` FOREIGN KEY (`authority_id`) REFERENCES `supervisory_authority` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.supervisory_authority_formuri
CREATE TABLE IF NOT EXISTS `supervisory_authority_formuri` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `authority_id` int(11) DEFAULT NULL,
  `formURI` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `authority_id` (`authority_id`),
  CONSTRAINT `supervisory_authority_formuri_ibfk_1` FOREIGN KEY (`authority_id`) REFERENCES `supervisory_authority` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.supervisory_authority_phone
CREATE TABLE IF NOT EXISTS `supervisory_authority_phone` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `authority_id` int(11) DEFAULT NULL,
  `phone` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `authority_id` (`authority_id`),
  CONSTRAINT `supervisory_authority_phone_ibfk_1` FOREIGN KEY (`authority_id`) REFERENCES `supervisory_authority` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.wallet_relying_party
CREATE TABLE IF NOT EXISTS `wallet_relying_party` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `provider_id` int(11) NOT NULL,
  `trade_name` varchar(255) DEFAULT NULL,
  `is_psb` tinyint(1) NOT NULL,
  `registry_uri` text NOT NULL,
  `is_intermediary` tinyint(1) NOT NULL,
  `supervisory_authority_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `provider_id` (`provider_id`),
  KEY `supervisory_authority_id` (`supervisory_authority_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `wallet_relying_party_ibfk_1` FOREIGN KEY (`provider_id`) REFERENCES `provider` (`id`),
  CONSTRAINT `wallet_relying_party_ibfk_2` FOREIGN KEY (`supervisory_authority_id`) REFERENCES `supervisory_authority` (`id`),
  CONSTRAINT `wallet_relying_party_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.wrp_entitlement
CREATE TABLE IF NOT EXISTS `wrp_entitlement` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `wrp_id` int(11) DEFAULT NULL,
  `entitlement` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wrp_id` (`wrp_id`),
  CONSTRAINT `wrp_entitlement_ibfk_1` FOREIGN KEY (`wrp_id`) REFERENCES `wallet_relying_party` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.wrp_intended_use
CREATE TABLE IF NOT EXISTS `wrp_intended_use` (
  `wrp_id` int(11) NOT NULL,
  `intended_use_id` int(11) NOT NULL,
  PRIMARY KEY (`wrp_id`,`intended_use_id`),
  KEY `intended_use_id` (`intended_use_id`),
  CONSTRAINT `wrp_intended_use_ibfk_1` FOREIGN KEY (`wrp_id`) REFERENCES `wallet_relying_party` (`id`),
  CONSTRAINT `wrp_intended_use_ibfk_2` FOREIGN KEY (`intended_use_id`) REFERENCES `intended_use` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.wrp_intermediary
CREATE TABLE IF NOT EXISTS `wrp_intermediary` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `wrp_id` int(11) DEFAULT NULL,
  `intermediary_wrp_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wrp_id` (`wrp_id`),
  KEY `intermediary_wrp_id` (`intermediary_wrp_id`),
  CONSTRAINT `wrp_intermediary_ibfk_1` FOREIGN KEY (`wrp_id`) REFERENCES `wallet_relying_party` (`id`),
  CONSTRAINT `wrp_intermediary_ibfk_2` FOREIGN KEY (`intermediary_wrp_id`) REFERENCES `wallet_relying_party` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.wrp_provided_attestation
CREATE TABLE IF NOT EXISTS `wrp_provided_attestation` (
  `wrp_id` int(11) NOT NULL,
  `provided_attestation_id` int(11) NOT NULL,
  PRIMARY KEY (`wrp_id`,`provided_attestation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.wrp_srv_description
CREATE TABLE IF NOT EXISTS `wrp_srv_description` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `wrp_id` int(11) DEFAULT NULL,
  `mls_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wrp_id` (`wrp_id`),
  KEY `mls_id` (`mls_id`),
  CONSTRAINT `wrp_srv_description_ibfk_1` FOREIGN KEY (`wrp_id`) REFERENCES `wallet_relying_party` (`id`),
  CONSTRAINT `wrp_srv_description_ibfk_2` FOREIGN KEY (`mls_id`) REFERENCES `multilanguage_string` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

-- A despejar estrutura para tabela wrp.wrp_support_uri
CREATE TABLE IF NOT EXISTS `wrp_support_uri` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `wrp_id` int(11) DEFAULT NULL,
  `uri` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `wrp_id` (`wrp_id`),
  CONSTRAINT `wrp_support_uri_ibfk_1` FOREIGN KEY (`wrp_id`) REFERENCES `wallet_relying_party` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados não seleccionada.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
