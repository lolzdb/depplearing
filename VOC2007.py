from xml.dom import minidom
import json
import os
from PIL import Image
from PIL import ImageDraw
import random
from PIL import ImageFont
from sklearn.externals import joblib

class voc2007: #创建满足要求的xml文件
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

width=512  #图片的宽
height=512  #图片的高
def createxml(vocpath,idspath,path,size=[width,height,3]): #创建xml文件 voc：保存新生成的物体位置信息文件 ids：图片列表文件
    voc_file=open(vocpath, encoding='utf-8')                #path：生成的xml文件的位置 
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



def convert(ids_path,result_path):  #将json格式的文件列表转换为txt格式，在制作数据集时需要用到这个文件
    ids_file=open(ids_path,'r')     #ids_path：图片列表文件
    ids=json.load(ids_file)
    vocids=open(result_path,'w')
    for i in ids:
        vocids.write(i+'\n')
    ids_file.close()
    vocids.close()

def fileter2(idspath,datapath):  #如果图片的宽高不满足要求，在生成xml时将不会有该图片的xml信息，该图片也不会被加入到tfrecord文件中
    ids=getjson(idspath)            ##idspath：图片列表文件
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
    file = open(datapath+'/filter.txt', 'w')
    for i in ids:
        file.write(i+'\n')
    file.close()

def merge(infopath1,infopath2,resultpath):   #和并两个包含物体位置信息的dict
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

def getjson(infopath):  #读取json文件并解析   infopath：json文件的路径
    infofile1=open(infopath)
    info1=json.load(infofile1)
    infofile1.close()
    return info1

def writejson(path,data): #将信息文件写入json文件
    file = open(path,'w')
    jdata=json.dumps(data)
    file.write(jdata)
    file.close()

def static(idspath,infopath): #将含有目标物坐标位置不满足条件的图片从列表中去掉
    ids=getjson(idspath)
    info=getjson(infopath)
    l=[]
    for i in ids:
        mark=0
        for k in info[i]['objects']:
            box = [int(k['bbox']['xmin'] ), int(k['bbox']['ymin']), int(k['bbox']['xmax'] ),
                   int(k['bbox']['ymax'] )]
            if box[0]<1 or box[1]<1 or box[2]>width-1 or box[3]>height-1:
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

def drawrect(text,box,img):  #在图片中画矩形框
    draw = ImageDraw.Draw(img)
    front = ImageFont.truetype('simsun.ttc',30)
    #draw.text(int(box['xmin'], int(box['ymin'])), str(text), fill=(0, 0, 255, 1),font=front)
    draw.polygon([(int(box['xmin']),int(box['ymin'])),(int(box['xmax']),int(box['ymin'])),(int(box['xmax']),int(box['ymax'])),(int(box['xmin']),int(box['ymax']))],outline=(255,0,0))


def drawall(idspath,infopath,datapath,resultpath): #在所有的图片中将目标用矩形框画出来
    ids=getjson(idspath)
    info=getjson(infopath)
    for i in ids:
        img=Image.open(datapath+'/'+i+'.jpg')
        for k in info[i]["objects"]:
            drawrect(k['category'],k['bbox'],img)
        img.save(resultpath+'/'+i+'.jpg')
        img.close()

def pad(box,img):  #将图片中的目标物用的像素覆盖
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


def clean(idspath,infopath,dic,datapath,resultpath): #将没有包含在dic字典中的种类使用pad函数覆盖
    ids=getjson(idspath)    #idspath：包含所有图片的文件列表的json文件路径  infopath：包含有物体位置和类别信息的dict，dict格式可参看数据集制作的文档，文档对该格式有说明
    info=getjson(infopath)  # #datapath：图片文件的路径      resultpath：覆盖结果的保存路径
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

def select(idspath,infopath,datapath,resultpath,up):   #将不满足条件的目标物删除 参数含义clean函数
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




voc='F:\\data\\0.75\\clean\\voc.json'  #包含有物体位置和类别信息的dict，dict格式可参看数据集制作的文
ids='F:\\data\\0.75\\clean\\ids.json'  #ids：图片列表
idstrain='F:\\data\\0.75\\train.txt'   #将ids的文件转为txt后保存的路径
xmlpath='F:\\data\\0.75\\xml'    #xml文件保存路径
datapath='F:\\data\\0.75\\data'  #数据路径
resultpath='F:\\data\\0.75\\clean'  #结果的保存路径
size=[width,height,3]   #图片的长宽高

dic={
    'pl30':(1,'Vehicle'),
'p11':(2,'Vehicle'),
'pl5':(3,'Vehicle'),
'i4':(4,'Vehicle'),
'il80':(5,'Vehicle'),
'pl40':(6,'Vehicle'),
'ip':(7,'Vehicle'),
'i2':(8,'Vehicle'),
'pne':(9,'Vehicle'),
'il60':(10,'Vehicle'),
'p10':(11,'Vehicle'),
'pl100':(12,'Vehicle'),
'p26':(13,'Vehicle'),
'i5':(14,'Vehicle'),
'pl80':(15,'Vehicle'),
'pn':(16,'Vehicle'),
'w57':(17,'Vehicle'),
'p5':(18,'Vehicle'),
'pl60':(19,'Vehicle'),
'pl50':(20,'Vehicle'),
'pl120':(21,'Vehicle'),
}
#static(ids,voc)
#createxml(voc,ids,xmlpath,size)
#drawall(ids,voc,datapath,resultpath)
#clean(ids,voc,dic,datapath,resultpath)
#drawall(ids,voc)
#copy(voc,ids,"F:\\ndata\\train3\\select\\000075.jpg")
#drawall(ids,voc,path,"F:\\data\\fill")
#cleanimage(ids,'F:\\ndata\\ct512\\data')
#fileter2(ids,datapath)

'''
使用流程：
    制作voc2007格式的xml文档：
        1.使用fileter2与static过滤不满足条件的图片
        2.使用clean除掉不需要的类
        3.使用createxml创建xml函数
        4.将文件列表保存为txt格式
'''