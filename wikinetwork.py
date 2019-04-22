#!/usr/bin/env python3
from graph_tool.all import *
import re
path="simplewiki"

page_ids = {}

ignored = 0
page_regex = re.compile("\((\d+),(\d+),'(.*?)','(.*?)',(\d),(\d),(0\.\d+),'(.*?)',('.*?'|NULL),(\d+),(\d+),(NULL|'.*?'),(NULL|'.*?')\)")

# Create the graph
g = Graph()
page_title = g.new_vertex_property("string")
page_categories = g.new_vertex_property("vector<string>")
g.vertex_properties["page_title"] = page_title
g.vertex_properties["page_categories"] = page_categories

vertex = {}

print("Reading page titles...")
with open(path+"/simplewiki-latest-page.sql", "r") as pages:
    for line in pages:
        for match in re.finditer(page_regex, line):
            page_id = int(match.group(1))
            namespace = int(match.group(2))
            title = match.group(3)

            if namespace != 0:
                ignored += 1
                continue

            v = g.add_vertex()
            vertex[page_id] = v
            page_title[v] = title

            page_ids[title] = page_id

print("\t{} articles".format(g.num_vertices()))
print("\t{} discarded pages".format(ignored))


###### Read page link file
valid_ns = set([0])
link_count = 0
red_links = 0
discarded = 0
link_regex = re.compile("\((\d+?),(\d+?),'(.*?)',(\d+?)\)")
print("Reading page links...")
with open(path+"/simplewiki-latest-pagelinks.sql", "r") as links:
    for line in links:
        for match in re.finditer(link_regex, line):
            # Id of parent page
            from_id = int(match.group(1))
            # Namespace of parent page
            from_ns = int(match.group(4))

            # Title of linked page
            linked_page = match.group(3)
            # Namespace of linked page
            linked_ns  = int(match.group(2))

            if linked_ns not in valid_ns or from_ns not in valid_ns:
                discarded += 1
                continue

            try:
                linked_id = page_ids[linked_page]
                link_count += 1

                g.add_edge(vertex[from_id], vertex[linked_id])

            except KeyError:
                red_links += 1
print("\t{} valid links".format(link_count))
print("\t{} broken links".format(red_links))
print("\t{} discarded links".format(discarded))
print("\t{}% edge density".format(100.0 * link_count / (g.num_vertices() * (g.num_vertices() - 1))))


##### Read catagory link file
print("Reading category assignments...")
category_regex = re.compile("\((\d+?),'(.*?)','(.*?)','(\d{4}\-\d\d-\d\d) (\d\d:\d\d:\d\d)','(.*?)','(.*?)','(.*?)'\)")
assignments = 0
with open(path+"/simplewiki-latest-categorylinks.sql", "r") as categories:
    for line in categories:
        for match in re.finditer(category_regex, line):
            # ID of page
            page_id = int(match.group(1))

            # Title of category of page
            category = match.group(2)
            try:
                page_categories[vertex[page_id]].append(category)

                assignments += 1
            except KeyError:
                print("Unknown category {} on page {}".format(category, page_id))
print("\t{} assignments".format(assignments))

g.save("simplewiki.xml.gz")

