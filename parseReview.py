from utils import sku_ids, texts, TmallText


def assort_review():
    # 获取sku_id
    # dir_list = []
    sku_list = sku_ids()
    # sku_list = [("528515320283", "SKU-fc0a25b5-bf4d-4605-80db-9a34c4a3a74a", "6"), ("574870586003", "SKU-4e16bc2e-a512-46f2-b3b4-4ee70ad02c69", "6")]
    for tuple in sku_list:
        code = tuple[2]
        sku_detail_id = tuple[1]
        if int(code) == 6:
            TmallText(sku_detail_id)
        else:
            texts(sku_detail_id, int(code))  # 生成好评与差评txt文件
    #     dir_list.append(new_dir)
    # return dir_list


if __name__ == '__main__':
    assort_review()