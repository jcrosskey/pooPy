#!/bin/bash

##================= parse command line arguments ===============##
NO_ARGS=0
E_OPTERROR=85
usage() { echo "Usage: `basename $0` [-f -h -l <read_len> -s <insert_len>] -i <input_file> -o <output_dir>" >&2;}

if [ $# -eq "$NO_ARGS" ] 
then
	usage
	exit $E_OPTERROR
fi

format=fastq
read_len=150
insert_len=400
prefix=""
out_dir=""

while getopts ":i:o:fhl:s:p:" opt 
do
	case $opt in
		h)
			usage
			exit 0
			;;
		f)
			format=fasta
			echo "input is in fasta format instead of fastq format" >&2
			;;
		l)
			read_len=$OPTARG
			echo "read length is specified as $OPTARG" >&2
			;;
		s)
			insert_len=$OPTARG
			echo "insert size is specified as $OPTARG" >&2
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
#==================================
# trimming
#==================================
do_trim(){
cat > ${out_dir}/trim.sh <<TrimmingScriptWriting
#!/bin/bash

#PBS -N trim_${prefix}
#PBS -q medium
#PBS -l nodes=1:ppn=1
#PBS -l walltime=24:00:00
#PBS -d $out_dir
#PBS -j oe
#PBS -o trim.out
sickle pe -c ${input} -t sanger -m ${prefix}_pe.fastq -s ${prefix}_se.fastq -l 60 -q 20 -n
qsub ec.sh
TrimmingScriptWriting
chmod u+x ${out_dir}/trim.sh
}
#==================================
# error correction
#==================================
do_ec(){
cat > ${out_dir}/ec.sh <<ErrorCorrectionScriptWriting
#!/bin/bash

#PBS -N ec_${prefix}
#PBS -q medium
#PBS -l nodes=1:ppn=48
#PBS -l walltime=24:00:00
#PBS -d ${out_dir}
#PBS -j oe
#PBS -o ec.out

bash /home/cjg/Software/BBTools/ecc.sh threads=48 ecclimit=7 ecr=140 eclt=3 echt=16  in=${prefix}_pe.fastq extra=${prefix}_se.fastq out=${prefix}_pe_trimmed_corrected.fastq > ${prefix}_pe_trimmed_correct.log
bash /home/cjg/Software/BBTools/ecc.sh threads=48 ecclimit=7 ecr=140 eclt=3 echt=16  in=${prefix}_se.fastq extra=${prefix}_pe.fastq out=${prefix}_se_trimmed_corrected.fastq  > ${prefix}_se_trimmed_correct.log 
qsub merge.sh
ErrorCorrectionScriptWriting
chmod u+x ${out_dir}/ec.sh
}
#==================================
# merge
#==================================
do_merge(){
cat > ${out_dir}/merge.sh <<MergePariedEndReadsScriptWriting
#!/bin/bash

#PBS -N merge_${prefix}
#PBS -q medium
#PBS -l nodes=1:ppn=16
#PBS -l walltime=24:00:00
#PBS -d ${out_dir}
#PBS -j oe
#PBS -o merge.out

# -m min-overlap (default 10)
# -M max-overlap  = 2.5 * fragment-len-stddev + overlap
# -r read-len
# -f fragment-len
# -s fragment-len-stddev
flash -r ${read_len} -f ${insert_len} -o ${prefix}_flash_merge -d \$PWD --interleaved-output -t 16 --interleaved-input ${prefix}_pe_trimmed_corrected.fastq

#qsub dup_con.sh
MergePariedEndReadsScriptWriting
chmod u+x ${out_dir}/merge.sh
}
merged_fastq=${prefix}_flash_merge.extendedFrags.fastq

#==================================
# remove duplicated and contained reads
#==================================
do_dedup(){
cat > ${out_dir}/dup_con.sh <<DeduplicationScriptWriting
#!/bin/bash

#PBS -N dup_con_${prefix}
#PBS -q medium
#PBS -l nodes=1:ppn=40
#PBS -l walltime=24:00:00
#PBS -d ${out_dir}
#PBS -j oe
#PBS -o dup_con.out

# split input file if it's bigger than 10G bases
if [[ \$(find $PWD -name ${dedup_input%.*}.fasta -size +10G 2>/dev/null) || \$(find $PWD -name ${dedup_input%.*}.fastq -size +20G 2>/dev/null) ]]; then
	python \$pyjj/splitReads.py -i ${dedup_input} -o ${prefix} -c 10000000000 -bp
	/chongle/qiuming/align_test/Release/align_test -i RemoveContainedReads --subject ${prefix}\${PBS_ARRAYID}.${format} --query ${dedup_input} -ht omega -l 40 -t 40 --out ${prefix}\${PBS_ARRAYID}_unique.${format}
else
	/chongle/qiuming/align_test/Release/align_test -i RemoveContainedReads --subject ${dedup_input} --query ${dedup_input} -ht omega -l 40 -t 40 --out ${prefix}_unique.${format}
fi
DeduplicationScriptWriting
chmod u+x ${out_dir}/dup_con.sh
}
#qsub trim.sh

if [[ $format == "fastq" ]]
then
	do_trim
	do_ec
	do_merge
	dedup_input=$merged_fastq
else
	dedup_input=$input
fi
do_dedup
exit #?
