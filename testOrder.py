import glb

# 初始化
glb.init()

id = 'yue'  # 账户在 config.json 中的 key
itemId = '3007224'  # 有货的商品 ID
glb.accountDict[id].buy(itemId)
