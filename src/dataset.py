# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pprint

from SPARQLWrapper import SPARQLWrapper, JSON

__author__ = "Sephirothxlx"

#Some configurations for DBPEDIA
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

def __execute_sparql(endpoint, sql):
    """
    Get the query results by SPARQL.
    :param endpoint: dataset's address
    :param sql: SPARQL query
    :return: <list> of entity
    """
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(DBPEDIA_PREFIX + sql)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

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

def get_category_member(category_id):
    """
    Get entities whose categories contain <category_id>
    :param category_id: uuid of the category
    :return: <list> of entity
    """
    dbpedia_sql = """
        SELECT DISTINCT ?subject
        WHERE {
            {?subject dct:subject <%s>}
            UNION
            {?subject dbo:category <%s>}
        }
    """ % (category_id, category_id)
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    return [result["subject"]["value"] for result in results]

def get_pv_pairs(entity_id):
    """
    Get property-value pairs of the target entity from YAGO and DB-pedia.
    :param entity_id: universal identifier of the entity
    :return: <list> of (property, value)
    """
    dbpedia_sql = """
        SELECT DISTINCT ?p ?o
        WHERE {
            {<%s> ?p ?o}
            FILTER (?p != <http://dbpedia.org/ontology/wikiPageID>)
            FILTER (?p != <http://dbpedia.org/ontology/wikiPageRevisionID>)
            FILTER (?p != <http://dbpedia.org/ontology/wikiPageWikiLink>)
            FILTER (?p != <http://dbpedia.org/ontology/wikiPageExternalLink>)

        }
        ORDER BY ?p
    """ % entity_id
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    return [(result["p"]["value"], result["o"]["value"]) for result in results]

def is_multi_valued(property_id, target_node):
    """
    Check if the property is multi-valued.
    Calculate all predicates of <SPO> in DB-pedia, those objectives values of
    predicates that occur more than once are treated as multi-value attributes.
    :return: <bool>
    """
    p = property_id.lstrip('\'').rstrip('\'')

    ss = ""
    for x in target_node.categories:
        if x.uuid !="":
            ss += "{?s dct:subject " + "<" + x.uuid.rstrip("\n") + ">} UNION"
    ss = ss.rstrip("UNION")

    dbpedia_sql = """
    SELECT COUNT(DISTINCT ?s) AS ?n
    WHERE {
        ?s  <%s> ?o1 .
        {
            %s
        }
    }
    """ % (p, ss)

    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    total = int(results[0]["n"]["value"])

    dbpedia_sql = """
    SELECT COUNT(DISTINCT ?s) AS ?n
    WHERE {
        ?s  <%s> ?o1 .
        ?s  <%s> ?o2 .
        FILTER (?o1 != ?o2)
        {
            %s
        }
    }
    """ % (p, p, ss)
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    multi = int(results[0]["n"]["value"])

    single = total - multi
    if single >= multi:
        return False
    else:
        return True

def has_pv_pair(subject_id, property_id, value_id):
    """
    Check if there is such a triple
    :param subject_id: uuid of the subject
    :param property_id: uuid of the property
    :parem value_id: uuid of the value
    :return: True of False
    """
    dbpedia_sql = """
        SELECT COUNT(DISTINCT ?s) AS ?n
        WHERE {
            ?s <%s> <%s>
            FILTER (?s = <%s>)
        }
    """ % (property_id, value_id, subject_id)
    results = __execute_sparql(DBPEDIA_ENDPOINT, dbpedia_sql)["results"]["bindings"]
    if int(results[0]["n"]["value"]) == 1:
        return True
    else:
        return False

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

def get_csks(entity_id):
    """
    Get common sense knowledge from ConceptNet.
    :param entity_id: universal identifier of the entity
    :return: <list> of (property, value)
    """
    # TODO
    return []

# This main function is just for function tests.
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
    
    # Test get_type_members()
    test_type_id = 'http://dbpedia.org/class/yago/WikicatBuildingsAndStructuresCompletedIn1889'
    logging.debug("Number of type members of type {}: {}".format(
        test_type_id,
        len(get_type_members(test_type_id))
    ))

    # Test get_resource_names()
    test_entity_id = "http://dbpedia.org/resource/Tiger"
    get_resource_name(test_entity_id)