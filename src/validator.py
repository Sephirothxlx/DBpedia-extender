# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import search
import dataset
from dbnode import Node

__author__ = "Sephirothxlx"

#coefficiency for search
A = 0.5
#coefficiency for siblings
B = 0.5

def validate(target_node, attributes):
	"""
	Validate every single valued attribute if it is valid
	:param target_node: <Node>
	:param attributes: <list> of (p, v)
	:return: <list> of (p, v) 
	"""
	target_id = target_node.uuid
	target_siblings = target_node.siblings

	multi_value = set()
	#Use a dictionary to store the single_value
	single_value = {}

	conflict = set()
	for x in attributes:
		if dataset.is_multi_valued(x[0],target_node) == False:
			if x[0] in single_value.keys():
				conflict.add((x[0],x[1]))
				conflict.add((x[0],single_value[x[0]]))
			else:
				single_value[x[0]] = x[1]
		else:
			multi_value.add(x)

	final_single_value = set()
	if len(conflict) != 0:
		search_score = validate_by_search(target_id, conflict)
		sibling_score = validate_by_siblings(target_siblings, conflict)

		final_score = {}
		for x in search_score.keys():
			for y in search_score[x]:
				score = search_score[x][y] * A + sibling_score[x][y] * B
				if x in final_score:
					final_score[x][y] = score
				else:
					final_score.update({x: {y: score}})

		i = 0
		temp0 = ""
		for x in final_score.keys():
			for y in final_score[x]:
				if final_score[x][y] > i:
					i = final_score[x][y]
					temp0 = y
			single_value[x] = temp0
		for x in single_value.keys():
			final_single_value.add((x,single_value[x]))
	else:
		for x in single_value.keys():
			final_single_value.add((x,single_value[x].strip()))

	final_attributes = multi_value | final_single_value

	return final_attributes

def validate_by_search(target_id, conflict):
	"""
	Calculate every score for every single value.
	:param single_value: <dictionary> of {p:{v}}
	:return: <dict> of {p:{v:score}}
	"""

	res = {}
	for x in conflict:
		s = target_id.split("/")[-1]
		p = x[0].split("/")[-1]
		o = x[1].split("/")[-1]
		keyword = s + " " + p +" "+o
		google = search.get_search_results_Google(keyword)
		baidu = search.get_search_results_Baidu(keyword)
		bing = search.get_search_results_Bing(keyword)
		total = google+baidu+bing
		if x[0] in res:
			res[x[0]][x[1]] = total
		else:
			res.update({x[0]:{x[1]:total}})

	total_number = 0
	for x in res:
		for y in res[x]:
			total_number += res[x][y]
		for y in res[x]:
			res[x][y] = res[x][y] / total_number
		total_number = 0

	return res

def validate_by_siblings(siblings, conflict):
	"""
	Calculate every score for single value.
	:param single_vlaue: <dictionary> of {p:{v}}
	:param siblings: <Node> of siblings
	:return: <dict> of {p:{v:score}}
	"""
	res = {}

	# for skipping this funciton to test
	# res = {}
	# for x in conflict:
	# 	if x[0] in res:
	# 		res[x[0]][x[1]] = 1
	# 	else:
	# 		res.update({x[0]:{x[1]:1}})
	# return res

	total_number = len(siblings)
	for x in conflict:
		n = 0
		for s in siblings:
			print (1)
			if dataset.has_pv_pair(s.uuid, x[0], x[1]) == True:
				n += 1
		m = n / total_number
		if x[0] in res:
			res[x[0]][x[1]] = 1
		else:
			res.update({x[0]:{x[1]:1}})
	return res

if __name__ == '__main__':
	n = Node("http://dbpedia.org/resource/Huawei_P9")
	siblings = set()
	f = open("siblings.txt", "r", encoding="utf-8")
	for l in f.readlines():
		if l != "":
			siblings.add(Node(l.strip('\n')))
	attributes = set()
	f = open("result.txt", "r", encoding="utf-8")
	for l in f.readlines():
		if l != "":
			l = l.lstrip('(')
			l = l.rstrip(')\n')
			attributes.add((l.split(",")[0].strip('\'').strip(),l.split(",")[1].strip().strip('\'').strip()))
	n.siblings = siblings
	c = set()
	c.add(Node("http://dbpedia.org/resource/Category:Smartphones"))
	c.add(Node("http://dbpedia.org/resource/Category:Mobile_phones_introduced_in_2016"))
	n.categories = c
	test_ress=validate(n, attributes)
	print (test_ress)