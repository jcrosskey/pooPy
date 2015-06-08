#!/usr/bin/python
import re
import sys

class Read:
    """ class Read, stores a read in a graph """
    read_count = 0
    def __init__(self, gdl_string):
        self.read_id = map(int, re.findall(r'\d+', gdl_string))[1]
        Read.read_count += 1
        self.list_of_edges = []
    def __str__(self):
        return 'Read with id %d, number of adjacent edges: %d' % (self.read_id, len(self.list_of_edges))
    def __repr__(self):
        return 'node: {title"%d" label:"%d"}' % (self.read_id, self.read_id)
    def __int__(self):
        return self.read_id
    def __eq__(self,other):
        return self.read_id == other.read_id
    def add_edge(self, edge):
        if edge not in self.list_of_edges:
            self.list_of_edges.append(edge)
    def get_neighbors(self):
        neighbors = []
        for edge in self.list_of_edges:
            if edge.target == self.read_id:
                neighbors.append(edge.source)
            else:
                neighbors.append(edge.target)
        return neighbors
                

class Edge:
    """ class Edge, stores an edge in a graph, and its properties, including:
        source read id
        target read id
        orientation
        flow
        coverage depth
        overlap offset
        number of reads contained in the edge (>0 if composite; =0 if simple)
        gdl_string
    """
    edge_count = 0
    def __init__(self, gdl_string):
        ''' Get an edge from a line starting with "edge:" in .gdl file '''
        if gdl_string.startswith("edge:"):
            integers = map(int,re.findall(r'\d+', gdl_string))
            self.source = integers[0]
            self.target = integers[1]
            if "backarrowstyle:solid" in gdl_string:
                self.orientation = 1 if "arrowstyle:solid" in gdl_string else 0
            elif "color: blue" in gdl_string:
                self.orientation = 2
            else:
                self.orientation = 3
            self.flow = integers[-4]
            self.coverage_depth = integers[-3]
            self.offset = integers[-2]
            self.reads = integers[-1]
            self.gdl_string = gdl_string
            Edge.edge_count += 1

    def __str__(self):
        return 'Edge: %d ---> %d \norientation: %d flow: %d \noffset: %d \nnumber of reads: %d' % \
                (self.source, self.target, self.orientation, self.flow, self.offset, self.reads)


class Graph:
    """ class Graph, with reads as nodes and edges between them """
    def __init__(self, gdl_file):
        ''' Read graph from a .gdl file '''
        gdl = open(gdl_file,'r')
        self.gdl_setting_str = ""
        self.reads = {}
        self.edges = {}
        edge_id = 0
        for line in gdl:
            if not (line.startswith("graph:") or line.startswith("node:") or line.startswith("edge:") or line.startswith("}")):
                self.gdl_setting_str += line
            elif line.startswith("node:"):
                read = Read(line)
                self.reads[int(read)] = read
            elif line.startswith("edge:"):
                edge_id += 1
                edge = Edge(line)
                self.edges[edge_id] = edge
                edge.edge_id = edge_id
                self.reads[edge.source].add_edge(edge)
                self.reads[edge.target].add_edge(edge)
        gdl.close()
        sys.stderr.write("{}\n".format(str(self)))


    def get_num_reads(self):
        return len(self.reads)

    def get_num_edges(self):
        return len(self.edges)

    def __str__(self):
        return 'Graph with %d nodes and %d edges' % (self.get_num_reads(), self.get_num_edges()) 

    def subgraph_node(self, read_ids, depth=10, quiet=False):
        ''' Get all the edges "depth" steps away from a list of read_ids '''
        edge_ids = []
        if type(read_ids) is not list:
            read_ids = [read_ids]
        read_ids = list(set(read_ids))
        reads = [self.reads.get(x,None) for x in read_ids] # reads corresponding to the read_ids, if read_id does not exist, read = None
        reads = [x for x in reads if x is not None] # Filter out None's in the read list
        sys.stderr.write("{} read(s) in the graph.\n".format(len(reads)))
        if len(reads) == 0:
            sys.stderr.write('Nodes are not in graph.\n')
            sys.exit()
        read_neighbors = set(sum([x.get_neighbors() for x in reads], []))
        if len(read_neighbors) == 0:
            sys.stderr.write('Specified reads do not have neighbors\n')
            sys.exit()
        adj_edges = sum([read.list_of_edges for read in reads],[]) # adjacent edges of those reads
        edge_ids += list(set([x.edge_id for x in adj_edges])) # unique edge ids for these edges
        d = 1
        finished_read_ids = read_ids
        new_neighbors = []
        while d < depth:
            new_neighbors = []
            new_edge_ids = []
            for r_id in read_neighbors: # for all the depth d neighbors
                if r_id not in finished_read_ids: # if it's not traversed already
                    r = self.reads[r_id]
                    new_neighbors += r.get_neighbors() # find its neighbors
                    new_edge_ids += [x.edge_id for x in r.list_of_edges]
                    finished_read_ids.append(r_id)
            d +=1 
            new_neighbors = set(new_neighbors) - set(finished_read_ids)
            new_edge_ids = set(new_edge_ids) - set(edge_ids)
            if len(new_neighbors) == 0 and not quiet:
                sys.stderr.write("no more new neighbors\n")
                break
            elif len(new_edge_ids) == 0 and not quiet:
                sys.stderr.write("no more new edges\n")
                break
            else:
                read_neighbors = new_neighbors
                edge_ids += list(new_edge_ids)
        read_ids = finished_read_ids + list(new_neighbors)
        if not quiet:
            sys.stderr.write("At depth %d, %d nodes and %d edges in total.\n" % (d, len(read_ids),len(edge_ids)))
        return read_ids, edge_ids

    def print_subgraph(self, read_ids, edge_ids, out=sys.stdout):
        ''' Given edge ids, print subgraph with these edges and corresponding nodes into a new gdl file '''
        out.write("graph: {\n")
        out.write(self.gdl_setting_str)
        read_ids.sort()
        for node in read_ids:
            out.write('node: { title:"%d" label:"%d" }\n' % (node, node))
        for edge_id in edge_ids:
            out.write(self.edges[edge_id].gdl_string)
        out.write("}")

    def get_subgraph_read(self, read_id, depth=10, out=sys.stdout):
        read_ids, edge_ids = self.subgraph_node(read_id, depth)
        self.print_subgraph(read_ids, edge_ids, out)

    def split_graph(self):
        ''' Split graph into connected subgraphs '''
        remaining_read_ids = self.reads.keys()
        subgraphs = []
        while len(remaining_read_ids) > 0:
            #sys.stderr.write('Remaining nodes in graph: %d\n' % len(remaining_read_ids))
            remaining_read_ids.sort()
            read_ids, edge_ids = self.subgraph_node(remaining_read_ids[0],len(remaining_read_ids),True)
            subgraphs.append((read_ids, edge_ids))
            remaining_read_ids = list(set(remaining_read_ids) - set(read_ids))
        sys.stderr.write("Graph has %d connected subgraphs.\n" % len(subgraphs))
        return subgraphs
