#!/usr/bin/python

''' Rename sequence names in fasta file so that paired end reads have different names
    with different suffixes: /1, or /2.
'''
import re
import argparse
import sys
## =================================================================
## Rename sequence names in fasta file so that paired end reads have different names
## with different suffixes: /1, or /2.
## =================================================================
def RenameFasta(fastaFile, outputFile):
    '''
    '''
    g = open(outputFile,'w')

    with open(fastaFile, 'r') as f:
        for line in f:
            if line[0]=='>':
                line = line.strip('\n')
                line = line.split()
                line = line[0] + '/' + line[1][0] + '\n'
                g.write(line)
            else:
                g.write(line)

    g.close()


## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="Rename sequence names in fasta file so that paired end reads have different names",
                                 prog = 'RenameFasta', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input fasta file",dest='fastaFile',required=True)

## output directory
parser.add_argument("-o","--out",help="output statistics file",dest='outputFile',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    RenameFasta(args.fastaFile,args.outputFile)

##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
