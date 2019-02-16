# -*- coding: UTF-8 -*-
from telegraph import Telegraph
import requests ,sys ,time ,os ,re ,multiprocessing
from multiprocessing import Process, Queue ,Pool

#这部分是代理配置，可根据需要更改
proxies = {
    'http': 'socks5://:@127.0.0.1:1080',
    'https': 'socks5://:@127.0.0.1:1080'
}


telegraph = Telegraph()
telegraph.create_account(short_name='8215')


#初始化输出文件
output_file = sys.argv[0] + '.txt'
output_log = sys.argv[0] + 'log.txt'


def takeFirst(elem):
    return elem[0]

#用来进行按自然数排序的文件上传，避免出现1-10-11-...-2-20-21此类问题
def sorted_aphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)


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


def tgImgUp(pathq,num,queue):
    i = 0
    fstr = isImg(pathq)
    if fstr =='0':
        return print('not image')
    else:
        while True:
            try:
                path = requests.post('https://telegra.ph/upload',files={'file':
                                                                         ('file',open(pathq,'rb'),fstr)},timeout = 15).json()
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
            finally:
                print('final',path)
                pathstr = str(path)
                imgdir = 'https://telegra.ph'+pathstr[10:-3]
                imghtml = "<img src = "+imgdir+"/>"
                queue.put([num,imghtml])

def tgLink(title,html):
    if html == "":return print("No File Uploaded")
    try:
        response = telegraph.create_page(
            title,
            html_content=html,
        )
    except:
        input('tgLinkError,Press Enter to continue')
        tgLink(title,html)
    return response


if __name__ == "__main__":
    for arg in sys.argv:
        print('start...')
        if arg == sys.argv[0]:continue
        title = os.path.basename(arg)
        manager = multiprocessing.Manager()
        queue = manager.Queue()
        p = Pool(16)
        print('Pool start success')
        if os.path.isdir(arg):
            for temp in sorted_aphanumeric(os.listdir(arg)):
                i = sorted_aphanumeric(os.listdir(arg))
                i = i.index(temp)
                p.apply_async(tgImgUp ,args = (os.path.join(arg,temp),i,queue,))
        else:
            break
        p.close() 
        p.join()
        print('upload final')
        value = []
        imghtml_all = ""
        while True:
            if not queue.empty():
                value.append(queue.get(False))
            else:
                break
        value.sort(key = takeFirst)
        #print(value)
        for arg in value:
            temp = str(arg)
            temp = temp[temp.find("<"):temp.find(">")+1]
            imghtml_all = imghtml_all + temp
        response = tgLink(title,imghtml_all)
        print('https://telegra.ph/{}'.format(response['path']))
        imghtml_all = ""
        print(value)
        with open (output_file,'a') as f:
            f.write('https://telegra.ph/{}'.format(response['path']))
            f.write('\n')
    with open (output_file,'a') as f :
        f.write('本次脚本运行结束，此后将会追加写入下次的路径\n')
    input('Upload over,press enter to exit.')
