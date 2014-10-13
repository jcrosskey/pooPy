#!/usr/bin/python

import argparse
import sys
import os
import re 
## =================================================================
## Given a fasta file of filtered subreads, find the number of passes
## for each ZMW.
## This is not exact, half pass will be counted as 1.
## =================================================================
def count_passes(fastaFile,countFile):
    ''' Given a fasta file of filtered subreads, find the number of passes
        for each ZMW

        Input:  fastaFile - file that includes filtered subreads
        Output: countFile - file that contains the number of passes for each ZMW
    '''
    if not os.path.exists(fastaFile):
        sys.stderr.write("fastaFile {} does not exist!\n".format(fastaFile))
        return -1
        
    fasta = open(fastaFile,'r') 
    passes = dict()
    lengths = dict()
    with open(fastaFile,'r') as fasta:
        for line in fasta:
            if line[0] == '>':
                seqID = line[1:line.rfind('/')]
                length = int(line[(line.rfind('_')+1):line.rfind('\n')]) - int(line[(line.rfind('/')+1):line.rfind('_')])
                if passes.has_key(seqID):
                    passes[seqID] += 1
                    lengths[seqID].append(length)
                else:
                    passes[seqID] = 1
                    lengths[seqID] = [length]
    mycount = open(countFile,'w')
    for seqID in passes:
        mycount.write("{}\t{}\t{}\t{}\n".format(seqID, passes[seqID],min(lengths[seqID]), max(lengths[seqID])))
    mycount.close()
                    
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="count number of passes for each ZMW from subreads fasta file",
                                 prog = 'count_passes', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input fasta file",dest='fastaFile',required=True)

## output directory
parser.add_argument("-o","--out",help="output file",dest='countFile',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    count_passes(args.fastaFile, args.countFile)
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
