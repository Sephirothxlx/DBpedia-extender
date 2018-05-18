# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import numpy
from collections import Counter

from dbnode import Node
import dataset
import validator

__author__ = "Sephirothxlx"

id_node_map = {}

def id2node(uuid):
    """
    Get the node of id
    :param uuid: universal identifier of the node
    :return: <Node>
    """
    if uuid in id_node_map:
        return id_node_map[uuid]
    else:
        node = Node(uuid)
        id_node_map[uuid] = node
        return node

def count_nodes_attributes(nodes, attributes_set):
    """
    Count the attributes of a list of nodes
    :param nodes: <list> of <Node>
    :param attributes_set: <set> of <Attributes>
    :return: <Counter> of attributes with their occurrences
    """
    attributes_counter = Counter()
    x=0
    for node in nodes:
        x+=1
        print(x)
        try:
            attributes = node.get_attributes()
            for attribute in attributes:
                attributes_set.add(attribute)
                attributes_counter[attribute] += 1
        except Exception as e:
            continue
    return attributes_counter

def immediate_category_filter(category_nodes):
    """
    Filter out those categories who are at a higher level in the hierarchy.
    Hierarchy information is available in DB-pedia Ontology.
    :param category_nodes: <list> of <Node>
    :return: <list> of <Node>, with no hierarchy conflict(granularity)
    """
    origin = category_nodes[:]
    result = category_nodes[:]

    for id in origin:
        cur_cate = dataset.get_categories(id)  # Does Category has parent category?
        result = list(set(result) - (set(result) & set(cur_cate)))
    return result

def extract(target_uuid, output_filename, ALPHA):
    """
    Extract the properties from the target entity.
    :param target_uuid: uuid of target_uuid
    """

    logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
    logging.root.setLevel(level=logging.INFO)

    target_node = id2node(target_uuid)
    logging.info("Extracting common sense knowledge for {}".format(target_node.get_name()))

    #Get the parents node for this entity
    parents = target_node.get_parents()
    num_parents = len(parents)
    logging.info("{} has {} parents: {}".format(
        target_node.get_name(),
        num_parents,
        ", ".join([p.get_name() for p in parents])
    ))

    siblings = target_node.get_siblings()
    num_siblings = len(siblings)
    logging.info("Total number of siblings: {}".format(num_siblings))

    #Count the number of every attribute of siblings
    siblings_attributes = set()
    siblings_attributes_counter = count_nodes_attributes(siblings, siblings_attributes)

    target_attributes=set()
    # Inherit from parent
    # But there are no need to get this properties.
    # for p in parents:
    #     p_attr = p.get_attributes()
    #     target_attributes.update(p_attr)

    threshold = num_siblings * ALPHA

    # Inference from sibling
    for a in siblings_attributes:
        if siblings_attributes_counter[a] > threshold:
            # This attribute is valid
            target_attributes.add(a)

    #For validation test
    # f=open("siblings.txt","a",encoding='utf-8')
    # f.write(target_node.uuid+"\n")
    # for x in siblings:
    #     f.write(str(x.uuid)+"\n")
    # f.write("\n")

    #Validation
    target_attributes = validator.validate(target_node, target_attributes)

    # Show the result
    f=open(output_filename,"a",encoding='utf-8')
    f.write(target_node.uuid+"\n")
    for x in target_attributes:
        f.write(str(x)+"\n")
    f.write("\n")

    logging.info("Extract successfully!")

if __name__ == '__main__':
    # logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
    # logging.root.setLevel(level=logging.INFO)

    #device
    #extract("http://dbpedia.org/resource/Huawei_P9")
    #extract("http://dbpedia.org/resource/Game_Gear")
    #extract("http://dbpedia.org/resource/AC4_tank")
    #extract("http://dbpedia.org/resource/Nock_gun")
    #extract("http://dbpedia.org/resource/Microsoft_Lumia_950")
    #extract("http://dbpedia.org/resource/Springfield_model_1880")
    #extract("http://dbpedia.org/resource/AMT_Skipper")
    #extract("http://dbpedia.org/resource/MBT_LAW")
    #extract("http://dbpedia.org/resource/Google_Daydream")
    #extract("http://dbpedia.org/resource/Nicolette_1080")

    #people
    # extract("http://dbpedia.org/resource/Lorine_Livington_Pruette")
    # extract("http://dbpedia.org/resource/Nikolaos_Ventouras")
    # extract("http://dbpedia.org/resource/Peter_Ceffons")

    #place
    extract("http://dbpedia.org/resource/Ternary_plot","test_result.txt",0.5)
    extract("http://dbpedia.org/resource/Town_Toyota_Center","test_result.txt",0.5)
    extract("http://dbpedia.org/resource/Balsas_River","test_result.txt",0.5)
    extract("http://dbpedia.org/resource/Baram_Dam","test_result.txt",0.5)
    extract("http://dbpedia.org/resource/Canada","test_result.txt",0.5)

    #plant
    extract("http://dbpedia.org/resource/Apple","test_result.txt",0.5)
    extract("http://dbpedia.org/resource/Aronia","test_result.txt",0.5)
    extract("http://dbpedia.org/resource/Bulbine","test_result.txt",0.5)
    extract("http://dbpedia.org/resource/Strawberry","test_result.txt",0.5)
    extract("http://dbpedia.org/resource/Willow","test_result.txt",0.5)