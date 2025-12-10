# coding: latin-1
###############################################################################
# Copyright (c) 2023 European Commission
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################
"""
This models.py file contains functions related to queries to add data to DB (user, Relying Party, access_certificate).

"""
import pymysql
from app_config.config import ConfService
from db import get_db_connection as conn

from app import logger

def check_user(hash_pid, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT user_id
                FROM user
                WHERE hash_pid = %s
            """
            
            cursor.execute(select_query, (hash_pid,))
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
                extra = {'code': log_id}
                logger.info(f"User, {user_id}, already exists.", extra=extra)
                print(f"User, {user_id}, already exists.")
                return user_id
            else:
                extra = {'code': log_id}
                logger.info("User with hash_pid not found.", extra=extra)
                print("User with hash_pid not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_user(hash_pid, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO user (hash_pid) VALUES (%s)"
            
            cursor.execute(insert_query, (hash_pid,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"User successfully added. New User ID: {cursor.lastrowid}", extra=extra)

            print(f"User successfully added. New User ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error inserting User: {e}", extra=extra)
        print(f"Error inserting User: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_user_legalPerson(legalName, legalBasis, user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legalperson (legalName, legalBasis, user_id) VALUES (%s, %s, %s)"
            
            cursor.execute(insert_query, (legalName, legalBasis, user_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Legal Person successfully added. New Legal Person ID: {cursor.lastrowid}", extra=extra)

            print(f"Legal Person successfully added. New Legal Person ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error inserting Legal Person: {e}", extra=extra)
        print(f"Error inserting Legal Person: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_user_naturalPerson(givenName, familyName, dateOfBirth, placeOfBirth, user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO naturalperson (givenName, familyName, dateOfBirth, placeOfBirth, user_id) VALUES (%s, %s, %s, %s, %s)"
            
            cursor.execute(insert_query, (givenName, familyName, dateOfBirth, placeOfBirth, user_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Natural Person successfully added. New Natural Person ID: {cursor.lastrowid}", extra=extra)

            print(f"Natural Person successfully added. New Natural Person ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error inserting Natural Person: {e}", extra=extra)
        print(f"Error inserting Natural Person: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_legal_person_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT legalperson_id, legalBasis, legalName
                FROM legalperson
                WHERE user_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                legal_person_data = [
                    {"legalperson_id": row[0], "legalBasis": row[1], "legalName": row[2]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"Legal Person found for the user_id: {user_id}", extra=extra)
                return legal_person_data
            else:
                extra = {'code': log_id}
                logger.info("Legal Person with user_id not found.", extra=extra)
                print("Legal Person with user_id not found.")
                return None
        else:
            return None
        
    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()
    

def get_natural_person_info_le(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT givenName
                FROM naturalperson
                WHERE naturalperson_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchone()
            
            if result: 
                
                extra = {'code': log_id} 
                logger.info(f"natural Person found for the user_id: {user_id}", extra=extra)
                return result
            else:
                extra = {'code': log_id}
                logger.info("natural Person with user_id not found.", extra=extra)
                print("natural Person with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_natural_person_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT naturalperson_id, givenName, familyName, dateOfBirth, placeOfBirth
                FROM naturalperson
                WHERE user_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                natural_person_data = [
                    {"naturalperson_id": row[0], "givenName": row[1], "familyName": row[2], "dateOfBirth": row[3], "placeOfBirth": row[4]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"natural Person found for the user_id: {user_id}", extra=extra)
                return natural_person_data
            else:
                extra = {'code': log_id}
                logger.info("natural Person with user_id not found.", extra=extra)
                print("natural Person with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_legal_entity(postalAddress, country, email, phone, infoURI, identifier, identifierType, user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legalentity (postalAddress, country, email, phone, infoURI, identifier, identifierType, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            
            cursor.execute(insert_query, (postalAddress, country, email, phone, infoURI, identifier, identifierType, user_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Legal Entity successfully added. New Legal Entity ID: {cursor.lastrowid}", extra=extra)

            print(f"Legal Entity successfully added. New Legal Entity ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error inserting Legal Person: {e}", extra=extra)
        print(f"Error inserting Legal Person: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_legal_entity_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT legalentity_id, legalperson_id, naturalperson_id, postalAddress, country, email, phone, infoURI, identifier, identifierType
                FROM legalentity
                WHERE user_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                legal_entity_data = [
                    {"legalentity_id": row[0], "legalperson_id": row[1], "naturalperson_id": row[2], "postalAddress": row[3], "country": row[4], "email": row[5], "phone": row[6], "infoURI": row[7], "identifier": row[8], "identifierType": row[9]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"Legal Entity found for the user_id: {user_id}", extra=extra)
                return legal_entity_data
            else:
                extra = {'code': log_id}
                logger.info("Legal Entity with user_id not found.", extra=extra)
                print("Legal Entity with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_check_legal_entity_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT legalentity_id
                FROM legalentity
                WHERE legalperson_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                legal_entity_data = [
                    {"legalentity": row[0]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"Legal Entity found for the user_id: {user_id}", extra=extra)
                return legal_entity_data
            else:
                extra = {'code': log_id}
                logger.info("Legal Entity with user_id not found.", extra=extra)
                print("Legal Entity with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_rp_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT wrp_id, tradeName, supportURI, srvDescription, intended_use, isPSB, entitlement, providesAttestations, supervisorAuthority, isIntermediary, usesIntermediary, registryURI, providerType, x5c, typePolicy, policyURI, legalEntity
                FROM walletrelyingparty
                WHERE user_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                rp_data = [
                    {"wrp_id": row[0], "tradeName": row[1], "supportURI": row[2], "srvDescription": row[3], "intended_use": row[4], "isPSB": row[5], "entitlement": row[6], "providesAttestations": row[7], "supervisorAuthority": row[8], "isIntermediary": row[9], "usesIntermediary": row[10], "registryURI": row[11], "providerType": row[12], "x5c": row[13], "typePolicy": row[14], "policyURI": row[15], "legalEntity": row[15]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"RP found for the user_id: {user_id}", extra=extra)
                return rp_data
            else:
                extra = {'code': log_id}
                logger.info("RP with user_id not found.", extra=extra)
                print("RP with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_RP(tradeName, supportURI, srvDescription, entitlement, registryURI, typePolicy, policyURI, x5c, user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO walletrelyingparty (tradeName, supportURI, srvDescription, entitlement, registryURI, typePolicy, policyURI, x5c, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            
            cursor.execute(insert_query, (tradeName, supportURI, srvDescription, entitlement, registryURI, typePolicy, policyURI, x5c, user_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Wallet Relying Party successfully added. New Wallet Relying Party ID: {cursor.lastrowid}", extra=extra)

            print(f"Wallet Relying Party successfully added. New Wallet Relying Party ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error inserting Legal Person: {e}", extra=extra)
        print(f"Error inserting Legal Person: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_intended_use_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT *
                FROM intendeduse
                WHERE user_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                intended_use_data = [
                    {"intendeduse_id": row[0], "createdAt": row[1], "revokedAt": row[2], "intendedUseIdentifier": row[3], "type_policy": row[4], "policy_uri": row[5], "purpose": row[6], "credential_id": row[7], "user_id": row[8]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"Intended Use found for the user_id: {user_id}", extra=extra)
                return intended_use_data
            else:
                extra = {'code': log_id}
                logger.info("Intended Use with user_id not found.", extra=extra)
                print("Intended Use with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_credential_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT *
                FROM credential
                WHERE user_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                credential_data = [
                    {"credential_id": row[0], "name": row[1], "format": row[2], "meta": row[3], "path": row[4], "credentialValues": row[5], "user_id": row[6]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"Credentail found for the user_id: {user_id}", extra=extra)
                return credential_data
            else:
                extra = {'code': log_id}
                logger.info("Credentail with user_id not found.", extra=extra)
                print("Credentail with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()


def insert_intended_use(createAt, revokeAt, intendedUseIdentifier, type_policy, policy_uri, purpose, user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO intendeduse (createdAt, revokedAt, intendedUseIdentifier, type_policy, policy_uri, purpose, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            
            cursor.execute(insert_query, (createAt, revokeAt, intendedUseIdentifier, type_policy, policy_uri, purpose, user_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Intended Use successfully added. New Intended Use ID: {cursor.lastrowid}", extra=extra)

            print(f"Intended Use successfully added. New Intended Use ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error inserting Intended Use: {e}", extra=extra)
        print(f"Error inserting Intended Use: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_credential(name, format, meta, path, credentialValues, user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO credential (name, format, meta, path, credentialValues, user_id) VALUES (%s, %s, %s, %s, %s, %s)"
            
            cursor.execute(insert_query, (name, format, meta, path, credentialValues, user_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Credential successfully added. New Credential ID: {cursor.lastrowid}", extra=extra)

            print(f"Credential successfully added. New Credential ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error inserting Credential: {e}", extra=extra)
        print(f"Error inserting Credential: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def update_naturalPerson_legal_entity(natural_id, legalEntity_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE legalentity 
                                SET naturalperson_id = %s
                                WHERE legalentity_id = %s
                            """
            cursor.execute(insert_query, (natural_id, legalEntity_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Legal Entity successfully updated: {id}", extra=extra)

            print(f"Legal Entity successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating Legal Entity: {e}", extra=extra)
        print(f"Error updating Legal Entity: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def remove_naturalPerson_legal_entity(legalEntity_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE legalentity 
                                SET naturalperson_id = NULL
                                WHERE legalentity_id = %s
                            """
            cursor.execute(insert_query, (legalEntity_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Legal Entity successfully updated: {id}", extra=extra)

            print(f"Legal Entity successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating Legal Entity: {e}", extra=extra)
        print(f"Error updating Legal Entity: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()


def get_check_legal_entity_info_lp(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT legalentity_id
                FROM legalentity
                WHERE legalperson_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                legal_entity_data = [
                    {"naturalperson_id": row[0]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"Legal Entity found for the user_id: {user_id}", extra=extra)
                return legal_entity_data
            else:
                extra = {'code': log_id}
                logger.info("Legal Entity with user_id not found.", extra=extra)
                print("Legal Entity with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def remove_legalPerson_legal_entity(legalEntity_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE legalentity 
                                SET legalperson_id = NULL
                                WHERE legalentity_id = %s
                            """
            cursor.execute(insert_query, (legalEntity_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Legal Entity successfully updated: {id}", extra=extra)

            print(f"Legal Entity successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating Legal Entity: {e}", extra=extra)
        print(f"Error updating Legal Entity: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def update_legalPerson_legal_entity(natural_id, legalEntity_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE legalentity 
                                SET legalperson_id = %s
                                WHERE legalentity_id = %s
                            """
            cursor.execute(insert_query, (natural_id, legalEntity_id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"Legal Entity successfully updated: {id}", extra=extra)

            print(f"Legal Entity successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating Legal Entity: {e}", extra=extra)
        print(f"Error updating Legal Entity: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_legal_person_info_le(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT legalName
                FROM legalperson
                WHERE legalperson_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchone()
            
            if result: 
                
                extra = {'code': log_id} 
                logger.info(f"Legal Person found for the user_id: {user_id}", extra=extra)
                return result
            else:
                extra = {'code': log_id}
                logger.info("Legal Person with user_id not found.", extra=extra)
                print("Legal Person with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()


def get_wrp_info_le(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT legalName
                FROM legalperson
                WHERE legalperson_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchone()
            
            if result: 
                
                extra = {'code': log_id} 
                logger.info(f"Legal Person found for the user_id: {user_id}", extra=extra)
                return result
            else:
                extra = {'code': log_id}
                logger.info("Legal Person with user_id not found.", extra=extra)
                print("Legal Person with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()


def get_legal_entity_info_rp(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT identifier
                FROM legalentity
                WHERE legalentity_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                extra = {'code': log_id} 
                logger.info(f"Legal Entity found for the user_id: {user_id}", extra=extra)
                return result
            else:
                extra = {'code': log_id}
                logger.info("Legal Entity with user_id not found.", extra=extra)
                print("Legal Entity with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_check_iu_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT intendeduse_id
                FROM intendeduse
                WHERE credential_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                rp_data = [
                    {"intendeduse_id": row[0]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"iu found for the user_id: {user_id}", extra=extra)
                return rp_data
            else:
                extra = {'code': log_id}
                logger.info("iu with user_id not found.", extra=extra)
                print("iu with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def remove_legal_entity_wrp(id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE walletrelyingparty 
                                SET supervisorAuthority = NULL
                                WHERE wrp_id = %s
                            """
            cursor.execute(insert_query, (id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"wrp successfully updated: {id}", extra=extra)

            print(f"wrp successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating wrp: {e}", extra=extra)
        print(f"Error updating wrp: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def update_wrp_legal_entity(le, wrp, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE walletrelyingparty 
                                SET supervisorAuthority = %s
                                WHERE wrp_id = %s
                            """
            cursor.execute(insert_query, (le, wrp,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"wrp successfully updated: {id}", extra=extra)

            print(f"wrp successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating wrp: {e}", extra=extra)
        print(f"Error updating wrp: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_iu_info_rp(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT intendedUseIdentifier
                FROM intendeduse
                WHERE intendeduse_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchone()
            
            if result: 
                
                extra = {'code': log_id} 
                logger.info(f"IU found for the user_id: {user_id}", extra=extra)
                return result
            else:
                extra = {'code': log_id}
                logger.info("IU with user_id not found.", extra=extra)
                print("IU with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_check_rp_info_iu(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT wrp_id
                FROM walletrelyingparty
                WHERE intended_use = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                rp_data = [
                    {"wrp_id": row[0]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"WRP found for the user_id: {user_id}", extra=extra)
                return rp_data
            else:
                extra = {'code': log_id}
                logger.info("WRP with user_id not found.", extra=extra)
                print("WRP with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def remove_iu_wrp(id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE walletrelyingparty 
                                SET intended_use = NULL
                                WHERE wrp_id = %s
                            """
            cursor.execute(insert_query, (id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"wrp successfully updated: {id}", extra=extra)

            print(f"wrp successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating wrp: {e}", extra=extra)
        print(f"Error updating wrp: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def update_wrp_iu(le, wrp, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE walletrelyingparty 
                                SET intended_use = %s
                                WHERE wrp_id = %s
                            """
            cursor.execute(insert_query, (le, wrp,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"wrp successfully updated: {id}", extra=extra)

            print(f"wrp successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating wrp: {e}", extra=extra)
        print(f"Error updating wrp: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_iu_info_cred(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT name
                FROM credential
                WHERE credential_id = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                extra = {'code': log_id} 
                logger.info(f"Legal Entity found for the user_id: {user_id}", extra=extra)
                return result
            else:
                extra = {'code': log_id}
                logger.info("Legal Entity with user_id not found.", extra=extra)
                print("Legal Entity with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_check_cred_info(user_id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            select_query = """
                SELECT wrp_id
                FROM walletrelyingparty
                WHERE supervisorAuthority = %s
            """
            
            cursor.execute(select_query, (user_id,))
            result = cursor.fetchall()
            
            if result: 
                rp_data = [
                    {"wrp_id": row[0]} 
                    for row in result
                ]
                extra = {'code': log_id} 
                logger.info(f"WRP found for the user_id: {user_id}", extra=extra)
                return rp_data
            else:
                extra = {'code': log_id}
                logger.info("WRP with user_id not found.", extra=extra)
                print("WRP with user_id not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code': log_id}
        logger.error(f"Error checking user: {e}", extra=extra)
        print(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def update_iu_cred(le, wrp, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE intendeduse 
                                SET credential_id = %s
                                WHERE intendeduse_id = %s
                            """
            cursor.execute(insert_query, (le, wrp,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"iu successfully updated: {id}", extra=extra)

            print(f"iu successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating iu: {e}", extra=extra)
        print(f"Error updating iu: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def remove_cred_iu(id, log_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = """
                                UPDATE intendeduse 
                                SET credential_id = NULL
                                WHERE intendeduse_id = %s
                            """
            cursor.execute(insert_query, (id,))
            
            connection.commit()
            
            extra = {'code': log_id} 
            logger.info(f"iu successfully updated: {id}", extra=extra)

            print(f"iu successfully updated: {id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code': log_id} 
        logger.error(f"Error updating iu: {e}", extra=extra)
        print(f"Error updating iu: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()