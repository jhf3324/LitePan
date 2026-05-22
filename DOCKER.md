# LitePan

LitePan 是一个轻量级网盘聚合工具，支持通过网页、WebDAV 和 STRM 的方式访问网盘内容。

本项目最初是个人自用工具，目前仍处于 Beta 测试阶段，可能存在一些 Bug 或兼容性问题。现在开放出来与大家分享，欢迎反馈使用过程中遇到的问题。

## 主要功能

- 支持多网盘账号管理（115 / 123 / 百度 / 夸克 / 光鸭 / 移动 / 天翼 / WebDAV）
- 支持对外 WebDAV 挂载分享
- 支持 STRM 生成与播放
- 支持缓存持久化与缓存保持
- 支持 Docker 部署

## 使用文档

如果你是第一次使用 LitePan，建议先查看文档站：

```text
https://www.litepan.top
```

## 快速启动

```bash
docker run -d \
  --name litepan \
  --restart unless-stopped \
  --network host \
  -e TZ=Asia/Shanghai \
  -p 5211:5211 \
  -v ./data:/app/data \
  -v ./log:/app/log \
  -v ./strm:/app/strm \
  -v ./plugins:/app/plugins \
  ponphil/litepan:latest
```

启动后访问：

```text
http://服务器IP:5211
```

## 数据目录

建议挂载以下目录，避免容器重建后数据丢失：

- `/app/data`
- `/app/log`
- `/app/strm`
- `/app/plugins`

## 说明

LitePan 目前主要面向个人自用和轻量部署场景，建议先在本地测试后再部署到公网。

如果需要公网访问，建议关闭公开文件列表，并设置强密码。

资源搜索插件导入代码查看密码：8888
