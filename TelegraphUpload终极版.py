# -*- coding: utf-8 -*-
from telegraph import Telegraph
import requests ,sys ,time ,os ,re ,traceback,math
from PIL import Image

proxies = {
    'http': 'socks5://:@127.0.0.1:7451',
    'https': 'socks5://:@127.0.0.1:7451'
}

telegraph = Telegraph()
telegraph.create_account(short_name='8215')


#初始化输出文件
output_file = sys.argv[0] + '.txt'
output_log = sys.path[0] + '\\telegraph_log.txt'


def takeFirst(elem):
    return elem[0]

#用来进行按自然数排序的文件上传，避免出现1-10-11-...-2-20-21此类问题
def sorted_aphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)

    
def fsize(f):
    q = 95
    size = os.path.getsize(f)
    savepath = f
    img =Image.open(f)
    img = img.convert("RGB")
    imgname = f[f.rfind("\\"):]
    if (img.width*img.height>24000000):
        savepath = sys.path[0] + "\\$temp$" +imgname+ ".jpg"
        resize_parament = math.sqrt(24000000/(img.width*img.height))
        resize_width = int(round(img.width*resize_parament))
        resize_height = int(round(img.height*resize_parament))
        img = img.resize((resize_width,resize_height),Image.ANTIALIAS)
        img = img.convert("RGB")
        img.save(savepath,quality = 95)
        size = os.path.getsize(savepath)
        print("dimensions too large,resize to 24MP")
    while size>= (5*1024*1024):
        savepath = sys.path[0] + "\\$temp$" +imgname+ ".jpg"
        img.save(savepath,quality = q)
        size = os.path.getsize(savepath)
        q -= 5
        print("This file has been compressed,size is",size)
    return savepath

#判断是否为图片文件，如是图片文件即可上传
def isImg(f):
    f = str(f)
    if os.path.isdir(f):return '0'
    filename = f[f.rfind("."):]
    #print(f,filename)
    if filename == '.jpg':
        return 'image/jpg'
    if filename == '.jpeg':
       return 'image/jpeg'
    if filename == '.png':
       return 'image/png'
    else:
       return '0'


def tgImgUp(pathq):
    i = 0
    fstr = isImg(pathq)
    pathq = fsize(pathq)
    if fstr =='0':
        return print('not image')
    else:
        while True:
            try:
                path = requests.post('https://telegra.ph/upload',files={'file':
                                                                      ('file',open(pathq,"rb"),fstr)},timeout = 10).json()
            except  Exception:
                print("network error")
            else:
                if str(path).find('error') == -1:
                    print(path,'success')
                    pathstr = str(path)
                    imgdir = 'https://telegra.ph'+pathstr[10:-3]
                    imghtml = "<img src = "+imgdir+"/>"
                    return [imghtml]
                else:
                    print(path)


def tgLink(title,html):
    if html == "":return "No File Uploaded"
    try:
        response = telegraph.create_page(
            title,
            html_content=html,
        )
    except:
        print('Function tgLink error')
        tgLink(title,html)
    return response

    
def pathEnter(DIR):
     if len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))]) == 0 and len([name for name in os.listdir(DIR) if os.path.isdir(os.path.join(DIR, name))]) ==1 :
        path = os.listdir(DIR)
        return pathEnter(os.path.join(DIR,path[0]))
     else:
        return DIR
#test_argv = [r"Z:\本子\[TVKD]C95_Content_1\Touhou\(C95) [somnia (Hajin)] てゐと一晩中 (東方Project) [中国翻訳]",r"Z:\本子\[TVKD]C95_Content_1\Touhou\(C95) [あんみつよもぎ亭 (みちきんぐ)] 居眠り上手の大図書館 (東方Project) [中国翻訳]",r"Z:\本子\[TVKD]C95_Content_1\Touhou\(C95) [ドットエイト (さわやか鮫肌)] フランちゃんとすけべする本 (東方Project) [中国翻訳]"]
if __name__ == "__main__":
    upload_mark = False
    if not os.path.isdir(sys.path[0] +"\\$temp$"):
        os.mkdir(sys.path[0]+"\\$temp$")
    print('start...')
    for arg in sys.argv:
        if arg == sys.argv[0]:continue
        title = os.path.basename(arg)
        img = []
        if os.path.isdir(arg):
            with open(output_log,"r") as f:
                for line in f:
                    #print(str(arg),str(line))
                    if str((arg)+'\n') == str(line):
                        print(arg,"has been skipped")
                        upload_mark = True
            if upload_mark ==True:
                upload_mark == False
                continue
            for temp in sorted_aphanumeric(os.listdir(pathEnter(arg))):
                img.append(tgImgUp(os.path.join(pathEnter(arg),temp)))
        else:
            break
        print('upload final')
        with open(output_log,'a') as f:
            f.write(str(arg)+'\n')
        value = img
        imghtml_all = ""
        for arg in value:
            temp = str(arg)
            temp = temp[temp.find("<"):temp.find(">")+1]
            imghtml_all = imghtml_all + temp
        response = tgLink(title,imghtml_all)
        if response == "No File Uploaded":
            input('No file Uploaded,waiting for input')
        else:
            print('https://telegra.ph/{}'.format(response['path']))
            imghtml_all = ""
            with open (output_file,'a') as f:
                f.write('https://telegra.ph/{}'.format(response['path']))
                f.write('\n')
    with open (output_file,'a') as f :
        f.write('\n')
    input('Upload over,press enter to exit.')
