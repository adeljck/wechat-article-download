**<u>微信公众号文章爬取</u>**

通过利用微信公众平台的引入外部链接的功能，使用**selenium**模拟登录微信公众号后，再通过**requests**库结合其他模块将文章的直链爬取下来并存入数据库

**使用到的模块**

**selenium** 用于打开浏览器模拟登录

**requests** 发送请求获取直链

**pymysql** 数据库操作

**fake-useragent** 生成随机UA