-- table: ads.ads_gmv_daily
-- metric: gmv_daily, refund_daily, net_gmv_daily
-- source: dwd.dwd_order_wide_di

INSERT OVERWRITE TABLE ads.ads_gmv_daily PARTITION (dt = '${bizdate}')
SELECT
  dt,
  SUM(CASE WHEN order_status = 'paid' THEN pay_amount ELSE 0 END) AS gmv_daily,
  SUM(CASE WHEN order_status = 'refunded' THEN refund_amount ELSE 0 END) AS refund_daily,
  SUM(CASE
        WHEN order_status = 'paid' THEN pay_amount
        WHEN order_status = 'refunded' THEN -1 * refund_amount
        ELSE 0
      END) AS net_gmv_daily
FROM dwd.dwd_order_wide_di
WHERE dt = '${bizdate}'
GROUP BY dt;

-- quality rule:
-- net_gmv_daily = gmv_daily - refund_daily
-- refund_daily depends on dwd_order_wide_di.refund_amount
