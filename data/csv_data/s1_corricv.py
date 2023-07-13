import pandas as pd
import numpy as np
import sys

## Read data
d_in = './Dset1.csv'
d_out = './Dset1Corr.csv'

#d_in = './Dset2.csv'
#d_out = './Dset2Corr.csv'

#d_in = './Dset3.csv'
#d_out = './Dset3Corr.csv'

#listROI = ['MUSE_ICV', 'MUSE_TBR', 'MUSE_GM', 'MUSE_WM', 'MUSE_VN', 'MUSE_HIPPOL', 'MUSE_HIPPOR']
#out_csv = d_out + '/ISTAGING_Centiles_SelROIS.csv'

listROI  = ['MUSE_ICV', 'MUSE_nTBR', 'MUSE_nGM', 'MUSE_nWM', 'MUSE_nVN', 'MUSE_nHIPPOL', 'MUSE_nHIPPOR']
out_csv = d_out + '/ISTAGING_Centiles_SelROIS_Norm.csv'

df = pd.read_csv(d_in)

dfa = df[['ID', 'MUSE_ICV', 'Age_At_Visit', 'IsF']]
dfb = df[['MUSE_TBR', 'MUSE_GM', 'MUSE_WM', 'MUSE_VN', 'MUSE_HIPPOL', 'MUSE_HIPPOR']]
dfb = dfb.div(dfa['MUSE_ICV'], axis = 0) * 1400000
dfb.columns = ['MUSE_nTBR', 'MUSE_nGM', 'MUSE_nWM', 'MUSE_nVN', 'MUSE_nHIPPOL', 'MUSE_nHIPPOR']

df_out = pd.concat([df, dfb], axis = 1)

## Write out files
df_out.to_csv(d_out, index = False)


