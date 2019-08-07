import re
import jieba
import numpy as np


class SentmentParse:
    def __init__(self):
        self.deny_word = self.open_dict('inverse')
        self.posdict = self.open_dict('positive')
        self.negdict = self.open_dict('negative')
        self.degree_word = self.open_dict('degree')
        self.mostdict = self.degree_word[self.degree_word.index('extreme') + 1: self.degree_word.index('very')]  # 权重4，即在情感前乘以3
        self.verydict = self.degree_word[self.degree_word.index('very') + 1: self.degree_word.index('more')]  # 权重3
        self.moredict = self.degree_word[self.degree_word.index('more') + 1: self.degree_word.index('ish')]  # 权重2
        self.ishdict = self.degree_word[self.degree_word.index('ish') + 1: self.degree_word.index('last')]  # 权重0.5

    def open_dict(self, Dict, path=r'C:/Users/hhh/Desktop/parse_review/Thesaurus/'):
        path = path + '%s.txt' % Dict
        dictionary = open(path, 'r', encoding='utf-8')
        dict = []
        for word in dictionary:
            word = word.strip('\n')
            dict.append(word)
        return dict

    def judgeodd(self, num):
        if num % 2 == 0:
            return 'even'
        else:
            return 'odd'

    def sentiment_score_list(self, dataset):
        posdict = self.posdict
        mostdict = self.mostdict
        verydict = self.verydict
        moredict = self.moredict
        ishdict = self.ishdict
        deny_word = self.deny_word
        negdict = self.negdict
        degree_word = self.degree_word
        # sen = dataset.split('\n')
        count1 = []
        count2 = []
        neg_list = []  # 差评
        good_list = []  # 好评
        # for sen in seg_sentence:  # 循环遍历每一个评论
        segtmp = jieba.lcut(dataset, cut_all=False)  # 把句子进行分词，以列表的形式返回
        i = 0  # 记录扫描到的词的位置
        a = 0  # 记录情感词的位置
        # a = i-3  # 记录情感词的位置
        poscount = 0  # 积极词的第一次分值
        poscount2 = 0  # 积极词反转后的分值
        poscount3 = 0  # 积极词的最后分值（包括叹号的分值）
        negcount = 0
        negcount2 = 0
        negcount3 = 0
        for word in segtmp:
            if word in posdict:  # 积极情感的分析
                poscount += 1
                c = 0
                max_pos = ["五星", "五分", "满分"]
                if word in max_pos:
                    poscount *= 100.0
                for w in segtmp[a:i]:  # 扫描.情感词前.的程度词
                    if w in mostdict:
                        poscount *= 4.0
                    elif w in verydict:
                        poscount *= 3.0
                    elif w in moredict:
                        poscount *= 2.0
                    elif w in ishdict:
                        poscount *= 0.5
                    elif w in deny_word:
                        c += 1
                if self.judgeodd(c) == 'odd':  # 扫描情感词前的否定词数
                    poscount *= -1.0
                    poscount2 += poscount
                    poscount = 0
                    poscount3 = poscount + poscount2 + poscount3
                    poscount2 = 0
                else:
                    poscount3 = poscount + poscount2 + poscount3
                    poscount = 0
                a = i + 1  # 情感词的位置变化

            elif word in negdict:  # 消极情感的分析，与上面一致
                negcount += 1
                d = 0
                max_pos = ["一星", "一分", "两星", "两分", "二星", "二分", "差评", "慎买", "慎重", "慎重考虑", "慎买"]
                if word in max_pos:
                    negcount *= 100.0
                for w in segtmp[a:i]:
                    if w in mostdict:
                        negcount *= 4.0
                    elif w in verydict:
                        negcount *= 3.0
                    elif w in moredict:
                        negcount *= 2.0
                    elif w in ishdict:
                        negcount *= 0.5
                    elif w in deny_word:
                        d += 1
                if self.judgeodd(d) == 'odd':
                    negcount *= -1.0
                    negcount2 += negcount
                    negcount = 0
                    negcount3 = negcount + negcount2 + negcount3
                    negcount2 = 0
                else:
                    negcount3 = negcount + negcount2 + negcount3
                    negcount = 0
                a = i + 1
            elif word == '！' or word == '!':  ##判断句子是否有感叹号
                for w2 in segtmp[::-1]:  # 扫描感叹号前的情感词，发现后权值+2，然后退出循环
                    if w2 in posdict or negdict:
                        poscount3 += 2
                        negcount3 += 2
                        break
                a = i + 1
            elif re.search(r"\s+", word):
                a = i + 1
            elif re.search("[\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b]", word):
                a = i + 1
            i += 1  # 扫描词位置前移
            # 以下是防止出现负数的情况
            pos_count = 0
            neg_count = 0
            if poscount3 < 0 and negcount3 > 0:
                neg_count += negcount3 - poscount3
                pos_count = 0
            elif negcount3 < 0 and poscount3 > 0:
                pos_count = poscount3 - negcount3
                neg_count = 0
            elif poscount3 < 0 and negcount3 < 0:
                neg_count = -poscount3
                pos_count = -negcount3
            else:
                pos_count = poscount3
                neg_count = negcount3

            count1.append([pos_count, neg_count])
        # count2.append(count1)
        score_array = np.array(count1)
        Pos = np.sum(score_array[:, 0])
        Neg = np.sum(score_array[:, 1])
        # AvgPos = np.mean(score_array[:, 0])
        # AvgPos = float('%.1f' % AvgPos)
        # AvgNeg = np.mean(score_array[:, 1])
        # AvgNeg = float('%.1f' % AvgNeg)
        # print(Pos, Neg)
        # print(AvgPos, AvgNeg)
        if Pos > Neg:
            return 1
        elif Pos < Neg:
            return 0
        else:
            return -1
        # 中评暂不处理

        # StdPos = np.std(score_array[:, 0])
        # StdPos = float('%.1f' % StdPos)
        # StdNeg = np.std(score_array[:, 1])
        # StdNeg = float('%.1f' % StdNeg)
        # score.append([AvgPos, AvgNeg])
        # score.append([Pos, Neg, AvgPos, AvgNeg, StdPos, StdNeg])
        # if AvgPos > AvgNeg:
        #     return 1
        # print(good_list)
        # print(neg_list)
        # return good_list, neg_list


def sentinment_parse_main(data):
    sp = SentmentParse()
    return sp.sentiment_score_list(data)


if __name__ == '__main__':
    data = "耳机架装不上"
    print(sentinment_parse_main(data))