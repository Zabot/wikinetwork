#!/usr/bin/env python3
import random
import numpy
import jellyfish
from graph_tool.all import *

from heapq import heappush, heappop
import itertools
import collections
import sys

print("Loading graph O(V+E)")
g = load_graph("simplewiki.xml.gz")

page_categories = g.vertex_properties["page_categories"]
page_title = g.vertex_properties["page_title"]

category_size = collections.defaultdict(int)

for v in g.vertices():
    for category in page_categories[v]:
        category_size[category] += 1

print("\t{} vertices".format(g.num_vertices()))
print("\t{} edges".format(g.num_edges()))

print("Extract largest component O(V+E)")
largest_component = label_largest_component(g)

wiki = GraphView(g, vfilt=largest_component)
print("\t{} vertices".format(wiki.num_vertices()))
print("\t{} edges".format(wiki.num_edges()))

def title(v):
    return page_title[v].replace("_", " ")

for i in range(10):
    s, t = random.sample(list(wiki.vertices()), 2)

    cur = s
    path = []

    abandonded = set([])

    try:
        t_category = max(map(lambda c: (category_size[c], c), page_categories[t]))[1]
    except ValueError:
        t_category = ""
        pass

    title_matches = []
    high_degree = []
    category_matches = []
    stack = []
    while cur != t:
        for n in cur.out_neighbors():
            if n not in abandonded:
                try:
                    c = sorted(map(lambda x: -jellyfish.jaro_winkler(x, t_category), page_categories[n]) )
                    heappush(category_matches, (c[0], n))
                except:
                    pass

                # Negative degree makes large degree nodes bubble to top of min
                # heap
                heappush(high_degree, (-n.out_degree(), n))

                heappush(title_matches, (-jellyfish.jaro_winkler(title(t), title(n)), n))

        try:
            if title_matches and title_matches[0][0] < -0.750:
                cur = heappop(title_matches)[1]

            elif category_matches and category_matches[0][0] < -0.700:
                cur = heappop(category_matches)[1]

            else:
                cur = heappop(high_degree)[1]

        except IndexError:
            abandonded.add(path.pop())
            cur = path[-1]
            continue

        title_matches = []
        category_matches = []
        high_degree = []
        path.append(cur)
        abandonded.add(cur)

    print("{}\t{} -> {}".format(len(path), title(s), title(t)))

