# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import dataset

__author__ = "Sephirothxlx"

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
        self.types=None
        self.categories=None
        self.parents = None
        self.siblings = None
        self.attributes = None  # CSK from ConceptNet and PV-pairs from DB-pedia are all considered as attributes
        self.extracted_attributes = None  # Newly extracted attributes during this extraction process
        self.extracted_correct_attributes = None  # Attributes that are considered as correct after validation

    def __eq__(self, other):
        return hasattr(other, "uuid") and self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)

    def get_uuid(self):
        return self.uuid

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
            all_types = [Node(type_id) for type_id in dataset.get_types(self.uuid)]
            self.types = set(all_types)
            type_parents=[]
            for type_node in all_types:
                type_parents = type_parents + dataset.get_super_classes(type_node.uuid) + dataset.get_types(type_node.uuid)
            self.types = {node for node in self.types if node.uuid not in type_parents}
            all_categories = [Node(category_id) for category_id in dataset.get_categories(self.uuid)]
            self.categories=set(all_categories)
            self.parents=self.types | self.categories
        return self.parents

    def get_siblings(self):
        """
        Get sibling nodes of the target node
        :return: <list> of <Node>
        """
        if not self.siblings:
            self.siblings = set()
            for p in self.types:
                children = dataset.get_type_members(p.uuid)
                self.siblings = self.siblings.union({Node(c) for c in children})
            for s in self.categories:
                children = dataset.get_category_member(s.uuid)
                self.siblings = self.siblings.union({Node(c) for c in children})

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