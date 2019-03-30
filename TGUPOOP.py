# -*- coding: utf-8 -*-
import datetime
import math
import numpy
import os
import re
import requests
import sys
import traceback
import json
import urllib
from urllib import request
from urllib.parse import quote
import string
from multiprocessing import Pool
from PIL import Image
from telegraph import Telegraph

# 设定telegraph超时的值
telegraph_img_upload_timeout = 30
# 初始化输入输出文件
output_file = sys.argv[0] + '.json'
output_log = os.path.join(sys.path[0], "telegraph_log.txt")
jimaku_file = os.path.join(sys.path[0], "jimaku_dhash.txt")
error_log = os.path.join(sys.path[0], "errors_log.txt")
config_file = os.path.join(sys.path[0], "config.json")
chinese_flag = False

if os.path.isfile(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.loads(f.read(), encoding='utf-8')
    telegraph = Telegraph(access_token=config['token'])
else:
    telegraph = Telegraph()


def initialize_method():
    if not os.path.isfile(config_file):
        print("尚未获取token，启动token获取方法，加*为必填项")
        short_name = ""
        while short_name == "":
            short_name = input("Please enter short name*:")
        author_name = input("Please enter author name:")
        author_url = input("Please enter author url:")
        telegraph.create_account(short_name=short_name, author_name=author_name, author_url=author_url)
        config_content = telegraph.get_account_info(['short_name', 'author_name', 'author_url'])
        config_content['token'] = telegraph.get_access_token()
        with open(config_file, 'w', encoding='utf-8')as file:
            file.write(json.dumps(config_content, indent=4, separators=(',', ': '), ensure_ascii=False))


# 初始化文件及文件夹所必要的函数
def create_file():
    def cre_file(file):
        if not os.path.isfile(file):
            opl = open(file, 'w')
            opl.close()

    cre_file(output_file)
    cre_file(jimaku_file)
    cre_file(error_log)
    if not os.path.isdir(os.path.join(sys.path[0], "$temp$")):
        os.makedirs(os.path.join(sys.path[0], "$temp$"))


create_file()
# 初始化文件及文件夹，无则创建一个

# 初始化字幕哈希表
jimaku_set_global = set()
with open(jimaku_file)as f:
    for line in f:
        jimaku_set_global.add(line)
# 初始化log文件哈希表
output_log_set = set()
with open(output_file, "r", encoding='utf-8') as f:
    for line in f:
        output_log_set.add(json.loads(line, encoding='utf-8')['basename'])
#
# #初始化图片哈希表
# all_dhsh_set = set()
# with open(all_dhsh_file,'r') as f:
#     for line in f :
#         all_dhsh_set.add(line)
#

# 初始化汉化组名称list
hanhua_list = ['CE家', '汉化', '漢化', '中文', 'chinese']


# 按照自然数排序文件
def sorted_aphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(data, key=alphanum_key)


# 进入相应的文件夹
def path_enter(folder):
    if os.path.isfile(folder):
        raise NotADirectoryError("Method path_enter error:argument is file")
    sub_folders = [file for file in os.listdir(folder) if is_img_folder(os.path.join(folder, file))]
    while len(sub_folders) == 1 and os.path.isdir(os.path.join(folder, sub_folders[0])):
        folder = os.path.join(folder, sub_folders[0])
    return folder


# 过滤非图片文件
def file_filter(folder):
    temp = []
    for file in sorted_aphanumeric(os.listdir(folder)):
        temp.append(os.path.join(folder, file))
    return list(filter(is_img, temp))


# 进入单个文件夹时不受非图片文件干扰
def is_img_folder(folder):
    if os.path.isdir(folder):
        return True
    if os.path.splitext(folder)[1].lower() in (".jpg", ".jpeg", ".png"):
        return True
    else:
        return False


# 过滤非图片文件所调用的函数
def is_img(file):
    if os.path.isdir(file):
        return False
    if os.path.splitext(file)[1].lower() in (".jpg", ".jpeg", ".png"):
        return True


# 文件压缩及图片识别主方法
def file_main_method(folder):
    per_upload_folder = path_enter(folder)
    if per_upload_folder == "":
        raise FileNotFoundError("File main method error:No folder in args")
    pre_upload_files = file_filter(per_upload_folder)
    checked_files = [file for file in list(map(img_main_check, pre_upload_files)) if file != ""]
    img_count = len(checked_files)
    if checked_files == 0:
        raise FileNotFoundError("File main method error:No image is ready to upload")
    full_color_img = [file for file in list(map(img_is_full_color, checked_files)) if file]
    if len(full_color_img) > len(checked_files) - len(full_color_img):
        full_color_mark = "全彩"
    elif 8 < len(full_color_img) < len(checked_files) - len(full_color_img):
        full_color_mark = "全彩and黑白"
    else:
        full_color_mark = "黑白"
    return checked_files, full_color_mark, img_count


# 检测是否需要压缩/是否需要删除字幕组文件，检查主入口
def img_main_check(im_file):
    if chinese_flag and classify(im_file):
        return ""
    im_file = check_pixiv(im_file)
    im_file = check_size(im_file)
    return im_file


# 检查大小主方法
def check_size(im_file):
    f_size = os.path.getsize(im_file)
    if f_size > 5242880:
        return img_compress(im_file)
    else:
        return im_file


# 检查图片尺寸主方法
def check_pixiv(im_file):
    imgname = os.path.basename(im_file)
    img = Image.open(im_file)
    img_w = img.width
    img_h = img.height
    resize_switch = False
    if img_w * img_h > 24000000:
        resize_paraments = math.sqrt(24000000 / (img_w * img_h))
        img_w = int(round(img_w * resize_paraments))
        img_h = int(round(img_h * resize_paraments))
        resize_switch = True
    if max(img_w, img_h) > 6000:
        resize_paraments = 6000 / max(img_w, img_h)
        img_w = int(round(img_w * resize_paraments))
        img_h = int(round(img_h * resize_paraments))
        resize_switch = True
    if resize_switch:
        return img_resize(img, img_w, img_h, imgname)
    return im_file


# 重设图片尺寸主方法
def img_resize(img, resize_width, resize_height, img_name):
    save_path = sys.path[0] + "\\$temp$\\" + img_name + "{}.jpg".format(os.getpid())
    img = img.resize((resize_width, resize_height), Image.ANTIALIAS)
    img = img.convert("RGB")
    img.save(save_path, quality=95, optimize=True)
    return save_path


# 压缩图片主方法
def img_compress(im_file):
    q = 95
    imgname = os.path.basename(im_file)
    img = Image.open(im_file)
    size = os.path.getsize(im_file)
    savepath = sys.path[0] + "\\$temp$\\" + imgname + "{}.jpg".format(os.getpid())
    while size >= (5 * 1024 * 1024):
        img = img.convert("RGB")
        img.save(savepath, quality=q, optimize=True)
        size = os.path.getsize(savepath)
        q -= 5
        print("This file has been compressed,size is {:.2f} MB".format(size / 1048576))
    return savepath


# 切割文本以及返回
def split_del(s):
    skip_flag = False
    lit = re.split(r'([\[\]()【】（）])', s)
    for i in lit:
        for j in hanhua_list:
            if re.search(j.lower(), i.lower()):
                lit.pop(lit.index(i) + 1)
                lit.pop(lit.index(i) - 1)
                lit.pop(lit.index(i))
                skip_flag = True
                break
        if skip_flag:
            break
    lit_str = "".join(lit)
    return re.sub(" ", "", lit_str)


# telegraph上传主方法
def tg_main_method(files, title):
    print("tg main method success{}".format(os.getpid()))
    img_html_list = []
    img_paras = list(map(img_type, files))
    for file in files:
        img_para = img_paras[files.index(file)]
        img_html_list.append(tg_img_up(file, img_para))
    img_html = "".join(img_html_list)
    if chinese_flag:
        title = split_del(title)
    tg_url = tg_link(title, img_html)
    return tg_url['url']


# 返回上传所需要的img类型
def img_type(file):
    file_ext = os.path.splitext(file)[1].lower()
    if file_ext == '.jpg':
        return 'image/jpg'
    if file_ext == '.jpeg':
        return 'image/jpeg'
    if file_ext == '.png':
        return 'image/png'


# 图片上传主方法
def tg_img_up(image, img_para):
    while True:
        try:
            path = requests.post('https://telegra.ph/upload',
                                 files={'file': ('file', open(image, "rb"), img_para)},
                                 timeout=telegraph_img_upload_timeout).json()
        except (OSError, IOError):
            print('error ，pid is {}'.format(os.getpid()))
        else:
            if "error" not in str(path):
                print(path[0], 'success ，pid is {}'.format(os.getpid()))
                return "<img src=https://telegra.ph/{}/>".format(path[0]['src'])
            else:
                print(path)


# 返回本子链接
def tg_link(title, html):
    response = dict()
    if html == "":
        raise OSError("No File Uploaded")
    for i in range(5):
        try:
            response = telegraph.create_page(
                title,
                html_content=html,
            )
        except OSError:
            if i >= 4:
                raise OSError("Method tgLink error:Cannot return link")
        else:
            break
    return response


# 返回图片的dHash
def d_hash(im_file):
    img = Image.open(im_file).convert("L")
    img = img.resize((17, 16))
    img_np = numpy.array(img)
    d_hash_str = ""
    for i in range(img.width - 2):
        for j in range(img.height - 1):
            if img_np[i][j] > img_np[i + 1][j]:
                d_hash_str += "1"
            else:
                d_hash_str += "0"
    d_hash_str = hex(int(d_hash_str, 2))
    return d_hash_str + '\n'


# 检查是否为字幕组文件主方法
def classify(file):
    if chinese_flag:
        try:
            im_hash = d_hash(file)
        except OSError:
            raise
        if im_hash in jimaku_set_global:
            print("Del file{}".format(file))
            return True
        else:
            return False
    else:
        return False


# 判断图片是否为全彩图片，全彩返回True，否则返回False
def img_is_full_color(file):
    def rb(i):
        return list(map(lambda h: h[0], i))

    def rb2(i):
        return list(map(lambda h: h[1], i))

    img = Image.open(file)
    img = img.resize((8, 8))
    img = img.convert("RGB")
    img = img.convert("HSV")
    im_array = numpy.array(img)
    var_map = list(map(rb, im_array))
    var_map2 = list(map(rb2, im_array))
    fc_var = numpy.var(var_map)
    fc_avg = numpy.mean(var_map2)
    if fc_avg > 12 and fc_var > 1000:
        return True
    else:
        return False


# 获取telegraph上的HTML文件，用以计数
def get_html(dic):
    url = dic['url']
    url_dc = quote(url, safe=string.printable)
    for i in range(3):
        try:
            res = urllib.request.urlopen(url_dc)
        except OSError:
            raise OSError("get html error")
        else:
            break
    else:
        raise OSError("Method get html error:cannot get html,url:\n{}".format(dic['url']))
    html = res.read().decode("utf-8")
    img_html = html[html.find("_tl_editor"):]
    im_con_html = img_html[:img_html.find("</article>")]
    im_con = im_con_html.count("<img src=")
    title_html = html[html.find('<h1 dir="auto">') + 15:html.find("</h1>")]
    img_html = img_html[img_html.find("<img src=") + 10:]
    img_html = img_html[:img_html.find(">") - 1]
    img_html = "https://telegra.ph" + img_html
    print(img_html, im_con)
    dic['img_url'] = img_html
    dic['web_img_count'] = im_con
    dic['web_title'] = title_html
    return dic


# 解决Windows的参数传入时不支持特殊字符的情况
def path_error_method(folder):
    error_path_list = []
    if os.path.exists(folder):
        return folder
    else:
        up_path = folder
        for i in range(255):
            if not os.path.isdir(up_path):
                error_path_list.append(os.path.basename(up_path))
                up_path = os.path.dirname(up_path)
            else:
                break
        else:
            raise NotADirectoryError("This argument is not a dir")
        error_path_list.reverse()
        for error_dir in error_path_list:
            path_list = []
            subbed_list = []
            for folder in os.listdir(up_path):
                path_list.append(os.path.join(up_path, folder))
            for folder in path_list:
                subbed_list.append(re.sub(r'[\W]', '', os.path.basename(folder)))
            fixed_path = re.sub(r'[\W]', '', os.path.basename(error_dir))
            for i in subbed_list:
                if fixed_path == i:
                    up_path = path_list[subbed_list.index(i)]
                    print(up_path)
                    break
            else:
                raise OSError("Method path error method error:Unknown error")
        return up_path


# 多进程主方法，程序的入口,错误处理中心
def main_up(folder):
    try:
        folder = path_error_method(folder)
        basename = os.path.basename(folder)
        if basename in output_log_set:
            raise FileExistsError("Method main up error:This folder has been uploaded,will be skipped.")
        pre_up_files = file_main_method(folder)
        print("图片处理完成，开始上传")
        tg_url = tg_main_method(pre_up_files[0], basename)
        print(tg_url)
        dic = {
            'url': tg_url,
            'path': folder,
            'basename': basename,
            'mark': pre_up_files[1],
            'img_url': '',
            'web_img_count': '',
            'web_title': '',
            'img_count': pre_up_files[2],
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        dic = get_html(dic)
        with open(output_file, 'a', encoding='utf-8') as file:
            file.write(json.dumps(dic, ensure_ascii=False) + '\n')
    except (OSError, IOError, TypeError, ValueError) as e:
        print(e)
        traceback.print_exc()
        with open(error_log, 'a', encoding='utf-8') as log:
            log.write("{0}{1}{0}\n".format('■' * 30 + '\n', traceback.format_exc()))


if __name__ == "__main__":
    try:
        initialize_method()
    except OSError:
        os.remove(config_file)
        input("程序初始化出现错误,请尝试重新启动.\n若仍出现问题，请尝试将本程序放入空文件夹内，按回车键退出.")
        exit(325)
    if len(sys.argv) > 1:
        print("main process start")
        p = Pool()
        print("pool start...")
        for arg in sys.argv:
            if arg == sys.argv[0]:
                continue
            p.apply_async(main_up, args=(arg,))
        p.close()
        p.join()
        print("upload final")
        input("waiting for input")
    else:
        inp = input("输入info获取信息,输入list获取所有的文章列表")
        if inp == "info":
            print(telegraph.get_account_info(['short_name', 'author_name',
                                              'author_url', 'auth_url', 'page_count']))
            print(telegraph.get_access_token())
        if inp == "list":
            offset = 0
            while True:
                page_list = telegraph.get_page_list(offset, 10)
                print("共有{total}篇文章，目前显示的是{page_s}-{page_e}页".format(total=page_list['total_count'], page_s=offset + 1,
                                                                     page_e=offset + 10))
                pages = page_list['pages']
                for args in pages:
                    for key, value in args.items():
                        print("{}:{}".format(key, value))
                    print("")
                flag = input("输入n下一页，输入b上一页，输入q退出")
                if flag == "q":
                    break
                elif flag == "n":
                    if offset + 10 > page_list['total_count']:
                        print("到头了")
                    else:
                        offset += 10
                elif flag == "b":
                    if offset >= 10:
                        offset -= 10
                    else:
                        print("到头了")
                else:
                    print("请输入正确的字母")
                os.system("cls")
        input()
