#!/usr/bin/env python3
"""LLM-Wiki 基座：把焊不进表结构的语义，切成一条条人能维护、模型能查的条目。

配套文章 C1-06A《宽表焊不进去的那些行话，得给它们盖一间模型能查的库房》。

宽表能焊死结构化口径（字段粒度、过滤条件、join 路径），但企业里还压着一堆
焊不进 CREATE VIEW 的语义：中文别名、行话、经典问法+标准 SQL、踩过的坑。
它们只能以"人写给人看、也写给模型看"的文字形式存在。这份清单就是那间库房。

每条五个字段：
  id       身份证，如 term.sales_amount
  type     四类之一：term(字段口径) / alias(业务词别名) / golden(经典问法+标准SQL) / pitfall(踩坑)
  title    一句话说清它讲什么
  aliases  会被哪些说法命中（用户怎么口语化地问都能挂上）
  content  正文，写给人也写给模型
  sql      仅 golden 有：那段被验证过的标准答案

库房最珍贵的性质：纯文本、结构一致、人一眼能读能改。懂业务的人就能维护，
不需要懂向量、不需要懂模型。所有内容都长在真实的 4 表电商数据集上，不编字段。
"""

WIKI_ENTRIES = [
    # ---- 字段口径 term ----
    {
        "id": "term.paid",
        "type": "term",
        "title": "“已支付”的口径",
        "aliases": ["已支付", "付掉了", "钱到账", "支付成功", "付款成功", "成交订单"],
        "content": "“已支付/付款成功”指订单主表 ord_order_main.payment_status = 2。"
                   "统计有效销售时通常还要带 is_deleted = 0，排除已删除订单。"
                   "payment_status 取值：0未支付/1部分支付/2已支付/3已退款，只有 2 是口径里的“已支付”。",
    },
    {
        "id": "term.sales_amount",
        "type": "term",
        "title": "“销售额”的口径（含扇出警告）",
        "aliases": ["销售额", "GMV", "卖了多少钱", "营业额", "成交额", "销售金额"],
        "content": "销售额要用订单明细表的明细金额汇总：SUM(ord_order_item.item_amount)。"
                   "绝对不要去 SUM 订单主表的 actual_amount。actual_amount 是订单级金额，"
                   "一个多商品订单 join 到明细后会占多行、每行都重复同一个订单金额，"
                   "直接求和会按商品件数成倍虚高（扇出双算）。",
    },
    {
        "id": "term.order_count",
        "type": "term",
        "title": "“订单数”的口径",
        "aliases": ["订单数", "多少单", "订单量", "成交笔数", "下了多少单"],
        "content": "订单数在订单粒度用 COUNT(*) 即可；但一旦 join 到明细表 ord_order_item，"
                   "一个多商品订单会占多行，必须用 COUNT(DISTINCT order_id)，否则会把订单数按件数放大。",
    },
    {
        "id": "term.region",
        "type": "term",
        "title": "“地区”字段与它的真实取值",
        "aliases": ["地区", "区域", "华东", "华北", "华南", "西南", "哪个区"],
        "content": "地区是 ord_order_main.region，是文本字段，真实取值只有四个："
                   "华东、华北、华南、西南。它不是编码，直接按这四个值过滤或分组即可。",
    },
    # ---- 业务词别名 alias ----
    {
        "id": "alias.category",
        "type": "alias",
        "title": "“一级类目 / 大类 / 品类”指什么",
        "aliases": ["一级类目", "大类", "品类", "类目", "分类", "商品分类"],
        "content": "用户说的“一级类目/大类/品类”，指类目表 prod_category.category_name。"
                   "从明细上卷到类目的路径：ord_order_item.product_id "
                   "-> prod_product.category_id -> prod_category.category_id。",
    },
    {
        "id": "alias.customer_price",
        "type": "alias",
        "title": "“客单价”指什么",
        "aliases": ["客单价", "人均消费", "平均每单", "单均"],
        "content": "客单价 = 已支付订单的实付金额之和 / 支付用户数，"
                   "在订单粒度用 SUM(actual_amount) / COUNT(DISTINCT user_id)，只算 payment_status = 2。"
                   "注意：客单价用订单级 actual_amount 是对的，因为它不 join 明细、不扇出。",
    },
    # ---- 经典问法 + 标准 SQL golden ----
    {
        "id": "golden.category_sales",
        "type": "golden",
        "title": "经典问法：各类目销售额",
        "aliases": ["各类目销售额", "每个类目卖了多少", "类目销售排名", "分类销售额", "各品类销售额"],
        "content": "标准解法：四表 join，只算已支付未删除订单，用明细金额汇总，按类目分组。",
        "sql": "SELECT c.category_name, ROUND(SUM(i.item_amount), 2) AS sales\n"
               "FROM ord_order_main o\n"
               "JOIN ord_order_item i ON o.order_id = i.order_id\n"
               "JOIN prod_product p ON i.product_id = p.product_id\n"
               "JOIN prod_category c ON p.category_id = c.category_id\n"
               "WHERE o.payment_status = 2 AND o.is_deleted = 0\n"
               "GROUP BY c.category_name",
    },
    {
        "id": "golden.region_orders",
        "type": "golden",
        "title": "经典问法：各地区订单数",
        "aliases": ["各地区订单数", "每个地区多少单", "地区订单量", "各区域下单数"],
        "content": "标准解法：订单粒度直接按地区分组计数，只算已支付未删除订单，不 join 明细。",
        "sql": "SELECT region, COUNT(*) AS order_count\n"
               "FROM ord_order_main\n"
               "WHERE payment_status = 2 AND is_deleted = 0\n"
               "GROUP BY region",
    },
    # ---- 踩坑记录 pitfall ----
    {
        "id": "pitfall.fanout",
        "type": "pitfall",
        "title": "高风险：明细粒度上的扇出双算",
        "aliases": ["扇出", "金额翻倍", "求和虚高", "多商品订单", "重复计算", "翻倍"],
        "content": "凡是把订单主表 join 到明细表、又要对金额求和的题，都要警惕扇出。"
                   "订单级字段（actual_amount、total_amount）在明细行里会重复，SUM 它们会虚高；"
                   "订单数要用 COUNT(DISTINCT order_id)，不能直接 COUNT(*)。",
    },
    {
        "id": "pitfall.out_of_scope",
        "type": "pitfall",
        "title": "高风险：越界表 / 敏感字段",
        "aliases": ["手机号", "用户表", "越界", "敏感字段", "白名单外"],
        "content": "本数据集只暴露 4 张业务表：prod_category、prod_product、ord_order_main、ord_order_item。"
                   "问到用户手机号、用户表 usr_user 等白名单外的东西，正确动作是明确拒绝，"
                   "不要凭空编一个字段名去凑 SQL。",
    },
]


def by_type(t: str):
    return [e for e in WIKI_ENTRIES if e["type"] == t]


def get(entry_id: str):
    for e in WIKI_ENTRIES:
        if e["id"] == entry_id:
            return e
    return None


if __name__ == "__main__":
    from collections import Counter
    c = Counter(e["type"] for e in WIKI_ENTRIES)
    print(f"LLM-Wiki 共 {len(WIKI_ENTRIES)} 条：", dict(c))
    for e in WIKI_ENTRIES:
        print(f"  [{e['type']:8}] {e['id']:24} {e['title']}")
