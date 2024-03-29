#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 10:51:41 2022

@author: iiit
"""

import numpy as np
#import os
import re
from subprocess import call
#import sys
#import numpy.matlib
import scipy.io
from scipy.signal import medfilt
import scikits.samplerate
import os
from os.path import exists
## Vocoder function definition #########################################################################################
from typical_FA_contextfeats import contextFeats
from myfunctions import spectral_selection,  temporal_corr#,temp_vec_corr
from myfunctions import spectral_corr,statFunctions_Syl,statFunctions_Vwl,smooth,get_labels,vocoder_func


transDir= "./"
dictDir= "./"
transFile = "ISLEtrans.txt"
dictName = "nativeEnglishDict_gt100_manoj.syl"
models = ['fisher-2000_FA_GT_ESTphnTrans_estStress']#'libri-960_FA_GT_ESTphnTrans_estStress','wsj_FA_GT_ESTphnTrans_estStress','fisher-2000_FA_GT_ESTphnTrans_estStress','fisher-30_FA_GT_ESTphnTrans_estStress']
#libri-30_FA_GT_ESTphnTrans_estStress
model_FA = ['FA_htkCorrectedLabWithFullAudio']
labels_mis_count=[]
for mod in range(0,len(models)):
    Features = []; phonecountError=1;   filenotExist=1; prevSuccessError=1; done=0;label_mismatch=0
    model = models[mod]
    filepath = '/home/iiit/Downloads/datasets/ISLEnew/'+model+'/lab/txt/phn/'
    files = os.listdir('/home/iiit/Desktop/Jhansi/Stress detection/Codes_jhansi/GER/train/') 
    wavPath = '/home/iiit/Desktop/Jhansi/Stress detection/Codes_jhansi/GER/train/'
    stressLabelspath = '/home/iiit/Downloads/datasets/ISLEnew/'+model_FA[0]+'/lab/mat/sylStress/'
    #VOWEL LIST
    vowelList= ['aa','ae','ah','ao','aw','ay','eh','er','ey','ih','iy','ow','oy','uh','uw']
    
    for fileN in range(0,len(files)): #len(files)
        
        is_looping = True
        wavFile =wavPath+files[fileN]#files[fileN]
        fileName = files[fileN]#files[fileN]
        phnFile = filepath+fileName[0:-4]+'.txt'
    
        if (exists(stressLabelspath+fileName[0:-4]+'.mat')):
            
            # loading of data
            call(["cat "+phnFile+" | tr \"\t\" \" \" > /tmp/tmp.txt; sudo cp /tmp/tmp.txt "+phnFile], shell = True)
            try:
    #    f = open('myfile.xlxs')
    #    f.close()
                fid = open(phnFile, 'r')
                dataArray = np.loadtxt(fid, dtype={'names':('a','b','c'),'formats':('f4','f4','S16')})
                fid.close
            except:
                print('File does not exist')
                filenotExist = filenotExist+1
                continue
            phnTimes1 = [row[0] for row in dataArray];phnTimes1 = np.array([phnTimes1]).T
            phnTimes2 = [row[1] for row in dataArray];phnTimes2 = np.array([phnTimes2]).T
            phnTimes = np.hstack((phnTimes1, phnTimes2))
            phones = [row[2] for row in dataArray];phones = np.array([phones])
            for kk in range (0,len(phones[0])):
                phones[0][kk] = phones[0][kk].lower()      # Made them lowercase since the syl dictionary is in lowercase
            origPhones = phones
            index = np.argwhere(origPhones[0]=='sil')
            phones = phones[phones!='sil']
            phones = np.array([phones])
        
            #Getting vowel data
            vowelStartTime = []; vowelEndTime = []; vowel = []
            for kk in range(0,len(dataArray)):
                if dataArray[kk][2].lower() in vowelList:
                    vowelStartTime.append(dataArray[kk][0]); vowelEndTime.append(dataArray[kk][1]); vowel.append(dataArray[kk][2].lower())
            vowelStartTime = np.array([vowelStartTime])
            vowelEndTime = np.array([vowelEndTime])
            vowel = np.array([vowel])
        
        
            #sylPhnTimes = phnTimes[index][0]
            phnTimes2 = np.delete(phnTimes2, index, axis=0)
            phnTimes = np.delete(phnTimes, index, axis=0)
            call(["cat "+transDir+transFile+" | grep \""+fileName[0:len(fileName)-4]+" \" | cut -d\" \" -f2- | sed \"s/ (/=/g\" | cut -d\"=\" -f1 | sed \"s/) /=/g\" | cut -d\"=\" -f2- | sed \"s/'/XXXXX/g\" | tr \"[:punct:]\" \" \" | tr -s \" \" | sed \"s/XXXXX/'/g\" | sed \"s/ '/ /g\" | tr \"[A-Z]\" \"[a-z]\" | tr -s \" \" | tr \" \" \"\\n\" > /tmp/tmp.txt"], shell = True)
            with open("/tmp/tmp.txt", 'r') as fid: words = [words.rstrip('\n') for words in fid]
            if '' in words:
                words.remove('')
            flag = 0
            word_syls = []
            for iterWord in range(0,len(words),1):
                call(["cat "+dictDir+dictName+" | sed -e \"s/^/+/g\" | grep \"+"+words[iterWord]+" \" | cut -d\"=\" -f2 > /tmp/tmp.txt"], shell = True)
                with open("/tmp/tmp.txt", 'r') as fid: tempArr = [tempArr.rstrip('\n') for tempArr in fid]
                word_syls.append(tempArr)
                sylSuccess_flag = 0
            k=0
        
            for i in range(0,len(word_syls)):
                for j in range(0,len(word_syls[i])):
                    if word_syls[i][j][0]== ' ':
                        word_syls[i][j] = word_syls[i][j].replace(' ', '', 1)


            ####################### def get_path_indices:
         
            # Finding the syllables path that matches phone transcriptions for each file.
            newSuccessInds_all = []
            newSuccessInds_all2 = []
            prevSuccessInds_all = [];prevSuccessInds_all.append(0)
            for iterWord in range(0,len(words)):
                currWordSyls = word_syls[iterWord]
                countSuccess = 1
                for iterPrev in range(0,len(prevSuccessInds_all)):
                    prevWordSyls = ""
                    if prevSuccessInds_all[iterPrev] is 0:
                        currPrevSylInds = []
                    else:
                        currPrevSylInds=prevSuccessInds_all[iterPrev]
                        for iterPrevSyls in range(0,len(currPrevSylInds)):
                            temp = word_syls[iterPrevSyls]
                            prevWordSyls = prevWordSyls+temp[currPrevSylInds[iterPrevSyls]]+" "
                    for iterCurr in range(0,len(currWordSyls)):
                        
                        currTestWordSyls = prevWordSyls+currWordSyls[iterCurr]
                        temp2 = currTestWordSyls.replace(' . ',' ')
                        inds = [m.start() for m in re.finditer(' ',temp2)]
                        if len(inds) is 0:
                            inds = [len(temp2)]
                        count = 1;temp = []
                        for iterTemp in range(0,len(inds),1):
                            if iterTemp is 0:
                                temp1 = temp2[0:inds[iterTemp]]
                            else:
                                temp1 = temp2[inds[iterTemp-1]+1:inds[iterTemp]]
                            if not((np.unique(temp1) == ' ').any() or (len(temp1)==0)):
                                temp.append(temp1)
                                count = count+1
                        if iterTemp==len(inds)-1 and len(inds)<len(currTestWordSyls):
                            temp1 = temp2[inds[iterTemp]+1:len(temp2)]
                            if not((len(temp1)==0) or (np.unique(temp1) == ' ').any()):
                                temp.append(temp1)
                                count = count+1
                        if iterWord+1==len(words):
                            currPhones = phones[0,0:len(phones[0])]
        
                        else:
                            currPhones = phones[0][0:len(temp)]
                        flag = 1
                        for iterFlag in range(0,len(currPhones),1):
                            if len(currPhones)!=len(temp):
                                flag = 0
                            else:
                                if currPhones[iterFlag]!=temp[iterFlag]:
                                    flag = 0
                        if flag==1:
                            if not currPrevSylInds==[]:
                                for i in range(0,len(currPrevSylInds)):
        #                            print('line 122::::::yes')
                                    newSuccessInds_all.append(currPrevSylInds[i])
                            newSuccessInds_all.append(iterCurr)
                            newSuccessInds_all2.append(newSuccessInds_all)
                            newSuccessInds_all = []
                            countSuccess = countSuccess+1
                prevSuccessInds_all = newSuccessInds_all2
                newSuccessInds_all2 = []
        
           

            # Compute syllable and word times
            if len(prevSuccessInds_all) != 1:              # NOTE different in python 3 code 
                prevSuccessError = prevSuccessError+1
                continue
            ########################  def get_syls_count:
            else:
                pathInds= prevSuccessInds_all[0]; sylCount= 1; phnCount= 1; spurtSyl= []; #spurtSylTimes= np.zeros((len(phnTimes),2))
        
                syls_word= np.zeros((1,len(pathInds)));spurtWordTimes= np.zeros((len(pathInds),2));
                for iterPath in range(0,len(pathInds)):
                    currWord = words[iterPath]
                    currWordSyls = word_syls[iterPath]
                    currSyl = currWordSyls[pathInds[iterPath]]
                    currSyl= currSyl.replace(' . ','.')
                    inds = [m.start() for m in re.finditer('\.',currSyl)]
                    if len(inds) is 0:
                        inds = [len(currSyl)]
                    count = 0
                    for iterTemp in range(0,len(inds)):
                        if iterTemp is 0:
                            temp1 = currSyl[0:inds[iterTemp]]
                        else:
                            temp1 = currSyl[inds[iterTemp-1]+1:inds[iterTemp]]
                        if not (temp1==' ' or len(temp1) is 0):
                            spurtSyl.append(temp1)
                            sylCount = sylCount+1
                            count = count+1
                    if iterTemp is len(inds)-1 and len(inds)<len(currTestWordSyls):
                        temp1 = currSyl[inds[iterTemp]+1:len(currSyl)]
                        if not (temp1==' ' or len(temp1) is 0):
                            spurtSyl.append(temp1)
                            sylCount = sylCount+1
                            count = count+1
                    syls_word[0][iterPath] = count

            ######################################

            #################### def get_spurts:
        
                spurtSylTimes = np.zeros((len(spurtSyl),2))
        
                for iterSyl in range(0,len(spurtSyl)):
                    temp2 = spurtSyl[iterSyl]
                    inds = [m.start() for m in re.finditer(' ',temp2)]
                    if len(inds) is 0:
                        inds = [len(temp2)]
                    count = 1; temp = []
                    for iterTemp in range(0,len(inds)):
                        if iterTemp is 0:
                            temp1 = temp2[0:inds[iterTemp]]
                        else:
                            temp1 = temp2[inds[iterTemp-1]+1:inds[iterTemp]]
                        if not(temp1 == ' ' or len(temp1) is 0):
                            temp.append(temp1)
                            count = count+1
                    if iterTemp==len(inds)-1 and len(inds)<len(currTestWordSyls):
                        temp1 = temp2[inds[iterTemp]+1:len(temp2)]
                        if not (temp1 == ' ' or len(temp1)==0):
                            temp.append(temp1)
                            count = count+1
        
                    nPhns_syl = len(temp)
                    spurtSylTimes[iterSyl,0] = phnTimes[phnCount-1,0]
                    phnCount = phnCount + nPhns_syl
                    spurtSylTimes[iterSyl,1] = phnTimes[phnCount-1-1,1]

                ##############################

                # NOTE ######################
                length_spurtSylTimes = iterSyl+1
                if len(phones[0]) != (phnCount-1):                # not in python 3 code 
                    phonecountError = phonecountError+1
                # NOTE ######################
 
            ############################### def get_spurt_word_times:
            
                sylIdx = 1
                for iterWordTimes in range(0,len(syls_word[0])):
                    spurtWordTimes[iterWordTimes,0] = spurtSylTimes[sylIdx-1,0]
                    sylIdx = sylIdx + syls_word[0][iterWordTimes].astype(int)
                    spurtWordTimes[iterWordTimes,1] = spurtSylTimes[sylIdx-1-1,1]
                length_spurtWordTimes = iterWordTimes+1
        
            ############################3
        
        # Create syllable files done    ########################################################################################
                                        ########################################################################################
        # Compute features              ########################################################################################
            twin = 5
            t_sigma = 1.4
            swin = 7
            s_sigma = 1.5
            mwin = 13
            max_threshold = 25
            
            vwlSB_num= 4
            vowelSB= [1,2,4,5,6,7,8,13,14,15,16,17]
            sylSB_num= 5
            sylSB= [1,2,3,4,5,6,13,14,15,16,17,18]
            
            startWordFrame_all = []; spurtStartFrame_all = []; spurtEndFrame_all=[]
            vowelStartFrame_all = []; vowelEndFrame_all = []; eng_full_all = []
            spurtStress_all = []
            
            # Execute the vocoder [MODIFICATION]: Get the audio file back so that it can be stored in a text file for C code.
            eng_full, xx = vocoder_func(wavFile)
            #eng_full = np.loadtxt('./ISLE_SESS0003_BLOCKD01_11_sprt1.e19' , delimiter=',')
            eng_full = eng_full.conj().transpose()
            
            # Processing word boundary file
            # FILE READ DELETED HERE

            ################################### def process_word_boundaries: 
            a = spurtWordTimes
            b = words
            if(len(a) is not len(b)):
                continue
            wordData = np.hstack((a, np.array([b], dtype='S32').T))
            startWordTime = [row[0] for row in wordData]  # Extract first coloumn of wordData
            endWordTime = [row[1] for row in wordData]
            startWordFrame = np.round((np.subtract(np.array(startWordTime, dtype='float'), spurtSylTimes[0][0].astype(float))*100))
            endWordFrame = np.round((np.subtract(np.array(endWordTime, dtype='float'), spurtSylTimes[0][0].astype(float))*100) + 1)
            startWordFrame = np.append(startWordFrame,endWordFrame[-1])

            ###############################

            # Processing of stress and syllable boundary file
            spurtSylTime = spurtSylTimes
            spurtStartTime = spurtSylTime[:, 0]
            spurtEndTime = spurtSylTime[:, 1]
            spurtStartFrame = np.round((spurtStartTime - spurtStartTime[0]) * 100)
            spurtEndFrame = np.round((spurtEndTime - spurtStartTime[0]) * 100)
            
            # Processing of Vowel boundary file
            vowelStartFrame = np.round(vowelStartTime*100 - spurtStartTime[0] * 100)
            vowelEndFrame = np.round(vowelEndTime*100 - spurtStartTime[0] * 100)
            
            # TCSSBC computation
            ############################### def get_sylTCSSBC:
            if len(sylSB) > sylSB_num:
                eng = spectral_selection(eng_full[np.subtract(sylSB, 1), :], sylSB_num)
            else:
                eng = eng_full[sylSB, :]

            t_cor = temporal_corr(eng, twin, t_sigma)
            s_cor = spectral_corr(t_cor)
            sylTCSSBC = smooth(s_cor, swin, s_sigma)
            sylTCSSBC = np.array([sylTCSSBC])
            
            # Modify TCSSBC contour by clipping from the syllable start
            start_idx = np.round(spurtStartTime[0]*100).astype(int)
            sylTCSSBC = np.array([sylTCSSBC[0][start_idx:-1]])
            
            sylTCSSBC = np.divide(sylTCSSBC, max(sylTCSSBC[0]))
            
            if len(vowelSB) > vwlSB_num:
                eng = spectral_selection(eng_full[np.subtract(vowelSB, 1), :], vwlSB_num)
            else:
                eng = eng_full[vowelSB, :]

            t_cor = temporal_corr(eng, twin, t_sigma)
            s_cor = spectral_corr(t_cor)
            vwlTCSSBC = smooth(s_cor, swin, s_sigma)
            
            vwlTCSSBC = np.array([vwlTCSSBC])
            
            # Modify TCSSBC contour by clipping from the vowel start
            start_idx = np.round(vowelStartTime[0][0]*100).astype(int)
            vwlTCSSBC = np.array([vwlTCSSBC[0][start_idx:-1]])
            
            vwlTCSSBC = np.divide(vwlTCSSBC, max(vwlTCSSBC[0]))
            
            # Compute silence statistics
            # Preprocessing of the data
            word_duration = np.zeros((1, len(startWordFrame) - 1))
            word_Sylsum = np.zeros((1, len(startWordFrame) - 1))
            word_Vwlsum = np.zeros((1, len(startWordFrame) - 1))
            
            for j in range(0, len(startWordFrame) - 1):
                temp_start = startWordFrame[j].astype(int)
                temp_end = startWordFrame[j + 1].astype(int) - 1
                #jhansi
                if (temp_end >= sylTCSSBC.shape[1]):
                    temp_end1 = sylTCSSBC.shape[1]-1
                    sylTCSSBC[0, np.arange(temp_start, temp_end1)] = medfilt(sylTCSSBC[0, np.arange(temp_start, temp_end1)], 3)
                    sylTCSSBC[0, temp_start] = sylTCSSBC[0, temp_start+1]
                    sylTCSSBC[0, temp_end1] = sylTCSSBC[0, temp_end1 - 1]
                    tempArr = sylTCSSBC[0, np.arange(temp_start, temp_end1)]
                    word_Sylsum[0, j] = tempArr.sum(axis=0)
                else:
                    sylTCSSBC[0, np.arange(temp_start, temp_end)] = medfilt(sylTCSSBC[0, np.arange(temp_start, temp_end)], 3)
                    sylTCSSBC[0, temp_start] = sylTCSSBC[0, temp_start+1]
                    sylTCSSBC[0, temp_end] = sylTCSSBC[0, temp_end - 1]
                    tempArr = sylTCSSBC[0, np.arange(temp_start, temp_end)]
                    word_Sylsum[0, j] = tempArr.sum(axis=0)
                if (temp_end >= vwlTCSSBC.shape[1]):
                    temp_end = vwlTCSSBC.shape[1]-1
            #    temp_end = np.min([temp_end,len(vwlTCSSBC)])
                vwlTCSSBC[0, np.arange(temp_start, temp_end)] = medfilt(vwlTCSSBC[0, np.arange(temp_start, temp_end)], 3)
                vwlTCSSBC[0, temp_start] = vwlTCSSBC[0, temp_start+1]
                vwlTCSSBC[0, temp_end] = vwlTCSSBC[0, temp_end - 1]
            
                word_duration[0, j] = temp_end - temp_start + 1
    
                tempArr = vwlTCSSBC[0, np.arange(temp_start, temp_end)]
                word_Vwlsum[0, j] = tempArr.sum(axis=0)

            sylTCSSBC[np.isnan(sylTCSSBC)] = 0
            vwlTCSSBC[np.isnan(vwlTCSSBC)] = 0

            ###############################

            tempOut = np.array([[]])
            
            wordIndication = []; peakVals = []; avgVals = []
            
            # Generating the features
            for j in range(0, len(spurtSyl), 1):
                inds = (startWordFrame <= spurtStartFrame[j]).nonzero()
                word_ind = inds[0][-1]; wordIndication.append(word_ind)
        #        print([0, np.arange(spurtStartFrame[j], spurtEndFrame[j]-1, 1).astype(int)])
                currFtr1SylSeg = sylTCSSBC[0, np.arange(spurtStartFrame[j], spurtEndFrame[j]-1, 1).astype(int)]
                currFtr1SylSeg = np.array([currFtr1SylSeg])
                temp = np.multiply(currFtr1SylSeg, len(currFtr1SylSeg[0]) / word_duration[0, word_ind])
                arrResampled = np.array([scikits.samplerate.resample(temp[0], float(30) / len(temp[0]), 'sinc_best')])
                
                #To be put in the output file
                peakVals.append(np.amax(arrResampled))
                avgVals.append(np.average(arrResampled))
            
                currSylFtrs = statFunctions_Syl(arrResampled)
                arr1 = np.array([np.array([np.sum(currFtr1SylSeg) / word_Sylsum[0, word_ind]])]).T
                currSylFtrs = np.vstack((currSylFtrs, arr1))
                ##########jhansi
                if (j>= vowelEndFrame.shape[1]):
                    break
                if (vowelEndFrame [0,j] >= vwlTCSSBC.shape[1]):
                    vowelEndFrame[0,j] = vwlTCSSBC.shape[1]-1
            
                currFtr1VowelSeg = vwlTCSSBC[0, np.arange(vowelStartFrame[0, j], vowelEndFrame[0, j]-1, 1).astype(int)]
                currFtr1VowelSeg = np.array([currFtr1VowelSeg])
                temp = np.multiply(currFtr1VowelSeg, len(currFtr1VowelSeg[0]) / word_duration[0, word_ind])
                if (len(temp[0])==0):
                    break
                    
                arrResampled = np.array([scikits.samplerate.resample(temp[0], float(20) / len(temp[0]), 'sinc_best')])
                currVowelFtrs = statFunctions_Vwl(arrResampled)
                arr1 = np.array([np.array([np.sum(currFtr1VowelSeg) / word_Sylsum[0, word_ind]])]).T
                currVowelFtrs = np.vstack((currVowelFtrs, arr1))
                if j == 0:
                    tempOut = np.vstack((currSylFtrs, currVowelFtrs, len(currFtr1VowelSeg[0]), len(currFtr1SylSeg[0])))
                else:
                    tempOut = np.hstack((tempOut, np.vstack((currSylFtrs, currVowelFtrs,len(currFtr1VowelSeg[0]), len(currFtr1SylSeg[0])))))
            if (len(temp[0])==0):
                   continue
            sylDurations = spurtEndTime - spurtStartTime
            
            ftrs = tempOut
            
            wordLabls = np.unique(wordIndication)
            for iterWrd in range(0, len(wordLabls)):
                inds = [i for i, x in enumerate(wordIndication) if x == wordLabls[iterWrd]] #doing argwhere(wordIndication==wordLabls[iterWrd]
                if len(inds)>1 :
                    ftrs[-1, inds] = ftrs[-1, inds] / sum(ftrs[-1, inds])
                    ftrs[-2, inds] = ftrs[-2, inds] / sum(ftrs[-2, inds])
            end=1
            print(ftrs.shape)
            fa = ftrs
            
            
            mat = scipy.io.loadmat(stressLabelspath+fileName[0:-4]+'.mat')
            lab = mat['spurtStress']
            lab_list = lab.tolist()
            if (fa.shape[1] is not len(lab_list)):
                label_mismatch = label_mismatch+1
    #            is_looping = False
                continue
            else:
                fb,filenm = get_labels(lab_list,fa,fileName)
                feats = fb #features ,last row:labels
                w=[];#polysyl_feat=[];
                for w_l in range(len(words)):
            #        cou = 0
                    w_st = spurtWordTimes[w_l][0]; w_ed = spurtWordTimes[w_l][1]
                    for s_l in range(len(w),len(spurtSyl)):
                        sy_st = spurtSylTimes[s_l][0];sy_ed = spurtSylTimes[s_l][1]
                        if (sy_ed <= w_ed):
                            w.append(w_l+1)
    #                        w.append('W'+str(w_l+1))
            #                cou=cou+1
                        else:
                            break
                if (len(w)>np.shape(feats)[1]):
                    continue
                feats = np.vstack((feats,w))#features ,last row:labels, word labels
                AF_inform = filenm
                CF_feats,CF_inform = contextFeats(spurtSyl,spurtSylTimes,spurtWordTimes,vowel);  
                if fileN == 0:#411 or fileN ==412:
                    AF = feats
                    AF_info = AF_inform
                    CF = CF_feats
                    CF_info =CF_inform                
                else:
                    AF = np.hstack((AF,feats)) 
                    AF_info = np.hstack((AF_info,AF_inform))
                    CF = np.hstack((CF,CF_feats))
                    CF_info = np.hstack((CF_info,CF_inform))
                    done=done+1
                    print('Done:::file number ' + str(done) + '  out of ' + str(len(files)))
          
    labels_mis_count.append(label_mismatch)
    scipy.io.savemat('/home/iiit/Desktop/Jhansi/Stress detection/Codes_jhansi/features/GER_train_'+model+'.mat', {'AF': AF,'CF': CF,'CF_info': CF_info,'AF_info': AF_info})
