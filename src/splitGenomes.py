#!/usr/bin/python

import argparse
import sys
import os
import re 
## =================================================================
## Find length of all sequences in a fasta file
## =================================================================
def splitGenomes(fasta,outDir):
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    myout = open(".tmp",'w')
    for line in fasta:
        line = line.strip("\n")
        if len(line) > 0 and line[0] == '>':
            myout.close()
            seqID = line[1:]
            sys.stdout.write(seqID+"\n")
            myout = open(outDir+'/'+seqID,'w')
            myout.write(">{}\n".format(seqID))
        else:
            myout.write(line+"\n")
    myout.close()
    os.remove(".tmp")
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="Put each genome sequence in a separate file",
                                 prog = 'splitGenomes', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input fasta file",dest='fastaFile',default=sys.stdin, type=argparse.FileType('r'))

## output directory
parser.add_argument("-o","--out",help="output directory",dest='outDir',default="./")

## =================================================================
## main function
## =================================================================
def main(argv=None):
    if argv is None:
        args = parser.parse_args()

    splitGenomes(args.fastaFile, args.outDir)
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
