import os
from utils import sku_ids, texts, tag_reviews, parse_jieba, tag_count, save_tag, update_tag, is_En, min_num, parse_nltk, parse_mecab, TmallText, tag_count_TM
import re


def create_tag():
    sku_list = sku_ids()
    # sku_list = [("574870586003", "SKU-4e16bc2e-a512-46f2-b3b4-4ee70ad02c69", "6")]
    for sku_id, sku_detail_id, code in sku_list:
        code = int(code)
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
        txt_dir = os.listdir(new_dir)
        for txt in txt_dir:
            if re.search(r"neg", txt):
                tag_type = 0
            else:
                tag_type = 1
            txt = os.path.join(new_dir, txt)
            # print(txt)
            if int(code) in [6, 7]:
                tags = parse_jieba(txt)  # 统计评论关键词(中文, 京东/天猫)
                for tag in tags:
                    #  去除英文关键词
                    if is_En(tag):
                        tags.remove(tag)
            elif int(code) in [1, 2, 100]:
                language = "english"
                tags = parse_nltk(txt, language)  # 统计评论关键词(英文, Amazon/BestBuy/..)
            elif int(code) in [4, 8]:
                language = "german"
                tags = parse_nltk(txt, language)  # 统计评论关键词(德文, Amazon/..)
            elif int(code) in [5]:
                language = "french"
                tags = parse_nltk(txt, language)  # 统计评论关键词(法文, Amazon/..)
            elif re.search(r"^3.*", str(code)):
                tags = parse_mecab(txt)  # 统计评论关键词(日文, Amazon/..)
            else:
                print("暂不支持其他语言分析")
                continue
            print(tags)
            n = 0
            if len(tags) < 1:
                continue
            for i in range(len(tags)):
                #  以评论关键词统计评论总数
                if int(code) == 6:
                    count = tag_count_TM(sku_detail_id, tags[i], tag_type)
                    # count = 0
                    # with open(txt, "r", encoding="utf8") as f:
                    #     total_review = f.readlines()
                    #     for review in total_review:
                    #         if tags[i] in review:
                    #             count += 1
                else:
                    count = tag_count(sku_detail_id, tags[i], tag_type)
                # print(count)
                if count < min_num:
                    continue
                #  生成tag_id
                tag_id = sku_detail_id + "_" + str(tag_type) + "_" + str(n)
                try:
                    # 保存数据库
                    save_tag(tag_id, sku_id, tags[i], count, tag_type, sku_detail_id, code)
                except:
                    # 更新数据库
                    update_tag(tags[i], count, tag_id, code)
                n += 1


if __name__ == '__main__':
    create_tag()