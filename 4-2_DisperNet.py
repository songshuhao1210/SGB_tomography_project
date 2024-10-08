import numpy as np
import h5py
import os 
import sys
import shutil
import yaml
sys.path.append('../tools_F-J/toollib_DisperNet_local/')
sys.path.append('../tools_F-J/')
from toollib_standard import plotlib
import dispernet_local_latest as dispernet
import pandas as pd


#%%
flag_project = 1 # 0--regular ; 1--repartition
#%%
if flag_project == 0:
    file_project = 'a-project.yml'
    with open('a-project.yml', 'r', encoding='utf-8') as f:
        proj = yaml.load(f.read(), Loader=yaml.FullLoader)
    name_project = proj['name']
    #name_project = 'project/output_FJSJ_16-01/'               # Harmon server
elif flag_project == 1:
    file_project = 'a-project_repar.yml'
    with open('a-project_repar.yml', 'r', encoding='utf-8') as f:
        proj = yaml.load(f.read(), Loader=yaml.FullLoader)
    name_project = proj['name']
    #name_project = 'project_repartrition/output_repar_01-03/'               # Harmon server

#%%
with open('0_config.yml', 'r', encoding='utf-8') as f:
    dir_config = yaml.load(f.read(), Loader=yaml.FullLoader)
dir_project_workspace = dir_config['dir_project_workspace']
dir_CC_workspace = dir_config['dir_CC_workspace']
print('dir_CC_workspace: ', dir_CC_workspace)
print('dir_project_workspace: ', dir_project_workspace)
dir_project = os.path.join(dir_project_workspace, name_project)
print('dir_project: ', dir_project)

#%%
filename = dir_project+'Basic_info.yml'
with open(filename, 'r', encoding='utf-8') as f:
    info_basic = yaml.load(f.read(), Loader=yaml.FullLoader)
filename_bi = dir_project+'Basic_info.npy'
info_basic_bi = np.load(filename_bi, allow_pickle='TRUE').item()      # setting dictionary

#%%
stainfo = pd.read_excel(info_basic['stalistname_all'])
nsta_all = len(stainfo.iloc[:,0])
stalist_all = stainfo['Station'].tolist()
lat_all = stainfo['latitude'].tolist() 
lon_all = stainfo['longitude'].tolist()

faults = np.load('clark_faults.npy', allow_pickle='TRUE').item()

#%%
dir_ds = dir_project + info_basic['dir_ds']
key_ds = info_basic['key_subworks']
#key_ds = ['13--20-03','22--29-03','28--35-03','41--49-03']
#key_ds  = info_basic['key_subworks_repick']
    
"""

key_ds = []
for key in info_basic['key_subworks']:
    num = int(key[3:])
    if num == 14:
        key_ds.append(key)
"""
"""
key_ds = []
for key in info_basic['key_subworks']:
    num = int(key[:2])
    if num >= 32 and num <= 42:
        key_ds.append(key)
"""

#%% 
info_basic['dir_inv_dispernet'] = 'inv_dispernet/'
dir_inv = dir_project + info_basic['dir_inv_dispernet']
if not os.path.exists(dir_inv):
    os.makedirs(dir_inv)
with open(dir_project+'Basic_info.yml', 'w', encoding='utf-8') as f:
   yaml.dump(data=info_basic, stream=f, allow_unicode=True)

#%%
#r_max = info_basic_bi['r_max']
r_max = {}
for key in key_ds:
    r_max[key] = 10

#%%

fmax = 30
fmin = 0.5
flag_repick = 1
inputfile = dir_inv + 'h5/'
outputfile = dir_inv + 'data/'
f = info_basic_bi['f']
c = np.linspace(info_basic['c_min'],info_basic['c_max'],info_basic['c_num'])
if flag_repick == 1:
    
    if os.path.exists(inputfile):
        os.system('rm -rf '+inputfile)
    os.makedirs(inputfile)
    if not os.path.exists(outputfile):
        os.makedirs(outputfile)
    for key in key_ds:
        data = h5py.File(dir_ds+'/ds_'+str(key)+'.h5', 'r')
        #f = data['f'][:]    
        #c = data['c'][:]
        #amp = data['ds_remove'][:][0][:,f<fmax]
        #amp_or = data['ds_linear'][:][0][:,f<fmax]
        amp = data['ds_remove'][:][0][:,np.logical_and(f>fmin,f<fmax)]
        amp_or = data['ds_linear'][:][0][:,np.logical_and(f>fmin,f<fmax)]
        amp = plotlib.smooth_ds(amp)
        amp_or = plotlib.smooth_ds(amp_or)
        outname = inputfile+'ds_'+str(key) +'.h5'
        data.close()
        dispernet.save2h5(amp, f[np.logical_and(f>fmin,f<fmax)], c,fileName=outname,spectrum_or = amp_or)

#%%
#old_curve_path = 'oldData/disp_data_15-01/'
old_curve_path = 'oldData/disp_data_repar_01-02/'
#old_curve_path = ''
key_olds = []
if os.path.exists(old_curve_path):
    print('exits old curve')
    # read all files in the folder
    files = os.listdir(old_curve_path)
    for file in files:
        if file.find('.xlsx') == -1:
            key_olds.append(file[file.find('_')+1:file.find('curve')])

#%%
fund_curve_path = dir_project + info_basic['dir_inv_dispernet']+'disp_model_fund/'
key_fund = []
if os.path.exists(fund_curve_path):
    print('exits fund curve')
    # read all files in the folder
    files = os.listdir(fund_curve_path)
    for file in files:
        
        key_fund.append(file[file.find('_')+1:file.find('curve')])

#%%
over_curve_path = dir_project + info_basic['dir_inv_dispernet']+'disp_model/'
#将config_inv.yml从San_Jansinto复制到inv_dispernet
outname_config = dir_inv+'config_inv.yml'
outname_config_fund = dir_inv+'config_inv_fund.yml'
if os.path.exists(outname_config)==False:
    shutil.copyfile('config_inv.yml', dir_inv+'config_inv.yml')
if os.path.exists(outname_config_fund)==False:
    shutil.copyfile('config_inv_fund.yml', dir_inv+'config_inv_fund.yml')

#%%    
fileList = os.listdir(inputfile)
num_fileList = [int(file[file.find('_')+1:file.find('--')]) for file in fileList]
index = np.argsort(num_fileList)
fileList = np.array(fileList)[index].tolist()

#%%
# Run Dispernet
#dispernet.App(filePath=inputfile, curveFilePath=outputfile,freqSeries=f, trigerMode=False, searchStep=2, cmap='jet', periodCutRate=0.12, semiAutoRange=0.1, autoT=True, url='http://10.20.64.63:8514')
print('fmax = '+str(fmax))
v_min = 0.01
flag_partrition = 1
flag_plot_or = 0
#dispernet.App(r_flag = r_max,vmin = v_min,oldfile=old_curve_path,oldkeys= key_olds,fundfile = fund_curve_path,overfile = over_curve_path,fundkeys = key_fund,filePath=inputfile, curveFilePath=outputfile,freqSeries=f[f<fmax], trigerMode=False, searchStep=2, cmap='jet', periodCutRate=0.8, semiAutoRange=0.1, autoT=True, url='http://10.20.64.63:8514')
dispernet.App(info_basic,lon_all,lat_all,fileList,faults = faults,file_project = file_project,flag_plot_or=flag_plot_or,flag_plot_partrition=flag_partrition,vmin = v_min,oldfile=old_curve_path,oldkeys= key_olds,fundfile = fund_curve_path,overfile = over_curve_path,fundkeys = key_fund,filePath=inputfile, curveFilePath=outputfile,freqSeries=f[f<fmax], trigerMode=False, searchStep=2, cmap='jet', periodCutRate=0.2, semiAutoRange=0.1, autoT=True, url='http://10.20.64.63:8514')

# transfer training
#dispernet.createTrainSet('./trainSetDAS.h5', inputfile, outputfile)