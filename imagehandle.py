import tensorflow as tf
import json
import numpy as np
import random
import cv2
import os
from PIL import ImageEnhance
from PIL import Image
from PIL import ImageFile
import time
ImageFile.LOAD_TRUNCATED_IMAGES = True

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

def randomresize(img,low=30):
    w, h = img.size
    rand = random.uniform(1.2, 2)
    while True:
        rw=int(w * rand)
        rh=int(h * rand)
        if rw>20 or rh>20:
            break
        rand+=0.1
    if rw>200 or rh>200:
        rw=int(float(rw)*0.75)
        rh=int(float(rh)*0.75)
    return img.resize((rw, rh))

def getnlocation(box,rw,rh):
    x = (box[2] + box[0]) / 2
    y = (box[3] + box[1]) / 2
    box[0] = int(x - rw / 2)
    box[2] = box[0]+rw
    box[1] = int(y - rh / 2)
    box[3] = box[1]+rh
    if box[0]<0:
        box[2] += abs(box[0])
        box[0]=0
    if box[1]<0:
        box[3] += abs(box[1])
        box[1]=0
    if box[2]>1023:
        box[0] -= (box[2] - 1023)
        box[2] = 1023
    if box[3]>1023:
        box[1] -= (box[3] - 1023)
        box[3] = 1023
    return box

def jdre(boxs,th=0.2):
    l=len(boxs)
    for i in range(0,l):
        j=i+1
        while j<l:
            xmin=np.max([boxs[i][0],boxs[j][0]])
            ymin=np.max([boxs[i][1],boxs[j][1]])
            xmax = np.min([boxs[i][2],boxs[j][2]])
            ymax = np.min([boxs[i][3],boxs[j][3]])
            xr=(xmax-xmin)*(ymax-ymin)
            if xr<=0:
                j += 1
                continue
            sr=(boxs[i][2]-boxs[i][0])*(boxs[i][3]-boxs[i][1])+(boxs[j][2]-boxs[j][0])*(boxs[j][3]-boxs[j][1])
            if xr/xr>th:
                return False
            j+=1
    return True

def static(dic,ilist,id):
    for i in ilist:
        if i['category'] not in dic:
            ndic={}
            ndic['count']=0
            ndic['id']=[]
            dic[i['category']]=ndic
        dic[i['category']]['count']+=1
        dic[i['category']]['id'].append(id)

def parsefile(jsonpath,imgspath):
    json_file = open(jsonpath, encoding='utf-8')
    list_file = open(imgspath, encoding='utf-8')
    imgs_list = list_file.readlines()
    data = json.load(json_file)
    cdic = {}
    length = len(imgs_list)
    i = 0
    while i < length:
        imgs_list[i] = imgs_list[i].replace('\n', '')
        i += 1
    for i in imgs_list:
        imgs = data['imgs'][i]
        static(cdic, imgs['objects'], i)
    json_file.close()
    list_file.close()
    return cdic,data

def parsefilej(jsonpath,imgspath):
    json_file = open(jsonpath, encoding='utf-8')
    list_file = open(imgspath, encoding='utf-8')
    imgs_list = json.load(list_file)
    data = json.load(json_file)
    cdic = {}
    for i in imgs_list:
        imgs = data[i]
        static(cdic, imgs['objects'], i)
    json_file.close()
    list_file.close()
    return cdic,data

def randomRotation(image,low,hig):
    random_angle = np.random.randint(low, hig)
    return image.rotate(random_angle)

def getback(backpath):
    flist=[]
    for file in os.listdir(backpath):
        flist.append(file)
    return flist

def fileter(dic,low,up):
    for i in list(dic.keys()):
        if dic[i]['count']<low or dic[i]['count']>up:
            dic.pop(i)

def objectinfo(category,box):
    boxinfo = {'category': category, 'bbox': {'xmin':box[0],'ymin':box[1],'xmax':box[2],'ymax':box[3]}}
    return boxinfo

def getmask(img):
    mask = np.asarray(img)[:, :, 0]
    mask = np.where(mask > 0, 255, 0)
    mask = Image.fromarray(mask.astype('uint8')).convert('1')
    return mask

def getadd(dicb,dica):
    for i in dica:
        print('type '+i+' add '+str(dica[i]['count']-dicb[i]['count']))

def judgexit(dic,typelist,currenttype):
    mark=False
    if dic[currenttype]['count']>999:
        mark=True
    for i in list(dic):
        if dic[i]['count']>999:
            print("count " + str(dic[i]['count'])+ "  type " + i)
            dic.pop(i)
            typelist.remove(i)
    return mark

def imghandl(bdic,backpath,info,idic,datapath):
    back=random.sample(bdic, 1)
    iback=random.sample(idic,1)
    backpath = backpath + back[0]
    ibackpath = datapath + iback[0]
    bimg=Image.open(backpath)
    ibimg = Image.open(ibackpath)
    i=iback[0].replace('.jpg', '')
    for k in info['imgs'][i]['objects']:
        box = (int(k['bbox']['xmin']), int(k['bbox']['ymin']), int(k['bbox']['xmax']), int(k['bbox']['ymax']))
        region = bimg.crop(box)
        ibimg.paste(region,box)
    bimg.close()
    return ibimg

def Rotat(dic,bdic,datapath,backpath,json_file,resultpath,imginfo,ids,idic):
    typelist=list(dic)
    count=0
    for i in typelist:
        id=dic[i]['id']
        for j in id:
            if judgexit(dic,typelist,i):
                break
            file=datapath+j+'.jpg'
            imgf=Image.open(file)
            info1 = {}
            info1['id'] = j + 'rotar'+str(count)
            info1['path'] = 'enhance/' + info1['id']+".jpg"
            info1['objects'] = []
            info2 = {}
            info2['id'] = j + 'rotal'+str(count)
            info2['path'] = 'enhance/' + info1['id']+".jpg"
            info2['objects'] = []
            for k in json_file[j]['objects']:
                if k['category'] in dic and k['category'][0]=='w':
                    box=(int(k['bbox']['xmin']),int(k['bbox']['ymin']),int(k['bbox']['xmax']),int(k['bbox']['ymax']))
                    info1['objects'].append(objectinfo(k['category'], box))
                    info2['objects'].append(objectinfo(k['category'], box))
                    region=imgf.crop(box)
                    regionr=randomRotation(region,-20,-5)
                    regionl=randomRotation(region,5,20)
                    maskr = getmask(regionr)
                    maskl = getmask(regionl)
                    imgb1.paste(regionr,box,maskr)
                    imgb2.paste(regionl,box,maskl)
                    dic[k['category']]['count']+=2
            if len(info2['objects'])>0:
                imginfo[info1['id']] = info1
                imginfo[info2['id']] = info2
                ids.append(info1['id'])
                ids.append(info2['id'])
                imgb1.save(resultpath + '/' + info1['id'] + '.jpg')
                imgb2.save(resultpath + '/' + info2['id'] + '.jpg')
                count += 1
            imgf.close()

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

def randomZ(img,n):
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    m = int((img.shape[0] * img.shape[1]) * n)
    for a in range(m):
        i = int(np.random.random() * img.shape[1])
        j = int(np.random.random() * img.shape[0])
        c=np.random.randint(0,255,3)
        if img.ndim == 2:
            img[j, i] = c[0]
        elif img.ndim == 3:
            img[j, i, 0] = c[0]
            img[j, i, 1] = c[1]
            img[j, i, 2] = c[2]
    image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return image

def Gaussian(dic,bdic,datapath,backpath,json_file,resultpath,imginfo,ids,idic):
    typelist = list(dic)
    count=0
    for i in typelist:
        id = dic[i]['id']
        for j in id:
            if judgexit(dic,typelist,i):
                break
            file = datapath + j+'.jpg'
            imgf = Image.open(file)
            info1 = {}
            info1['id'] = j + 'Gaussian1'+str(count)
            info1['path'] = 'enhance/' + info1['id']+".jpg"
            info1['objects'] = []
            info2 = {}
            info2['id'] = j + 'Gaussian2' + str(count)
            info2['path'] = 'enhance/' + info2['id'] + ".jpg"
            info2['objects'] = []
            for k in json_file[j]['objects']:
                if k['category'] in dic and k['category'][0]=='w':
                    box = (int(k['bbox']['xmin']), int(k['bbox']['ymin']), int(k['bbox']['xmax']), int(k['bbox']['ymax']))
                    info1['objects'].append(objectinfo(k['category'], box))
                    info2['objects'].append(objectinfo(k['category'], box))
                    dic[k['category']]['count'] += 2
                else:
                    pad(k['bbox'], imgf)
            if len(info1['objects']) > 0:
                img1 = randomGaussian(imgf,0.06)
                #img2 = randomZ(imgf,0.04)
                imginfo[info1['id']] = info1
                ids.append(info1['id'])
                img1.save(resultpath + '/' + info1['id'] + '.jpg')
                imginfo[info2['id']] = info2
                ids.append(info2['id'])
                #img2.save(resultpath + '/' + info2['id'] + '.jpg')
                count += 1
            imgf.close()

def randomColor(image):
    random_factor = np.random.randint(0, 6) / 10.  # 随机因子
    color_image = ImageEnhance.Color(image).enhance(random_factor)  # 调整图像的饱和度
    random_factor = np.random.randint(10, 14) / 10.  # 随机因子
    brightness_image = ImageEnhance.Brightness(color_image).enhance(random_factor)  # 调整图像的亮度
    random_factor = np.random.randint(10, 14) / 10.  # 随机因1子
    contrast_image = ImageEnhance.Contrast(brightness_image).enhance(random_factor)  # 调整图像对比度
    random_factor = np.random.randint(0, 6) / 10.  # 随机因子
    return ImageEnhance.Sharpness(contrast_image).enhance(random_factor)  # 调整图像锐度

def fillback(bdic,backpath,dboxs,img):
    back = random.sample(bdic, 1)
    backpath = backpath + back[0]
    bimg = Image.open(backpath)
    for i in dboxs:
        region = bimg.crop(i)
        img.paste(region,i)
    return img

def Color(dic,bdic,datapath,backpath,json_file,resultpath,imginfo,ids,idic):
    typelist = list(dic)
    count=0
    for i in typelist:
        id=dic[i]['id']
        for j in id:
            if judgexit(dic,typelist,i):
                break
            file=datapath+j+'.jpg'
            imgf=Image.open(file)
            info1 = {}
            info1['id'] = j + 'color1'+str(count)
            info1['path'] = 'enhance/' + info1['id']+".jpg"
            info1['objects'] = []
            info2 = {}
            info2['id'] = j + 'color2'+str(count)
            info2['path'] = 'enhance/' + info1['id']+".jpg"
            info2['objects'] = []
            for k in json_file[j]['objects']:
                if k['category'] in dic and k['category'][0]=='w':
                    box=[int(k['bbox']['xmin']),int(k['bbox']['ymin']),int(k['bbox']['xmax']),int(k['bbox']['ymax'])]
                    info1['objects'].append(objectinfo(k['category'], box))
                    #info2['objects'].append(objectinfo(k['category'], box))
                    dic[k['category']]['count']+=1
                else:
                    pad(k['bbox'], imgf)
            if len(info1['objects'])>0:
                imgb1 = randomColor(imgf.copy())
                #imgb2 = randomColor(imgf.copy())
                imginfo[info1['id']] = info1
                #imginfo[info2['id']] = info2
                ids.append(info1['id'])
                #ids.append(info2['id'])
                imgb1.save(resultpath + '/' + info1['id'] + '.jpg')
                #imgb2.save(resultpath + '/' + info2['id'] + '.jpg')
                count += 1
            imgf.close()



def resize(dic,bdic,datapath,backpath,json_file,resultpath,imginfo,ids,idic):
    typelist = list(dic)
    count=0
    for i in typelist:
        id=dic[i]['id']
        for j in id:
            if judgexit(dic,typelist,i):
                break
            file=datapath+j+'.jpg'
            imgf=Image.open(file)
            img=imghandl(bdic,backpath,json_file,idic,datapath)
            info = {}
            info['id'] = j + 'resize'+str(count)
            info['path'] = 'enhance/' + info['id']+".jpg"
            info['objects'] = []
            boxs=[]
            for k in json_file['imgs'][j]['objects']:
                if k['category'] in dic:
                    box=[int(k['bbox']['xmin']),int(k['bbox']['ymin']),int(k['bbox']['xmax']),int(k['bbox']['ymax'])]
                    region=imgf.crop(box)
                    region=randomresize(region,20)
                    rw, rh=region.size
                    box=getnlocation(box,rw,rh)
                    boxs.append(box)
                    info['objects'].append(objectinfo(k['category'], box))
                    img.paste(region,[box[0],box[1]])
                    dic[k['category']]['count']+=1
            if jdre(boxs) and len(boxs)>0:
                imginfo[info['id']] = info
                ids.append(info['id'])
                img.save(resultpath + '/' + info['id'] + '.jpg')
                count += 1
            else:
                for k in json_file['imgs'][j]['objects']:
                    if k['category'] in dic:
                        dic[k['category']]['count'] -= 1
            img.close()
            imgf.close()

def getscale():
    scale=[ random.uniform(0,0.1), random.uniform(0,0.1),random.uniform(0.9,1),random.uniform(0,0.1),random.uniform(0,0.1),random.uniform(0.9,1)]
    return scale

def spinning(img,scale):
    cimg = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    rows, cols, ch = cimg.shape
    src = np.float32([[0, 0], [cols - 1, 0], [0, rows - 1]])
    des = np.float32([[cols * scale[0], rows * scale[1]], [cols * scale[2], rows * scale[3]], [cols * scale[4], rows * scale[5]]])
    M = cv2.getAffineTransform(src, des)
    dst = cv2.warpAffine(cimg, M, (cols, rows))
    image = Image.fromarray(cv2.cvtColor(dst, cv2.COLOR_BGR2RGB))
    return image,des

def getlocation(location,box):
    location=np.array(location)
    min=np.min(location,axis=0)
    max=np.max(location,axis=0)
    result=[min[0]+box[0],min[1]+box[1],max[0]+box[0],max[1]+box[1]]
    return result

def createback(bidc,backpath,suffix):
    filename='back'
    count=0
    for i in bidc:
        path=backpath+i
        img=Image.open(path)
        imgn=randomColor(img)
        imgn.save(backpath+'/'+filename+str(count)+suffix+'.jpg')
        count+=1

def randomspinning(dic,bdic,datapath,backpath,json_file,resultpath,imginfo,suffix,ids,idic):
    typelist = list(dic)
    count=0
    for i in typelist:
        id=dic[i]['id']
        for j in id:
            if judgexit(dic,typelist,i):
                break
            file=datapath+j+'.jpg'
            imgf=Image.open(file)
            imgb=imghandl(bdic,backpath,json_file,idic,datapath)
            info = {}
            info['id'] = j + 'sping'+suffix+str(count)
            info['path'] = 'enhance/' + info['id']+".jpg"
            info['objects'] = []
            scale=getscale()
            for k in json_file['imgs'][j]['objects']:
                if k['category'] in dic:
                    box=(int(k['bbox']['xmin']),int(k['bbox']['ymin']),int(k['bbox']['xmax']),int(k['bbox']['ymax']))
                    region=imgf.crop(box)
                    region,location=spinning(region,scale)
                    mask=getmask(region)
                    info['objects'].append(objectinfo(k['category'],getlocation(location,box)))
                    imgb.paste(region,box,mask)
                    dic[k['category']]['count']+=1
            if len(info['objects'])>0:
                imginfo[info['id']] = info
                ids.append(info['id'])
                imgb.save(resultpath + '/' + info['id'] + '.jpg')
                count += 1
            imgf.close()

def transform(datapath,info,result_path):
            info=getjson(info)
            file_list=os.listdir(datapath)
            ids=[]
            for i in file_list:
                ids.append(os.path.splitext(i)[0])
            voc={}
            for i in ids:
                voc[i]=info[i]
            writejson(os.path.join(result_path,'tids.json'),ids)
            writejson(os.path.join(result_path, 'tvoc.json'), voc)


def enhance(dic,bdic,datapath,backpath,resultpath,imginfo,json_file,ids,idic):
    Color(dic, bdic, datapath, backpath, json_file, resultpath, imginfo, ids, idic)
    print('\n\n===============    Color    ================\n\n')
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '\n\n\n')
    # resize(dic, bdic, datapath, backpath, json_file, resultpath, imginfo, ids, idic)
    # print('\n\n===============    resize    ================\n\n')
    # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '\n\n\n')
    #Rotat(dic, bdic, datapath, backpath, json_file, resultpath, imginfo, ids, idic)
    #print('\n\n===============    Rotat    ================\n\n')
    # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '\n\n\n')
    Gaussian(dic,bdic,datapath,backpath,json_file,resultpath,imginfo,ids,idic)
    print('\n\n===============    Gaussian    ================\n\n')
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '\n\n\n')
    # Gaussian(dic,bdic,datapath,backpath,json_file,resultpath,imginfo,ids,idic)
    # print('\n\n===============    Gaussian    ================\n\n')
    # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '\n\n\n')
    # randomspinning(dic, bdic, datapath, backpath, json_file, resultpath, imginfo, '2', ids,idic)
    # print('\n\n===============    randomspinning2    ================\n\n')
    # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '\n\n\n')

   # Gaussian(dic, datapath, json_file, resultpath, imginfo,ids,idic)

def generatefilelist(path,resultpath):
    filelist = os.listdir(path)
    imgs_list=[]
    for i in filelist:
        imgs_list.append(i[:-4])
    filelist=json.dumps(imgs_list)
    fids = open(resultpath+'/'+'ids.json', 'w')
    fids.write(filelist)
    fids.close()

def shrink(datapath,idspath,imginfo,resultpath,path):
    fimginfo=open(imginfo)
    fids=open(idspath)
    ids=json.load(fids)
    imginfo=json.load(fimginfo)
    info={}
    for i in ids:
        filepath=datapath+i+'.jpg'
        img=Image.open(filepath)
        w, h = img.size
        infoitem={}
        infoitem['id']=i
        infoitem['objects'] = []
        for k in imginfo[i]['objects']:
            box = [int(k['bbox']['xmin']*0.75), int(k['bbox']['ymin']*0.75), int(k['bbox']['xmax']*0.75), int(k['bbox']['ymax']*0.75)]
            infoitem['objects'].append(objectinfo(k['category'],box))
        info[i] = infoitem
        imgn = img.resize((int(w *0.75), int(h *0.75)))
        imgn.save(resultpath + '/' + i + '.jpg')
    finfo = open(resultpath+"\\info.json", 'w')
    info=json.dumps(info)
    finfo.write(info)
    finfo.close()

def getjson(infopath):
    infofile1=open(infopath)
    info1=json.load(infofile1)
    infofile1.close()
    return info1
# result,json_file=parsefilej("F:\\ndata\\1280\\info.json","F:\\ndata\\1280\\ids.json")
# #json_file=getjson('F:\\ndata\\1280\\info.json')
# dic=result.copy()
# fileter(dic,0,1000)
# backpath='F:\\data\\background\\'
# datapath='F:\\ndata\\1280\\720\\'
# resultpath="F:\\ndata\\1280\\enhance"
# bdic=getback(backpath)
# #idic=getback('F:\\data\\select')
# idic={}
# imginfo={}
# ids=[]
# #dicb=dic.copy()
# print(len(dic))
# enhance(dic,bdic,datapath,backpath,resultpath,imginfo,json_file,ids,idic)
# # #resize(dic,bdic,datapath,backpath,json_file,resultpath,imginfo,ids)
# # # print(len(dic))
# # #getadd(dicb,dic)
# info=json.dumps(imginfo)
# idsj=json.dumps(ids)
# finfo=open("F:\\ndata\\1280\\enhance\\sinfo.json",'w')
# fids=open("F:\\ndata\\1280\\enhance\\sids.json",'w')
# finfo.write(info)
# finfo.close()
# fids.write(idsj)
# fids.close()
shrink('F:\\data\\test\\',"F:\\data\\ninfo\\tids.json","F:\\data\\ninfo\\tvoc.json","F:\data\\0.75\\test",'train')

#transform('F:\\data\\test','F:\\data\\annotations.json','F:\\data\\ninfo')


# w,h=region.size
#                     if w<20 and h<20:
#                         region = randomresize(region, 20)
#                         rw, rh = region.size
#                         box = getnlocation(box, rw, rh)
#                     info1['objects'].append(objectinfo(k['category'], box))
#                     info2['objects'].append(objectinfo(k['category'], box))
#                     try:
#                         imgb1.paste(region,box)
#                         imgb2.paste(region,box)
#                     except:
#                         print(file,'\n',box,'\n',k['category'],'\n',rw,rh)
#                         print(json_file['imgs'][j]['objects'])
#                     dic[k['category']]['count']+=2
#             if jdre(boxs) and len(info1['objects'])>0:
#                 imgb1 = randomColor(imgb1)
#                 imgb2 = randomColor(imgb2)
#                 imginfo[info1['id']] = info1
#                 imginfo[info2['id']] = info2
#                 ids.append(info1['id'])
#                 ids.append(info2['id'])
#                 imgb1.save(resultpath + '/' + info1['id'] + '.jpg')
#                 imgb2.save(resultpath + '/' + info2['id'] + '.jpg')
#                 count += 1
#             else:
#                 for k in json_file['imgs'][j]['objects']:
#                     if k['category'] in dic:
#                         dic[k['category']]['count'] -= 2