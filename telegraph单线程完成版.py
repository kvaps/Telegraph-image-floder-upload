# -*- coding: UTF-8 -*-
from telegraph import Telegraph
import requests ,sys ,os ,re

#这部分是代理配置，可根据需要更改
proxies = {
    'http': 'socks5://:@127.0.0.1:1080',
    'https': 'socks5://:@127.0.0.1:1080'
}


telegraph = Telegraph()
telegraph.create_account(short_name='8215')


#初始化输出文件
output_file = sys.argv[0]+'.txt'
imghtml_all = ""

def takeFirst(elem):
    return elem[1]

def sorted_aphanumeric(data):#用来进行按自然数排序的文件上传，避免出现1-10-11-...-2-20-21此类问题
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)

def isImg(f):
    f = str(f)
    if os.path.isdir(f):return '0'
    filename = f[f.rfind("."):]
    if filename == '.jpg':
        return 'image/jpg'
    if filename == '.jpeg':
       return 'image/jpeg'
    if filename == '.png':
       return 'image/png'
    else:
       return '0'

def tgImgUp(f):
    i = 0
    fstr = isImg(f)
    if fstr =='0':
        return '0'
    else:
        while i<5:
            try:
                path = requests.post('https://telegra.ph/upload',files={'file':
                                                                         ('file',open(f,'rb'),fstr)},timeout = 15).json()
            except:
                i+=1
                print("Upload error!({}/5)".format(i))
            else:
                if str(path).find('error') == -1:
                    print(f,path,'success')
                    break
                else:
                    print('file empty error!({}/5)'.format(i))
                    print(f)
                    i+=1
        pathstr = str(path)
        imgdir = 'https://telegra.ph'+pathstr[10:-3]
        imghtml = "<img src = "+imgdir+"/>"
        return imghtml

def tgLink(title,html):
    try:
        response = telegraph.create_page(
            title,
            html_content=html,
        )
    except:
        input('tgLinkError')
        tgLink(title,html)
    return response

def htmlGen(path):
    img_html = str(tgImgUp(path))
    return img_html


for arg in sys.argv:
    if arg == sys.argv[0]:continue
    title = os.path.basename(arg)
    if os.path.isdir(arg):
        sorted_list = sorted_aphanumeric(os.listdir(arg))
        for temp in sorted_list:
            html = htmlGen(os.path.join(arg,temp))
            imghtml_all = imghtml_all + html
    else:
        break
    response = tgLink(title,imghtml_all)
    print('https://telegra.ph/{}'.format(response['path']))
    imghtml_all = ""
    with open (output_file,'a') as f:
        f.write('https://telegra.ph/{}'.format(response['path']))
        f.write('\n')



with open (output_file,'a') as f :
    f.write('本次脚本运行结束，此后将会追加写入下次的路径\n')
