# -*- coding: utf-8 -*-
import re
import shutil
import MeCab
from snownlp import SnowNLP
import matplotlib.pyplot as plt
from wordcloud import WordCloud, ImageColorGenerator
import PIL.Image as Image
import numpy as np
import jieba
import jieba.analyse
import cx_Oracle
import os
from datetime import datetime
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from sentiment_parse import sentinment_parse_main
# nltk.download('punkt')
# nltk.download('stopwords')

# 数据库连接
# dsnStr = cx_Oracle.makedsn("192.168.110.214", 1521, "HORNEIP")  # 测试库
dsnStr = cx_Oracle.makedsn("192.168.110.205", 1521, "EIP")
conn = cx_Oracle.connect("EIP", "EIP", dsnStr)
c = conn.cursor()

# 每个产品关键词最小评论数量
min_num = 3
# 每个产品返回关键词的数量
topK = 10
# 日文停用词
JaStopWords = '''】【( )＿・）（★」「.1234567890、。がガがガぎギぐグげゲごゴざザざザじジずズぜゼぞゾだダだダぢヂづヅでデどドばバばバびビぶブべベぼボぱパぱパぴピぷプぺペぽポ
あアあアいイうウえエおオかカかカきキくクけケこコさサさサしシすスせセそソたタたタちチつツてテとトなナなナにニぬヌねネのノはハ
はハひヒふフへヘほホまマまマみミむムめメもモやヤやヤゆユよヨらラらラりリるルれレろロわワわワをヲ'''


# 加入新停用词(英文)
def EnStopWords():
    En_list = []
    f = open("stop_words\\stop_en.txt", "r").readlines()
    for i in f:
        En_list.append(i.strip())
    return En_list


# 查询出所有sku_id
def sku_ids():
    # sql = "select distinct SKU_CODE, SKU_ID, ECOMMERCE_CODE from ECOMMERCE_SKU_DETAIL"
    sql = "select distinct SKU_CODE, SKU_ID, ECOMMERCE_CODE from ECOMMERCE_SKU_DETAIL where ECOMMERCE_CODE=6"
    # sql = "select distinct SKU_CODE, SKU_ID, ECOMMERCE_CODE from ECOMMERCE_SKU_DETAIL where REGEXP_LIKE(ECOMMERCE_CODE, '^3.*')"
    res = c.execute(sql).fetchall()
    return res


# 保存关键词数据(新增)
def save_tag(tag_id, sku_id, tag, count, tag_type, sku_detail_id, code):
    create_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    sql = "insert into ECOMMERCE_REVIEW_TAG(TAG_ID, SKU_ID, TAG, TAG_COUNT, TAG_TYPE, CREATE_TIME, UPDATE_TIME, SKU_DETAIL_ID, TEXT_1) values('{}','{}', '{}', {}, {},to_date('{}','yyyy/MM/dd HH24:mi:ss'), to_date('{}','yyyy/MM/dd HH24:mi:ss'), '{}', '{}')".format(
        tag_id, sku_id, tag, count, tag_type, create_time, create_time, sku_detail_id, code)
    c.execute(sql)
    conn.commit()


# 保存关键词数据(更新)
def update_tag(tag, count, tag_id, code):
    create_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    sql = "update ECOMMERCE_REVIEW_TAG set TAG='{}', TAG_COUNT={}, UPDATE_TIME=to_date('{}','yyyy/MM/dd HH24:mi:ss'), TEXT_1='{}' where TAG_ID='{}'".format(
        tag, count, create_time, code, tag_id)
    c.execute(sql)
    conn.commit()


# 修改ECOMMERCE_REVIEW_P表字段TASK_ID(天猫)
def update_task_id(num, REVIEW_ID):
    sql = "update ECOMMERCE_REVIEW_P set TASK_ID='{}' where REVIEW_ID='{}'".format(num, REVIEW_ID)
    c.execute(sql)
    conn.commit()


# 查询数据库所有评论标题内容
def titles(sku_id):
    sql = "select review_title from ECOMMERCE_REVIEW_P where sku_id='{}'".format(sku_id)
    res = c.execute(sql).fetchall()
    rev_list = []
    for r in res:
        if r[0]:
            rev_list.append(r[0])
    format = "title.txt"
    save_txt(rev_list, format)


# 查询数据库所有评论星级
def stars(sku_id):
    sql = "select review_star from ECOMMERCE_REVIEW_P where sku_id='{}'".format(sku_id)
    res = c.execute(sql).fetchall()
    rev_list = []
    for r in res:
        rev_list.append(str(r[0]))
    format = "star.txt"
    save_txt(rev_list, format)


# 以评论关键词统计评论总数
def tag_count(sku_detail_id, tag, tag_type):
    if tag_type == 0:
        sql = "select count(*) from ECOMMERCE_REVIEW_P where sku_detail_id='{}' and REVIEW_STAR < 4 and (review_text1 like '%{}%' or review_text2 like '%{}%' or review_text3 like '%{}%' or review_text4 like '%{}%' or review_text5 like '%{}%')".format(
            sku_detail_id, tag, tag, tag, tag, tag)
        count = c.execute(sql).fetchone()
    else:
        sql = "select count(*) from ECOMMERCE_REVIEW_P where sku_detail_id='{}' and REVIEW_STAR >= 4 and (review_text1 like '%{}%' or review_text2 like '%{}%' or review_text3 like '%{}%' or review_text4 like '%{}%' or review_text5 like '%{}%')".format(
            sku_detail_id, tag, tag, tag, tag, tag)
        count = c.execute(sql).fetchone()
    return count[0]


# 以评论关键词统计评论总数(天猫)
def tag_count_TM(sku_detail_id, tag, tag_type):
    sql = "select count(*) from ECOMMERCE_REVIEW_P where sku_detail_id='{}' and TASK_ID = '{}' and (review_text1 like '%{}%' or review_text2 like '%{}%' or review_text3 like '%{}%' or review_text4 like '%{}%' or review_text5 like '%{}%')".format(
        sku_detail_id, tag_type, tag, tag, tag, tag, tag)
    count = c.execute(sql).fetchone()
    return count[0]

# 查询数据库所有评论内容并以好评论(4,5),差评(1,2,3)保存
def texts(sku_detail_id, code):
    sql = "select review_star,review_text1,review_text2,review_text3,review_text4 from ECOMMERCE_REVIEW_P where sku_detail_id='{}'".format(
        sku_detail_id)
    res = c.execute(sql).fetchall()
    neg_list = []  # 差评
    good_list = []  # 好评
    for r in res:
        if r[1] and (r[0] in [4, 5]):
            rev = r[1] + (r[2] if r[2] else "") + (r[3] if r[3] else "") + (r[4] if r[4] else "")
            good_list.append(rev.replace("\n", ""))
        elif r[1] and (r[0] in [1, 2, 3]):
            rev = r[1] + (r[2] if r[2] else "") + (r[3] if r[3] else "") + (r[4] if r[4] else "")
            neg_list.append(rev.replace("\n", ""))
        else:
            # print("无评论or评论星级")
            continue
    # 保存评论txt文件地址
    reviews_path = os.path.dirname(os.path.abspath(__file__)) + "\\reviews"
    if code == 6:
        reviews_path = reviews_path + "\\TMALL"
    elif code == 7:
        reviews_path = reviews_path + "\\JD"
    elif code == 8:
        reviews_path = reviews_path + "\\teufel"
    elif code == 100:
        reviews_path = reviews_path + "\\BestBuy"
    elif code == 31:
        reviews_path = reviews_path + "\\yodobashi"
    elif code == 32:
        reviews_path = reviews_path + "\\biccamera"
    elif code == 33:
        reviews_path = reviews_path + "\\kakaku"
    elif code == 34:
        reviews_path = reviews_path + "\\earphone"
    else:
        reviews_path = reviews_path + "\\Amazon"
    new_dir = os.path.join(reviews_path, sku_detail_id)
    try:
        os.makedirs(new_dir)
    except:
        shutil.rmtree(new_dir)
        os.makedirs(new_dir)
    format = "{}\\neg.txt".format(new_dir)
    save_txt(neg_list, format)
    format = "{}\\good.txt".format(new_dir)
    save_txt(good_list, format)
    # return new_dir


# 天猫评论情感分析(好差评分类)并保存
def TmallText(sku_detail_id):
    # 查询天猫所有评论
    sql = "select review_text1,review_text2,review_text3,review_text4,REVIEW_ID from ECOMMERCE_REVIEW_P where sku_detail_id='{}'".format(sku_detail_id)
    res = c.execute(sql).fetchall()
    reviews_path = os.path.dirname(os.path.abspath(__file__)) + "\\reviews\\TMALL"
    new_dir = os.path.join(reviews_path, sku_detail_id)
    try:
        os.makedirs(new_dir)
    except:
        shutil.rmtree(new_dir)
        os.makedirs(new_dir)
    good_list = []  # 好评
    neg_list = []  # 差评
    for r in res:
        if r[0] and r[0] != "此用户没有填写评论!":
            rev = r[0] + (r[1] if r[1] else "") + (r[2] if r[2] else "") + (r[3] if r[3] else "")
            if sentinment_parse_main(rev) == 1:
                good_list.append(rev)
                # 修改ECOMMERCE_REVIEW_P表字段TASK_ID为1(好评)
                update_task_id(1, r[4])
            elif sentinment_parse_main(rev) == 0:
                neg_list.append(rev)
                # 修改ECOMMERCE_REVIEW_P表字段TASK_ID为0(差评)
                update_task_id(0, r[4])
            else:
                # (中评或无用评论)
                update_task_id(-1, r[4])
        else:
            continue
    good_txt = "{}\\good.txt".format(new_dir)
    save_txt(good_list, good_txt)
    neg_txt = "{}\\neg.txt".format(new_dir)
    save_txt(neg_list, neg_txt)
    # return new_dir


def save_txt(rev_list, txt):
    f = open(txt, "w+", encoding="utf_8")
    for rev in rev_list:
        f.write(rev + "\n")
    f.close()


# 中文关键词分析
def parse_jieba(file_txt):
    stoplist = [line.strip() for line in open('stop_words\\stop.txt', 'r', encoding="utf8").readlines()]
    # 导入停用词
    text_from_file_with_apath = open(file_txt, 'r', encoding="utf8").read()
    # 打开本地txt数据文件.注意文件名不能用中文
    for stop in stoplist:
        jieba.del_word(stop)
    # 去除停用词
    wordlist_after_jieba = jieba.cut(text_from_file_with_apath, cut_all=False, HMM=True)
    wl_space_split = " ".join(wordlist_after_jieba)
    # 提取关键词
    # tags = jieba.analyse.extract_tags(wl_space_split, topK=5, withWeight=True, allowPOS=())
    tags = jieba.analyse.extract_tags(wl_space_split, topK=topK, allowPOS=())
    # print(tags)
    return tags


# 英文关键词分析
def parse_nltk(file_txt, language):
    files = open(file_txt, 'r', encoding="utf8").readlines()
    files_list = []
    for file in files:
        fs = word_tokenize(file.strip(), language)
        for f in fs:
            files_list.append(f)
    # print(files_list)
    sr = stopwords.words(language)
    newStopWords = EnStopWords()
    sr.extend(newStopWords)
    for token in files_list:
        if token in sr:
            files_list.remove(token)
    wl_space_split = " ".join(files_list)
    # 使用jieba统计提取前10关键词
    tags = jieba.analyse.extract_tags(wl_space_split, topK=topK, allowPOS=())
    return tags


# 日文关键词分析
def parse_mecab(file_txt):
    mecab = MeCab.Tagger("-Owakati")
    files = open(file_txt, 'r', encoding="utf8").readlines()
    files_list = []
    word_dict = {}
    for file in files:
        # str = "MeCabを用いて文章を分割してみます。"
        p1 = mecab.parse(file)
        for p in p1.split(" "):
            files_list.append(p)
    # print(files_list)
    for item in files_list:
        if item in JaStopWords:
            continue
        if item not in word_dict:
            word_dict[item] = 1
        else:
            word_dict[item] = word_dict[item] + 1
    d_order = sorted(word_dict.items(), key=lambda x: x[1], reverse=True)
    # print(d_order)
    tags = []
    for word, fre in d_order[0:topK]:
        tags.append(word)
    # print(tags)
    return tags


# 英文判断
def is_En(str):
    for s in str:
        if 97 <= ord(s) <= 122 or 48 <= ord(s) <= 90:
            pass
        else:
            return False
    return True


# 评论情感分析snownlp
def parse_snownlp(reviews_txt):
    x = 0
    # 好评计数
    k = 0
    # 中评计数
    y = 0
    # 差评计数
    z = 0
    # 总数
    with open(reviews_txt, "r", encoding="utf-8") as text:
        # 打开目标文件
        # with open("neg_reviews.txt", "w", encoding="utf-8") as text1:
        good_txt = open("good5.txt", "w", encoding="utf-8")
        neg_txt = open("neg5.txt", "w", encoding="utf-8")
        # 打开保存差评的文件
        for comment in text:
            z += 1
            s = SnowNLP(comment)
            # 文本分析
            s = s.sentiments
            # 情感系数
            if s >= 0.5:
                x += 1
                good_txt.write(comment)
            else:
                neg_txt.write(comment)
                # print(comment)
                # 写入差评数
                y += 1
        good_txt.close()
        neg_txt.close()
    print("好评数：" + str(x))
    print("差评数：" + str(y))
    print("中评数：" + str(k))
    print("总评论数：" + str(z))
    print("差评率：" + str(round(y / z, 2) * 100) + "%")


# 制作词云
def word_cloud(wl_space_split):
    coloring = np.array(Image.open("112._TTD.jpg"))
    # 获取背景图片,new.jpg
    my_wordcloud = WordCloud(background_color="white",
                             mask=coloring,
                             width=617, height=306,
                             font_path="simsun.ttc",
                             max_words=400,
                             max_font_size=100,
                             min_font_size=20,
                             random_state=42)
    my_wordcloud = my_wordcloud.generate(wl_space_split)
    # 用wordcloud设计显示字体
    image_colors = ImageColorGenerator(coloring)
    plt.imshow(my_wordcloud.recolor(color_func=image_colors))
    # 背景图片颜色与字体匹配
    plt.imshow(my_wordcloud)
    # print(plt.text(617,306,wl_space_split))
    # 保存图片
    plt.savefig('res_png\\good_res\\{}.png'.format("100005152874"))
    # 显示图片
    plt.axis("off")
    # 关闭坐标轴
    plt.show()


# 以关键词查询每条评论
def tag_reviews(tags, sku_detail_id, tag_type):
    tag_path = os.path.dirname(os.path.abspath(__file__)) + "\\tag_reviews"
    new_dir = os.path.join(tag_path, sku_detail_id)
    try:
        os.makedirs(new_dir)
    except:
        shutil.rmtree(new_dir)
        os.makedirs(new_dir)
    for tag in tags:
        if tag_type == 0:
            f = open(new_dir + "\\neg_tag.txt", "a+", encoding="utf-8")
            sql = "select review_text1,review_text2,review_text3,review_text4,review_text5 from ECOMMERCE_REVIEW_P where sku_detail_id='{}' and REVIEW_STAR < 4 and (review_text1 like '%{}%' or review_text2 like '%{}%' or review_text3 like '%{}%' or review_text4 like '%{}%' or review_text5 like '%{}%')".format(
                sku_detail_id, tag, tag, tag, tag, tag)
        else:
            f = open(new_dir + "\\good_tag.txt", "a+", encoding="utf-8")
            sql = "select review_text1,review_text2,review_text3,review_text4,review_text5 from ECOMMERCE_REVIEW_P where sku_detail_id='{}' and REVIEW_STAR >= 4 and (review_text1 like '%{}%' or review_text2 like '%{}%' or review_text3 like '%{}%' or review_text4 like '%{}%' or review_text5 like '%{}%')".format(
                sku_detail_id, tag, tag, tag, tag, tag)
        res = c.execute(sql).fetchall()
        count = len(res)
        f.write(tag + "\t" + str(count) + "\n")
        rev_list = []
        num = 0
        for r in res:
            if r[0]:
                num += 1
                rev = r[0] + (r[1] if r[1] else "") + (r[2] if r[2] else "") + (r[3] if r[3] else "") + (
                    r[4] if r[4] else "")
                rev_list.append(rev)
                f.write(str(num) + "." + rev + "\n")
        # print(rev_list)
        f.close()


