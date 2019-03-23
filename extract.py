from xml.dom import minidom
import json
import os
import cv2
from PIL import Image
from PIL import ImageDraw
import random
from PIL import ImageFont
import numpy as np
import os

def getjson(infopath):
    infofile1=open(infopath)
    info1=json.load(infofile1)
    infofile1.close()
    return info1

def writejson(path,data):
    file = open(path,'w')
    jdata=json.dumps(data)
    file.write(jdata)
    file.close()

def merge(infopath1,infopath2,resultpath):
    infofile1=open(infopath1)
    infofile2=open(infopath2)
    info1=json.load(infofile1)
    info2=json.load(infofile2)
    dic={}
    dic.update(info1)
    dic.update(info2)
    result=open(resultpath,'w')
    dicjson=json.dumps(dic)
    result.write(dicjson)

def static(dic,ilist,id):
    for i in ilist:
        if i['category'] not in dic:
            ndic={}
            ndic['count']=0
            ndic['id']=[]
            dic[i['category']]=ndic
        dic[i['category']]['count']+=1
        dic[i['category']]['id'].append(id)

def parsefile(voc_path,ids_path):
    voc = getjson(voc_path)
    ids = getjson(ids_path)
    cdic = {}
    for i in ids:
        imgs = voc[i]
        static(cdic, imgs['objects'], i)
    return cdic

def objectinfo(category,box):
    boxinfo = {'category': category, 'bbox': {'xmin':box[0],'ymin':box[1],'xmax':box[2],'ymax':box[3]}}
    return boxinfo

def pad(box,img):
    nbox=[int(box['xmin']),int(box['ymin']),int(box['xmax']),int(box['ymax'])]
    bbox=nbox.copy()
    w=nbox[2]-nbox[0]
    h = nbox[3] - nbox[1]
    nbox[0] -=2
    nbox[2]=nbox[0]+1
    nbox[3]=nbox[1]+2
    region=img.crop(nbox)
    nregion=region.resize((w,h))
    img.paste(nregion,bbox)

def clean(idspath,infopath,dic,datapath,resultpath):
    ids=getjson(idspath)
    info=getjson(infopath)
    nids=[]
    ninfo={}
    for i in ids:
        object=[]
        count=0
        img=Image.open(datapath+'/'+i+'.jpg')
        for k in info[i]['objects']:
            if k['category'] in dic:
                object.append(k)
                count+=1
            else:
                pad(k['bbox'], img)
        if count != 0:
            infoitem = {}
            infoitem['id'] = i
            infoitem['objects'] = object
            ninfo[i]=infoitem
            nids.append(i)
            img.save(resultpath+'/'+i+'.jpg')
        img.close()
    writejson(os.path.join(resultpath, 'ids.json'), nids)
    writejson(os.path.join(resultpath, 'voc.json'), ninfo)

def randomGaussian(img,n):
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    m=int((img.shape[0]*img.shape[1])*n)
    for a in range(m):
        i=int(np.random.random()*img.shape[1])
        j=int(np.random.random()*img.shape[0])
        if img.ndim==2:
            img[j,i]=255
        elif img.ndim==3:
            img[j,i,0]=255
            img[j,i,1]=255
            img[j,i,2]=255
    for b in range(m):
        i=int(np.random.random()*img.shape[1])
        j=int(np.random.random()*img.shape[0])
        if img.ndim==2:
            img[j,i]=0
        elif img.ndim==3:
            img[j,i,0]=0
            img[j,i,1]=0
            img[j,i,2]=0
    image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return image

def judgexit(dic,typelist,currenttype):
    mark=False
    if dic[currenttype]['count']>500:
        mark=True
    for i in list(dic):
        if dic[i]['count']>500:
            print("count " + str(dic[i]['count'])+ "  type " + i)
            dic.pop(i)
            if i!=currenttype:
                typelist.remove(i)
    return mark

def Gaussian(dic,datapath,json_file,resultpath,imginfo,ids):
    typelist = list(dic.keys())
    print('typlsit',typelist)
    count=0
    while len(typelist)!=0:
        i=typelist.pop()
        id = dic[i]['id']
        for j in id:
            if judgexit(dic,typelist,i):
                break
            file = os.path.join(datapath,j+'.jpg')
            imgf = Image.open(file)
            info1 = {}
            info1['id'] = j + 'Gaussian1'+str(count)
            info1['objects'] = []
            for k in json_file[j]['objects']:
                if k['category'] in dic:
                    box = (int(k['bbox']['xmin']), int(k['bbox']['ymin']), int(k['bbox']['xmax']), int(k['bbox']['ymax']))
                    info1['objects'].append(objectinfo(k['category'], box))
                    dic[k['category']]['count'] += 1
                else:
                    pad(k['bbox'], imgf)
            if len(info1['objects']) > 0:
                img1 = randomGaussian(imgf,0.03)
                imginfo[info1['id']] = info1
                ids.append(info1['id'])
                img1.save(os.path.join(resultpath,info1['id'] + '.jpg'))
                count += 1
            imgf.close()
        if i in dic and dic[i]['count']<500:
            typelist.append(i)

def filter(voc,ids,dic,datapath,resultpath):
    ids = getjson(ids)
    info = getjson(voc)
    stic={}
    for i in dic:
        stic[i]=0
    nids = []
    ninfo = {}
    for i in ids:
        object=[]
        count=0
        img=Image.open(datapath+'/'+i+'.jpg')
        for k in info[i]['objects']:
            if k['category'] in dic:
                object.append(k)
                count+=1
                stic[k['category']]+=1
                if stic[k['category']]>500:
                    dic.pop(k['category'])
            else:
                pad(k['bbox'], img)
        if count != 0:
            infoitem = {}
            infoitem['id'] = i
            infoitem['objects'] = object
            ninfo[i]=infoitem
            nids.append(i)
            img.save(resultpath+'/'+i+'.jpg')
        img.close()
    writejson(os.path.join(resultpath,'ids.json'),nids)
    writejson(os.path.join(resultpath, 'voc.json'), ninfo)

def generateids(datapath,resultpath):
    file_list=os.listdir(datapath)
    ids=[]
    for i in file_list:
        ids.append(os.path.splitext(i)[0])
    writejson(resultpath,ids)

def select(dic,low,up):
    keys=list(dic.keys())
    for i in keys:
       if dic[i]['count']<low or dic[i]['count']>up:
           dic.pop(i)
    return dic

def rename(path,idspath,vocpath,start):
    info = getjson(vocpath)
    filelist = getjson(idspath)
    voc = {}
    ids = []
    i = start
    n = 6
    for item in filelist:
        n = 6 - len(str(i))
        vname = str(0) * n + str(i)
        name = item
        img = {}
        img['id'] = vname
        img['objects'] = info[name]['objects']
        voc[vname] = img
        ids.append(vname)
        src = os.path.join(os.path.abspath(path), item + '.jpg')
        dst = os.path.join(os.path.abspath(path), vname + '.jpg')
        print(i)
        os.rename(src, dst)
        i = i + 1

    writejson(os.path.join(path, 'nids.json'), ids)
    writejson(os.path.join(path, 'nvoc.json'), voc)

voc='G:\\data\\data\\voc.json'
ids='G:\\data\\data\\ids.json'

datapath='G:\\data\\newdata'
resultpath='G:\\data\\data'

#dic={'pl100':1,'i4':2,'pl80':3,'pl60':4,'i5':5,'p11':6,'pl40':7,'pl50':9,'pn':0,'pne':0,'p26':0}
dic=parsefile(voc,ids)
#dic=select(dic,190,10000)
voc=getjson(voc)
for i in dic:
    print(i,dic[i]['count'])
#clean(ids,voc,dic,datapath,resultpath)
#filter(voc,ids,dic,datapath,resultpath)
#info={}
#ids=[]
#Gaussian(dic,datapath,voc,resultpath,info,ids)
#writejson(os.path.join(resultpath,'voc.json'),info)
#writejson(os.path.join(resultpath,'ids.json'),ids)
#rename('G:\\data\\enhance','G:\\data\\enhance\\ids.json','G:\\data\\enhance\\voc.json',30000)


