import numpy as np
import bitstring
import math
import time
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import mplhep as hep
from sklearn import metrics
import os



colours=["red","black","blue","orange","purple","goldenrod",'green',"yellow","turquoise","magenta"]
linestyles = ["-","--","dotted",(0, (3, 5, 1, 5)),(0, (3, 5, 1, 5, 1, 5)),(0, (3, 10, 1, 10)),(0, (3, 10, 1, 10, 1, 10))]


def setmatplotlib():
        #hep.set_style("CMSTex")
    hep.cms.label()
    hep.cms.text("Simulation")
    plt.style.use(hep.style.CMS)

    SMALL_SIZE = 20
    MEDIUM_SIZE = 25
    BIGGER_SIZE = 30

    LEGEND_WIDTH = 20
    LINEWIDTH = 3
    MARKERSIZE = 20

    colormap = "jet"

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', titlesize=MEDIUM_SIZE)    # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('axes', linewidth=LINEWIDTH)              # thickness of axes
    plt.rc('xtick', labelsize=SMALL_SIZE+2)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE-2)            # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

    matplotlib.rcParams['xtick.major.size'] = 10
    matplotlib.rcParams['xtick.major.width'] = 3
    matplotlib.rcParams['xtick.minor.size'] = 10
    matplotlib.rcParams['xtick.minor.width'] = 3

    matplotlib.rcParams['ytick.major.size'] = 20
    matplotlib.rcParams['ytick.major.width'] = 3
    matplotlib.rcParams['ytick.minor.size'] = 10
    matplotlib.rcParams['ytick.minor.width'] = 2

def pttoR(pt):
    B = 3.8112 #Tesla for CMS magnetic field
    return abs((B*(3e8/1e11))/(2*pt))

def tanL(eta):
    return abs(np.sinh(eta))

def predhitpattern(dataframe):
    
        
    hitpat = dataframe["trk_hitpattern"].apply(bin).astype(str).to_numpy()
    eta = dataframe["trk_eta"].to_numpy()
    
    hit_array = np.zeros([7,len(hitpat)])
    expanded_hit_array = np.zeros([12,len(hitpat)])
    ltot = np.zeros(len(hitpat))
    dtot = np.zeros(len(hitpat))
    for i in range(len(hitpat)):
        for k in range(len(hitpat[i])-2):
            hit_array[k,i] = hitpat[i][-(k+1)]

    eta_bins = [0.0,0.2,0.41,0.62,0.9,1.26,1.68,2.08,2.5]
    conversion_table = np.array([[0, 1,  2,  3,  4,  5,  11],
                                 [0, 1,  2,  3,  4,  5,  11],
                                 [0, 1,  2,  3,  4,  5,  11],
                                 [0, 1,  2,  3,  4,  5,  11],
                                 [0, 1,  2,  3,  4,  5,  11],
                                 [0, 1,  2,  6,  7,  8,  9 ],
                                 [0, 1,  7,  8,  9, 10,  11],
                                 [0, 6,  7,  8,  9, 10,  11]])
   
    for i in range(len(hitpat)):
        for j in range(8):
            if ((abs(eta[i]) >= eta_bins[j]) & (abs(eta[i]) < eta_bins[j+1])):
                for k in range(7):
                    expanded_hit_array[conversion_table[j][k]][i] = hit_array[k][i]


        ltot[i] = sum(expanded_hit_array[0:6,i])
        dtot[i] = sum(expanded_hit_array[6:11,i])
    
    dataframe["pred_layer1"] = expanded_hit_array[0,:]
    dataframe["pred_layer2"] = expanded_hit_array[1,:]
    dataframe["pred_layer3"] = expanded_hit_array[2,:]
    dataframe["pred_layer4"] = expanded_hit_array[3,:]
    dataframe["pred_layer5"] = expanded_hit_array[4,:]
    dataframe["pred_layer6"] = expanded_hit_array[5,:]
    dataframe["pred_disk1"] = expanded_hit_array[6,:]
    dataframe["pred_disk2"] = expanded_hit_array[7,:]
    dataframe["pred_disk3"] = expanded_hit_array[8,:]
    dataframe["pred_disk4"] = expanded_hit_array[9,:]
    dataframe["pred_disk5"] = expanded_hit_array[10,:]
    dataframe["pred_ltot"] = ltot
    dataframe["pred_dtot"] = dtot
    dataframe["pred_nstub"] = ltot + dtot

    del [hit_array,hitpat,expanded_hit_array,ltot,dtot]

    return dataframe

def PVTracks(dataframe):
    return (dataframe[dataframe["trk_fake"]==1])

def pileupTracks(dataframe):
    return (dataframe[dataframe["trk_fake"]==2])

def fakeTracks(dataframe):
    return (dataframe[dataframe["trk_fake"]==0])

def genuineTracks(dataframe):
    return (dataframe[dataframe["trk_fake"] != 0])

def set_nlaymissinterior(hitpat):
    bin_hitpat = np.binary_repr(hitpat)
    bin_hitpat = bin_hitpat.strip('0')
    return bin_hitpat.count('0')

def nstub(hitpattern):
    bin_hitpat = hitpattern[2:]
    bin_hitpat = bin_hitpat.strip('0')
    return bin_hitpat.count('1')
   
def splitter(x,granularity,signed):
    import math

    mult = 1

    if signed: 
        mult = 2
      # Get the bin index
    t = (mult*x)/granularity

    return math.floor(t)

def bitsplitter(x,granularity,signed,nbits):

    mult = 1

    if signed: 
        mult = 1
      # Get the bin index

    t = (mult*x)/granularity
    try:
        tbin = bitstring.Bits(int=math.floor(t), length=nbits)
    except:
        tbin = bitstring.Bits(int=math.floor(0), length=nbits)


    return tbin

def bitdigitiser(x,bins,nbits):
    tbin = np.digitize(x,bins=bins) - 1
    tbit = bitstring.Bits(int=math.floor(tbin), length=nbits)
    return tbit

def bindigitiser(x,nbits):
    tbit = bitstring.Bits(int=math.floor(x), length=nbits)
    return tbit

def bitstringintwrapper(x):
    return x.int

def CalculateROC(sample_y_true,sample_y_predict, weights, n_CV_splits=10,n_ROC_thresholds=100):

    chunk_size = int(len(sample_y_true)/ n_CV_splits)
    fprs = np.zeros([ n_CV_splits,n_ROC_thresholds])
    tprs = np.zeros([ n_CV_splits,n_ROC_thresholds])
    roc_aucs = np.zeros([ n_CV_splits])
    thresholds = np.linspace(0,1,n_ROC_thresholds)
    for split in range( n_CV_splits):
        for it,threshold in enumerate(thresholds):
            y_predict_1s = (sample_y_predict[chunk_size*split:chunk_size*(split+1)] > threshold).astype(int)
            tn, fp, fn, tp = metrics.confusion_matrix(sample_y_true[chunk_size*split:chunk_size*(split+1)], y_predict_1s).ravel()

            fprs[split][it] = fp/(fp+tn)
            tprs[split][it] = tp/(tp+fn)

        roc_aucs[split] = (metrics.roc_auc_score(sample_y_true[chunk_size*split:chunk_size*(split+1)], sample_y_predict[chunk_size*split:chunk_size*(split+1)], sample_weight=weights[chunk_size*split:chunk_size*(split+1)]))

    roc_dict = {"fpr_mean":np.mean(fprs,axis=0),
                "fpr_err":np.std(fprs,axis=0),
                "tpr_mean":np.mean(tprs,axis=0),
                "tpr_err":np.std(tprs,axis=0),
                "thresholds": thresholds,
                "thresholds_err": np.ones_like(thresholds)*(1/len(thresholds)),
                "roc_auc_mean": np.mean(roc_aucs),
                "roc_auc_err": np.std(roc_aucs),
                "score_mean":np.mean(sample_y_predict),
                "score_err": 1/np.sqrt(len(sample_y_predict))  }
    return roc_dict
    
def calculate_ROC_bins(Dataset,y_predict,variable="",var_range=[-1,1],n_bins=5):
    var_bins = np.linspace(var_range[0],var_range[1],n_bins)
    rate_dict = {i:{"roc":{},"var":0,"var_gap":0} for i in range(n_bins-1)}
    for ibin in range(n_bins-1):
            
        indices = (Dataset.X_test.index[ ((Dataset.X_test[variable] >= var_bins[ibin]) & (Dataset.X_test[variable] < var_bins[ibin+1]))  ].tolist())
        rate_dict[ibin]["roc"] = CalculateROC(Dataset.y_test.iloc[indices],y_predict[indices],Dataset.X_test["weight"][indices])
        rate_dict[ibin][variable] = var_bins[ibin]
        rate_dict[ibin][variable+"_gap"] = abs(var_bins[ibin] - var_bins[ibin+1])

    return rate_dict

def plot_ROC_bins(rate_dicts,labels,save_dir,variable="",var_range=[-1,1],n_bins=5,typesetvar="",what="ROC",threshold=0.0):
    # Rate dicts = list of rate_dict for each model
    # Rate_dict is n_bins long with roc, variable variable_gap for each bin
    # roc is fpr_mean,tpr_mean,fpr_err,tpr_err,thresholds,thresholds_err,roc_auc_mean,roc_auc_err
    # fpr mean is n_thresholds long
    n_thresholds = len(rate_dicts[0][0]["roc"]["thresholds"])
    match what:
        case "ROC":
            indices = ["roc_auc_mean","roc_auc_err"]
            ylabel = "ROC Score"
            ylim = [0.8,1.0]
            name = "_ROC_scan"
            threshold_int = 0

        case "FPR":
            indices = ["fpr_mean","fpr_err"]
            ylabel = "False Positive Rate"
            ylim = [0.0,1.0]
            name = "_FPR_scan"
            threshold_int = int(threshold*n_thresholds)

        case "TPR":
            indices = ["tpr_mean","tpr_err"]
            ylabel = "True Positive Rate"
            ylim = [0.0,1.0]
            name = "_TPR_scan"
            threshold_int = int(threshold*n_thresholds)

        case "score":
            indices = ["score_mean","score_err"]
            ylabel = "BDT Output"
            ylim = [0.0,1.0]
            name = "_Score_scan"
            threshold_int = int(threshold*n_thresholds)

    fig, ax = plt.subplots(1,1, figsize=(10,10)) 
    hep.cms.label(llabel="Phase-2 Simulation Preliminary",rlabel="14 TeV, 200 PU",ax=ax)

    for i in range(len(rate_dicts)):
        var = [ rate_dicts[i][j][variable] for j in range(n_bins-1)]
        var_gaps = [ rate_dicts[i][j][variable+"_gap" ]/2 for j in range(n_bins-1)]
        if (indices[0] == 'roc_auc_mean') or (indices[0] == 'score_mean'):
            rocs = [ rate_dicts[i][j]["roc" ][indices[0]] for j in range(n_bins-1)]
            roc_errs = [ rate_dicts[i][j]["roc" ][indices[1]] for j in range(n_bins-1)]
            label = labels[i].split("=")[0]
        else:
            rocs = [ rate_dicts[i][j]["roc" ][indices[0]][threshold_int] for j in range(n_bins-1)]
            roc_errs = [ rate_dicts[i][j]["roc" ][indices[1]][threshold_int] for j in range(n_bins-1)]
            label = labels[i]
            
        ax.errorbar([var[i]+var_gaps[i] for i in range(len(var))],rocs,roc_errs,var_gaps, color=colours[i],label=label,markersize=6, fmt='o', mfc='white')

    ax.set_xlim([var_range[0],var_range[1]])
    ax.set_ylim(ylim)
    ax.set_xlabel(typesetvar,ha="right",x=1)
    ax.set_ylabel(ylabel,ha="right",y=1)
    ax.legend()
    ax.grid()
    os.system("mkdir " + save_dir)
    plt.savefig(save_dir+"/"+variable+name+".png",dpi=600)
    plt.clf()

def plot_ROC(roc_dicts,labels,save_dir):

    fig, ax = plt.subplots(1,1, figsize=(10,10)) 
    hep.cms.label(llabel="Phase-2 Simulation Preliminary",rlabel="14 TeV, 200 PU",ax=ax)

    # fpr_mean,tpr_mean,fpr_err,tpr_err,thresholds,thresholds_err,roc_auc_mean,roc_auc_err
    for i,roc_dict in enumerate(roc_dicts):
        if (roc_dict["tpr_mean"][0] == roc_dict["tpr_mean"][1]): 
            ax.errorbar(roc_dict["fpr_mean"][0],roc_dict["fpr_err"][0],roc_dict["tpr_mean"][0],roc_dict["tpr_err"][0], color=colours[i],label=labels[i],markersize=6, fmt='o', mfc='white')
        else:
            ax.plot(roc_dict["fpr_mean"], roc_dict["tpr_mean"],label=labels[i]+ " AUC: %.3f $\\pm$ %.3f"%(roc_dict["roc_auc_mean"],roc_dict["roc_auc_err"]),linewidth=2,color=colours[i])
            ax.fill_between(roc_dict["fpr_mean"],  roc_dict["tpr_mean"] , roc_dict["tpr_mean"] - roc_dict["tpr_err"],alpha=0.5,color=colours[0])
            ax.fill_between(roc_dict["fpr_mean"],  roc_dict["tpr_mean"],  roc_dict["tpr_mean"] + roc_dict["tpr_err"],alpha=0.5,color=colours[0])

    ax.set_xlim([0.0,0.4])
    ax.set_ylim([0.8,1.0])
    ax.set_xlabel("False Positive Rate",ha="right",x=1)
    ax.set_ylabel("Identification Efficiency",ha="right",y=1)
    ax.legend()
    ax.grid()
    os.system("mkdir " + save_dir)

    plt.savefig(save_dir+"/ROC.png",dpi=600)
    plt.savefig(save_dir+"/ROC.pdf")
    plt.clf()
 
def SynthBDTmodel(model,backend,cfg,directory,precision,test_events=10000,build=False):
        from scipy.special import expit
        import conifer

        if cfg is not None:
            cfg['Precision'] = precision
                # Set the output directory to something unique
            cfg['OutputDir'] = directory
            cfg["XilinxPart"] = 'xcvu13p-flga2577-2-e'
            cfg["ClockPeriod"] = 2.78
        match backend:
            case 'xgboost':
                converted_model = conifer.converters.convert_from_xgboost(model.model, cfg)
            case 'tfdf':
                converted_model = conifer.converters.convert_from_tf_df(model.inspector, cfg)
        if cfg is not None:
            converted_model.compile()
            # Run HLS C Simulation and get the output
        synth_y_predict_proba = 0
        if test_events > 0:
            temp_decision = converted_model.decision_function(model.DataSet.X_test[model.training_features][0:test_events].to_numpy())
            synth_y_predict_proba = expit(temp_decision)
        
        report = None

        if build:
            converted_model.build()
            converted_model.write()
            report = converted_model.read_report()

        return (synth_y_predict_proba,report)

def plot_model(model,save_dir):
    
    importances = model.model.get_booster().get_score(importance_type='gain').values()

    plt.close()
    plt.clf()
    fig,ax = plt.subplots(1,1,figsize=(13,10))
    hep.cms.label(llabel="Phase-2 Simulation Preliminary",rlabel="14 TeV, 200 PU",ax=ax)

    #ax.hist(track_data_frame['trk_matchtp_pdgid'],histtype="step",
    #                    linewidth=LINEWIDTH,
    #                    color = 'k',
    #                    density=True)
    labels = "$|\\tan(\\lambda)|$","|$z_0$|","$\\chi^2_{bend}$","# Stubs","# Missing \n Internal Stubs","$\\chi^2_{r\\phi}$","$\\chi^2_{rz}$"
    plt.bar(labels,[i/sum(importances) for i in importances], linewidth=4,edgecolor='r',color='white',width=0.5)

    for tick in ax.xaxis.get_minor_ticks():
        tick.tick1line.set_markersize(0)
        tick.tick2line.set_markersize(0)
    #for tick in ax.xaxis.get_major_ticks():
    #    tick.label1.set_horizontalalignment('center')

    dx = 1/72; dy = 0/72. 
    offset = matplotlib.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)

    # apply offset transform to all x ticklabels.
    for label in ax.xaxis.get_majorticklabels():
        label.set_transform(label.get_transform() + offset)
    #ax.xaxis.get_major_ticks()[0].label1.set_visible(False) ## set last x tick label invisible


    plt.xticks(rotation='vertical')
    ax.grid(True)
    ax.set_xlabel("Feature",ha="right",x=1)
    ax.set_ylabel("Relative Feature Importance",ha="right",y=1)
    #ax.set_yscale("log")
    ax.xaxis.labelpad = -75

    plt.tight_layout()
    plt.savefig(save_dir+"/feat_importance.png")

def ONNX_convert_model(model,directory,test_events=10000):
        import onnxmltools
        from onnxmltools.convert.common.data_types import FloatTensorType
        import onnxruntime as rt

        num_features = len(model.DataSet.config_dict["trainingFeatures"])
        X = model.DataSet.X_test[model.training_features][0:test_events]
        
        # The name of the input is needed in Clasifier_cff as GBDTIdONNXInputName
        initial_type = [('feature_input', FloatTensorType([1, num_features]))]

        match model.backend:
            case 'xgboost':
                onx = onnxmltools.convert.convert_xgboost(model.model, initial_types=initial_type)

            case 'tfdf':
                onx = onnxmltools.convert.convert_xgboost(model.model, initial_types=initial_type)

        # Save the model
        with open(directory+".onnx", "wb") as f:
          f.write(onx.SerializeToString())

        # This tests the model

        # setup runtime - load the persisted ONNX model
        sess = rt.InferenceSession(directory+".onnx")

        # get model metadata to enable mapping of new input to the runtime model.
        input_name = sess.get_inputs()[0].name
        # This label will access the class probabilities when run in CMSSW, use index 0 for class prediction
        label_name = sess.get_outputs()[1].name


        #print(sess.get_inputs()[0].name)
        # The name of the output is needed in Clasifier_cff as GBDTIdONNXOutputName
        #print(label_name)
        pred_onx = []
        # predict on random input and compare to previous XGBoost model
        for i in range(len(X)):
          pred_onx.append(sess.run([], {input_name: X[i:i+1].to_numpy(dtype=np.float32)})[1][0][1])
        return pred_onx

def synth_model(model,sim : bool = True,hdl : bool = True,hls : bool = True, cpp : bool = True,onnx : bool = True,python : bool = False,
                test_events : int = 10000, precisions : list = None, plot : bool = True, save_dir : str = ''):
        import shutil
        from sklearn import metrics
        from pathlib import Path
        import os
        import conifer


        model.csim_predictions = {}
        model.hdl_predictions = {}
        model.hls_predictions = {}
        model.onnx_predictions = 0
        model.cpp_predictions = {}
        model.py_predictions = 0
    
        hdlreport = {x:[] for x in precisions}
        hlsreport = {x:[] for x in precisions}

        if test_events > 0:
            xgb_roc_auc = metrics.roc_auc_score(model.DataSet.y_test[0:test_events],model.y_predict_proba[0:test_events], sample_weight = model.DataSet.X_test["weight"][0:test_events])
            xgb_roc_dict = CalculateROC(model.DataSet.y_test[0:test_events],model.y_predict_proba[0:test_events], model.DataSet.X_test["weight"][0:test_events])
            print("xgb ROC: ",xgb_roc_auc)


        if Path(save_dir+"/FW").is_dir():
            shutil.rmtree(save_dir+"/FW")
        os.system("mkdir " + save_dir + "/FW")

        if hdl or hls:
            with open(save_dir+"/FW/gamma_fixed_scan.txt", 'w') as f:
                    print('Type,','Precision,','Gamma,','xgb_roc_auc,','synth_roc_auc,','LUT %,','FF %,','Latency',file=f)

        for precision in precisions:
            start_time = time.time()

            fig, ax = plt.subplots(1,1, figsize=(10,10)) 
            hep.cms.label(llabel="Phase-2 Simulation Preliminary",rlabel="14 TeV, 200 PU",ax=ax)

            print("===========================")
            print(" Precision: ",precision)
            directory_name=precision.replace('ap_fixed<', '')
            directory_name=directory_name.replace('>', '')
            directory_name=directory_name.replace(',', '')

            if sim and (test_events > 0):
                if Path(save_dir+"/FW/sim"+directory_name).is_dir():
                    shutil.rmtree(save_dir+"/FW/sim"+directory_name)
                simcfg = conifer.backends.xilinxhls.auto_config()
                model.csim_predictions[precision] = SynthBDTmodel(model,'xgboost',simcfg,save_dir+"/FW/sim"+directory_name,precision,test_events=test_events)[0]
                sim_roc_auc = metrics.roc_auc_score(model.DataSet.y_test[0:test_events],model.csim_predictions[precision], sample_weight=model.DataSet.X_test["weight"][0:test_events])
                print("sim ROC: ",sim_roc_auc, " Ratio: ",sim_roc_auc/xgb_roc_auc)

                sim_roc_dict = CalculateROC(model.DataSet.y_test[0:test_events],model.csim_predictions[precision], model.DataSet.X_test["weight"][0:test_events])
                ax.plot(sim_roc_dict['fpr_mean'], sim_roc_dict['tpr_mean'],label="C-Sim " + precision + " AUC: %.3f $\\pm$ %.3f"%(sim_roc_dict['roc_auc_mean'],sim_roc_dict['roc_auc_err']),linewidth=2,color=colours[5])
                
                ax.fill_between(sim_roc_dict['fpr_mean'], sim_roc_dict['tpr_mean'], sim_roc_dict['tpr_mean'] + sim_roc_dict['tpr_err'],alpha=0.5,color=colours[5])
                ax.fill_between(sim_roc_dict['fpr_mean'], sim_roc_dict['tpr_mean'], sim_roc_dict['tpr_mean'] - sim_roc_dict['tpr_err'],alpha=0.5,color=colours[5])

            if hdl:
                if Path(save_dir+"/FW/hdl"+directory_name).is_dir():
                    shutil.rmtree(save_dir+"/FW/hdl"+directory_name)
                hdlcfg = conifer.backends.vhdl.auto_config()
                model.hdl_predictions[precision],hdlreport[precision] = SynthBDTmodel(model,'xgboost',hdlcfg,save_dir+"/FW/hdl"+directory_name,precision,build=True,test_events=test_events)
                
                if test_events > 0:
                    hdl_roc_auc = metrics.roc_auc_score(model.DataSet.y_test[0:test_events],model.hdl_predictions[precision], sample_weight = model.DataSet.X_test["weight"][0:test_events])
                    print("hdl ROC: ",hdl_roc_auc, " Ratio: ",hdl_roc_auc/xgb_roc_auc)
                    hdlreport[precision]['roc'] = hdl_roc_auc/xgb_roc_auc
                    with open(save_dir+"/FW/gamma_fixed_scan.txt", 'a') as f:
                        print('hdl: ',precision,model.model.gamma,xgb_roc_auc,hdl_roc_auc,hdlreport[precision]["lut"]/7881.60,hdlreport[precision]["ff"]/15763.20,hdlreport[precision]['latency'],file=f)

                    hdl_roc_dict = CalculateROC(model.DataSet.y_test[0:test_events],model.hdl_predictions[precision], model.DataSet.X_test["weight"][0:test_events])
                    ax.plot(hdl_roc_dict['fpr_mean'], hdl_roc_dict['tpr_mean'],label="HDL " + precision + " AUC: %.3f $\\pm$ %.3f"%(hdl_roc_dict['roc_auc_mean'],hdl_roc_dict['roc_auc_err']),linewidth=2,color=colours[1])
                    ax.fill_between(hdl_roc_dict['fpr_mean'], hdl_roc_dict['tpr_mean'], hdl_roc_dict['tpr_mean'] + hdl_roc_dict['tpr_err'],alpha=0.5,color=colours[1])
                    ax.fill_between(hdl_roc_dict['fpr_mean'], hdl_roc_dict['tpr_mean'], hdl_roc_dict['tpr_mean'] - hdl_roc_dict['tpr_err'],alpha=0.5,color=colours[1])

            if hls:
                if Path(save_dir+"/FW/hls"+directory_name).is_dir():
                    shutil.rmtree(save_dir+"/FW/hls"+directory_name)
                hlscfg = conifer.backends.xilinxhls.auto_config()
                print(hlsreport)
                model.hls_predictions[precision],hlsreport[precision] = SynthBDTmodel(model,'xgboost',hlscfg,save_dir+"/FW/hls"+directory_name,precision,build=True,test_events=test_events)
                print(hlsreport)
                if test_events > 0:
                    hls_roc_auc = metrics.roc_auc_score(model.DataSet.y_test[0:test_events],model.hls_predictions[precision], sample_weight = model.DataSet.X_test["weight"][0:test_events])
                    print("hls ROC: ",hls_roc_auc, " Ratio: ",hls_roc_auc/xgb_roc_auc)
                    hlsreport[precision]['roc'] = hls_roc_auc/xgb_roc_auc

                    with open(save_dir+"/FW/gamma_fixed_scan.txt", 'a') as f:
                        print('hls: ',precision,model.model.gamma,xgb_roc_auc,hls_roc_auc,hlsreport[precision]["lut"]/7881.60,hlsreport[precision]["ff"]/15763.20,hlsreport[precision]['latency'],file=f)

                    hls_roc_dict = CalculateROC(model.DataSet.y_test[0:test_events],model.hls_predictions[precision], model.DataSet.X_test["weight"][0:test_events])
                    ax.plot(hls_roc_dict['fpr_mean'], hls_roc_dict['tpr_mean'],label="HLS " + precision + " AUC: %.3f $\\pm$ %.3f"%(hls_roc_dict['roc_auc_mean'],hls_roc_dict['roc_auc_err']),linewidth=2,color=colours[2])
                    ax.fill_between(hls_roc_dict['fpr_mean'], hls_roc_dict['tpr_mean'], hls_roc_dict['tpr_mean'] + hls_roc_dict['tpr_err'],alpha=0.5,color=colours[2])
                    ax.fill_between(hls_roc_dict['fpr_mean'], hls_roc_dict['tpr_mean'], hls_roc_dict['tpr_mean'] - hls_roc_dict['tpr_err'],alpha=0.5,color=colours[2])

            if cpp and (test_events > 0):
                if Path(save_dir+"/FW/cpp"+directory_name).is_dir():
                    shutil.rmtree(save_dir+"/FW/cpp"+directory_name)
                cppcfg = conifer.backends.cpp.auto_config()
                model.cpp_predictions[precision],_ = SynthBDTmodel(model,'xgboost',cppcfg,save_dir+"/FW/cpp"+directory_name,precision,build=False,test_events=test_events)
                cpp_roc_auc = metrics.roc_auc_score(model.DataSet.y_test[0:test_events],model.cpp_predictions[precision], sample_weight = model.DataSet.X_test["weight"][0:test_events])
                print("cpp ROC: ",cpp_roc_auc, " Ratio: ",cpp_roc_auc/xgb_roc_auc)

                cpp_roc_dict = CalculateROC(model.DataSet.y_test[0:test_events],model.cpp_predictions[precision], model.DataSet.X_test["weight"][0:test_events])
                ax.plot(cpp_roc_dict['fpr_mean'], cpp_roc_dict['tpr_mean'],label="cpp " + precision + " AUC: %.3f $\\pm$ %.3f"%(cpp_roc_dict['roc_auc_mean'],cpp_roc_dict['roc_auc_err']),linewidth=2,color=colours[3])
                ax.fill_between(cpp_roc_dict['fpr_mean'], cpp_roc_dict['tpr_mean'], cpp_roc_dict['tpr_mean'] + cpp_roc_dict['tpr_err'],alpha=0.5,color=colours[3])
                ax.fill_between(cpp_roc_dict['fpr_mean'], cpp_roc_dict['tpr_mean'], cpp_roc_dict['tpr_mean'] - cpp_roc_dict['tpr_err'],alpha=0.5,color=colours[3])

            end_time = time.time()
            print("Synthesis Complete in: ",end_time-start_time, " seconds")

        if python and (test_events > 0):
            if Path(save_dir+"/FW/cpp"+directory_name).is_dir():
                shutil.rmtree(save_dir+"/FW/cpp"+directory_name)
            pycfg = None
            model.py_predictions,_ = SynthBDTmodel(model,'xgboost',pycfg,save_dir+"/FW/py"+directory_name,precision,build=False,test_events=test_events)
            py_roc_auc = metrics.roc_auc_score(model.DataSet.y_test[0:test_events],model.py_predictions, sample_weight = model.DataSet.X_test["weight"][0:test_events])
            print("python ROC: ",py_roc_auc, " Ratio: ",py_roc_auc/xgb_roc_auc)

            py_roc_dict = CalculateROC(model.DataSet.y_test[0:test_events],model.py_predictions, model.DataSet.X_test["weight"][0:test_events])
            ax.plot(py_roc_dict['fpr_mean'], py_roc_dict['tpr_mean'],label="python AUC: %.3f $\\pm$ %.3f"%(py_roc_dict['roc_auc_mean'],py_roc_dict['roc_auc_err']),linewidth=2,color=colours[4])
            ax.fill_between(py_roc_dict['fpr_mean'], py_roc_dict['tpr_mean'], py_roc_dict['tpr_mean'] + py_roc_dict['tpr_err'],alpha=0.5,color=colours[4])
            ax.fill_between(py_roc_dict['fpr_mean'], py_roc_dict['tpr_mean'], py_roc_dict['tpr_mean'] - py_roc_dict['tpr_err'],alpha=0.5,color=colours[4])

        if onnx and test_events > 0:
            if Path(save_dir+"FW/onnxdir").is_dir():
                shutil.rmtree(save_dir+"FW/onnxdir")
            else:
                os.system("mkdir -p " + save_dir+"/FW/onnxdir")
            model.onnx_predictions = ONNX_convert_model(model,save_dir+'/FW/onnxdir/xgboost',test_events=test_events)
            onnx_roc_auc = metrics.roc_auc_score(model.DataSet.y_test[0:test_events],model.onnx_predictions, sample_weight = model.DataSet.X_test["weight"][0:test_events])
            onnx_roc_dict = CalculateROC(model.DataSet.y_test[0:test_events],model.onnx_predictions, model.DataSet.X_test["weight"][0:test_events])
            print("onnx ROC: ",onnx_roc_auc, " Ratio: ",onnx_roc_auc/xgb_roc_auc)

            ax.plot(onnx_roc_dict['fpr_mean'], onnx_roc_dict['tpr_mean'],label="ONNX AUC: %.3f $\\pm$ %.3f"%(onnx_roc_dict['roc_auc_mean'],onnx_roc_dict['roc_auc_err']),linewidth=2,color=colours[4])
            ax.fill_between(onnx_roc_dict['fpr_mean'],  onnx_roc_dict['tpr_mean'], onnx_roc_dict['tpr_mean'] - onnx_roc_dict['tpr_err'],alpha=0.5,color=colours[4])
            ax.fill_between(onnx_roc_dict['fpr_mean'],  onnx_roc_dict['tpr_mean'], onnx_roc_dict['tpr_mean'] + onnx_roc_dict['tpr_err'],alpha=0.5,color=colours[4])

        if test_events > 0:
            ax.plot(xgb_roc_dict['fpr_mean'], xgb_roc_dict['tpr_mean'],label="xgb AUC: %.3f $\\pm$ %.3f"%(xgb_roc_dict['roc_auc_mean'],xgb_roc_dict['roc_auc_err']),linewidth=2,color=colours[0])
            ax.fill_between(xgb_roc_dict['fpr_mean'],  xgb_roc_dict['tpr_mean'] , xgb_roc_dict['tpr_mean'] - xgb_roc_dict['tpr_err'],alpha=0.5,color=colours[0])
            ax.fill_between(xgb_roc_dict['fpr_mean'],  xgb_roc_dict['tpr_mean'],  xgb_roc_dict['tpr_mean'] + xgb_roc_dict['tpr_err'],alpha=0.5,color=colours[0])

            ax.set_xlim([0.0,1.0])
            ax.set_ylim([0.0,1.0])
            ax.set_xlabel("False Positive Rate",ha="right",x=1)
            ax.set_ylabel("Identification Efficiency",ha="right",y=1)
            ax.legend()
            ax.grid()
            plt.savefig(save_dir+"/FW/ROC"+directory_name+".png",dpi=600)
            plt.clf()

        if plot:
            if sim and (test_events > 0):
                fig, ax = plt.subplots(1,1, figsize=(10,10)) 
                hep.cms.label(llabel="Phase-2 Simulation Preliminary",rlabel="14 TeV, 200 PU",ax=ax)
                ax.plot(xgb_roc_dict['fpr_mean'], xgb_roc_dict['tpr_mean'],label="xgb AUC: %.3f $\\pm$ %.3f"%(xgb_roc_dict['roc_auc_mean'],xgb_roc_dict['roc_auc_err']),linewidth=2,color=colours[0])
                ax.fill_between(xgb_roc_dict['fpr_mean'],  xgb_roc_dict['tpr_mean'] , xgb_roc_dict['tpr_mean'] - xgb_roc_dict['tpr_err'],alpha=0.5,color=colours[0])
                ax.fill_between(xgb_roc_dict['fpr_mean'],  xgb_roc_dict['tpr_mean'],  xgb_roc_dict['tpr_mean'] + xgb_roc_dict['tpr_err'],alpha=0.5,color=colours[0])
                for i,precision in enumerate(precisions):                         
                    sim_roc_dict = CalculateROC(model.DataSet.y_test[0:test_events],model.csim_predictions[precision], model.DataSet.X_test["weight"][0:test_events])
                    ax.plot(sim_roc_dict['fpr_mean'], sim_roc_dict['tpr_mean'],label="sim " + precision + " AUC: %.3f $\\pm$ %.3f"%(sim_roc_dict['roc_auc_mean'],sim_roc_dict['roc_auc_err']),linewidth=2,color=colours[i+1])
                    ax.fill_between(sim_roc_dict['fpr_mean'], sim_roc_dict['tpr_mean'], sim_roc_dict['tpr_mean'] + sim_roc_dict['tpr_err'],alpha=0.5,color=colours[i+1])
                    ax.fill_between(sim_roc_dict['fpr_mean'], sim_roc_dict['tpr_mean'], sim_roc_dict['tpr_mean'] - sim_roc_dict['tpr_err'],alpha=0.5,color=colours[i+1])

                ax.set_xlim([0.0,1.0])
                ax.set_ylim([0.0,1.0])
                ax.set_xlabel("False Positive Rate",ha="right",x=1)
                ax.set_ylabel("Identification Efficiency",ha="right",y=1)
                ax.legend()
                ax.grid()
                plt.savefig(save_dir+"/FW/ROC_scan.png",dpi=600)
                plt.clf()

            if hdl or hls:
                fig, ax = plt.subplots(2,2, figsize=(20,20),sharex = True) 

                for precision in precisions:
                    if hdl:
                        ax[0,0].bar(precision,hdlreport[precision]["lut"]/7881.60, linewidth=4,edgecolor='r',color='None',width=0.5)
                        ax[0,1].bar(precision,hdlreport[precision]["ff"]/15763.20, linewidth=4,edgecolor='r',color='None',width=0.5,label="HDL")
                        ax[1,0].bar(precision,hdlreport[precision]["latency"], linewidth=4,edgecolor='r',color='None',width=0.5)
                    if hls:
                        ax[0,0].bar(precision,hlsreport[precision]["lut"]/7881.60, linewidth=4,edgecolor='b',color='None',width=0.5)
                        ax[0,1].bar(precision,hlsreport[precision]["ff"]/15763.20, linewidth=4,edgecolor='b',color='None',width=0.5,label="HLS")
                        ax[1,0].bar(precision,hlsreport[precision]["latency"], linewidth=4,edgecolor='b',color='None',width=0.5)

                    if test_events > 0:
                        if hdl:
                            ax[1,1].bar(precision,hdlreport[precision]["roc"], linewidth=4,edgecolor='r',color='None',width=0.5)
                        if hls:
                            ax[1,1].bar(precision,hlsreport[precision]["roc"], linewidth=4,edgecolor='b',color='None',width=0.5)

                for a in ax[0,:]:
                    hep.cms.label(llabel="Phase-2 Simulation Preliminary",rlabel="14 TeV, 200 PU",ax=a)
                    for tick in a.xaxis.get_minor_ticks():
                            tick.tick1line.set_markersize(0)
                            tick.tick2line.set_markersize(0)
                for a in ax[1,:]:
                    for tick in a.xaxis.get_minor_ticks():
                        tick.tick1line.set_markersize(0)
                        tick.tick2line.set_markersize(0)
                    #for tick in ax.xaxis.get_major_ticks():
                    #    tick.label1.set_horizontalalignment('center')

                    dx = 1/72; dy = 0/72. 
                    offset = matplotlib.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)

                    # apply offset transform to all x ticklabels.
                    for label in a.xaxis.get_majorticklabels():
                        label.set_transform(label.get_transform() + offset)
                    #ax.xaxis.get_major_ticks()[0].label1.set_visible(False) ## set last x tick label invisible
                    a.tick_params(axis='x', labelrotation=90)
                    a.grid(True)
                    a.xaxis.labelpad = -75

                ax[1,1].set_xlabel("Precision",ha="right",x=-0.01,fontsize=30)
                ax[0,1].legend(bbox_to_anchor=(1.04, 1), loc="upper left",fontsize=30)
                ax[0,0].set_ylabel("% LUTs",ha="right",y=1)
                ax[0,1].set_ylabel("% FFs",ha="right",y=1)
                ax[1,0].set_ylabel("Latency (clock cycles)",ha="right",y=1)
                ax[1,1].set_ylabel("ROC AUC Ratio to XGBoost",ha="right",y=1)

                #ax.set_yscale("log")
                plt.tight_layout()
                plt.savefig(save_dir+"/FW/resources.png")
