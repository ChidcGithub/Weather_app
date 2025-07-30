# Version 1.0-beta
# A simple Weather App by Chidc
# A qweather key is required, please read README.md in github for further information
# If you like this project, please leave a star for this project ~~~


import sys
import os
import time
import datetime
import random
import requests
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTabWidget, QFrame, QGridLayout, QListWidget,
                             QListWidgetItem, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QPixmap, QIcon, QFont, QColor, QPalette
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
# 在文件顶部添加geopy相关导入
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


# 和风天气API配置
QWEATHER_KEY = os.environ.get('QWEATHER_KEY', '[Your_Qweather_API_KEY]') #这里需要一个可使用的API KEY
QWEATHER_BASE_URL = "https://devapi.qweather.com/v7"
QWEATHER_GEO_URL = "https://geoapi.qweather.com/v2/city"

# 天气图标映射
WEATHER_ICONS = {
    "晴": "☀️",
    "多云": "⛅",
    "阴": "☁️",
    "雨": "🌧️",
    "雷阵雨": "⛈️",
    "雪": "❄️",
    "雾": "🌫️",
    "风": "💨"
}


class WeatherData:
    """天气数据管理类"""

    def __init__(self):
        self.current = {}
        self.forecast = []
        self.last_updated = None
        self.city = "北京"

    def update_city(self, city):
        self.city = city

    def get_location_id(self, city):
        """获取城市的Location ID"""
        try:
            response = requests.get(
                f"{QWEATHER_GEO_URL}/lookup",
                params={
                    "location": city,
                    "key": QWEATHER_KEY,
                    "lang": "zh"
                }
            )
            data = response.json()

            if data["code"] != "200" or not data["location"]:
                return None

            # 返回第一个匹配的城市ID
            return data["location"][0]["id"]

        except Exception as e:
            print(f"获取城市ID出错: {e}")
            return None

    def format_time(self, timestamp):
        """格式化时间戳为本地时间"""
        try:
            # 和风天气返回的是UTC时间，需要转换为本地时间
            utc_time = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M%z")
            local_time = utc_time.astimezone()
            return local_time.strftime("%Y-%m-%d %H:%M")
        except:
            return timestamp

    def fetch_weather_data(self):
        """获取天气数据"""
        # 先获取城市ID
        location_id = self.get_location_id(self.city)
        if not location_id:
            return {"error": f"无法找到城市: {self.city}"}

        try:
            # 获取当前天气
            current_response = requests.get(
                f"{QWEATHER_BASE_URL}/weather/now",
                params={
                    "location": location_id,
                    "key": QWEATHER_KEY,
                    "lang": "zh"
                }
            )
            current_data = current_response.json()

            if current_data["code"] != "200":
                return {"error": "获取实时天气失败"}

            # 获取未来7天预报
            forecast_response = requests.get(
                f"{QWEATHER_BASE_URL}/weather/7d",
                params={
                    "location": location_id,
                    "key": QWEATHER_KEY,
                    "lang": "zh"
                }
            )
            forecast_data = forecast_response.json()

            if forecast_data["code"] != "200":
                return {"error": "获取天气预报失败"}

            # 获取日出日落信息（从当天预报中获取）
            daily_data = forecast_data["daily"][0] if forecast_data["daily"] else {}

            # 处理当前天气数据
            self.current = {
                "city": current_data["now"].get("obsTime", ""),
                "temperature": current_data["now"]["temp"],
                "description": current_data["now"]["text"],
                "icon": current_data["now"]["icon"],
                "humidity": current_data["now"]["humidity"],
                "wind_speed": current_data["now"]["windSpeed"],
                "wind_dir": current_data["now"]["windDir"],
                "pressure": current_data["now"]["pressure"],
                "vis": current_data["now"]["vis"],
                "feels_like": current_data["now"]["feelsLike"],
                "sunrise": daily_data.get("sunrise", ""),
                "sunset": daily_data.get("sunset", ""),
                "updated_at": self.format_time(current_data["now"]["obsTime"]),
                "windDir": current_data["now"]["windDir"],
                "windScale": current_data["now"]["windScale"],
                "sources":current_data["refer"]["sources"]
            }

            #示例
            '''{'code': '200', 'fxLink': 'https://www.qweather.com/weather/beijing-101010100.html', 
            'now': {'cloud': '7', 'dew': '24', 'feelsLike': '32', 'humidity': '67', 'icon': '101',
             'obsTime': '2025-07-29T19:16+08:00', 'precip': '0.0', 'pressure': '995', 'temp': '29', 
             'text': '多云', 'vis': '30', 'wind360': '180', 'windDir': '南风', 'windScale': '2', 'windSpeed': '6'}, 
             'refer': {'license': ['QWeather Developers License'], 'sources': ['QWeather']},
              'updateTime': '2025-07-29T19:18+08:00'}
              
              "refer" : {
    "sources" : [ "QWeather" ],
    "license" : [ "QWeather Developers License" ]
  }'''

            # 处理未来预报数据
            self.forecast = []
            for day in forecast_data["daily"]:
                date_obj = datetime.datetime.strptime(day["fxDate"], "%Y-%m-%d")
                self.forecast.append({
                    "date": date_obj.strftime("%m-%d"),
                    "day": date_obj.strftime("%A"),
                    "temp_max": day["tempMax"],
                    "temp_min": day["tempMin"],
                    "description": day["textDay"],
                    "night_desc": day["textNight"],
                    "icon": day["iconDay"],
                    "wind_dir": day["windDirDay"],
                    "wind_scale": day["windScaleDay"],
                    "precip": day["precip"],
                    "humidity": day["humidity"]
                })

            self.last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True}

        except Exception as e:
            print(f"获取天气数据出错: {e}")
            return {"error": f"获取天气数据失败: {str(e)}"}


    def get_public_city(self):
        """获取公网IP地址，增加重试和备用API"""
        # 备用IP查询API列表
        ip_apis = [
            'https://ipinfo.io/json',
            'https://ip.cn/json'
        ]

        for api in ip_apis:
            try:
                # 增加超时时间和重试机制
                for attempt in range(3):  # 每个API重试3次
                    try:
                        response = requests.get(api, timeout=8)
                        return response.json().get('city')
                    except (requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout) as e:
                        print("获取api失败:",e)
                        continue  # 继续下一次尝试
            except Exception as e:
                print(f"使用API {api} 获取IP失败: {e}")
                continue  # 尝试下一个API

        print("所有IP查询API均失败")
        return None

    def get_city_by_location(self):
        """通过IP定位获取城市名"""
        try:
            city = self.get_public_city()
            return city
        except:
            print("获取城市失败,未知原因")
            return None




class WeatherThread(QThread):
    """天气数据获取线程"""
    weather_updated = pyqtSignal(dict)

    def __init__(self, weather_data):
        super().__init__()
        self.weather_data = weather_data
        self.running = True
        self.update_interval = 300  # 5分钟更新一次

    def run(self):
        while self.running:
            result = self.weather_data.fetch_weather_data()
            self.weather_updated.emit(result)
            # 等待更新间隔
            for _ in range(self.update_interval):
                if not self.running:
                    break
                time.sleep(1)

    def stop(self):
        self.running = False
        self.wait()


class SkyBox:
    """3D天空盒渲染类"""

    def __init__(self):
        self.textures = {}
        self.initialized = False

    def initialize(self):
        """初始化天空盒纹理"""
        # 这里我们使用颜色渐变代替实际纹理
        self.initialized = True

    def render(self, weather_type):
        """根据天气类型渲染天空盒"""
        if not self.initialized:
            self.initialize()

        glPushMatrix()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

        # 根据天气类型设置天空颜色
        if "晴" in weather_type:
            # 晴天 - 蓝色渐变
            glBegin(GL_QUADS)
            # 顶部 - 浅蓝色
            glColor3f(0.529, 0.808, 0.922)
            glVertex3f(1.0, 1.0, -1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(1.0, 1.0, 1.0)

            # 底部 - 深蓝色
            glColor3f(0.137, 0.412, 0.557)
            glVertex3f(1.0, -1.0, 1.0)
            glVertex3f(-1.0, -1.0, 1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(1.0, -1.0, -1.0)

            # 前面
            glColor3f(0.341, 0.624, 0.812)
            glVertex3f(1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, -1.0, 1.0)
            glVertex3f(1.0, -1.0, 1.0)

            # 后面
            glColor3f(0.341, 0.624, 0.812)
            glVertex3f(1.0, -1.0, -1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(1.0, 1.0, -1.0)

            # 左面
            glColor3f(0.341, 0.624, 0.812)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(-1.0, -1.0, 1.0)

            # 右面
            glColor3f(0.341, 0.624, 0.812)
            glVertex3f(1.0, 1.0, -1.0)
            glVertex3f(1.0, 1.0, 1.0)
            glVertex3f(1.0, -1.0, 1.0)
            glVertex3f(1.0, -1.0, -1.0)
            glEnd()

        elif "雨" in weather_type or "雷阵" in weather_type:
            # 雨天 - 灰色渐变
            glBegin(GL_QUADS)
            # 顶部
            glColor3f(0.5, 0.5, 0.6)
            glVertex3f(1.0, 1.0, -1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(1.0, 1.0, 1.0)

            # 底部
            glColor3f(0.3, 0.3, 0.4)
            glVertex3f(1.0, -1.0, 1.0)
            glVertex3f(-1.0, -1.0, 1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(1.0, -1.0, -1.0)

            # 其他面
            glColor3f(0.4, 0.4, 0.5)
            # 前面
            glVertex3f(1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, -1.0, 1.0)
            glVertex3f(1.0, -1.0, 1.0)

            # 后面
            glVertex3f(1.0, -1.0, -1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(1.0, 1.0, -1.0)

            # 左面
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(-1.0, -1.0, 1.0)

            # 右面
            glVertex3f(1.0, 1.0, -1.0)
            glVertex3f(1.0, 1.0, 1.0)
            glVertex3f(1.0, -1.0, 1.0)
            glVertex3f(1.0, -1.0, -1.0)
            glEnd()

        elif "云" in weather_type or "阴" in weather_type:
            # 多云/阴天 - 灰白色渐变
            glBegin(GL_QUADS)
            # 顶部
            glColor3f(0.7, 0.75, 0.8)
            glVertex3f(1.0, 1.0, -1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(1.0, 1.0, 1.0)

            # 底部
            glColor3f(0.5, 0.55, 0.6)
            glVertex3f(1.0, -1.0, 1.0)
            glVertex3f(-1.0, -1.0, 1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(1.0, -1.0, -1.0)

            # 其他面
            glColor3f(0.6, 0.65, 0.7)
            # 前面
            glVertex3f(1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, -1.0, 1.0)
            glVertex3f(1.0, -1.0, 1.0)

            # 后面
            glVertex3f(1.0, -1.0, -1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(1.0, 1.0, -1.0)

            # 左面
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(-1.0, -1.0, 1.0)

            # 右面
            glVertex3f(1.0, 1.0, -1.0)
            glVertex3f(1.0, 1.0, 1.0)
            glVertex3f(1.0, -1.0, 1.0)
            glVertex3f(1.0, -1.0, -1.0)
            glEnd()

        elif "雪" in weather_type:
            # 雪天 - 蓝白色渐变
            glBegin(GL_QUADS)
            # 顶部
            glColor3f(0.8, 0.9, 1.0)
            glVertex3f(1.0, 1.0, -1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(1.0, 1.0, 1.0)

            # 底部
            glColor3f(0.6, 0.7, 0.8)
            glVertex3f(1.0, -1.0, 1.0)
            glVertex3f(-1.0, -1.0, 1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(1.0, -1.0, -1.0)

            # 其他面
            glColor3f(0.7, 0.8, 0.9)
            # 前面
            glVertex3f(1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, -1.0, 1.0)
            glVertex3f(1.0, -1.0, 1.0)

            # 后面
            glVertex3f(1.0, -1.0, -1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(1.0, 1.0, -1.0)

            # 左面
            glVertex3f(-1.0, 1.0, 1.0)
            glVertex3f(-1.0, 1.0, -1.0)
            glVertex3f(-1.0, -1.0, -1.0)
            glVertex3f(-1.0, -1.0, 1.0)

            # 右面
            glVertex3f(1.0, 1.0, -1.0)
            glVertex3f(1.0, 1.0, 1.0)
            glVertex3f(1.0, -1.0, 1.0)
            glVertex3f(1.0, -1.0, -1.0)
            glEnd()

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()


class Cloud:
    """3D云朵类"""

    def __init__(self, x, y, z, size):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.speed = 0.001 + (size * 0.002)
        self.rotation = 0

    def update(self):
        """更新云朵位置"""
        self.x -= self.speed
        self.rotation += 0.01

        # 云朵移出视野后重新放置到右侧
        if self.x < -2.0:
            self.x = 2.0
            self.y = np.random.uniform(0.3, 0.8)
            self.z = np.random.uniform(-1.0, 1.0)

    def render(self):
        """渲染云朵"""
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)

        # 云朵由多个白色球体组成
        glColor3f(1.0, 1.0, 1.0)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])

        # 主体
        quad = gluNewQuadric()
        gluSphere(quad, self.size * 0.4, 16, 16)

        # 附加部分
        glTranslatef(self.size * 0.3, 0, 0)
        gluSphere(quad, self.size * 0.3, 16, 16)

        glTranslatef(-self.size * 0.6, 0, 0)
        gluSphere(quad, self.size * 0.35, 16, 16)

        glTranslatef(self.size * 0.2, self.size * 0.2, 0)
        gluSphere(quad, self.size * 0.3, 16, 16)

        glTranslatef(0, -self.size * 0.4, 0)
        gluSphere(quad, self.size * 0.25, 16, 16)

        gluDeleteQuadric(quad)
        glPopMatrix()


class Raindrop:
    """雨滴类"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置雨滴位置"""
        self.x = np.random.uniform(-1.5, 1.5)
        self.y = np.random.uniform(0.5, 1.5)
        self.z = np.random.uniform(-1.0, 1.0)
        self.length = np.random.uniform(0.03, 0.08)
        self.speed = np.random.uniform(0.01, 0.03)

    def update(self):
        """更新雨滴位置"""
        self.y -= self.speed

        # 雨滴落到地面后重置
        if self.y < -1.0:
            self.reset()

    def render(self):
        """渲染雨滴"""
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)

        glDisable(GL_LIGHTING)
        glColor3f(0.5, 0.7, 0.9)
        glLineWidth(2.0)

        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, -self.length, 0)
        glEnd()

        glEnable(GL_LIGHTING)
        glPopMatrix()


class Snowflake:
    """雪花类"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置雪花位置"""
        self.x = np.random.uniform(-1.5, 1.5)
        self.y = np.random.uniform(0.5, 1.5)
        self.z = np.random.uniform(-1.0, 1.0)
        self.size = np.random.uniform(0.01, 0.03)
        self.speed = np.random.uniform(0.005, 0.015)
        self.rotation = np.random.uniform(0, 360)
        self.rotation_speed = np.random.uniform(-1, 1)

    def update(self):
        """更新雪花位置"""
        self.y -= self.speed
        self.x += np.sin(self.y * 2) * 0.005  # 左右摇摆
        self.rotation += self.rotation_speed

        # 雪花落到地面后重置
        if self.y < -1.0:
            self.reset()

    def render(self):
        """渲染雪花"""
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)

        glDisable(GL_LIGHTING)
        glColor3f(1.0, 1.0, 1.0)

        # 绘制六边形雪花
        glBegin(GL_POLYGON)
        for i in range(6):
            angle = 2 * np.pi * i / 6
            glVertex3f(np.cos(angle) * self.size, np.sin(angle) * self.size, 0)
        glEnd()

        glEnable(GL_LIGHTING)
        glPopMatrix()


class Sun:
    """太阳类"""

    def __init__(self):
        self.angle = 45  # 初始角度（上午）
        self.radius = 1.2
        self.size = 0.2

    def update(self, hour):
        """根据时间更新太阳位置"""
        # 根据小时计算太阳角度（0-24小时映射到0-360度）
        self.angle = (hour % 24) * 15  # 15度/小时

    def get_position(self):
        """获取太阳位置"""
        rad = np.radians(self.angle)
        x = np.sin(rad) * self.radius
        y = np.cos(rad) * self.radius - 0.3  # 调整Y位置使中午太阳最高
        return x, max(y, -0.5)  # 确保太阳不会低于地平线太多

    def render(self):
        """渲染太阳"""
        x, y = self.get_position()

        # 只在白天渲染太阳
        if y > -0.3:
            glPushMatrix()
            glTranslatef(x, y, -1.0)

            # 太阳核心
            glColor3f(1.0, 0.8, 0.0)
            glMaterialfv(GL_FRONT, GL_EMISSION, [1.0, 0.8, 0.0, 1.0])

            quad = gluNewQuadric()
            gluSphere(quad, self.size, 32, 32)
            gluDeleteQuadric(quad)

            # 阳光效果（辉光）
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.9, 0.3, 0.3)
            quad = gluNewQuadric()
            gluSphere(quad, self.size * 1.5, 32, 32)
            gluDeleteQuadric(quad)

            glColor4f(1.0, 0.9, 0.3, 0.1)
            quad = gluNewQuadric()
            gluSphere(quad, self.size * 2.0, 32, 32)
            gluDeleteQuadric(quad)

            glEnable(GL_LIGHTING)
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
            glPopMatrix()


class WeatherGLWidget(QGLWidget):
    """3D天气场景渲染部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.weather_type = "晴"
        self.skybox = SkyBox()
        self.sun = Sun()
        self.clouds = [Cloud(np.random.uniform(-2.0, 2.0),
                             np.random.uniform(0.3, 0.8),
                             np.random.uniform(-1.0, 1.0),
                             np.random.uniform(0.1, 0.45)) for _ in range(7)]
        self.raindrops = [Raindrop() for _ in range(100)]
        self.snowflakes = [Snowflake() for _ in range(100)]
        self.rotation = 0
        self.time_hour = datetime.datetime.now().hour

        # 设置定时器更新动画
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(60)  # 约33fps

        # 设置视角
        self.eye_x = 0
        self.eye_y = 0
        self.eye_z = 2

    def initializeGL(self):
        """初始化OpenGL"""
        glClearColor(0.5, 0.7, 0.9, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # 设置光源
        light_pos = [1.0, 1.0, 1.0, 0.0]  # 方向光
        light_ambient = [0.2, 0.2, 0.2, 1.0]
        light_diffuse = [0.8, 0.8, 0.8, 1.0]
        light_specular = [1.0, 1.0, 1.0, 1.0]

        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

        self.skybox.initialize()

    def resizeGL(self, width, height):
        """调整OpenGL视图"""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, width / height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        """绘制OpenGL场景"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # 设置相机位置
        gluLookAt(self.eye_x, self.eye_y, self.eye_z,
                  0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0)

        # 绘制天空盒
        self.skybox.render(self.weather_type)

        # 绘制太阳
        self.sun.update(self.time_hour)
        self.sun.render()

        # 根据天气类型绘制相应元素
        if "云" in self.weather_type or "阴" in self.weather_type or "晴" in self.weather_type:
            for cloud in self.clouds:
                cloud.render()

        if "雨" in self.weather_type or "雷阵" in self.weather_type:
            for raindrop in self.raindrops:
                raindrop.render()

        if "雪" in self.weather_type:
            for snowflake in self.snowflakes:
                snowflake.render()

        # 绘制地面
        self.render_ground()

    def render_ground(self):
        """渲染地面"""
        glPushMatrix()
        glTranslatef(0, -1.0, 0)
        glScalef(5, 0.1, 5)

        # 根据天气设置地面颜色
        if "雪" in self.weather_type:
            glColor3f(0.9, 0.95, 1.0)  # 雪地
        else:
            glColor3f(0.3, 0.6, 0.2)  # 草地

        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.3, 0.6, 0.2, 1.0])

        quad = gluNewQuadric()
        gluDisk(quad, 0, 5, 32, 1)
        gluDeleteQuadric(quad)
        glPopMatrix()

    def update_animation(self):
        """更新动画元素"""
        self.rotation += 0.1

        # 更新云朵
        for cloud in self.clouds:
            cloud.update()

        # 更新雨滴
        for raindrop in self.raindrops:
            raindrop.update()

        # 更新雪花
        for snowflake in self.snowflakes:
            snowflake.update()

        # 更新时间（模拟时间流逝）
        current_time = datetime.datetime.now()
        self.time_hour = current_time.hour + current_time.minute / 60.0

        # 重绘场景
        self.updateGL()

    def set_weather_type(self, weather_type):
        """设置天气类型，用于更新3D场景"""
        self.weather_type = weather_type

        # 根据天气类型调整光照
        if "晴" in weather_type:
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 0.9, 1.0])
        elif "阴" in weather_type or "云" in weather_type:
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])
        elif "雨" in weather_type or "雪" in weather_type:
            glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.5, 0.5, 0.6, 1.0])


class WeatherMainWindow(QMainWindow):
    """天气应用主窗口"""

    def __init__(self):
        super().__init__()
        self.weather_data = WeatherData()
        self.init_ui()
        self.init_threads()
        self.auto_locate()  # 自动定位

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("天气")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧：3D天气场景
        self.gl_widget = WeatherGLWidget()
        main_layout.addWidget(self.gl_widget, 1)

        # 右侧：天气信息面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, 1)

        # 搜索框
        search_layout = QHBoxLayout()
        self.city_input = QLineEdit("北京")
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.search_city)
        search_layout.addWidget(self.city_input)
        search_layout.addWidget(self.search_btn)
        right_layout.addLayout(search_layout)

        # 状态标签
        self.status_label = QLabel("正在加载天气数据...")
        self.status_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.status_label)

        # 选项卡控件
        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)

        # 当前天气标签页
        self.current_tab = QWidget()
        self.init_current_tab()
        self.tabs.addTab(self.current_tab, "当前天气")

        # 预报标签页
        self.forecast_tab = QWidget()
        self.init_forecast_tab()
        self.tabs.addTab(self.forecast_tab, "未来预报")

        # 详细信息标签页
        self.details_tab = QWidget()
        self.init_details_tab()
        self.tabs.addTab(self.details_tab, "详细信息")

        # 状态栏显示最后更新时间
        self.statusBar().showMessage("就绪")

    def init_current_tab(self):
        """初始化当前天气标签页"""
        layout = QVBoxLayout(self.current_tab)

        # 城市和时间信息
        self.city_info = QLabel("城市信息加载中...")
        self.city_info.setAlignment(Qt.AlignCenter)
        self.city_info.setFont(QFont("SimHei", 16, QFont.Bold))
        layout.addWidget(self.city_info)

        # 当前温度
        temp_layout = QHBoxLayout()
        self.temp_label = QLabel("--°C")
        self.temp_label.setFont(QFont("SimHei", 48, QFont.Bold))
        self.temp_label.setAlignment(Qt.AlignCenter)

        self.desc_label = QLabel("天气描述加载中...")
        self.desc_label.setFont(QFont("SimHei", 24))
        self.desc_label.setAlignment(Qt.AlignCenter)

        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.desc_label)
        layout.addLayout(temp_layout)

        # 基本天气信息网格
        grid = QGridLayout()
        grid.setSpacing(10)

        self.feels_like_label = QLabel("--°C")
        self.humidity_label = QLabel("--%")
        self.wind_label = QLabel("--")
        self.pressure_label = QLabel("-- hPa")

        # 添加标签和值
        grid.addWidget(QLabel("体感温度:"), 0, 0)
        grid.addWidget(self.feels_like_label, 0, 1)
        grid.addWidget(QLabel("湿度:"), 0, 2)
        grid.addWidget(self.humidity_label, 0, 3)

        grid.addWidget(QLabel("风向风速:"), 1, 0)
        grid.addWidget(self.wind_label, 1, 1)
        grid.addWidget(QLabel("气压:"), 1, 2)
        grid.addWidget(self.pressure_label, 1, 3)

        layout.addLayout(grid)

        # 日出日落信息
        sun_layout = QHBoxLayout()
        self.sunrise_label = QLabel("日出: --")
        self.sunset_label = QLabel("日落: --")
        sun_layout.addWidget(self.sunrise_label)
        sun_layout.addWidget(self.sunset_label)
        layout.addLayout(sun_layout)

        # 填充空间
        layout.addStretch(1)

    def init_forecast_tab(self):
        """初始化预报标签页"""
        layout = QVBoxLayout(self.forecast_tab)
        self.forecast_list = QListWidget()
        layout.addWidget(self.forecast_list)

    def init_details_tab(self):
        """初始化详细信息标签页"""
        layout = QVBoxLayout(self.details_tab)

        # 创建详细信息表单
        form_group = QGroupBox("天气详细信息")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        self.detail_vis = QLabel("-- km")
        self.windDir = QLabel("--°")
        self.windScale = QLabel("--级")
        self.detail_updated = QLabel("--")

        form_layout.addRow("风向:",self.windDir)
        form_layout.addRow("风力(蒲福风力等级):", self.windScale)
        form_layout.addRow("能见度:", self.detail_vis)
        form_layout.addRow("最后更新:", self.detail_updated)

        layout.addWidget(form_group)
        layout.addStretch(1)

    def init_threads(self):
        """初始化数据获取线程"""
        self.weather_thread = WeatherThread(self.weather_data)
        self.weather_thread.weather_updated.connect(self.on_weather_updated)
        self.weather_thread.start()

    def search_city(self):
        """搜索城市天气"""
        city = self.city_input.text().strip()
        if city:
            self.status_label.setText(f"正在获取 {city} 的天气数据...")
            self.weather_data.update_city(city)
            # 立即获取数据
            QTimer.singleShot(100, lambda: self.weather_thread.weather_updated.emit(
                self.weather_data.fetch_weather_data()
            ))

    def on_weather_updated(self, result):
        """处理天气数据更新"""
        if "error" in result:
            self.status_label.setText(f"错误: {result['error']}")
            return

        self.status_label.setText(f"天气数据更新于: {self.weather_data.last_updated}")
        self.statusBar().showMessage(f"最后更新: {self.weather_data.last_updated}")

        # 更新当前天气信息
        current = self.weather_data.current
        self.city_info.setText(f"{current['city']}")
        self.temp_label.setText(f"{current['temperature']}°C")

        # 获取天气图标
        weather_icon = "☀️"
        for key, icon in WEATHER_ICONS.items():
            if key in current["description"]:
                weather_icon = icon
                break

        self.desc_label.setText(f"{weather_icon} {current['description']}")
        self.feels_like_label.setText(f"{current['feels_like']}°C")
        self.humidity_label.setText(f"{current['humidity']}%")
        self.wind_label.setText(f"{current['wind_dir']} {current['wind_speed']} km/h")
        self.pressure_label.setText(f"{current['pressure']} hPa")
        self.sunrise_label.setText(f"日出: {current['sunrise']}")
        self.sunset_label.setText(f"日落: {current['sunset']}")

        # 更新详细信息
        self.detail_vis.setText(f"{current['vis']} km")
        self.windDir.setText(current['windDir'])
        self.windScale.setText(f"{current['windScale']}级")
        self.detail_updated.setText(current['updated_at'])

        # 更新预报列表
        self.forecast_list.clear()
        for day in self.weather_data.forecast:
            # 获取天气图标
            day_icon = "☀️"
            for key, icon in WEATHER_ICONS.items():
                if key in day["description"]:
                    day_icon = icon
                    break

            item = QListWidgetItem(
                f"{day['date']} {day['day']}: {day_icon} {day['description']}, "
                f"最高 {day['temp_max']}°C, 最低 {day['temp_min']}°C, "
                f"{day['wind_dir']} {day['wind_scale']}级"
            )
            self.forecast_list.addItem(item)

        # 更新3D场景
        self.gl_widget.set_weather_type(current["description"])

    def auto_locate(self):
        """自动定位并更新城市"""
        self.status_label.setText("正在自动定位...")
        tmp = self.weather_data.get_city_by_location()
        if tmp is not None:
            city = tmp
        else:
            print("获取城市失败，使用默认参数：北京")
            city = "北京"
        if city:
            self.city_input.setText(city)
            self.weather_data.update_city(city)
            self.status_label.setText(f"已定位到: {city}，正在获取天气数据...")
            # 立即获取数据
            QTimer.singleShot(100, lambda: self.weather_thread.weather_updated.emit(
                self.weather_data.fetch_weather_data()
            ))
        else:
            self.status_label.setText("自动定位失败，使用默认城市")

    def closeEvent(self, event):
        """窗口关闭时停止线程"""
        self.weather_thread.stop()
        event.accept()


if __name__ == "__main__":
    # 初始化OpenGL
    glutInit(sys.argv)

    app = QApplication(sys.argv)

    # 设置全局字体，确保中文显示正常
    font = QFont("SimHei")
    app.setFont(font)

    window = WeatherMainWindow()
    window.show()

    sys.exit(app.exec_())
