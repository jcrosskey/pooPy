#!/usr/bin/python

import argparse
import sys
import os
import re 

def getReadFromFasta(fin):
    output = ""
    for line in fin:
        if line.strip("\n").strip() != "":
            if line[0] != ">":
                output += line
            else:
                if output != "":
                    yield output
                output = line
    yield output
## =================================================================
## Given a fasta file, find the sequence for the specific region of 
## a sequence with given ID. 
## Return -1 if the sequence does not exist or its sequence does not
## include the specified region.
## =================================================================
def get_contig(fastaFile, seqID, start, end, limit):
    ''' Given a fasta file, find the sequence for the specific region of 
        a sequence with given ID. 
        Return -1 if the sequence does not exist or its sequence does not
        include the specified region.
        
        Input:  fastaFile - file that includes all the sequences
                seqID - ID of the sequence of interest
                start - 1-based starting position
                end - 1-based ending position
        Output: sequence string if found, -1 if not found
    '''
    if not os.path.exists(fastaFile):
        sys.stderr.write("fastaFile {} does not exist!\n".format(fastaFile))
        return -1
    if end != -1 and start > end:
        sys.stderr.write("Please check input for starting and ending positiosn.\n")
        return -1
        
    fasta = open(fastaFile,'r') 
    line = fasta.readline()
    count = 0
    nextline = ''
    while line != "" and (limit==-1 or count < limit):
        if line[0] == '>':
            thisID = line.strip().split()[0][1:] # sequence ID until the first space
            if seqID in thisID :
                #print thisID
                count += 1
                seq = ""
                sys.stdout.write('>{}\n'.format(thisID))
                nextline = fasta.readline().strip("\n")
                while nextline!='' and nextline[0] != '>' and (end==-1 or len(seq)<=end):
                    seq += nextline
                    nextline = fasta.readline().strip("\n")
                if start <= end and end <= len(seq):
                    sys.stdout.write('{}\n'.format(seq[(start - 1):end]))
                elif end == -1:
                    sys.stdout.write('{}\n'.format(seq[(start - 1):]))
                else:
                    sys.stderr.write("end position passed end of the sequence!\n")
                    sys.stdout.write('{}\n'.format(seq[(start - 1):]))
                    return -1
        if nextline != '' and nextline[0] == '>':
            line = nextline # look into  header line that was read just now
            nextline = ''
        else:
            line = fasta.readline()
    if seq == "":
        sys.stderr.write("sequence {} was not found in file {}!\n".format(seqID, fastaFile))
        return -1
    fasta.close()
                    
def get_IDs(id_file):
    seqIDs = []
    with open(id_file, 'r') as ids:
        for line in ids:
            seqIDs.append(line.strip("\n").split()[0])
    seqIDs = map(int,list(set(seqIDs)))
    seqIDs.sort()
    seqIDs = map(str, seqIDs)
    sys.stderr.write("Number of IDs to extract: {}\n".format(len(seqIDs)) )
    return seqIDs

def get_contigs(fastaFile, seqIDs):
    index = 0
    with open(fastaFile, 'r') as fin:
        for readLines in getReadFromFasta(fin):
            seq_id = readLines.split()[0][1:] # sequence name
            if seq_id == seqIDs[index]:
                sys.stdout.write(readLines)
                index += 1
                if index == len(seqIDs):
                    break
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="fetch sequence from fasta file given an ID and the starting, ending positions",
                                 prog = 'get_contig', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input fasta file",dest='fastaFile',required=True)
parser.add_argument("-f","--id_file",help="file with reads/contigs ids to extract",dest='id_file')
parser.add_argument("-n","--name",help="ID of the sequence to find",dest='seqID')
parser.add_argument("-s","--start",help="1-based starting position of the sequence",dest='start',default=1, type=int)
parser.add_argument("-e","--end",help="1-based ending position of the sequence",dest='end',default=-1, type=int)
parser.add_argument("-l","--limit",help="maximum number of sequences to return",dest='limit',default=-1, type=int)

## output directory
#parser.add_argument("-o","--out",help="output directory",dest='outputDir',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()
    if args.seqID is None and args.id_file is None:
        sys.exit("At least a sequence ID or a file of IDs is needed.\n")
    if args.seqID is not None:
        get_contig(args.fastaFile,args.seqID,args.start,args.end, args.limit)
    elif args.id_file is not None:
        seqIDs = get_IDs(args.id_file)
        get_contigs(args.fastaFile, seqIDs)
        

##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
