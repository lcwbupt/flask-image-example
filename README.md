# 接口框架说明

## 1. 基本结构

example`目录结构如下

```
.
├── README.md
├── log
├── run_server.py
├── src
│   ├── __init__.py
│   ├── server.py
└── tmp
```

`log`可以用来存放日志文件

`tmp`用来存放下载到本地的图片，按日期生成文件夹，需要写脚本定期清理。

`src`是程序文件，主函数在`server.py`中，配置写在`__init__.py`中。

`run_server.py`是程序启动文件。

## 2. 主程序

### 2.1.主接口detect.json

接受一个图片请求，调用模型，输出一个json结果。

- 先解析http请求，分析是文件格式的图片，还是url格式的图片。
- 把文件保存在临时存放位置，生成图片id
- 调用模型预测本地图片
- 将结果封装成json串返回

```python
@app.route("/face_feature/v0.1/detect.json", methods=["POST"])
def detect():
  """ 识别图片中的人脸 
  接受一个post请求，传入image_file或者image_url, 返回json形式的查询结果 
  curl -X POST -F "image_file=@QQ20161123-0.jpg" -F "image_url=http://wx2.sinaimg.cn/large/a716fd45ly1fe1enwnazzj21kw1637wh.jpg" "http://localhost:5000/face_feature/v0.1/detect.json"
  """
    ## 解析请求
  image_file, image_url, image_type = parse_image_request(request)
  if not image_file and not image_url:
    abort(400, "NO FILE SUMBMITTED")

  ## 获取查询id，图片临时存放位置等
  request_id, input_image_id, output_image_id, input_image_file, output_image_file = genereate_image_id_path()

  ## 原始图片的地址，如果是上传的图片，则地址是本地，否则是保存到本地
  buffer_input_status = save_image_to_local(image_file, image_url, image_type, input_image_file)

  ## 获取人脸识别结果
  logging.info("START DETECT FACES FOR %s", input_image_id)
  # TODO: 在这里写模型预测，输入是本地缓存的文件，输出是json串
  results = {"result": ""} # model.predict_image_file(input_image_file) 

  if not results:
    abort(500, "INTERNAL ERROR: %s" % (image_file.filename or image_url))
  logging.info("END DETECT %d FACES FOR %s", len(results), input_image_id)
  return jsonify(results)
```

### 2.2.辅助接口get_image

返回本地图片。输入一个图片id，从缓存路径下把图片输出出去。

```python
@app.route("/face_feature/v0.1/get_image/<string:image_id>", methods=["GET"])
def get_image(image_id):    
  filename = image_id + ".jpg"
  date = filename.split("-", 1)[0]
  if not date.isdigit():
    abort(404, "IMAGE NOT FOUND %s" % filename)
  image_path = os.path.join(UPLOAD_DIR, date, filename)
  try:
    return send_file(image_path)
  except:
    abort(404, "IMAGE NOT FOUND %s" % filename)
```

## 3. 运行

### 3.1. 运行

修改`run_server.py`中的`host`和`port`，默认是`host=0.0.0.0, port=7777`。

在`example`目录下运行

```bash
$ python run_server.py
```

即可看到程序运行，输出日志。

### 3.2. 测试调用

#### 根目录

```bash
$ curl -X GET "http://localhost:7777/face_feature/v0.1/"
{
  "message": "Hello World!"
}
```

#### `detect.json`

```bash
$ curl -X POST -F "image_url=http://wx2.sinaimg.cn/large/a716fd45ly1fe1enwnazzj21kw1637wh.jpg" "http://localhost:7777/face_feature/v0.1/detect.json"
{
  "image_id": "20170504-4f7fab0c53a84d2abf0f1714af6172e6"
}
```

会看到在`tmp`目录下生成了一个日期命名的文件夹`20170504`，里面缓存了这张图片`20170504-4f7fab0c53a84d2abf0f1714af6172e6.jpg`。

#### `get_image.json`

在浏览器中打开，http://localhost:7777/face_feature/v0.1/get_image/20170504-4f7fab0c53a84d2abf0f1714af6172e6，可以看到刚刚保存的图片

