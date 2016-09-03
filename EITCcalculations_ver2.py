import pandas as pd
import numpy as np
import re
data_path = "C:/Users/SpiffyApple/Documents/USC/RaphaelBostic"

#################################################################
################### load tax data ###############################
#upload tax data
tx = pd.read_csv("/".join([data_path, "metro_TY13.csv"]))

#there is some weird formatting here:
tx['cbsa'] = tx.cbsa.apply(lambda x: re.sub("=|\"", "",x))

tx.iloc[:,3:] = tx.iloc[:,3:].replace(",", "",regex=True).astype(np.int64)

tx.set_index('cbsa', inplace=True)

#################################################################
################ Read & Process EITC data #######################
##parse the EITC data:
eitc = pd.ExcelFile("/".join([data_path, "EITC Calculator-2-14.xlsx"]))
sheets = eitc.sheet_names
eitc.close()

eitc_dict = pd.read_excel("/".join([data_path, "EITC Calculator-2-14.xlsx"]), sheetname =  sheets[9:17], skiprows = 14 )

eitc = pd.concat(eitc_dict)

#filter the data down a bit
eitc = eitc.iloc[:,[0,40]]
eitc.dropna(inplace=True)
eitc = eitc.loc[eitc[2014]>0,:]
eitc.reset_index(level=0, inplace=True)
eitc.reset_index(drop=True, inplace=True)
eitc['num_kids'] = eitc.level_0.str.extract("(\d)", expand=False)
eitc['married'] = eitc.level_0.str.contains("Married").astype(int)

#calculate fair share of income for housing
eitc['total_income'] = eitc['Nominal Earnings']+eitc[2014]
eitc['haus_share'] = eitc.total_income*.3

#remove "Nominal"
eitc.level_0.replace(", Nominal", "", regex=True, inplace=True)

##Map FMR data to EITC data (Variable)
#assigned bedrooms to child counts
repl_dict ={'Married, 0 Kid':'fmr1', 'Married, 1 Kid':'fmr2', 'Married, 2 Kids':'fmr2',
       'Married, 3 Kids':'fmr3', 'Single, 0 Kid':'fmr1', 'Single, 1 Kid':'fmr2',
       'Single, 2 Kids':'fmr2', 'Single, 3 Kids':'fmr3'}

eitc['r_type'] = eitc.level_0.replace(repl_dict)

haus_share = eitc[['level_0', 'haus_share', 'r_type', 'Nominal Earnings']]

#################################################################
################# Read & process fmr data  ######################
#read in fmr data
fmr = pd.read_excel("/".join([data_path, "FY2014_4050_RevFinal.xls"]))

#drop non Metro areas:
fmr = fmr[fmr.Metro_code.str.contains("METRO")]

#extract cbsa code:
fmr['cbsa'] = fmr.Metro_code.str.extract("O(\d{4,5})[MN]", expand=False)
cbsa_chng_map = {'14060':'14010', '29140':'29200', '31100':'31080', '42060':'4220', '44600':'48260'}
fmr.cbsa.replace(cbsa_chng_map, inplace=True)

#drop duplicates based on cbsa code:
#fmr = fmr.drop_duplicates(['cbsa','Areaname'])
fmr = fmr.drop_duplicates('cbsa')

fmr.reset_index(drop=True, inplace=True)

#clean up the area names:
fmr['Areaname'] = fmr.Areaname.apply(lambda x: re.sub(" MSA| HUD Metro FMR Area", "", x))

fmr.set_index("cbsa", inplace=True)

fmr_cols = fmr.columns[fmr.columns.str.contains("fmr\d")]

#reformat fmr to annual cost of rent
fmr[fmr_cols] = fmr[fmr_cols]*12

#subset to only matching cbsa codes between tax and fmr data
common_cbsa = fmr.index.intersection(tx.index)

fmr = fmr.loc[common_cbsa]
tx = tx.loc[common_cbsa]

print("The number of CBSAs matches?:", fmr.shape[0] == tx.shape[0])

###################################################################
####################### calculations ##############################
######################################
##I. Make a vector of income bin means
######################################
min_earn = 2500
mid_earn = 37500
step = 5000
income_vect = np.linspace(min_earn,mid_earn,((mid_earn-min_earn)/step+1))

add_vect = [45000,52000]
income_vect = np.concatenate([income_vect, add_vect])

groups = haus_share.groupby(by = 'level_0')

def calc_haus_eitc(group, income):
    details = group[group['Nominal Earnings'] == income]
    if details.shape[0] > 0:
        aid = fmr[details.r_type]-details.haus_share.iloc[0]
        aid[aid<0] = 0
    else:
        aid = pd.DataFrame(np.array([np.nan]*fmr.shape[0]))
        aid.index = fmr.index
        #aid.columns = [group.r_type.iloc[0]]
    aid.columns = ['aid']
    return(aid)
    
aid_incomes = {}
for income in income_vect:
    aid_per_income = groups.apply(calc_haus_eitc, income=income)
    aid_incomes[income] = aid_per_income.unstack(level=0)
    
one_family_aid = pd.concat(aid_incomes)

#################################################################
###################### process tax data #########################

#calculate proportions
prop_married = 1-50.2/100    #some Christian Science article (not sure if credible source)

eagi_cols = tx.columns[tx.columns.str.contains("EAGI")]

#it doesn't seem that the total eligible for eitc matches the distributional count of incomes
print("Prop accounted for in income distribution counts\n",(tx[eagi_cols].sum(axis=1)/tx.eitc13).quantile(np.linspace(0,1,5)))
 
#-> we must assume that the proportions hold across income distributions
eqc_cols = tx.columns[tx.columns.str.contains("EQC\d_")]

#half the 50-60 bin number
tx['EAGI50_13'] = tx['EAGI50_13']/2

#calculate proportions
chld_prop = tx[eqc_cols].div(tx.eitc13,axis=0)
m_chld_prop = chld_prop*prop_married
s_chld_prop = chld_prop - m_chld_prop

m_chld_prop.columns = m_chld_prop.columns + "_married"
s_chld_prop.columns = s_chld_prop.columns + "_single"

tx = pd.concat([tx, m_chld_prop,s_chld_prop],axis=1)

eqc_cols = tx.columns[tx.columns.str.contains('EQC\d_13_married|EQC\d_13_single', regex=True)]

#this is confusing, this is a 3D matrix with metros on y axis.
C_3D=np.einsum('ij,ik->jik',tx[eagi_cols],tx[eqc_cols])

#make into a pandas dataframe
C_2D=pd.Panel(np.rollaxis(C_3D,2)).to_frame()

C_2D.columns = one_family_aid.columns

C_2D.index = one_family_aid.index

##################################################################
############### aggregate aid and filers #########################
disaggregated =np.multiply(C_2D, one_family_aid)

total = disaggregated.sum(axis=1).sum()
