#!/bin/bash

##================= parse command line arguments ===============##
NO_ARGS=0
E_OPTERROR=85
usage() { echo "Usage: `basename $0` [-p prefix] -i <input_file> -o <output_dir>" >&2;}

if [ $# -eq "$NO_ARGS" ] 
then
	usage
	exit $E_OPTERROR
fi

prefix=""
out_dir=""

while getopts ":i:o:ph" opt 
do
	case $opt in
		h)
			usage
			exit 0
			;;
		p)
			prefix=$OPTARG
			echo "prefix for the output files is $OPTARG" >&2
			;;
		i)
			input=$OPTARG
			echo "input file is $OPTARG" >&2
			;;
		o)
			out_dir=$OPTARG
			echo "output directory is $OPTARG" >&2
			;;
		:)
			echo "Option -$OPTARG requires an argument" >&2
			exit 1
			;;
		\?)
			echo "Invalid option: -$OPTARG" >&2
			exit 1
			;;
	esac
done

# check if input file exists
if [ ! -e $input ]
then
	echo "Input file $input does not exist, quit."
	exit 1
fi

if [[ $input != /* ]]
then
	input=$PWD/${input}
fi

# get prefix for all output file names
if [ -z $prefix ] 
then
	prefix=`basename $input`
	prefix=${prefix%%\.*}
fi

# get the output directory name
if [ -z $out_dir ]
then
	out_dir=$PWD/$prefix
fi

# create output directory if it does not exit already
if [ ! -d $out_dir ]
then
	mkdir -p $out_dir
fi

echo Input file is $input
echo Output directory is $out_dir
echo Output file prefix is $prefix

BBmap=/global/homes/p/pcl/Software/bbmap
adapters=/global/homes/p/pcl/Software/bbmap/resources/adapters.fa
phiX_adapters=/global/homes/p/pcl/Software/bbmap/resources/phix174_ill.ref.fa.gz
outp=${out_dir}/${prefix}

#==================================
# trimming
#==================================
do_trim(){
cat > ${out_dir}/trim_merge.sh <<TrimmingScriptWriting
#!/bin/bash

#$ -N trim_merge_${prefix}
#$ -cwd
#$ -M jjchai01@gmail.com
#$ -m abe
#$ -j y
#$ -l h_rt=12:00:00
#$ -l ram.c=120G
#$ -l exclusive.c

echo Starting Time is \$(date)
echo Starting Trimming and Filtering \$(date)

${BBmap}/bbduk.sh in=$input out=${outp}_trim.fq.gz interleaved=t ftm=5 k=23 ktrim=r mink=11 hdist=1 tbo tpe qtrim=r trimq=10 minlen=70 ref=$adapters 1>${outp}_trim.o 2>&1
${BBmap}/bbduk.sh in=${outp}_trim.fq.gz out=${outp}_filter.fq.gz ref=$phiX_adapters hdist=1 k=31 threads=16 1>${outp}_filter.o 2>&1


echo Merge Before Error Correction \$(date)
${BBmap}/bbmerge.sh in=${outp}_filter.fq.gz out=${outp}_noEC_merged.fq.gz outu=${outp}_noEC_unmerged.fq.gz \\
	extend2=20 iterations=10 &> ${outp}_noEC_bbmerge.o

qsub ${out_dir}/ec.sh

echo Ending Time is \$(date)
TrimmingScriptWriting
chmod u+x ${out_dir}/trim_merge.sh
}
#==================================
# error correction
#==================================
do_ec(){
cat > ${out_dir}/ec.sh <<ErrorCorrectionScriptWriting
#!/bin/bash

#$ -N ec_${prefix}
#$ -cwd
#$ -M jjchai01@gmail.com
#$ -m abe
#$ -j y
#$ -l h_rt=12:00:00
#$ -l ram.c=120G
#$ -l exclusive.c


${BBmap}/tadpole.sh in=${outp}_noEC_merged.fq.gz,${outp}_noEC_unmerged.fq.gz \\
	oute=${outp}_merged_EC.fq.gz,${outp}_unmerged_EC.fq.gz \\
	mode=correct markbadbases=2 ecc=t shave rinse threads=16 -Xmx115g &> ${outp}_merge_ec.o

${BBmap}/reformat.sh in=${outp}_merged_EC.fq.gz out=${outp}_merged_EC_reformat.fq.gz maxns=0 \\
	1>> ${outp}_merge_ec.o 2>&1

${BBmap}/reformat.sh in=${outp}_unmerged_EC.fq.gz out=${outp}_unmerged_EC_reformat.fq.gz maxns=0 \\
	1>> ${outp}_merge_ec.o 2>&1

qsub ${out_dir}/split.sh
ErrorCorrectionScriptWriting
chmod u+x ${out_dir}/ec.sh
}

#==================================
# Split big data set , prepare for duplicate removal
#==================================
do_split(){
cat > ${out_dir}/split.sh <<SplitReadsScriptWriting
#!/bin/bash

#$ -N split_${prefix}
#$ -cwd
#$ -M jjchai01@gmail.com
#$ -m abe
#$ -j y
#$ -l h_rt=12:00:00

gunzip ${outp}_merged_EC_reformat.fq.gz
if [[ find ${out_dir} -maxdepth 1 -type f -size -name "*_merged_EC_reformat.fq" +20G ]]
then
	python2.7 /global/homes/p/pcl/Software/poopy/src/splitReads.py -i ${outp}_merged_EC_reformat.fq \\
	-o ${outp}_merged -c 10000000000 -bp
else
	ln -s ${outp}_merged_EC_reformat.fq ${outp}_merged1.fastq
fi

gunzip ${outp}_unmerged_EC_reformat.fq.gz
if [[ find ${out_dir} -maxdepth 1 -type f -size -name "*_unmerged_EC_reformat.fq" +20G ]]
then
	python2.7 /global/homes/p/pcl/Software/poopy/src/splitReads.py -i ${outp}_unmerged_EC_reformat.fq \\
	-o ${outp}_unmerged -c 10000000000 -bp
else
	ln -s ${outp}_unmerged_EC_reformat.fq ${outp}_unmerged1.fastq
fi

fastqs=(${outp}*merged[1-9]*.fastq)
qsub -t 1-\$(echo \${#fastqs[@]}) ${out_dir}/dedup.sh

SplitReadsScriptWriting
chmod u+x ${out_dir}/split.sh
}

#==================================
# remove duplicated and contained reads
#==================================
do_dedup(){
cat > ${out_dir}/dedup.sh <<DeduplicationScriptWriting
#!/bin/bash

#$ -N dedup_${prefix}
#$ -cwd
#$ -M jjchai01@gmail.com
#$ -m abe
#$ -j y -o ${outp}_dedup.o
#$ -l h_rt=12:00:00
#$ -l exclusive.c


fastqs=(${outp}*[1-9]*.fastq)
query=\$(echo \${fastqs[@]} | tr " " ",")
index=\$(( \$SGE_TASK_ID-1 ))
/global/homes/p/pcl/Software/align_test/Release/align_test -i RemoveContainedReads \\
	--subject \${fastqs[\$index]} --query \$query -ht single \\
	-l 40 -k 39 -m 0 -t 16 -z 32000 --out ${outp}_unique_\$SGE_TASK_ID.fasta

qsub ${out_dir}/split_fasta.sh
DeduplicationScriptWriting
chmod u+x ${out_dir}/dedup.sh
}

#==================================
# split unique fasta if necessary
#==================================
do_split_fasta(){
cat > ${out_dir}/split_fasta.sh <<SplitFastaScriptWriting
#!/bin/bash

#$ -N split_fasta${prefix}
#$ -cwd
#$ -M jjchai01@gmail.com
#$ -m abe
#$ -j y -o ${outp}_split_fasta.o
#$ -l h_rt=12:00:00
#$ -l exclusive.c

fastas=(${outp}_unique*.fasta)
awk -f /global/homes/p/pcl/Software/poopy/shell/rename_fasta.awk ${outp}_unique_*.fasta \\
	&> ${outp}_unique.fasta

if [[ find ${out_dir} -maxdepth 1 -type f -size -name "${prefix}_unique.fasta" +10G ]]
then
	python2.7 /global/homes/p/pcl/Software/poopy/src/splitReads.py -i ${outp}_unique.fasta \\
	-o ${outp}_unique -c 10000000000 -bp
else
	ln -s ${outp}_unique.fasta ${outp}_unique1.fasta
fi

fastas=(${outp}_unique[1-9]*.fasta)
qsub -t 1-\${#fastas[@]} ${out_dir}/align.sh
SplitFastaScriptWriting
chmod u+x ${out_dir}/split_fasta.sh
}

#==================================
# build graph and remove transitive edges
#==================================
do_align(){
cat > ${out_dir}/align.sh <<AlignScriptWriting
#!/bin/bash

#$ -N align_${prefix}
#$ -cwd
#$ -M jjchai01@gmail.com
#$ -m abe
#$ -j y -o ${outp}_align.o
#$ -l h_rt=12:00:00
#$ -l exclusive.c

fastas=(${outp}_unique[1-9]*.fasta)
index=\$(( \$SGE_TASK_ID-1 ))

/global/homes/p/pcl/Software/align_test/Release/align_test -i ConstructOverlapGraph -ht single \\
	--TransitiveReduction --query \${fastas[\$index]} --subject ${outp}_unique.fasta \\
	--out ${outp}\$SGE_TASK_ID.align \\
	-l 40 -k 39 -m 0 -t 64 -z 64000
AlignScriptWriting
chmod u+x ${out_dir}/align.sh
}

do_trim
do_ec
do_split
do_dedup
do_split_fasta
do_align
exit #?
