# 京东商品补货监控及自动下单

一些代码、接口参考了 `https://github.com/tychxn/jd-assistant`

# 特性

- 最快约 0.2s 检查 100 件商品的库存
- 一个实例监控一个地区
- 可以配置多个账户, 有货后同时下单

# 使用方法

将 `configTemplate.json` 文件更名为 `config.json`, 并按照说明配置, 运行 `main.py`

## 获取下单相关的值

向购物车中加入任意商品, 点击去结算, 在订单结算页面打开开发者工具, 在 Console 中执行以下代码, 将输出复制至配置文件:

```js
let eid = $('#eid').val();
let fp = $('#fp').val();
let trackId = getTakId();
console.log(`"eid": "${eid}",\n"fp": "${fp}",\n"trackId": "${trackId}"\n`);
```

## 获取 cookies

在任意京东页面打开开发者工具, 刷新, 查看网络请求, 过滤 `passport.jd.com/loginservice.aspx`, 将请求 cookie 复制至配置文件

## 测试下单

按照说明编辑 `testOrder.py` 文件, 并运行它

# 说明

- 监控库存正常或超时都不会输出
- cookies 24h 过期
- 下单后自行支付