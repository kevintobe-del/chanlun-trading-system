# 群晖 NAS 部署指南

推荐使用群晖 **Container Manager + Docker Compose**。容器内已经包含前端静态资源、FastAPI 服务、Yahoo Finance、Tushare 和 AKShare 依赖。

> 本应用没有用户登录或权限系统。建议只在局域网、Tailscale/ZeroTier 等可信 VPN 内访问；若需要公网访问，必须在反向代理前增加身份认证。不要直接把 8791 端口映射到公网。

## 一、部署前准备

1. 在套件中心安装 Container Manager。
2. 在控制面板启用 SSH，登录 NAS。
3. 确认 Git 和 Docker Compose 可用：

```bash
git --version
docker compose version
```

4. 选择存放项目的共享目录，例如：

```bash
cd /volume1/docker
git clone https://github.com/noahnan-max/chanlun-trading-system.git
cd chanlun-trading-system
```

## 二、设置容器运行用户

查询当前群晖用户的 UID/GID：

```bash
id
```

在项目目录创建 `.env`，把下面数字替换成 `id` 返回的值：

```dotenv
PUID=1026
PGID=100
CHANLUN_PORT=8791
```

创建持久化目录，并确保当前用户可写：

```bash
mkdir -p data
chmod 700 data
```

数据源配置和股票池分别保存在 `data/data-sources.json` 与 `data/watchlists.json`。更新或重建容器不会丢失。

## 三、构建并启动

```bash
docker compose -f docker-compose.synology.yml up -d --build
docker compose -f docker-compose.synology.yml ps
docker compose -f docker-compose.synology.yml logs --tail=100
```

健康检查：

```bash
curl http://127.0.0.1:8791/api/health
```

局域网浏览器访问：

```text
http://群晖局域网IP:8791
```

## 四、群晖反向代理

在“控制面板 → 登录门户 → 高级 → 反向代理服务器”中新建规则：

- 来源：HTTPS、自定义域名、443；
- 目标：HTTP、`127.0.0.1`、`8791`；
- 为域名绑定有效证书；
- 公网场景在入口前增加 Cloudflare Access、Authelia、Authentik 或可信 VPN，不能只依赖一个难猜的域名。

如果仅通过反向代理或 VPN 使用，可以在 `docker-compose.synology.yml` 中把端口映射改成：

```yaml
ports:
  - "127.0.0.1:8791:8791"
```

部分群晖 Docker 版本不接受绑定到回环地址；遇到这种情况，保留原映射并用群晖防火墙限制 8791 只允许局域网网段访问。

## 五、更新与备份

更新：

```bash
git pull --ff-only
docker compose -f docker-compose.synology.yml up -d --build
docker image prune -f
```

不要执行 `docker compose down -v`，也不要删除 `data` 目录。备份只需归档配置目录：

```bash
tar -czf chanlun-visual-config-backup.tgz data
```

## 六、行情数据注意事项

- AKShare 会优先使用东方财富，失败时自动回退新浪行情；
- Yahoo Finance 可能根据网络出口限流，群晖长期运行更适合配置 AKShare 或 Tushare；
- Tushare Token 只保存在 `data/data-sources.json`，请把 `data` 目录权限限制为部署用户可读写；
- 若 NAS 使用全局代理，检查容器的 `HTTP_PROXY`、`HTTPS_PROXY` 与 `NO_PROXY`，避免国内行情域名被送入不可用代理；
- AKShare/Pandas 占用内存较高，建议至少为容器预留 1 GB，较低配置的 ARM 群晖建议预留 2 GB 并避免频繁刷新。

## 七、常用排错命令

```bash
docker compose -f docker-compose.synology.yml ps
docker compose -f docker-compose.synology.yml logs -f --tail=200
docker inspect --format '{{json .State.Health}}' chanlun-visual
curl http://127.0.0.1:8791/api/health
```

如果看到权限错误，确认 `.env` 中的 PUID/PGID 与 `data` 目录所有者一致；如果镜像在低端 NAS 上构建过慢，可在电脑上构建并推送到私有镜像仓库，再让群晖直接拉取。
