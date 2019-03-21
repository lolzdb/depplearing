from xml.dom import minidom
import json
import os
from PIL import Image
from PIL import ImageDraw
import random
from PIL import ImageFont
from sklearn.externals import joblib

class voc2007:
    def __init__(self,path):
        self.path=path

    def initnode(self,dom,root,img_name):
        self.appendnvalue(root,'folder','VOC2007',dom)
        self.appendnvalue(root,'filename', img_name+'.jpg', dom)
        source = dom.createElement('source')
        root.appendChild(source)
        self.appendnvalue(source, 'database', 'xws', dom)
        self.appendnvalue(source, 'annotation', 'xws', dom)
        self.appendnvalue(source, 'image', '0', dom)
        self.appendnvalue(source, 'flickrid', '0', dom)
        owner = dom.createElement('owner')
        root.appendChild(owner)
        self.appendnvalue(owner, 'flickrid', '0', dom)
        self.appendnvalue(owner, 'name', 'xws', dom)
        self.appendnvalue(root, 'segmented', '1', dom)

    def addsize(self,size,root,dom):
        nsize = dom.createElement('size')
        root.appendChild(nsize)
        self.appendnvalue(nsize, 'width',str(size[0]), dom)
        self.appendnvalue(nsize, 'height',str(size[1]), dom)
        self.appendnvalue(nsize, 'depth',str(size[2]), dom)

    def appendnvalue(self,root,node_name,text,dom):
        node = dom.createElement(node_name)
        root.appendChild(node)
        text = dom.createTextNode(text)
        node.appendChild(text)

    def addobject(self,dom,root,label,box):
        object = dom.createElement('object')
        root.appendChild(object)
        self.appendnvalue(object, 'name', label, dom)
        self.appendnvalue(object, 'pose', '0', dom)
        self.appendnvalue(object, 'truncated', '0', dom)
        self.appendnvalue(object, 'difficult', '0', dom)
        bndbox = dom.createElement('bndbox')
        object.appendChild(bndbox)
        self.appendnvalue(bndbox, 'xmin', str(box[0]), dom)
        self.appendnvalue(bndbox, 'ymin', str(box[1]), dom)
        self.appendnvalue(bndbox, 'xmax', str(box[2]), dom)
        self.appendnvalue(bndbox, 'ymax', str(box[3]), dom)

    def convert(self,img_name,label_list,box_list,size):
        dom=minidom.Document()
        root=dom.createElement('annotation')
        dom.appendChild(root)
        self.initnode(dom, root, img_name)
        self.addsize(size,root,dom)
        for label,box in zip(label_list,box_list):
            self.addobject(dom,root,label,box)
        with open(self.path+'/'+img_name+'.xml', 'w', encoding='UTF-8') as fh:
            dom.writexml(fh, indent='', addindent='\t', newl='\n', encoding='UTF-8')

width=512
height=512
def createxml(vocpath,idspath,path,size=[width,height,3]):
    voc_file=open(vocpath, encoding='utf-8')
    ids_file=open(idspath, encoding='utf-8')
    voc=json.load(voc_file)
    ids=json.load(ids_file)
    vocxml=voc2007(path)
    for i in ids:
        lable_list=[]
        box_list=[]
        for k in voc[i]["objects"]:
            lable_list.append(k["category"])
            box=[int(k['bbox']['xmin']),int(k['bbox']['ymin']),int(k['bbox']['xmax']),int(k['bbox']['ymax'])]
            box_list.append(box)
        vocxml.convert(i,lable_list,box_list,size)

def getback(backpath):
    flist=[]
    for file in os.listdir(backpath):
        flist.append(file)
    return flist

def convert(ids_path,result_path):
    ids_file=open(ids_path,'r')
    ids=json.load(ids_file)
    vocids=open(result_path,'w')
    for i in ids:
        vocids.write(i+'\n')
    ids_file.close()
    vocids.close()

def fileter(idspath,infopath,datapath):
    idsfile=open(idspath,'r')
    infofile=open(infopath,'r')
    ids=json.load(idsfile)
    info=json.load(infofile)
    dlist=[]
    for i in ids:
        path=datapath+'/'+i+'.jpg'
        img=Image.open(path)
        w,h=img.size
        if w<width or h<height:
            print(w,h)
            dlist.append(i)
        img.close()
    print(len(dlist))
    for i in dlist:
        ids.remove(i)
        info.pop(i)
    idsfile.close()
    infofile.close()
    idsfile = open(idspath, 'w')
    infofile = open(infopath, 'w')
    idsjson=json.dumps(ids)
    vocjson=json.dumps(info)
    idsfile.write(idsjson)
    infofile.write(vocjson)

def fileter2(idspath,datapath):
    ids=getjson(idspath)
    length = len(ids)
    i = 0
    while i < length:
        ids[i] = ids[i].replace('\n', '')
        i += 1
    dlist=[]
    for i in ids:
        path=datapath+'/'+i+'.jpg'
        img=Image.open(path)
        w,h=img.size
        if w<width or h<height:
           dlist.append(i)
        img.close()
    for i in dlist:
        ids.remove(i)
    writejson(idspath,ids)

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

def static(idspath,infopath):
    ids=getjson(idspath)
    info=getjson(infopath)
    l=[]
    for i in ids:
        mark=0
        for k in info[i]['objects']:
            box = [int(k['bbox']['xmin'] ), int(k['bbox']['ymin']), int(k['bbox']['xmax'] ),
                   int(k['bbox']['ymax'] )]
            if box[0]<0 or box[1]<0 or box[2]>width or box[3]>height:
                mark=1
        if mark==1:
            l.append(i)
    for i in l:
        ids.remove(i)
        info.pop(i)
    print(len(l))
    writejson(idspath,ids)
    writejson(infopath,info)
    return l

def drawrect(text,box,img):
    draw = ImageDraw.Draw(img)
    front = ImageFont.truetype('simsun.ttc',30)
    #draw.text(int(box['xmin'], int(box['ymin'])), str(text), fill=(0, 0, 255, 1),font=front)
    draw.polygon([(int(box['xmin']),int(box['ymin'])),(int(box['xmax']),int(box['ymin'])),(int(box['xmax']),int(box['ymax'])),(int(box['xmin']),int(box['ymax']))],outline=(255,0,0))

def drawfill(box,img):
    draw = ImageDraw.Draw(img)
    draw.rectangle((box['xmin'],box['ymin'],box['xmax'],box['ymax']),fill=(255, 0, 0, 1))


def drawall(idspath,infopath,datapath,resultpath):
    ids=getjson(idspath)
    info=getjson(infopath)
    for i in ids:
        img=Image.open(datapath+'/'+i+'.jpg')
        for k in info[i]["objects"]:
            drawrect(k['category'],k['bbox'],img)
        img.save(resultpath+'/'+i+'.jpg')
        img.close()

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

def gettype(voc,ids):
    ids = getjson(ids)
    voc = getjson(voc)
    t=set()
    for i in ids:
        for k in voc[i]['objects']:
            t.add(k['category'])
    t=list(t)
    dic={}
    for i in t:
        dic[i]=0
    return t,dic

def copy(infopath,idspath,imgpath):
    ids = getjson(idspath)
    info = getjson(infopath)
    img=Image.open(imgpath)
    nids=[]
    ninfo={}
    i=76
    while i<476:
        n = 6 - len(str(i))
        name = str(0) * n + str(i)
        ninfo[name]=info['000075']
        nids.append(name)
        img.save('F:\\ndata\\train3\\copy\\'+name+'.jpg')
        i+=1
    writejson('F:\\ndata\\train3\\copy\\ids.json', nids)
    writejson('F:\\ndata\\train3\\copy\\info.json', ninfo)

def drawDark(box,img,bdic,backpath):
    draw = ImageDraw.Draw(img)
    draw.rectangle((box['xmin'],box['ymin'],box['xmax'],box['ymax']),fill=(0, 0, 0))

def clean(idspath,infopath,dic,datapath,resultpath):
    ids = getjson(idspath)
    info = getjson(infopath)
    nids=[]
    ninfo={}
    for i in ids:
        object=[]
        mark=0
        count=0
        img=Image.open(datapath+'/'+i+'.jpg')
        for k in info[i]['objects']:
            if k['category'] not in dic:
                object.append(k)
                count+=1
            else:
                # box = (int(k['bbox']['xmin']), int(k['bbox']['ymin']), int(k['bbox']['xmax']), int(k['bbox']['ymax']))
                # bregion = bimg.crop(box)
                # img.paste(bregion,box)
                #drawDark(k['bbox'], img, bdic, backpath)
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

def select(idspath,infopath,datapath,resultpath,up):
    ids = getjson(idspath)
    info = getjson(infopath)
    nids=[]
    ninfo={}
    for i in ids:
        object=[]
        count=0
        img=Image.open(datapath+'/'+i+'.jpg')
        for k in info[i]['objects']:
            w =int(k['bbox']['xmax'])-int(k['bbox']['xmin'])
            h= int(k['bbox']['ymax'])-int(k['bbox']['ymin'])
            if w>up and h>up:
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
            img.save(resultpath+'\\'+i+'.jpg')
        img.close()
    print(len(ninfo))
    writejson(resultpath+'/ids.json', nids)
    writejson(resultpath+'/voc.json', ninfo)

def sample(dic,voc,ids,datapath,resultpath,bdic,backpath,idstrain,selectpath="",mark=False,up=16):
    clean(ids, voc, dic, datapath, resultpath)
    static(ids, voc)
    if mark==True:
        select(ids, voc, resultpath, selectpath, up)
        voc=selectpath+'/'+'voc.json'
        ids = selectpath + '/' + 'ids.json'
        createxml(voc, ids, xmlpath)
        convert(ids,idstrain)
    else:
        createxml(voc, ids, xmlpath)
        convert(ids, idstrain)

def exchange(voc,ids):
    info=getjson(voc)
    ids=getjson(ids)
    for i in ids:
        for k in info[i]['objects']:
            k['category']=k['category'][0]
    writejson(voc,info)

def createids(path):
    file=open('F:\\ndata\\yuan\\train.txt','r')
    l=file.readlines()
    ids=[]
    for i in l:
        ids.append(i.replace('\n',''))
    writejson('F:\\ndata\\yuan\\ids.json')

def cleanimage(ids,datapath):
    ids=getjson(ids)
    flist=os.listdir(datapath)
    fl=[i.replace('.jpg','') for i in flist]
    for i in fl:
        if i not in ids:
            path=datapath+'/'+i+'.jpg'
            print(path)
            os.remove(path)




voc='/media/x/0F6B14F90F6B14F9/data/data/voc.json'
ids='/media/x/0F6B14F90F6B14F9/data/data/ids.json'
idstrain='/media/x/0F6B14F90F6B14F9/data/data/train.txt'
xmlpath='/media/x/0F6B14F90F6B14F9/data/xml'
datapath='/media/x/0F6B14F90F6B14F9/data/data'
resultpath='/media/x/0F6B14F90F6B14F9/data/data'
size=[width,height,3]

#dic=['pn','pne','pnl','pr40','ps','pg','pl50','po','p26','p14']
dic=['io','po']
#fileter2(ids,datapath)
#drawall(ids,voc,datapath,resultpath)
#static(ids,voc)
#drawall(ids,voc)
#copy(voc,ids,"F:\\ndata\\train3\\select\\000075.jpg")
#drawall(ids,voc,path,"F:\\data\\fill")
#cleanimage(ids,'F:\\ndata\\ct512\\data')
convert(ids,'/home/x/workspace/ndata/dataset/train.txt')
#createxml(voc,ids,xmlpath,size)
#clean(ids,voc,dic,datapath,resultpath)