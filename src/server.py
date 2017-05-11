# -*- coding: utf-8 -*-
#!/usr/bin/python                        
##################################################
# AUTHOR : Yandi LI
# CREATED_AT : 2016-07-12
# LAST_MODIFIED : 2017-05-04 11:25:40
# USAGE : 
# PURPOSE : 
##################################################
from __future__ import print_function
import os
import time
import uuid
import logging
import requests
import numpy as np
import cv2
from flask import (
    Flask, 
    jsonify, 
    request, 
    make_response, 
    send_file,
    abort,
)
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'log')
UPLOAD_DIR = os.path.join(BASE_DIR, "tmp")

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
logging = logging.getLogger(__name__)

app = Flask(__name__)
cors = CORS(app)

@app.route("/")
def index():
  return jsonify(message="Hello World!")


@app.route("/face_feature/v0.1/")
def home():
  return jsonify(message="Hello World!")


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
  results = {"image_id": input_image_id} # model.predict_image_file(input_image_file) 

  if not results:
    abort(500, "INTERNAL ERROR: %s" % (image_file.filename or image_url))
  logging.info("END DETECT %d FACES FOR %s", len(results), input_image_id)
  #return jsonify(results)
  # Response
  resp = jsonify(results)
  resp.headers['Access-Control-Allow-Origin'] = '*'
  return resp


def genereate_image_id_path():
  """ 获取查询id，生成图片的id，根据当前日期创建文件夹，把图片的缓存地址设定在文件夹中
  @returns request_id
  @returns input_image_id
  @returns output_image_id
  @returns input_image_file with folder created
  @returns output_image_file with folder created
  """
  date = time.strftime('%Y%m%d', time.localtime())
  request_id = uuid.uuid4().hex
  image_id = date + '-' + request_id
  input_image_id = image_id
  output_image_id = "{}_out".format(image_id)
  daily_folder = os.path.join(os.path.join(UPLOAD_DIR), date)
  if not os.path.exists(daily_folder):
    os.makedirs(daily_folder, mode=0774)
  input_image_file = os.path.join(daily_folder, input_image_id) + ".jpg"
  output_image_file = os.path.join(daily_folder, output_image_id) + ".jpg"
  return request_id, input_image_id, output_image_id, input_image_file, output_image_file


def parse_image_request(request_):
  """ 从请求中解析出图片名称，图片格式，图片来源
  如果不符合要求，则返回请求错误
  """
  image_file = None
  image_type = None
  image_url = None
  if "image_file" in request_.files:
    image_file = request_.files["image_file"]
    image_type = image_file.mimetype
    if image_file.filename:
      return image_file, image_url, image_type
  if "image_url" in request_.form:
    image_url = request_.form["image_url"]
    if image_url and image_url.startswith("http"):
      return image_file, image_url, image_type

  return image_file, image_url, image_type


def save_image_to_local(image_file, image_url, image_type, input_image_file):
  """ 把请求给出的图片保存在缓存文件夹中
  @param image_file: request.File, or url
  @param image_type: image mimetype e.g. "image/jpeg" or "url"
  @param image_source: "file" or "url"
  @param input_image_file: local buffer path of input image
  @returns True/False
  """
  if image_file:
    if image_type in {"image/jpg", "image/png", "image/jpeg", "image/bmp"}:
      image_file.save(input_image_file)
    # elif image_type in {"image/gif"}:
    #   scipy.misc.imread(image_file.read())  
    #   pass
    else:
      abort(400, "IMAGE_ERROR_UNSUPPORTED_FORMAT: %s, %s" \
            % (image_file.filename, image_file.mimetype))
    return True
  elif image_url:
    save_url_to_file(image_url, input_image_file)
    return True
  return False


def save_url_to_file(url, image_path):
  """ 下载url内容，将图片保存在本地缓存地址
  """
  try:
    req = requests.get(url, timeout=3)
  except:
    abort(412, "IMAGE_DOWNLOAD_TIMEOUT: %s" % url)
  try:
    image = np.asarray(bytearray(req.content), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    cv2.imwrite(image_path, image)
  except:
    logging.exception("%s, %s", url, image_path)
    abort(400, "IMAGE URL CONTAIN INVALID IMAGE FORMAT: %s" % url)


@app.errorhandler(400)
def unsupported_format(error):
  """ 文件格式不符合要求的，在这里标记返回
  e.g. {"error": "IMAGE_ERROR_UNSUPPORTED_FORMAT: pwktQBx_jpg.gif, image/gif" }
  """
  return make_response(jsonify({'error': error.description}), 400)


@app.errorhandler(404)
def not_found_error(error):
  """ 内部错误
  e.g. { "error": "IMAGE NOT FOUND: https://damyanon.net/flask-series-logging/" }
  """
  return make_response(jsonify({'error': error.description}), 404)


@app.errorhandler(412)
def download_timeout(error):
  """ url内容下载失败
  e.g. { "error": "IMAGE_DOWNLOAD_TIMEOUT: https://damyanon.net/flask-series-logging/" }
  """
  return make_response(jsonify({'error': error.description}), 412)


@app.errorhandler(500)
def internal_error(error):
  """ 内部错误
  e.g. { "error": "INTERNAL ERROR: https://damyanon.net/flask-series-logging/" }
  """
  return make_response(jsonify({'error': "INTERNAL ERROR"}), 500)
