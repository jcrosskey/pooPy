#!/bin/bash

# synchronize the RoI reads (single sequences) from viper to local directory
rsync -rav viper:/chongle/shared/database/03_PacBio/MockCommunity/PacBio/RoI/ $pbdata/PacBio/RoI/

# synchronize the bbmap alignments from Illumina reads to RoI reads (single sequences) from viper to local directory, only include *.sam, *.stat.read, *.stat.ref files
rsync -rav --include '*/' --include='a.sam' --include='bbmap.sam' --include='bbmap.stat.read' --include='bbmap.stat.ref' --exclude='*' viper:/chongle/shared/work/pacbio_test/02_test_mock_community/align_to_roi/Illu_reads_to_roi_each/ $pbwork/Illu_reads_to_roi_each/
