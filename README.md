# 天气应用 (Weather App)

一个简单美观的天气应用，支持实时天气查询和未来7天预报，包含3D天气场景可视化效果。

## 功能特点

- 实时天气查询，包括温度、湿度、风向风速等信息
- 未来7天天气预报
- 3D天气场景可视化，根据天气状况动态展示
- 自动定位功能，获取当前城市天气
- 支持手动搜索城市天气

## 截图预览

(此处可添加应用截图)

## 安装与使用

### 前提条件

- Python 3.6+
- 所需依赖库：`PyQt5`, `requests`, `numpy`, `geopy`, `PyOpenGL`

### 安装步骤

1. 克隆或下载本项目
   ```bash
   git clone https://github.com/yourusername/weather-app.git
   cd weather-app
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 配置和风天气API密钥
   - 注册和风天气开发者账号并获取API密钥
   - 设置环境变量：`export QWEATHER_KEY="你的API密钥"`
   - 或直接在代码中替换`QWEATHER_KEY`的值

4. 运行应用
   ```bash
   python app-release.py
   ```

## 许可证

本项目采用 **GNU GENERAL PUBLIC LICENSE** 许可协议。详情请参见 [LICENSE](LICENSE) 文件。

## 致谢

- 使用 [和风天气API](https://dev.qweather.com/) 提供天气数据
- 使用 PyQt5 构建GUI界面
- 使用 OpenGL 实现3D天气场景可视化

## 贡献

欢迎提交issue和pull request，帮助改进这个项目。如果喜欢本项目，请给它一个星标⭐！

## 作者

Chidc
