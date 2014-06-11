#!/usr/bin/python

# -*- coding: utf-8 -*-
"""
samStat

Created on Fri May 23 13:14:18 2014

@author: cjg
"""
import sys
import argparse
import pysam
import mapStat

def samStat_pysam(samFile, outputFile):
    ''' From resulted sam or bam file of mapping, find information of reference sequences and reads.
        For reference sequences: 
        1. coverage percentage
        2. coverage depth at each base pair
        3. error rate/number (ins, del, sub)
        4. number of reads mapped to it
        
        For reads:
        1. number of reported alignments that contains the query read
        2. for each such alignment, what's the reference name and the qregion of the read
        
        Input:
        1. samFile: sam (bam) file name
        2. outputFile: file for writing output
        3. fileformat: either sam or bam, should do auto detect..
    '''
    mysam = pysam.Samfile(samFile,'r')

    # total number of ref seqs
    nRef = mysam.nreferences
    sys.stdout.write(">> Number of reference sequences: {} \n".format(nRef))

    # lengths of reference sequences
    refLens = mysam.lengths

    # dictionary including information about all the reference sequences and the reads
    refSeq_dict = dict()
    readSeq_dict = dict()


    sys.stdout.write(">> go through each read \n")
    count = 0


    for read in mysam.fetch():
        count += 1

        rname = mysam.getrname(read.tid) # ref seq to which this read is mapped
        qname = read.qname # name of the query sequence (read)
        print qname, "\t", rname, "\t"
        print read.cigarstring
        
        
        # if this reference sequence is not in the dictionary, add it
        if not refSeq_dict.has_key(rname):
            refLen = refLens[read.tid] # length of the reference sequence
            refSeq_dict[rname] = {'refLen':refLen, 'nReads':0, 'nReadsBp':0, 'nMatchBp':0,'nInsBp':0, 'nDelBp':0, 'nSubBp':0, 'coverage':[0]*refLen}

        if not readSeq_dict.has_key(qname):
            readSeq_dict[qname] = {'nMapping':0, 'mapInfo':list()}

        ## check CIGAR string                
        cigarstring = read.cigarstring # CIGAR string for this aligned read
        cigarLens = mapStat.cigar(cigarstring)

        ## update the dictionary corresponding to the reference sequence
        refSeq_dict[rname]['nReads'] += 1 # update number of mapped reads
        readSeq_dict[qname]['nMapping'] += 1 # update number of mappings

        refSeq_dict[rname]['nReadsBp'] += cigarLens['seq_len'] # update number of bps mapped to this ref seq
        # update matching and substitution bps if possible
        if cigarLens['match_len'] is not None:
            refSeq_dict[rname]['nMatchBp'] += cigarLens['match_len']
        if cigarLens['sub_len'] is not None:
            refSeq_dict[rname]['nSubBp'] += cigarLens['sub_len']

        refSeq_dict[rname]['nInsBp'] += cigarLens['ins_len'] # update number of insertion bps
        refSeq_dict[rname]['nDelBp'] += cigarLens['del_len'] # update number of deletion bps
        for apos in read.positions:
            refSeq_dict[rname]['coverage'][apos] += 1

        readSeq_dict[qname]['mapInfo'].append((read.qstart,read.qend, read.pos, read.aend, rname))

        if count % 10000 == 0:
            sys.stdout.write('  scanned {} records\n'.format(count))
                
    mysam.close()

    ## get number of covered base pairs in the refrence sequences
#    sys.stdout.write(">> Get number of covered basepairs \n")
#    for key in refSeq_dict:
#        refSeq_dict[key]['nCovBp'] = len(refSeq_dict[key]['mappedPos'])

    sys.stdout.write(">> Write statistics in output file \n")
    myout1 = open(outputFile+".ref", 'w')
    myout1.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format('refName', 'refLen','nReads', 'nReadsBp', 'nMatchBp','nInsBp','nDelBp','nSubBp','nCovBp','maxCov','avgCov'))

    for key in refSeq_dict:
        d = refSeq_dict[key]
        myout1.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(key, d['refLen'],d['nReads'], d['nReadsBp'], d['nMatchBp'],d['nInsBp'],d['nDelBp'],d['nSubBp'],d['refLen'] - d['coverage'].count(0),max(d['coverage']),float(d['nReadsBp'])/float(d['refLen'])))

    myout1.close()

    myout2 = open(outputFile+".read", 'w')
    myout2.write("{}\t{}\t{}\n".format('readName', 'nMappings','Mappings'))
    for key in readSeq_dict:
        d = readSeq_dict[key]
        myout2.write("{}\t{}\t".format(key, d['nMapping']))
        for map in d['mapInfo']:
            myout2.write("({}, {} # {}, {} @ {})".format(map[0],map[1],map[2],map[3],map[4]))
        myout2.write("\n")

    myout2.close()

## =================================================================
## samStat function without using pysam, which is unstable sometimes
## =================================================================
def samStat(samFile, outputFile):
    ''' From resulted sam or bam file of mapping, find information of reference sequences and reads.
        For reference sequences: 
        1. coverage percentage
        2. coverage depth at each base pair
        3. error rate/number (ins, del, sub)
        4. number of reads mapped to it
        
        For reads:
        1. number of reported alignments that contains the query read
        2. for each such alignment, what's the reference name and the qregion of the read
        
        Input:
        1. samFile: sam (bam) file name
        2. outputFile: file for writing output
        3. fileformat: either sam or bam, should do auto detect..
    '''
    nReferences = 0 # number of reference sequences
    refLens = [] # list of reference length
    refNames = []# list of reference names
    count = 0 # number of aligned records in the sam file

    # dictionaries for the reference sequences and the read sequences
    refSeq_dict = dict()
    readSeq_dict = dict()

    sys.stdout.write(">> Scan sam file \n")
    # start scanning sam file
    with open(samFile,'r') as mysam:
        for line in mysam:
            if line[0] == '@': # header line
                if line[1:3] == 'SQ': # reference sequence dictionary
                    nReferences += 1
                    rname = line[(line.find('SN:') + len('SN:')) : line.find('\t',line.find('SN:'))] # referenece sequence name
                    rLen = line[(line.find('LN:') + len('LN:')) : line.find('\t',line.find('LN:'))] # reference sequence length
                    refLens.append(int(rLen))
                    refNames.append(rname)
            else: # non-header line
                line = line.strip()            
                count += 1
                read = mapStat.readAlign(line) # parse the alignment record

                if read['cigarstring']=='*':
                    continue
                rname = read['rname'] # ref seq to which this read is mapped
                qname = read['qname'] # name of the query sequence (read)
                #print qname, "\t", rname, "\t"
                #print read['cigarstring']
                
                
                # if this reference sequence is not in the dictionary, initiate it
                if not refSeq_dict.has_key(rname):
                    refLen = refLens[refNames.index(rname)] # length of the reference sequence
                    refSeq_dict[rname] = {'refLen':refLen, 'nReads':0, 'nReadsBp':0, 'nMatchBp':0,'nInsBp':0, 'nDelBp':0, 'nSubBp':0, 'nEdit':0,'coverage':[0]*refLen}

                if not readSeq_dict.has_key(qname):
                    readSeq_dict[qname] = {'nMapping':0, 'mapInfo':list()}

                #print qname, '\t', rname, '\t', refLen

                ## check CIGAR string                
                cigarstring = read['cigarstring'] # CIGAR string for this aligned read
                cigarLens = mapStat.cigar(cigarstring)

                ## update the dictionary corresponding to the reference sequence
                refSeq_dict[rname]['nReads'] += 1 # update number of mapped reads
                readSeq_dict[qname]['nMapping'] += 1 # update number of mappings

                refSeq_dict[rname]['nReadsBp'] += cigarLens['seq_len'] # update number of bps mapped to this ref seq
                # update matching and substitution bps if possible
                if cigarLens['match_len'] is not None:
                    refSeq_dict[rname]['nMatchBp'] += cigarLens['match_len']
                if cigarLens['sub_len'] is not None:
                    refSeq_dict[rname]['nSubBp'] += cigarLens['sub_len']

                refSeq_dict[rname]['nInsBp'] += cigarLens['ins_len'] # update number of insertion bps
                refSeq_dict[rname]['nDelBp'] += cigarLens['del_len'] # update number of deletion bps

                # update edit distance
                if read['NM'] is not None:
                    refSeq_dict[rname]['nEdit'] += 1

                # update the coverage at the mapped positions
                for apos in read['positions']:
                    refSeq_dict[rname]['coverage'][apos-1] += 1

                # store the mapping information for this read:
                # start and end positions for both the query read and the ref seq
                # is this a secondary alignment?
                # is this a reverse complement?
                readSeq_dict[qname]['mapInfo'].append((read['qstart'],read['qend'], read['rstart'], read['rend'], read['is_secondary_alignment'], read['is_reversecomplement'],read['NM'],rname))

                if count % 10000 == 0:
                    sys.stdout.write('  scanned {} records\n'.format(count))
                
    ## get number of covered base pairs in the refrence sequences
#    sys.stdout.write(">> Get number of covered basepairs \n")
#    for key in refSeq_dict:
#        refSeq_dict[key]['nCovBp'] = len(refSeq_dict[key]['mappedPos'])

    sys.stdout.write(">> Write statistics in output file \n")

    # print out statistics information for the reference sequences
    myout1 = open(outputFile+".ref", 'w')
    myout1.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format('refName', 'refLen','nReads', 'nReadsBp', 'nMatchBp','nInsBp','nDelBp','nSubBp','nEdit','nCovBp','maxCov','avgCov','coverage'))

    for key in refSeq_dict:
        d = refSeq_dict[key]
        nCovBp = d['refLen'] - d['coverage'].count(0)
        myout1.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(key, d['refLen'],d['nReads'], d['nReadsBp'], d['nMatchBp'],d['nInsBp'],d['nDelBp'],d['nSubBp'],d['nEdit'],nCovBp,max(d['coverage']),float(d['nReadsBp'])/float(d['refLen']),float(nCovBp)/float(d['refLen'])))

    myout1.close()

    # print out statistics information for the reads
    myout2 = open(outputFile+".read", 'w')
    myout2.write("{}\t{}\t{}\n".format('readName', 'nMappings','Mappings'))
    for key in readSeq_dict:
        d = readSeq_dict[key]
        myout2.write("{}\t{}\t".format(key, d['nMapping']))
        for thismap in d['mapInfo']:
            # qstart, qend # rstart, rend # secondary # forward/backward @  edit distance, refName
            myout2.write("({}, {} # {}, {} # {} # {} @ {}, {})".format(thismap[0],thismap[1],thismap[2],thismap[3],-1 if thismap[4] else 1, -1 if thismap[5] else 1,thismap[6],thismap[7]))
        myout2.write("\n")

    myout2.close()
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="parse sam file and get summary statistics",
                                 prog = 'samStat', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input sam file",dest='samFile',required=True)

## output directory
parser.add_argument("-o","--out",help="output statistics file",dest='outputFile',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    samStat(args.samFile,args.outputFile)

##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
