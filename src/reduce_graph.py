#!/home/cjg/bin/python

# -*- coding: utf-8 -*-
"""
reduce_graph.py

Created on Mon Jun  1 14:17:44 EDT 2015
@author: JJ Crosskey
"""
from graph_manip.Modules import *
import sys, os
import time
import argparse

## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="Extract subgraph from a big graph, starting from a specific node",
                                 prog = 'reduce_graph', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input graph file (in .gdl format)",dest='gdlFile',required=True)

## other input
parser.add_argument("-n","--node",help="starting node",dest='node',nargs='+', type = int)
parser.add_argument("-f","--nodefile",help="file including nodes",dest='nodefile', type = argparse.FileType('r'))

## output directory
parser.add_argument("-o","--out",help="output file",dest='outFile', default=sys.stdout, type=argparse.FileType('w'))

## options
parser.add_argument("-d", "--depth", help="depth of search in graph from node", dest='depth', required=False, default=10, type=int)
parser.add_argument("-v","--verbose",help="verbose, more output",action='store_true',dest='verbose')
## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    if args.verbose:
        sys.stderr.write("Input file is {}\n".format(args.gdlFile))
        sys.stderr.write("Output file is {}\n".format(args.outFile))
        if args.nodefile is not None:
            sys.stderr.write("Starting from node file: {} \n".format(args.nodefile))

    sys.stderr.write("\n===========================================================\n")
    start_time = time.time()

    if args.node is None:
        args.node = []
    if args.nodefile is not None:
        args.node += map(int, re.findall(r'\d+', args.nodefile.read()))
    if len(args.node) > 0:
        if args.verbose:
            sys.stderr.write("Starting from nodes: {} \n".format(",".join(map(str,args.node))))
        g = Graph(args.gdlFile)
        g.get_subgraph_read(args.node, args.depth, args.outFile)
    else:
        sys.stderr.write("There is no node specified, split graph into components instead.\n")
        g = Graph(args.gdlFile)
        g.split_graph(args.outFile)

    sys.stderr.write("total time :" + str(time.time() - start_time) +  " seconds")
    sys.stderr.write("\n===========================================================\nDone\n")
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
