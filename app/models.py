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
import json

import pymysql
from app_config.config import ConfService
from db import get_db_connection as conn

from app import logger

def serialize_json(value):
    return json.dumps(value) if value is not None else None

def deserialize_json(value):
    return json.loads(value) if value else None

def check_user(hash_pid):
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
            row = cursor.fetchone()
            if row:
                return row
            else:
                return None
            
            if result:
                user_id = result[0]
                logger.info(f"User, {user_id}, already exists.")
                return user_id
            else:
                logger.info("User with hash_pid not found.")
                return None
        else:
            return None

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error checking user: {e}")
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_user(hash_pid):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO user (hash_pid) VALUES (%s)"
            
            cursor.execute(insert_query, (hash_pid,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"User successfully added. New User ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting User: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -legal person-insert
def insert_legal_person(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_person (" \
            "user_id) " \
            "VALUES (%s)"
            
            cursor.execute(insert_query, (user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Person successfully added. New Legal Person  ID: {cursor.lastrowid} - {user_id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Legal Person : {e} - {user_id}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_legal_person_name(legal_person_id, name):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_person_name (" \
            "legal_person_id, " \
            "name) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legal_person_id, name,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Person Name successfully added. New Legal Person Name ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Legal Person Name: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -legal person-update
def associate_legal_person_law(legal_person_id, law_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_person_law (" \
            "legal_person_id, " \
            "law_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legal_person_id, law_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Person - Law successfully added. New Legal Person - Law ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Legal Person - Law: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def delete_legal_person_laws(legal_person_id, law_ids):
    if not law_ids:
        return 0

    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            placeholders = ','.join(['%s'] * len(law_ids))

            delete_query = "DELETE FROM legal_person_law " \
                "WHERE legal_person_id = %s " \
                f"AND law_id IN ({placeholders})"

            params = [legal_person_id] + law_ids

            cursor.execute(delete_query, params)

            connection.commit()

            deleted_count = cursor.rowcount

            extra = {'code'}
            logger.info(f"Legal Person - Law associations removed successfully. Rows affected: {deleted_count}")

            return deleted_count

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error deleting Legal Person - Law associations: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()

## -legal person-get
def get_legal_person(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    lp.id,
                    lpn.name,
                    law.id,
                    law.legislative_identifier,
                    llb.legal_basis
                FROM legal_person lp

                LEFT JOIN legal_person_name lpn 
                    ON lpn.legal_person_id = lp.id

                LEFT JOIN legal_person_law lpl 
                    ON lpl.legal_person_id = lp.id

                LEFT JOIN law 
                    ON law.id = lpl.law_id

                LEFT JOIN law_legal_basis llb
                    ON llb.law_id = law.id

                WHERE lp.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = {}

            for lp_id, name, law_id, legislative_identifier, legal_basis in rows:

                if lp_id not in result:
                    result[lp_id] = {
                        "legal_person_id": lp_id,
                        "legal_names": [],
                        "laws": {}
                    }

                if name and name not in result[lp_id]["legal_names"]:
                    result[lp_id]["legal_names"].append(name)

                if law_id:
                    laws = result[lp_id]["laws"]

                    if law_id not in laws:
                        laws[law_id] = {
                            "law_id": law_id,
                            "legislative_identifier": legislative_identifier,
                            "legal_basis": []
                        }

                    if legal_basis and legal_basis not in laws[law_id]["legal_basis"]:
                        laws[law_id]["legal_basis"].append(legal_basis)

            final_result = []

            for lp in result.values():
                lp["laws"] = list(lp["laws"].values())
                final_result.append(lp)

            return final_result

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
def insert_legal_person_law(legal_person_id, law_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_person_law (" \
            "legal_person_id, " \
            "law_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legal_person_id, law_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Person - Law successfully added. New Law ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Law: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_legal_person(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    lp.user_id
                FROM legal_person lp
                WHERE lp.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
            
## -law-insert
def insert_law(legislative_identifier, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO law (" \
            "legislative_identifier, " \
            "user_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legislative_identifier, user_id,))
            
            connection.commit()
            
            logger.info(f"Law successfully added. New Law ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Law: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_law_legal_basis(law_id, legal_basis):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO law_legal_basis (" \
            "law_id, " \
            "legal_basis) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (law_id, legal_basis,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Law Legal Basis successfully added. New Law Legal Basis ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Law Legal Basis: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -law-get
def get_law(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    l.id,
                    l.legislative_identifier,
                    llb.legal_basis

                FROM law l

                LEFT JOIN law_legal_basis llb 
                    ON llb.law_id = l.id

                WHERE l.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = {}

            for l_id, legislative_identifier, legal_basis in rows:

                if l_id not in result:
                    result[l_id] = {
                        "law_id": l_id,
                        "legislativeIdentifier": legislative_identifier,
                        "legalBasis": []
                    }

                if legal_basis and legal_basis not in result[l_id]["legalBasis"]:
                    result[l_id]["legalBasis"].append(legal_basis)

            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []

    finally:
        if connection:
            cursor.close()
            connection.close()


def check_law(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    l.user_id

                FROM law l

                WHERE l.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []

    finally:
        if connection:
            cursor.close()
            connection.close()


## -natural person-insert
def insert_natural_person(family_name, given_name, date_of_birth, place_of_birth, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO natural_person (" \
            "family_name, " \
            "given_name, " \
            "date_of_birth, " \
            "place_of_birth, " \
            "user_id) " \
            "VALUES (%s, %s, %s, %s, %s)"
            
            cursor.execute(insert_query, (family_name, given_name, date_of_birth, place_of_birth, user_id))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Natural Person successfully added. New Natural Person ID: {cursor.lastrowid} - {user_id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Natural Person: {e} - {user_id}")
    finally:
        if connection:
            cursor.close()
            connection.close()
           
## -natural person-get
def get_natural_person(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    np.id,
                    np.family_name,
                    np.given_name,
                    np.date_of_birth,
                    np.place_of_birth
                FROM natural_person np
                WHERE np.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = []

            for np_id, family_name, given_name, date_of_birth, place_of_birth in rows:
                result.append({
                    "natural_person_id": np_id,
                    "family_name": family_name,
                    "given_name": given_name,
                    "date_of_birth": str(date_of_birth) if date_of_birth else None,
                    "place_of_birth": place_of_birth
                })

            return result

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
def get_natural_person_id(natural_person_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    np.id,
                    np.family_name,
                    np.given_name,
                    np.date_of_birth,
                    np.place_of_birth
                FROM natural_person np
                WHERE np.id = %s
            """

            cursor.execute(query, (natural_person_id,))
            rows = cursor.fetchall()

            result = []

            for np_id, family_name, given_name, date_of_birth, place_of_birth in rows:
                result.append({
                    "natural_person_id": np_id,
                    "family_name": family_name,
                    "given_name": given_name,
                    "date_of_birth": str(date_of_birth) if date_of_birth else None,
                    "place_of_birth": place_of_birth
                })

            return result

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
def check_natural_person(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    np.user_id
                FROM natural_person np
                WHERE np.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []
            
    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
## -legal entity-insert
def insert_legal_entity(legalPerson, naturalPerson, country, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_entity (" \
            "legal_person_id, " \
            "natural_person_id, " \
            "country, " \
            "user_id) " \
            "VALUES (%s, %s, %s, %s)"
            
            cursor.execute(insert_query, (legalPerson, naturalPerson, country, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Entity successfully added. New Legal Entity  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Legal Entity : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_legal_entity_identifier(legal_entity_id, identifier_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_entity_identifier (" \
            "legal_entity_id, " \
            "identifier_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legal_entity_id, identifier_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Identifier successfully added. New Identifier  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Identifier : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_legal_entity_postal_address(legal_entity_id, address):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_entity_postal_address (" \
            "legal_entity_id, " \
            "address) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legal_entity_id, address,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Entity Address successfully added. New Legal Entity Address  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Legal Entity Address : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_legal_entity_info_uri(legal_entity_id, uri):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_entity_info_uri (" \
            "legal_entity_id, " \
            "uri) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legal_entity_id, uri,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Entity Info Uri successfully added. New Legal Entity Info Uri  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Legal Entity Info Uri : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()  

def insert_legal_entity_email(legal_entity_id, email):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_entity_email (" \
            "legal_entity_id, " \
            "email) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legal_entity_id, email,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Entity Email successfully added. New Legal Entity Email  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Legal Entity Email : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_legal_entity_phone(legal_entity_id, phone):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO legal_entity_phone (" \
            "legal_entity_id, " \
            "phone) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (legal_entity_id, phone,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Legal Entity Phone successfully added. New Legal Entity Phone  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Legal Entity Phone : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def delete_legal_entity_identifier(legal_entity_id, identifier_ids):
    if not identifier_ids:
        return 0

    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            placeholders = ','.join(['%s'] * len(identifier_ids))

            delete_query = "DELETE FROM legal_entity_identifier " \
                "WHERE legal_entity_id = %s " \
                f"AND identifier_id IN ({placeholders})"

            params = [legal_entity_id] + identifier_ids

            cursor.execute(delete_query, params)

            connection.commit()

            deleted_count = cursor.rowcount

            extra = {'code'}
            logger.info(f"Legal Entity - Identifier associations removed successfully. Rows affected: {deleted_count}")

            return deleted_count

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error deleting Legal Entity - Identifier associations: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()

## -legal entity-get
def get_legal_entity(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                    SELECT 
                        le.id,
                        le.country,

                        lepa.address,
                        leiu.uri,
                        lee.email,
                        lep.phone,

                        i.id,
                        i.identifier,
                        i.type,

                        lpn.name,

                        np.given_name,
                        np.family_name

                    FROM legal_entity le

                    LEFT JOIN legal_entity_postal_address lepa
                        ON lepa.legal_entity_id = le.id
                        
                    LEFT JOIN legal_entity_info_uri leiu
                        ON leiu.legal_entity_id = le.id
                        
                    LEFT JOIN legal_entity_email lee
                        ON lee.legal_entity_id = le.id
                        
                    LEFT JOIN legal_entity_phone lep
                        ON lep.legal_entity_id = le.id
                        
                    LEFT JOIN legal_person_name lpn
                        ON lpn.legal_person_id = le.legal_person_id
                        
                    LEFT JOIN natural_person np
                        ON np.id = le.natural_person_id
                        
                    LEFT JOIN legal_entity_identifier lei
                        ON lei.legal_entity_id = le.id

                    LEFT JOIN identifier i
                        ON i.id = lei.identifier_id

                    WHERE le.user_id = %s;
                    """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                le_id, country,
                address, uri, email, phone,
                i_id, identifier, id_type,
                legal_name,
                given_name, family_name
            ) in rows:

                if le_id not in result:
                    result[le_id] = {
                        "legal_entity_id": le_id,
                        "country": country,
                        "postalAddress": [],
                        "infoURI": [],
                        "email": [],
                        "phone": [],
                        "identifier": [],
                        "LegalPerson": None,
                        "NaturalPerson": None
                    }

                entity = result[le_id]

                # arrays simples
                if address and address not in entity["postalAddress"]:
                    entity["postalAddress"].append(address)

                if uri and uri not in entity["infoURI"]:
                    entity["infoURI"].append(uri)

                if email and email not in entity["email"]:
                    entity["email"].append(email)

                if phone and phone not in entity["phone"]:
                    entity["phone"].append(phone)

                # identifiers
                if identifier:
                    id_obj = {
                        "identifier_id": i_id,
                        "identifier": identifier,
                        "type": id_type
                    }
                    if id_obj not in entity["identifier"]:
                        entity["identifier"].append(id_obj)

                # LegalPerson (opcional)
                if legal_name:
                    if entity["LegalPerson"] is None:
                        entity["LegalPerson"] = {
                            "legalName": []
                        }

                    if legal_name not in entity["LegalPerson"]["legalName"]:
                        entity["LegalPerson"]["legalName"].append(legal_name)

                # NaturalPerson (opcional)
                if given_name or family_name:
                    entity["NaturalPerson"] = {
                        "givenName": given_name,
                        "familyName": family_name
                    }

            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_legal_entity(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                    SELECT 
                        le.user_id

                    FROM legal_entity le

                    WHERE le.id = %s;
                    """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_legal_entity_id(provider_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                    SELECT 
                        le.id,
                        le.country,

                        lepa.address,
                        leiu.uri,
                        lee.email,
                        lep.phone,

                        i.id,
                        i.identifier,
                        i.type,

                        lpn.name,

                        np.given_name,
                        np.family_name

                    FROM legal_entity le

                    LEFT JOIN provider p
                        ON p.legal_entity_id = le.id

                    LEFT JOIN legal_entity_postal_address lepa
                        ON lepa.legal_entity_id = le.id
                        
                    LEFT JOIN legal_entity_info_uri leiu
                        ON leiu.legal_entity_id = le.id
                        
                    LEFT JOIN legal_entity_email lee
                        ON lee.legal_entity_id = le.id
                        
                    LEFT JOIN legal_entity_phone lep
                        ON lep.legal_entity_id = le.id
                        
                    LEFT JOIN legal_person_name lpn
                        ON lpn.legal_person_id = le.legal_person_id
                        
                    LEFT JOIN natural_person np
                        ON np.id = le.natural_person_id
                        
                    LEFT JOIN legal_entity_identifier lei
                        ON lei.legal_entity_id = le.id

                    LEFT JOIN identifier i
                        ON i.id = lei.identifier_id

                    WHERE p.id = %s;
                    """

            cursor.execute(query, (provider_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                le_id, country,
                address, uri, email, phone,
                i_id, identifier, id_type,
                legal_name,
                given_name, family_name
            ) in rows:

                if le_id not in result:
                    result[le_id] = {
                        "legal_entity_id": le_id,
                        "country": country,
                        "postalAddress": [],
                        "infoURI": [],
                        "email": [],
                        "phone": [],
                        "identifier": [],
                        "LegalPerson": None,
                        "NaturalPerson": None
                    }

                entity = result[le_id]

                # arrays simples
                if address and address not in entity["postalAddress"]:
                    entity["postalAddress"].append(address)

                if uri and uri not in entity["infoURI"]:
                    entity["infoURI"].append(uri)

                if email and email not in entity["email"]:
                    entity["email"].append(email)

                if phone and phone not in entity["phone"]:
                    entity["phone"].append(phone)

                # identifiers
                if identifier:
                    id_obj = {
                        "identifier_id": i_id,
                        "identifier": identifier,
                        "type": id_type
                    }
                    if id_obj not in entity["identifier"]:
                        entity["identifier"].append(id_obj)

                # LegalPerson (opcional)
                if legal_name:
                    if entity["LegalPerson"] is None:
                        entity["LegalPerson"] = {
                            "legalName": []
                        }

                    if legal_name not in entity["LegalPerson"]["legalName"]:
                        entity["LegalPerson"]["legalName"].append(legal_name)

                # NaturalPerson (opcional)
                if given_name or family_name:
                    entity["NaturalPerson"] = {
                        "givenName": given_name,
                        "familyName": family_name
                    }

            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
   
def get_identifiers_legal_entity(legal_entity_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                    SELECT 
                        lei.identifier_id

                    FROM legal_entity_identifier lei

                    WHERE lei.legal_entity_id = %s;
                    """

            cursor.execute(query, (legal_entity_id,))
            row = cursor.fetchall()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

## -identifier-insert
def insert_identifier(identifier, type, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO identifier (" \
            "identifier, " \
            "type, " \
            "user_id) " \
            "VALUES (%s, %s, %s)"
            
            cursor.execute(insert_query, (identifier, type, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Identifier successfully added. New Identifier  ID: {cursor.lastrowid} - {user_id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Identifier : {e} - {user_id}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -identifier-get
def get_identifier(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    i.id,
                    i.identifier,
                    i.type
                FROM identifier i
                WHERE i.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = []

            for i_id, i_identifier, i_type in rows:
                result.append({
                    "identifier_id": i_id,
                    "identifier": i_identifier,
                    "type": i_type,
                })

            return result

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
def check_identifier(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    i.user_id
                FROM identifier i
                WHERE i.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
## -provider-insert
def insert_provider(legal_entity_id, provider_type, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO provider (" \
            "legal_entity_id, " \
            "provider_type, " \
            "user_id) " \
            "VALUES (%s, %s, %s)"
            
            cursor.execute(insert_query, (legal_entity_id, provider_type, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Provider successfully added. New Provider ID: {cursor.lastrowid} - {user_id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Provider : {e} - {user_id}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_provider_x5c(provider_id, certificate):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO provider_x5c (" \
            "provider_id, " \
            "certificate) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (provider_id, certificate,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Provider x5c successfully added. New Provider x5c  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Provider x5c : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -provider-get
def get_provider(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """ 
                SELECT 
                    p.id,
                    p.provider_type,
                    p.legal_entity_id,

                    px.certificate,

                    pol.id,
                    pol.policy_uri,
                    pol.type

                FROM provider p

                LEFT JOIN provider_x5c px
                    ON px.provider_id = p.id

                LEFT JOIN provider_policy pp
                    ON pp.provider_id = p.id

                LEFT JOIN policy pol
                    ON pol.id = pp.policy_id

                WHERE p.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                p_id, provider_type, legal_entity_id,
                certificate,
                pol_id, policy_uri, policy_type
            ) in rows:

                if p_id not in result:
                    result[p_id] = {
                        "provider_id": p_id,
                        "provider_type": provider_type,
                        "legal_entity_id": legal_entity_id,
                        "x5c": [],
                        "policy": []
                    }

                provider = result[p_id]

                # certificates
                if certificate and certificate not in provider["x5c"]:
                    provider["x5c"].append(certificate)

                # policies
                if policy_uri:
                    policy_obj = {
                        "policy_id": pol_id,
                        "policyURI": policy_uri,
                        "type": policy_type
                    }

                    if policy_obj not in provider["policy"]:
                        provider["policy"].append(policy_obj)

            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_provider(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """ 
                SELECT 
                    p.user_id
                FROM provider p
                WHERE p.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_provider_policy(provider_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """ 
                SELECT 
                    pp.policy_id
                    
                FROM provider_policy pp

                WHERE pp.provider_id = %s
            """

            cursor.execute(query, (provider_id,))
            row = cursor.fetchall()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

## -policy-insert
def insert_policy(policy_uri, type, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO policy (" \
            "policy_uri, " \
            "type, " \
            "user_id) " \
            "VALUES (%s, %s, %s)"
            
            cursor.execute(insert_query, (policy_uri, type, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Policy successfully added. New Policy ID: {cursor.lastrowid} - {user_id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Policy : {e} - {user_id}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -policy-get
def get_policy(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    p.id,
                    p.policy_uri,
                    p.type
                FROM policy p
                WHERE p.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = []

            for p_id, p_policy_uri, p_type in rows:
                result.append({
                    "policy_id": p_id,
                    "policy_uri": p_policy_uri,
                    "type": p_type,
                })

            return result

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
def check_policy(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    p.user_id,
                    p.type
                FROM policy p
                WHERE p.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return [None, None]

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_provider_policy(provider_id, policy_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO provider_policy (" \
            "provider_id, " \
            "policy_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (provider_id, policy_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Provider - Policy successfully added. New Provider - Policy  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Provider - Policy : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def delete_provider_policy(provider_id, policy_ids):
    if not policy_ids:
        return 0

    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            placeholders = ','.join(['%s'] * len(policy_ids))

            delete_query = "DELETE FROM provider_policy " \
                "WHERE provider_id = %s " \
                f"AND policy_id IN ({placeholders})"

            params = [provider_id] + policy_ids

            cursor.execute(delete_query, params)

            connection.commit()

            deleted_count = cursor.rowcount

            extra = {'code'}
            logger.info(f"Provider - Policy associations removed successfully. Rows affected: {deleted_count}")

            return deleted_count

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error deleting Provider - Policy associations: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()

## -supervisory authority-insert
def insert_supervisory_authority(name, country, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO supervisory_authority (" \
            "name, " \
            "country, " \
            "user_id) " \
            "VALUES (%s, %s, %s)"
            
            cursor.execute(insert_query, (name, country, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Supervisory Authority successfully added. New Supervisory Authority ID: {cursor.lastrowid} - {user_id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Supervisory Authority : {e} - {user_id}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_supervisory_authority_phone(authority_id, phone):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO supervisory_authority_phone (" \
            "authority_id, " \
            "phone) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (authority_id, phone,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Supervisory Authority Phone successfully added. New Supervisory Authority Phone  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Supervisory Authority Phone : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_supervisory_authority_formuri(authority_id, formURI):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO supervisory_authority_formuri (" \
            "authority_id, " \
            "formURI) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (authority_id, formURI,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Supervisory Authority Form URI successfully added. New Supervisory Authority Form URI  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Supervisory Authority Form URI : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
                        
def insert_supervisory_authority_email(authority_id, email):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO supervisory_authority_email (" \
            "authority_id, " \
            "email) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (authority_id, email,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Supervisory Authority Email successfully added. New Supervisory Authority Email  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Supervisory Authority Email : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -supervisory authority-get
def get_supervisory_authority(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    sa.id,
                    sa.name,
                    sa.country,
                    sae.email,
                    sap.phone,
                    saf.formURI
                FROM supervisory_authority sa
                LEFT JOIN supervisory_authority_email sae
                    ON sae.authority_id = sa.id
                LEFT JOIN supervisory_authority_phone sap
                    ON sap.authority_id = sa.id
                LEFT JOIN supervisory_authority_formuri saf
                    ON saf.authority_id = sa.id
                WHERE sa.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = {}

            for sa_id, name, country, email, phone, formURI in rows:

                if sa_id not in result:
                    result[sa_id] = {
                        "supervisory_authority_id": sa_id,
                        "name": name,
                        "country": country,
                        "email": [],
                        "phone": [],
                        "formURI": []
                    }

                sa = result[sa_id]

                if email and email not in sa["email"]:
                    sa["email"].append(email)

                if phone and phone not in sa["phone"]:
                    sa["phone"].append(phone)

                if formURI and formURI not in sa["formURI"]:
                    sa["formURI"].append(formURI)

            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_supervisory_authority(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    sa.user_id
                FROM supervisory_authority sa
                WHERE sa.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

## -wrp-insert
def insert_wrp(provider_id, trade_name, ispsb, regristry_uri, is_intermediary, supervisory_authority_id, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO wallet_relying_party (" \
            "provider_id, " \
            "trade_name, " \
            "is_psb, " \
            "registry_uri, " \
            "is_intermediary, " \
            "supervisory_authority_id, " \
            "user_id) " \
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            
            cursor.execute(insert_query, (provider_id, trade_name, ispsb, regristry_uri, is_intermediary, supervisory_authority_id, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Wallet Relying Party successfully added. New Wallet Relying Party ID: {cursor.lastrowid} - {user_id}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Wallet Relying Party : {e} - {user_id}")
    finally:
        if connection:
            cursor.close()
            connection.close()
             
def insert_wrp_entitlement(wrp_id, entitlement):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO wrp_entitlement (" \
            "wrp_id, " \
            "entitlement) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (wrp_id, entitlement,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Wallet Relying Party Entitlement successfully added. New Wallet Relying Party Entitlement  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Wallet Relying Party Entitlement : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_wrp_intermediary(wrp_id, intermediary_wrp_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO wrp_intermediary (" \
            "wrp_id, " \
            "intermediary_wrp_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (wrp_id, intermediary_wrp_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Wallet Relying Party Intermediary successfully added. New Wallet Relying Party Intermediary  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Wallet Relying Party Intermediary : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_wrp_srv_description(wrp_id, mls_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO wrp_srv_description (" \
            "wrp_id, " \
            "mls_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (wrp_id, mls_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Wallet Relying Party Srv Description successfully added. New Wallet Relying Party Srv Description  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Wallet Relying Party Srv Description : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_wrp_support_uri(wrp_id, uri):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO wrp_support_uri (" \
            "wrp_id, " \
            "uri) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (wrp_id, uri,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Wallet Relying Party Support Uri successfully added. New Wallet Relying Party Support Uri  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Wallet Relying Party Support Uri : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_wrp_provided_attestation(wrp_id, provided_attestation_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO wrp_provided_attestation (" \
            "wrp_id, " \
            "provided_attestation_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (wrp_id, provided_attestation_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Wallet Relying Party Provided Attestation successfully added. New Wallet Relying Party Provided Attestation  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Wallet Relying Party Provided Attestation : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_wrp_intended_use(wrp_id, intended_use_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO wrp_intended_use (" \
            "wrp_id, " \
            "intended_use_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (wrp_id, intended_use_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Wallet Relying Party Intended Use successfully added. New Wallet Relying Party Intended Use  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Wallet Relying Party Intended Use : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def delete_wrp_intended_use(wrp_id, intended_use_ids):
    if not intended_use_ids:
        return 0

    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            placeholders = ','.join(['%s'] * len(intended_use_ids))

            delete_query = "DELETE FROM wrp_intended_use " \
                "WHERE wrp_id = %s " \
                f"AND intended_use_id IN ({placeholders})"

            params = [wrp_id] + intended_use_ids

            cursor.execute(delete_query, params)

            connection.commit()

            deleted_count = cursor.rowcount

            extra = {'code'}
            logger.info(f"Wrp Intended Use associations removed successfully. Rows affected: {deleted_count}")

            return deleted_count

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error deleting Wrp Intended Use associations: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()

def delete_wrp_provided_attestion(wrp_id, provided_attestation_ids):
    if not provided_attestation_ids:
        return 0

    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            placeholders = ','.join(['%s'] * len(provided_attestation_ids))

            delete_query = "DELETE FROM wrp_provided_attestation " \
                "WHERE wrp_id = %s " \
                f"AND provided_attestation_id IN ({placeholders})"

            params = [wrp_id] + provided_attestation_ids

            cursor.execute(delete_query, params)

            connection.commit()

            deleted_count = cursor.rowcount

            extra = {'code'}
            logger.info(f"Wrp Intended Use associations removed successfully. Rows affected: {deleted_count}")

            return deleted_count

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error deleting Wrp Intended Use associations: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()
            
def delete_wrp_intermediary(wrp_id, intermediary_wrp_ids):
    if not intermediary_wrp_ids:
        return 0

    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            placeholders = ','.join(['%s'] * len(intermediary_wrp_ids))

            delete_query = "DELETE FROM wrp_intermediary " \
                "WHERE wrp_id = %s " \
                f"AND intermediary_wrp_id IN ({placeholders})"

            params = [wrp_id] + intermediary_wrp_ids

            cursor.execute(delete_query, params)

            connection.commit()

            deleted_count = cursor.rowcount

            extra = {'code'}
            logger.info(f"Wrp intermediary Wrp associations removed successfully. Rows affected: {deleted_count}")

            return deleted_count

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error deleting Wrp intermediary Wrp associations: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()

## -wrp-get
def get_wrp(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    wrp.id,
                    wrp.provider_id,
                    wrp.trade_name,
                    wrp.is_psb,
                    wrp.registry_uri,
                    wrp.is_intermediary,
                    wrp.supervisory_authority_id,

                    su.uri,
                    we.entitlement,

                    wi.intermediary_wrp_id,

                    mls.lang,
                    mls.content,

                    sa.name,
                    sa.country,
                    sae.email,
                    sap.phone,
                    saf.formURI,

                    iu.id,
                    iu.intended_use_identifier,

                    pa.id,
                    pa.format,
                    pa.meta

                FROM wallet_relying_party wrp

                LEFT JOIN wrp_support_uri su
                    ON su.wrp_id = wrp.id

                LEFT JOIN wrp_entitlement we
                    ON we.wrp_id = wrp.id

                LEFT JOIN wrp_intermediary wi
                    ON wi.wrp_id = wrp.id

                LEFT JOIN wrp_srv_description wsd
                    ON wsd.wrp_id = wrp.id

                LEFT JOIN multilanguage_string mls
                    ON mls.id = wsd.mls_id

                LEFT JOIN supervisory_authority sa
                    ON sa.id = wrp.supervisory_authority_id

                LEFT JOIN supervisory_authority_email sae
                    ON sae.authority_id = sa.id

                LEFT JOIN supervisory_authority_phone sap
                    ON sap.authority_id = sa.id
                
                LEFT JOIN supervisory_authority_formuri saf
                    ON saf.authority_id = sa.id

                LEFT JOIN wrp_intended_use wrpiu
                    ON wrpiu.wrp_id = wrp.id
                    
                LEFT JOIN intended_use iu
                    ON iu.id = wrpiu.intended_use_id

                LEFT JOIN wrp_provided_attestation wpa
                    ON wpa.wrp_id = wrp.id
                    
                LEFT JOIN provided_attestation pa
                    ON pa.id = wpa.provided_attestation_id

                WHERE wrp.user_id = %s;
                """
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                wrp_id, provider_id, trade_name,
                is_psb, registry_uri, is_intermediary, sa_id,
                support_uri, entitlement,
                intermediary_id,
                lang, content,
                sa_name, sa_country,
                sa_email, sa_phone, sa_form,
                iu_id, iu_intended_use_identifier,
                pa_id, pa_format, pa_meta
            ) in rows:

                if wrp_id not in result:
                    result[wrp_id] = {
                        "wrp_id": wrp_id,
                        "provider_id": provider_id,
                        "trade_name": trade_name,
                        "isPSB": bool(is_psb),
                        "registryURI": registry_uri,
                        "isIntermediary": bool(is_intermediary),

                        "supportURI": [],
                        "entitlements": [],
                        "srvDescription": [],
                        "usesIntermediary": [],

                        "SupervisoryAuthority": None,

                        "intendedUses": [],

                        "providedAttestation": [] 
                    }

                wrp = result[wrp_id]

                # supportURI
                if support_uri and support_uri not in wrp["supportURI"]:
                    wrp["supportURI"].append(support_uri)

                # entitlements
                if entitlement and entitlement not in wrp["entitlements"]:
                    wrp["entitlements"].append(entitlement)

                # intermediary
                if intermediary_id and intermediary_id not in wrp["usesIntermediary"]:
                    wrp["usesIntermediary"].append(intermediary_id)

                # srvDescription
                if lang and content:
                    obj = {"lang": lang, "content": content}
                    if obj not in wrp["srvDescription"]:
                        wrp["srvDescription"].append(obj)

                # Supervisory Authority
                if sa_name:
                    if wrp["SupervisoryAuthority"] is None:
                        wrp["SupervisoryAuthority"] = {
                            "name": sa_name,
                            "country": sa_country,
                            "email": [],
                            "phone": [],
                            "formURI": []
                        }

                    sa = wrp["SupervisoryAuthority"]

                    if sa_email and sa_email not in sa["email"]:
                        sa["email"].append(sa_email)

                    if sa_phone and sa_phone not in sa["phone"]:
                        sa["phone"].append(sa_phone)

                    if sa_form and sa_form not in sa["formURI"]:
                        sa["formURI"].append(sa_form)
                
                # Intended Uses
                if iu_id:
                    obj = {
                        "id": iu_id,
                        "identifier": iu_intended_use_identifier
                    }

                    if obj not in wrp["intendedUses"]:
                        wrp["intendedUses"].append(obj)

                # Provided Attestation
                if pa_id:
                    obj = {
                        "id": pa_id,
                        "format": pa_format,
                        "meta": pa_meta
                    }

                    if obj not in wrp["providedAttestation"]:
                        wrp["providedAttestation"].append(obj)


            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_wrp(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    wrp.user_id

                FROM wallet_relying_party wrp

                WHERE wrp.id = %s;
                """
            
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def get_wrp_intermediary(intermediary_wrp_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    wrpi.wrp_id

                FROM wrp_intermediary wrpi

                WHERE wrpi.intermediary_wrp_id = %s;
                """
            
            cursor.execute(query, (intermediary_wrp_id))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
  
def get_wrp_id(wrp_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    wrp.id,
                    wrp.provider_id,
                    wrp.trade_name,
                    wrp.is_psb,
                    wrp.registry_uri,
                    wrp.is_intermediary,
                    wrp.supervisory_authority_id,

                    su.uri,
                    we.entitlement,

                    wi.intermediary_wrp_id,

                    mls.lang,
                    mls.content,

                    sa.name,
                    sa.country,
                    sae.email,
                    sap.phone,
                    saf.formURI

                FROM wallet_relying_party wrp

                LEFT JOIN wrp_support_uri su
                    ON su.wrp_id = wrp.id

                LEFT JOIN wrp_entitlement we
                    ON we.wrp_id = wrp.id

                LEFT JOIN wrp_intermediary wi
                    ON wi.wrp_id = wrp.id

                LEFT JOIN wrp_srv_description wsd
                    ON wsd.wrp_id = wrp.id

                LEFT JOIN multilanguage_string mls
                    ON mls.id = wsd.mls_id

                LEFT JOIN supervisory_authority sa
                    ON sa.id = wrp.supervisory_authority_id

                LEFT JOIN supervisory_authority_email sae
                    ON sae.authority_id = sa.id

                LEFT JOIN supervisory_authority_phone sap
                    ON sap.authority_id = sa.id

                LEFT JOIN supervisory_authority_formuri saf
                    ON saf.authority_id = sa.id

                WHERE wrp.id = %s;
                """
            
            cursor.execute(query, (wrp_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                wrp_id, provider_id, trade_name,
                is_psb, registry_uri, is_intermediary, sa_id,
                support_uri, entitlement,
                intermediary_id,
                lang, content,
                sa_name, sa_country,
                sa_email, sa_phone, sa_form
            ) in rows:

                if wrp_id not in result:
                    result[wrp_id] = {
                        "trade_name": trade_name,
                        "isPSB": bool(is_psb),
                        "registryURI": registry_uri,
                        "isIntermediary": bool(is_intermediary),
                        "provider_id": provider_id,

                        "supportURI": [],
                        "entitlements": [],
                        "srvDescription": [],
                        "usesIntermediary": [],

                        "SupervisoryAuthority": None
                    }

                wrp = result[wrp_id]

                # supportURI
                if support_uri and support_uri not in wrp["supportURI"]:
                    wrp["supportURI"].append(support_uri)

                # entitlements
                if entitlement and entitlement not in wrp["entitlements"]:
                    wrp["entitlements"].append(entitlement)

                # intermediary
                if intermediary_id and intermediary_id not in wrp["usesIntermediary"]:
                    wrp["usesIntermediary"].append(intermediary_id)

                # srvDescription
                if lang and content:
                    obj = {"lang": lang, "content": content}
                    if obj not in wrp["srvDescription"]:
                        wrp["srvDescription"].append(obj)

                # Supervisory Authority
                if sa_name:
                    if wrp["SupervisoryAuthority"] is None:
                        wrp["SupervisoryAuthority"] = {
                            "name": sa_name,
                            "country": sa_country,
                            "email": [],
                            "phone": [],
                            "formURI": []
                        }

                    sa = wrp["SupervisoryAuthority"]

                    if sa_email and sa_email not in sa["email"]:
                        sa["email"].append(sa_email)

                    if sa_phone and sa_phone not in sa["phone"]:
                        sa["phone"].append(sa_phone)

                    if sa_form and sa_form not in sa["formURI"]:
                        sa["formURI"].append(sa_form)

            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

  
def get_wrp_intended_id(intended_use_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    wrp.id,
                    wrp.provider_id,
                    wrp.trade_name,
                    wrp.is_psb,
                    wrp.registry_uri,
                    wrp.is_intermediary,
                    wrp.supervisory_authority_id,

                    su.uri,
                    we.entitlement,

                    wi.intermediary_wrp_id,

                    mls.lang,
                    mls.content,

                    sa.name,
                    sa.country,
                    sae.email,
                    sap.phone,
                    saf.formURI

                FROM wallet_relying_party wrp

                LEFT JOIN wrp_intended_use wiu
                    ON wiu.wrp_id = wrp.id

                LEFT JOIN wrp_support_uri su
                    ON su.wrp_id = wrp.id

                LEFT JOIN wrp_entitlement we
                    ON we.wrp_id = wrp.id

                LEFT JOIN wrp_intermediary wi
                    ON wi.wrp_id = wrp.id

                LEFT JOIN wrp_srv_description wsd
                    ON wsd.wrp_id = wrp.id

                LEFT JOIN multilanguage_string mls
                    ON mls.id = wsd.mls_id

                LEFT JOIN supervisory_authority sa
                    ON sa.id = wrp.supervisory_authority_id

                LEFT JOIN supervisory_authority_email sae
                    ON sae.authority_id = sa.id

                LEFT JOIN supervisory_authority_phone sap
                    ON sap.authority_id = sa.id

                LEFT JOIN supervisory_authority_formuri saf
                    ON saf.authority_id = sa.id

                WHERE wiu.intended_use_id = %s;
                """
            
            cursor.execute(query, (intended_use_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                wrp_id, provider_id, trade_name,
                is_psb, registry_uri, is_intermediary, sa_id,
                support_uri, entitlement,
                intermediary_id,
                lang, content,
                sa_name, sa_country,
                sa_email, sa_phone, sa_form
            ) in rows:

                if wrp_id not in result:
                    result[wrp_id] = {
                        "wrp_id": wrp_id,
                        "trade_name": trade_name,
                        "isPSB": bool(is_psb),
                        "registryURI": registry_uri,
                        "isIntermediary": bool(is_intermediary),
                        "provider_id": provider_id,

                        "supportURI": [],
                        "entitlements": [],
                        "srvDescription": [],
                        "usesIntermediary": [],

                        "SupervisoryAuthority": None
                    }

                wrp = result[wrp_id]

                # supportURI
                if support_uri and support_uri not in wrp["supportURI"]:
                    wrp["supportURI"].append(support_uri)

                # entitlements
                if entitlement and entitlement not in wrp["entitlements"]:
                    wrp["entitlements"].append(entitlement)

                # intermediary
                if intermediary_id and intermediary_id not in wrp["usesIntermediary"]:
                    wrp["usesIntermediary"].append(intermediary_id)

                # srvDescription
                if lang and content:
                    obj = {"lang": lang, "content": content}
                    if obj not in wrp["srvDescription"]:
                        wrp["srvDescription"].append(obj)

                # Supervisory Authority
                if sa_name:
                    if wrp["SupervisoryAuthority"] is None:
                        wrp["SupervisoryAuthority"] = {
                            "name": sa_name,
                            "country": sa_country,
                            "email": [],
                            "phone": [],
                            "formURI": []
                        }

                    sa = wrp["SupervisoryAuthority"]

                    if sa_email and sa_email not in sa["email"]:
                        sa["email"].append(sa_email)

                    if sa_phone and sa_phone not in sa["phone"]:
                        sa["phone"].append(sa_phone)

                    if sa_form and sa_form not in sa["formURI"]:
                        sa["formURI"].append(sa_form)

            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

### -provided attestation-insert
def insert_provided_attestation(format, meta, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO provided_attestation (" \
            "format, " \
            "meta, " \
            "user_id) " \
            "VALUES (%s, %s, %s)"
            
            cursor.execute(insert_query, (format, meta, user_id))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Provided Attestation successfully added. New Provided Attestation  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Provided Attestation : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -provided attestation-get
def get_provided_attestation(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT
                    pa.id,
                    pa.format,
                    pa.meta
                FROM provided_attestation pa
                WHERE pa.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = []

            for pa_id, format_, meta in rows:
                result.append({
                    "provided_attestation_id": pa_id,
                    "format": format_,
                    "meta": deserialize_json(meta)
                })

            return result

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_provided_attestation(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    pa.user_id
                FROM provided_attestation pa
                WHERE pa.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

## -multilanguage string-insert
def insert_multilanguage_string(lang, content, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO multilanguage_string (" \
            "lang, " \
            "content, " \
            "user_id) " \
            "VALUES (%s, %s, %s)"
            
            cursor.execute(insert_query, (lang, content, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Multilanguage String successfully added. New Multilanguage String  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Multilanguage String : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -intended use-insert
def insert_intended_use(intended_use_identifier, created_at, revoked_at, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO intended_use (" \
            "intended_use_identifier, " \
            "created_at, " \
            "revoked_at, " \
            "user_id) " \
            "VALUES (%s, %s, %s, %s)"
            
            cursor.execute(insert_query, (intended_use_identifier, created_at, revoked_at, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Intended Use successfully added. New Intended Use  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Intended Use : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_intended_use_purpose(intended_use_id, mls_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO intended_use_purpose (" \
            "intended_use_id, " \
            "mls_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (intended_use_id, mls_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Intended Use Purpose successfully added. New Intended Use Purpose  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Intended Use Purpose : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_intended_use_policy(intended_use_id, policy_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO intended_use_policy (" \
            "intended_use_id, " \
            "policy_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (intended_use_id, policy_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Intended Use - Policy successfully added. New Intended Use - Policy  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Intended Use - Policy : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def insert_intended_use_credential(intended_use_id, credential_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO intended_use_credential (" \
            "intended_use_id, " \
            "credential_id) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (intended_use_id, credential_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Intended Use - Credential successfully added. New Intended Use - Credential  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Intended Use - Credential : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def delete_intended_use_credential(intended_use_id, credential_ids):
    if not credential_ids:
        return 0

    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            placeholders = ','.join(['%s'] * len(credential_ids))

            delete_query = "DELETE FROM intended_use_credential " \
                "WHERE intended_use_id = %s " \
                f"AND credential_id IN ({placeholders})"

            params = [intended_use_id] + credential_ids

            cursor.execute(delete_query, params)

            connection.commit()

            deleted_count = cursor.rowcount

            extra = {'code'}
            logger.info(f"Intended Use - Credential associations removed successfully. Rows affected: {deleted_count}")

            return deleted_count

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error deleting Intended Use - Credential associations: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()
            
def delete_intended_use_policy(intended_use_id, policy_ids):
    if not policy_ids:
        return 0

    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            placeholders = ','.join(['%s'] * len(policy_ids))

            delete_query = "DELETE FROM intended_use_policy " \
                "WHERE intended_use_id = %s " \
                f"AND policy_id IN ({placeholders})"

            params = [intended_use_id] + policy_ids

            cursor.execute(delete_query, params)

            connection.commit()

            deleted_count = cursor.rowcount

            extra = {'code'}
            logger.info(f"Intended Use - Policy associations removed successfully. Rows affected: {deleted_count}")

            return deleted_count

    except pymysql.MySQLError as e:
        extra = {'code'}
        logger.error(f"Error deleting Intended Use - Policy associations: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()

## -intended use-get
def get_intended_use(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    iu.id,
                    iu.intended_use_identifier,
                    iu.created_at,
                    iu.revoked_at,

                    mls.lang,
                    mls.content,

                    pol.id,
                    pol.policy_uri,
                    pol.type,

                    c.id,
                    c.format,
                    c.meta,

                    cl.path,
                    
                    wrpiu.wrp_id

                FROM intended_use iu

                LEFT JOIN intended_use_purpose iup
                    ON iup.intended_use_id = iu.id

                LEFT JOIN multilanguage_string mls
                    ON mls.id = iup.mls_id

                LEFT JOIN intended_use_policy iupol
                    ON iupol.intended_use_id = iu.id

                LEFT JOIN policy pol
                    ON pol.id = iupol.policy_id
                    
                LEFT JOIN intended_use_credential iuc
                    ON iuc.intended_use_id = iu.id

                LEFT JOIN credential c
                    ON c.id = iuc.credential_id 

                LEFT JOIN claim cl
                    ON cl.credential_id = c.id
                    
                LEFT JOIN wrp_intended_use wrpiu
                    ON wrpiu.intended_use_id = iu.id

                WHERE iu.user_id = %s;
            """
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                iu_id, identifier, created_at, revoked_at,
                lang, content,
                pol_id, policy_uri, policy_type,
                cred_id, cred_format, cred_meta,
                claim_path,
                wrpiu_wrp_id
            ) in rows:

                # Intended Use base
                if iu_id not in result:
                    result[iu_id] = {
                        "intended_use_id": iu_id,
                        "intendedUseIdentifier": identifier,
                        "createdAt": str(created_at),
                        "revokedAt": str(revoked_at) if revoked_at else None,
                        "purpose": [],
                        "privacyPolicy": [],
                        "credentials": {},
                        "_purpose_seen": set(),
                        "_policy_seen": set(),
                        "wrp_id": wrpiu_wrp_id
                    }

                iu = result[iu_id]

                # PURPOSE
                if lang and content:
                    key = (lang, content)
                    if key not in iu["_purpose_seen"]:
                        iu["purpose"].append({
                            "lang": lang,
                            "content": content
                        })
                        iu["_purpose_seen"].add(key)

                # POLICY
                if policy_uri:
                    key = (policy_uri, policy_type)
                    if key not in iu["_policy_seen"]:
                        iu["privacyPolicy"].append({
                            "policy_id": pol_id,
                            "policyURI": policy_uri,
                            "type": policy_type
                        })
                        iu["_policy_seen"].add(key)

                # CREDENTIALS
                if cred_id:
                    if cred_id not in iu["credentials"]:
                        iu["credentials"][cred_id] = {
                            "credential_id": cred_id,
                            "format": cred_format,
                            "meta": cred_meta,
                            "claims": [],
                            "_claims_seen": set()
                        }

                    cred = iu["credentials"][cred_id]

                    # CLAIMS
                    if claim_path and claim_path not in cred["_claims_seen"]:
                        cred["claims"].append({
                            "path": claim_path
                        })
                        cred["_claims_seen"].add(claim_path)

            # CLEAN FINAL
            final_result = []

            for iu in result.values():

                # limpar sets internos
                del iu["_purpose_seen"]
                del iu["_policy_seen"]

                # credentials -> lista + limpar sets internos
                creds = []
                for cred in iu["credentials"].values():
                    del cred["_claims_seen"]
                    creds.append(cred)

                iu["credentials"] = creds

                final_result.append(iu)

            return final_result

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_intended_use_credential(intended_use_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    iuc.credential_id

                FROM intended_use_credential iuc

                WHERE iuc.intended_use_id = %s;
            """
            
            cursor.execute(query, (intended_use_id,))
            row = cursor.fetchall()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_intended_use_policy(intended_use_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """ 
                SELECT 
                    iup.policy_id
                    
                FROM intended_use_policy iup

                WHERE iup.intended_use_id = %s
            """

            cursor.execute(query, (intended_use_id,))
            row = cursor.fetchall()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_intendedUse(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    iu.user_id

                FROM intended_use iu

                WHERE iu.id = %s;
            """
            
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()
    
def check_wrp_intendedUse(iu_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    wiu.wrp_id

                FROM wrp_intended_use wiu

                WHERE wiu.intended_use_id = %s;
            """
            
            cursor.execute(query, (iu_id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_wrp_intendedUse(wrp_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    wiu.intended_use_id

                FROM wrp_intended_use wiu

                WHERE wiu.wrp_id = %s;
            """
            
            cursor.execute(query, (wrp_id,))
            row = cursor.fetchall()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_wrp_intermediary(intermediary_wrp_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    wrpi.intermediary_wrp_id

                FROM wrp_intermediary wrpi

                WHERE wrpi.intermediary_wrp_id = %s;
            """
            
            cursor.execute(query, (intermediary_wrp_id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_intended_use_id(intended_use_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    iu.id,
                    iu.intended_use_identifier,
                    iu.created_at,
                    iu.revoked_at,

                    mls.lang,
                    mls.content,

                    pol.id,
                    pol.policy_uri,
                    pol.type,

                    c.id,
                    c.format,
                    c.meta,

                    cl.path

                FROM intended_use iu

                LEFT JOIN intended_use_purpose iup
                    ON iup.intended_use_id = iu.id

                LEFT JOIN multilanguage_string mls
                    ON mls.id = iup.mls_id

                LEFT JOIN intended_use_policy iupol
                    ON iupol.intended_use_id = iu.id

                LEFT JOIN policy pol
                    ON pol.id = iupol.policy_id
                    
                LEFT JOIN intended_use_credential iuc
                    ON iuc.intended_use_id = iu.id

                LEFT JOIN credential c
                    ON c.id = iuc.credential_id 

                LEFT JOIN claim cl
                    ON cl.credential_id = c.id

                WHERE iu.id = %s;
            """
            
            cursor.execute(query, (intended_use_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                iu_id, identifier, created_at, revoked_at,
                lang, content,
                pol_id, policy_uri, policy_type,
                cred_id, cred_format, cred_meta,
                claim_path
            ) in rows:

                # Intended Use base
                if iu_id not in result:
                    result[iu_id] = {
                        "intended_use_id": iu_id,
                        "intendedUseIdentifier": identifier,
                        "createdAt": str(created_at),
                        "revokedAt": str(revoked_at) if revoked_at else None,
                        "purpose": [],
                        "privacyPolicy": [],
                        "credentials": {},
                        "_purpose_seen": set(),
                        "_policy_seen": set()
                    }

                iu = result[iu_id]

                # PURPOSE
                if lang and content:
                    key = (lang, content)
                    if key not in iu["_purpose_seen"]:
                        iu["purpose"].append({
                            "lang": lang,
                            "content": content
                        })
                        iu["_purpose_seen"].add(key)

                # POLICY
                if policy_uri:
                    key = (policy_uri, policy_type)
                    if key not in iu["_policy_seen"]:
                        iu["privacyPolicy"].append({
                            "policy_id": pol_id,
                            "policyURI": policy_uri,
                            "type": policy_type
                        })
                        iu["_policy_seen"].add(key)

                # CREDENTIALS
                if cred_id:
                    if cred_id not in iu["credentials"]:
                        iu["credentials"][cred_id] = {
                            "format": cred_format,
                            "meta": deserialize_json(cred_meta),
                            "claims": [],
                            "_claims_seen": set()
                        }

                    cred = iu["credentials"][cred_id]

                    # CLAIMS
                    if claim_path and claim_path not in cred["_claims_seen"]:
                        cred["claims"].append({
                            "path": deserialize_json(claim_path)
                        })
                        cred["_claims_seen"].add(claim_path)

            # CLEAN FINAL
            final_result = []

            for iu in result.values():

                # limpar sets internos
                del iu["_purpose_seen"]
                del iu["_policy_seen"]

                # credentials -> lista + limpar sets internos
                creds = []
                for cred in iu["credentials"].values():
                    del cred["_claims_seen"]
                    creds.append(cred)

                iu["credentials"] = creds

                final_result.append(iu)

            return final_result

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

## -credential-insert
def insert_credential(format, meta, user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO credential (" \
            "format, " \
            "meta, " \
            "user_id) " \
            "VALUES (%s, %s, %s)"
            
            cursor.execute(insert_query, (format, meta, user_id,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Credential successfully added. New Credential  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Credential : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

## -credential-get
def get_credentials(user_id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    c.id,
                    c.format,
                    c.meta,
                    cl.id,
                    cl.path

                FROM credential c

                LEFT JOIN claim cl 
                    ON cl.credential_id = c.id

                WHERE c.user_id = %s
            """

            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()

            result = {}

            for (
                cred_id,
                format,
                meta,
                claim_id,
                path
            ) in rows:

                if cred_id not in result:
                    result[cred_id] = {
                        "credential_id": cred_id,
                        "format": format,
                        "meta": deserialize_json(meta),
                        "claims": []
                    }

                if claim_id:
                    result[cred_id]["claims"].append({
                        "claim_id": claim_id,
                        "path": deserialize_json(path)
                    })

            return list(result.values())

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def check_credentials(id):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            query = """
                SELECT 
                    c.user_id

                FROM credential c

                WHERE c.id = %s
            """

            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                return []

    except pymysql.MySQLError as e:
        logger.error(f"Error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

## -claim-insert 
def insert_claim(credential_id, path):
    try:
        connection = conn()
        if connection:
            cursor = connection.cursor()

            insert_query = "INSERT INTO claim (" \
            "credential_id, " \
            "path) " \
            "VALUES (%s, %s)"
            
            cursor.execute(insert_query, (credential_id, path,))
            
            connection.commit()
            
            extra = {'code'} 
            logger.info(f"Claim successfully added. New Claim  ID: {cursor.lastrowid}")
            return cursor.lastrowid

    except pymysql.MySQLError as e:
        extra = {'code'} 
        logger.error(f"Error inserting Claim : {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def search_wrp_public(
    identifier=None,
    legalname=None,
    tradename=None,
    policy=None,
    entitlement=None,
    providesattestation=None,
    intendeduseidentifier=None,
    isintermediary=None,
    usesintermediary=None
):
    try:
        connection = conn()
        if not connection:
            return []

        cursor = connection.cursor()

        query = """
            SELECT 
                wrp.id,
                wrp.trade_name,
                wrp.is_intermediary,

                mls.lang,
                mls.content,

                we.entitlement,

                pol.policy_uri,

                wi.intermediary_wrp_id,

                pa.format

            FROM wallet_relying_party wrp

            LEFT JOIN wrp_srv_description wsd
                ON wsd.wrp_id = wrp.id

            LEFT JOIN multilanguage_string mls
                ON mls.id = wsd.mls_id

            LEFT JOIN wrp_entitlement we
                ON we.wrp_id = wrp.id

            LEFT JOIN provider p
                ON p.id = wrp.provider_id

            LEFT JOIN provider_policy pp
                ON pp.provider_id = p.id

            LEFT JOIN policy pol
                ON pol.id = pp.policy_id

            LEFT JOIN wrp_intermediary wi
                ON wi.wrp_id = wrp.id

            LEFT JOIN wrp_provided_attestation wrppa
                on wrppa.wrp_id = wrp.id

            LEFT JOIN provided_attestation pa
                ON pa.id = wrppa.provided_attestation_id

            WHERE 1=1
        """

        params = []

        # filters

        if tradename:
            query += " AND wrp.trade_name LIKE %s"
            params.append(f"%{tradename}%")

        if isintermediary is not None:
            query += " AND wrp.is_intermediary = %s"
            params.append(isintermediary)

        if entitlement:
            query += """
                AND wrp.id IN (
                    SELECT wrp_id 
                    FROM wrp_entitlement
                    WHERE entitlement LIKE %s
                )
            """
            params.append(f"%{entitlement}%")

        if policy:
            if policy:
                query += """
                    AND wrp.id IN (
                        SELECT wrp2.id
                        FROM wallet_relying_party wrp2
                        JOIN provider p2 ON p2.id = wrp2.provider_id
                        JOIN provider_policy pp2 ON pp2.provider_id = p2.id
                        JOIN policy pol2 ON pol2.id = pp2.policy_id
                        WHERE pol2.policy_uri LIKE %s
                    )
                """
                params.append(f"%{policy}%")

        if providesattestation:
            query += """
                AND wrp.id IN (
                    SELECT wrppa.wrp_id
                    FROM wrp_provided_attestation wrppa
                    JOIN provided_attestation pa 
                        ON pa.id = wrppa.provided_attestation_id
                    WHERE pa.format LIKE %s
                )
            """
            params.append(f"%{providesattestation}%")

        if intendeduseidentifier:
            query += """
                AND wrp.id IN (
                    SELECT wi.wrp_id
                    FROM wrp_intended_use wi
                    JOIN intended_use iu 
                        ON iu.id = wi.intended_use_id
                    WHERE iu.intended_use_identifier LIKE %s
                )
            """
            params.append(f"%{intendeduseidentifier}%")

        if usesintermediary is not None:
            if usesintermediary:
                query += """
                    AND wrp.id IN (
                        SELECT wrp_id FROM wrp_intermediary
                    )
                """
            else:
                query += """
                    AND wrp.id NOT IN (
                        SELECT wrp_id FROM wrp_intermediary
                    )
                """

        # identifier (legal_entity_identifier)
        if identifier:
            query += """
                AND wrp.id IN (
                    SELECT wrp2.id
                    FROM wallet_relying_party wrp2
                    JOIN provider p2 ON p2.id = wrp2.provider_id
                    JOIN legal_entity le2 ON le2.id = p2.legal_entity_id
                    JOIN legal_entity_identifier lei ON lei.legal_entity_id = le2.id
                    JOIN identifier i ON i.id = lei.identifier_id
                    WHERE i.identifier LIKE %s
                )
            """
            params.append(f"%{identifier}%")

        # legalname
        if legalname:
            query += """
                AND wrp.id IN (
                    SELECT wrp3.id
                    FROM wallet_relying_party wrp3
                    JOIN provider p3 ON p3.id = wrp3.provider_id
                    JOIN legal_entity le3 ON le3.id = p3.legal_entity_id
                    JOIN legal_person_name lpn ON lpn.legal_person_id = le3.legal_person_id
                    WHERE lpn.name LIKE %s
                )
            """
            params.append(f"%{legalname}%")

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        # Agregation
        result = {}

        for (
            wrp_id,
            trade_name,
            is_intermediary,
            lang,
            content,
            entitlement_val,
            policy_uri,
            intermediary_id,
            attestation_format
        ) in rows:

            if wrp_id not in result:
                result[wrp_id] = {
                    "tradeName": trade_name,
                    "srvDescription": [],
                    "entitlements": [],
                    "providesAttestations": [],
                    "isIntermediary": bool(is_intermediary) if is_intermediary is not None else None,
                    "usesIntermediary": None,
                    "policyURI": None
                }

            wrp = result[wrp_id]

            # srvDescription
            if lang and content:
                obj = {"lang": lang, "srvDescription": content}
                if obj not in wrp["srvDescription"]:
                    wrp["srvDescription"].append(obj)

            # entitlements
            if entitlement_val and entitlement_val not in wrp["entitlements"]:
                wrp["entitlements"].append(entitlement_val)

            # policy 
            if policy_uri:
                wrp["policyURI"] = policy_uri

            # usesIntermediary
            if intermediary_id:
                wrp["usesIntermediary"] = True

            # providesAttestations
            if attestation_format and attestation_format not in wrp["providesAttestations"]:
                wrp["providesAttestations"].append(attestation_format)

        # cleanup
        final = []

        for wrp in result.values():

            if not wrp["entitlements"]:
                wrp["entitlements"] = None

            if not wrp["providesAttestations"]:
                wrp["providesAttestations"] = None

            final.append(wrp)

        return final

    except pymysql.MySQLError as e:
        logger.error(f"search_wrp_public error: {e}")
        return []

    finally:
        if connection:
            cursor.close()
            connection.close()

def get_wrp_by_identifier(identifier):
    try:
        connection = conn()
        cursor = connection.cursor()

        query = """
            SELECT wrp.id
            FROM wallet_relying_party wrp

            JOIN provider p ON p.id = wrp.provider_id
            JOIN legal_entity le ON le.id = p.legal_entity_id
            JOIN legal_entity_identifier lei ON lei.legal_entity_id = le.id
            JOIN identifier i ON i.id = lei.identifier_id

            WHERE i.identifier = %s
        """

        cursor.execute(query, (identifier,))
        row = cursor.fetchone()

        if not row:
            return None

        wrp_id = row[0]

        return get_wrp_id(wrp_id)

    except Exception as e:
        logger.error(e)
        return None

def check_intended_use(
    identifier,
    claim_path=None,
    credential_format=None,
    credential_meta=None,
    intended_use_identifier=None
):
    try:
        connection = conn()
        cursor = connection.cursor()

        query = """
            SELECT 1
            FROM wallet_relying_party wrp

            JOIN provider p 
                ON p.id = wrp.provider_id
            JOIN legal_entity le 
                ON le.id = p.legal_entity_id
            JOIN legal_entity_identifier lei 
                ON lei.legal_entity_id = le.id
            JOIN identifier i 
                ON i.id = lei.identifier_id

            JOIN wrp_intended_use wi 
                ON wi.wrp_id = wrp.id
            JOIN intended_use iu 
                ON iu.id = wi.intended_use_id

            LEFT JOIN intended_use_credential iuc
                ON iuc.intended_use_id = iu.id
            LEFT JOIN credential c 
                ON c.id = iuc.credential_id

            LEFT JOIN claim cl 
                ON cl.credential_id = c.id

            WHERE i.identifier = %s
        """

        params = [identifier]

        if intended_use_identifier:
            query += " AND iu.intended_use_identifier = %s"
            params.append(intended_use_identifier)

        if credential_format:
            query += " AND c.format = %s"
            params.append(credential_format)

        if credential_meta:
            query += " AND c.meta = %s"
            params.append(credential_meta)

        if claim_path:
            query += " AND cl.path = %s"
            params.append(claim_path)

        query += " LIMIT 1"

        cursor.execute(query, tuple(params))
        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        logger.error(e)
        return False