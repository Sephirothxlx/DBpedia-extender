# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import pprint

from SPARQLWrapper import SPARQLWrapper, JSON

"""
    
"""

__author__ = "freemso"

DBPEDIA_ENDPOINT = "http://dbpedia.org/sparql"
DBPEDIA_PREFIX = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX : <http://dbpedia.org/resource/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX dbpedia2: <http://dbpedia.org/property/>
PREFIX dbpedia: <http://dbpedia.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dbo: <http://dbpedia.org/ontology/>
"""


def get_categories(entity_id):
    """
    Get all the categories of an entity from DB-pedia.
    :param entity_id: universal identifier of the entity
    :return: <list> of entity, each is a category of the target entity
    """
    dbpedia_sql = """
        PREFIX e: <%s>
        SELECT DISTINCT ?category
        WHERE {
            {
                e: dct:subject ?category .
                FILTER NOT EXISTS {
                    e: dct:subject ?subCategory .
                    ?subCategory skos:broader* ?type .
                    FILTER (?subtype != ?type)
                }
            }
            UNION
            {e: dbo:category ?category .}
        }
    """ % entity_id
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    return [result["category"]["value"] for result in results]


def get_types(entity_id):
    """
    Get types of an entity from DB-pedia and YAGO.
    :param entity_id: universal identifier of the entity
    :return: <list> of entity, each is a type of the target entity
    """
    dbpedia_sql = """
        PREFIX e: <%s>
        SELECT DISTINCT ?type
        WHERE {
            {{e: dbo:type ?type .}
            UNION
            {e: rdf:type ?type .}}
            UNION
            {e: dbpedia2:type ?type .}
            FILTER NOT EXISTS {
                {e: dbo:type ?subtype .}
                UNION
                {e: rdf:type ?subtype .}
                ?subtype rdfs:subClassOf ?type .
                FILTER (?subtype != ?type)
            }
        }
    """ % entity_id
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    return [result["type"]["value"] for result in results]


def get_pv_pairs(entity_id):
    """
    Get property-value pairs of the target entity from YAGO and DB-pedia.
    :param entity_id: universal identifier of the entity
    :return: <list> of (property, value)
    """
    dbpedia_sql = """
        SELECT DISTINCT ?p ?o
        WHERE {
            <%s> ?p ?o
        }
        ORDER BY ?p
    """ % entity_id
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    return [(result["p"]["value"], result["o"]["value"]) for result in results]


def get_csks(entity_id):
    """
    Get common sense knowledge from ConceptNet.
    :param entity_id: universal identifier of the entity
    :return: <list> of (property, value)
    """
    # TODO
    return []


def is_multi_valued(property_id):
    """
    Check if the property is multi-valued.
    Calculate all predicates of <SPO> in DB-pedia, those objectives values of
    predicates that occur more than once are treated as multi-value attributes.
    :return: <bool>
    """
    dbpedia_sql = """
        SELECT ?s ?o1 ?o2
        WHERE {
            ?s  %s ?o1 .
            ?s  %s ?o2 .
            FILTER (?o1 != ?o2)
        }
        LIMIT 1
    """ % (property_id, property_id)
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    return len(results) > 0


def get_type_members(type_id):
    """
    Get entities whose types contain <type_id>
    :param type_id: uuid of th type
    :return: <list> of entity
    """
    dbpedia_sql = """
        SELECT DISTINCT ?subject
        WHERE {
           {?subject dbo:type <%s> .}
           UNION
           {?subject rdf:type <%s> .}
           UNION
           {?subject dbr:type <%s> .}
           UNION
           {?subject owl:type <%s> .}
        }
        ORDER BY ?type
    """ % (type_id, type_id, type_id, type_id)
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    return [result["subject"]["value"] for result in results]


def get_resource_name(resource_id):
    """
    Get human-readable English name of the resource if available
    :param resource_id: uuid of the resource, resource could be any entity and relation
    :return: <str> name from dbpedia if available, extract from uuid if not
    """
    dbpedia_sql = """
        SELECT DISTINCT ?name
        WHERE {
            {<%s> foaf:name ?name . }
            UNION
            {<%s> rdfs:label ?name . }
            FILTER (LANG(?name) = "en")
        }
    """ % (resource_id, resource_id)
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    if results:
        return results[0]["name"]["value"]
    else:
        return resource_id.rsplit("/", 1)[-1]


def get_super_classes(class_id):
    """
    Get the super classes of the dbpedia class
    :param class_id: uuid the class
    :return: <list> of super classes
    """
    dbpedia_sql = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX classes: <http://dbpedia.org/resource/classes#>
        SELECT DISTINCT ?o
        FROM NAMED classes:
        WHERE {
            GRAPH classes: {
                <%s> rdfs:subClassOf ?o
            }
        }
    """ % class_id
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    return [result["o"]["value"] for result in results]


def __execute_sparql(endpoint, sql):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(DBPEDIA_PREFIX + sql)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
    logging.root.setLevel(level=logging.DEBUG)

    # Testing

    #Test get_categories()
    test_entity_id = "http://dbpedia.org/resource/Tiger"
    test_entity_categories = get_categories(test_entity_id)
    logging.debug("Categories of {}:\n{}\nTotal number: {}".format(
        test_entity_id,
        pprint.pformat(test_entity_categories),
        len(test_entity_categories)
    ))

    # Test get_types()
    test_entity_id = "http://dbpedia.org/resource/Yao_Ming"
    test_entity_types = get_types(test_entity_id)
    logging.debug("Types of {}:\n{}\nTotal number: {}".format(
        test_entity_id,
        pprint.pformat(test_entity_types),
        len(test_entity_types)
    ))
    
    #Test is_multi_valued()
    test_property_id_1 = "dbo:wikiPageID"
    test_property_id_2 = "dbo:abstract"
    test_property_id_3 = "foaf:gender"
    logging.debug("{} is multi-valued? {}".format(
        test_property_id_1,
        is_multi_valued(test_property_id_1)
    ))
    logging.debug("{} is multi-valued? {}".format(
        test_property_id_2,
        is_multi_valued(test_property_id_2)
    ))
    logging.debug("{} is multi-valued? {}".format(
        test_property_id_3,
        is_multi_valued(test_property_id_3)
    ))
    
    # Test get_type_members()
    test_type_id = 'http://dbpedia.org/class/yago/WikicatBuildingsAndStructuresCompletedIn1889'
    logging.debug("Number of type members of type {}: {}".format(
        test_type_id,
        len(get_type_members(test_type_id))
    ))

    # Test get_resource_names()
    test_entity_id = "http://dbpedia.org/resource/Tiger"
    get_resource_name(test_entity_id)