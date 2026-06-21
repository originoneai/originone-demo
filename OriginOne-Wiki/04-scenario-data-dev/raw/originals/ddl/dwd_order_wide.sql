-- table: dwd.dwd_order_wide_di
-- grain: one row per order
-- purpose: 订单宽表，给 GMV、退款、履约看板使用。

CREATE TABLE dwd.dwd_order_wide_di (
  dt DATE COMMENT '分区日期',
  order_id BIGINT COMMENT '订单 ID',
  user_id BIGINT COMMENT '用户 ID',
  product_id BIGINT COMMENT '商品 ID',
  order_status VARCHAR(32) COMMENT '订单状态',
  pay_amount DECIMAL(18,2) COMMENT '支付金额',
  refund_amount DECIMAL(18,2) COMMENT '退款金额，从 ods_order_di.refund_amount 映射',
  net_pay_amount DECIMAL(18,2) COMMENT '净支付金额，pay_amount - refund_amount',
  pay_time DATETIME COMMENT '支付时间',
  updated_at DATETIME COMMENT '更新时间'
);

-- field mapping:
-- dwd_order_wide_di.pay_amount <- ods_order_di.pay_amount
-- dwd_order_wide_di.refund_amount <- ods_order_di.refund_amount
-- dwd_order_wide_di.net_pay_amount <- pay_amount - refund_amount
