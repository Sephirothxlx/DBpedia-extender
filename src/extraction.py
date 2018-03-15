# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    
"""

import logging
from collections import Counter

import dataset

import numpy

__author__ = "freemso"

# Hyper-parameters
ALPHA = 1

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


def extract(target_uuid):
    target_node = id2node(target_uuid)
    logging.info("Extracting common sense knowledge for {}".format(target_node.get_name()))

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

    #for comparision
    #target_attributes = target_node.get_attributes()
    target_attributes=set()
    parents_attributes_counter = count_nodes_attributes(parents)

    siblings_attributes_counter = count_nodes_attributes(siblings)


    # Inherit from parent
    for p in parents:
        p_attr = p.get_attributes()
        target_attributes.update(p_attr)

    # Inference from sibling
    for attribute in siblings_attributes_counter:
        if siblings_attributes_counter[attribute] > 0 * ALPHA:
            # This attribute is valid
            target_attributes.update(attribute)

    # Merge results(from parents and from siblings) and conflict detection
    # duplicate conflict will be eliminated by attribute of set datatype
    

    # Show the result
    f=open("result.txt","w",encoding='utf-8')
    for x in target_attributes:
        print(str(x))
        f.write(str(x)+"\n")


def count_nodes_attributes(nodes):
    """
    Count the attributes of a list of nodes
    :param nodes: <list> of <Node>
    :return: <Counter> of attributes with their occurrences
    """
    attributes_counter = Counter()
    x=0
    for node in nodes:
        x=x+1
        try:
            attributes = node.get_attributes()
            for attribute in attributes:
                attributes_counter[attribute] += 1
            if x==10:
                break
        except Exception as e:
            continue
    return attributes_counter


class Node(object):
    """
    Node of the knowledge graph.
    Entity, category, type and value in PV-pair are all nodes.
    """

    def __init__(self, uuid):
        """
        :param uuid: universal identifier
        """
        self.uuid = uuid  # uri
        self.parents = None
        self.siblings = None
        self.attributes = None  # CSK from ConceptNet and PV-pairs from DB-pedia are all considered as attributes
        self.extracted_attributes = None  # Newly extracted attributes during this extraction process
        self.extracted_correct_attributes = None  # Attributes that are considered as correct after validation

    def __eq__(self, other):
        return hasattr(other, "uuid") and self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)

    def get_name(self):
        """
        Get a human readable name of the node
        :return: <str>
        """
        name = dataset.get_resource_name(self.uuid)
        return name if len(name) > 0 else self.uuid.rsplit("/", 1)[-1]

    def get_parents(self):
        """
        Get parent nodes of the target node
        :return: <list> of <Node>
        """
        if not self.parents:
            all_types = [id2node(type_id) for type_id in dataset.get_types(self.uuid)]
            self.parents = set(all_types)
            for type_node in all_types:
                type_parents = dataset.get_super_classes(type_node.uuid)
                self.parents = {node for node in self.parents if node.uuid not in type_parents}
        return self.parents

    def get_siblings(self):
        """
        Get sibling nodes of the target node
        :return: <list> of <Node>
        """
        if not self.siblings:
            self.siblings = set()
            for p in self.parents:
                children = dataset.get_type_members(p.uuid)
                self.siblings = self.siblings.union({id2node(c) for c in children})
        return self.siblings

    def get_attributes(self):
        """
        Get the valid attributes of the node
        :return: <list> of (property<Edge>, value<Node>)
        """
        if not self.attributes:
            # Get PV-pairs and CSK from database
            pv_pairs = dataset.get_pv_pairs(self.uuid)
            csks = dataset.get_csks(self.uuid)
            # Merge duplicated attributes
            self.attributes = set(pv_pairs + csks)

        if self.extracted_correct_attributes:
            return self.attributes.union(self.extracted_correct_attributes)
        else:
            return self.attributes


def is_multi_valued(property_id):
    """
    Check if the edge is multi-valued.
    Calculate all predicates of <SPO> in DB-pedia, those objectives values of
    predicates that occur more than once are treated as multi-value attributes.
    :return: <bool>
    """
    pairs = dataset.get_all_subjects(property_id)
    return len(pairs) > len(set(pairs))


# def immediate_category_filter(category_nodes):
#     """
#     Filter out those categories who are at a higher level in the hierarchy.
#     Hierarchy information is available in DB-pedia Ontology.
#     :param category_nodes: <list> of <Node>
#     :return: <list> of <Node>, with no hierarchy conflict(granularity)
#     """
#     origin = category_nodes[:]
#     result = category_nodes[:]
#
#     for id in origin:
#         cur_cate = dataset.get_categories(id)  # Does Category has parent category?
#         result = list(set(result) - (set(result) & set(cur_cate)))
#     return result


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s: %(levelname)s: %(message)s")
    logging.root.setLevel(level=logging.INFO)
    extract("http://dbpedia.org/resource/Huawei_P9")
