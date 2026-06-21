-- source: business_db.orders
-- sync target: ods.ods_order_di
-- owner: data-dev-demo
-- note: 原始 DDL 只做演示，不连接真实数据库。

CREATE TABLE business_db.orders (
  order_id BIGINT COMMENT '订单 ID',
  user_id BIGINT COMMENT '用户 ID',
  product_id BIGINT COMMENT '商品 ID',
  order_status VARCHAR(32) COMMENT '订单状态：created/paid/refunded/cancelled',
  pay_amount DECIMAL(18,2) COMMENT '支付金额',
  refund_amount DECIMAL(18,2) COMMENT '退款金额',
  pay_time DATETIME COMMENT '支付时间',
  updated_at DATETIME COMMENT '业务库更新时间'
);

-- sync rule:
-- 1. ods_order_di 每小时同步一次。
-- 2. dwd_order_wide_di 依赖 ods_order_di。
-- 3. ads_gmv_daily 依赖 dwd_order_wide_di 的 pay_amount、refund_amount、order_status。
