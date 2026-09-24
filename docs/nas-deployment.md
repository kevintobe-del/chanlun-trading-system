# 群晖 NAS（DSM 7）部署指南

推荐使用群晖 **Container Manager + Docker Compose**。容器内已经包含前端静态资源、FastAPI 服务、Yahoo Finance、Tushare、AKShare 和本地化多周期缠论报告引擎。

> 本应用没有用户登录或权限系统，设置页面还可能保存行情 Token 和 Webhook。推荐通过 Tailscale IP 从外网访问，不需要开放路由器端口。公网 IP 端口映射仅适合临时联通测试，不适合长期裸露运行。

## 一、部署前准备

1. 在套件中心安装 Container Manager。
2. 在控制面板启用 SSH，登录 NAS。
3. 确认 CPU 架构、Git 和 Docker Compose 可用：

```bash
uname -m
git --version
docker compose version
```

常见输出为 `x86_64` 或 `aarch64`；本项目使用的 Node/Python 基础镜像均提供这两种架构。若套件中心没有 Container Manager，需要先确认该 NAS 型号是否支持容器。

4. 选择存放项目的共享目录，例如：

```bash
cd /volume1/docker
git clone https://github.com/kevintobe-del/chanlun-trading-system.git
cd chanlun-trading-system
```

## 二、设置容器运行用户

查询当前群晖用户的 UID/GID：

```bash
id
```

复制示例配置并把 PUID/PGID 替换成 `id` 返回的值：

```bash
cp .env.synology.example .env
vi .env
```

创建持久化目录，并确保当前用户可写：

```bash
mkdir -p data
chmod 700 data
```

数据源配置和股票池分别保存在 `data/data-sources.json` 与 `data/watchlists.json`。报告历史、缓存、Webhook 加密配置与本机密钥位于 `data/reports/`。更新或重建容器不会丢失。

## 三、构建并启动

报告引擎已经放在纯英文路径 `src/chanlun_local`，并从 Docker 构建上下文排除了原始中文子项目目录，以兼容 DSM 7 较旧 BuildKit 的 `followpaths` 限制。

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

## 四、推荐：使用 Tailscale IP 从外网访问

这种方式依然是通过 IP 访问，但 IP 是 NAS 的 Tailscale 私网地址（通常为 `100.x.y.z`）。访问设备必须加入同一个 Tailscale 网络；通信端到端加密，不需要公网 IPv4、DDNS、路由器端口转发或把应用公开给所有互联网用户。

1. 在群晖套件中心安装 Tailscale，并登录自己的 Tailscale 账户。
2. 在需要外网访问的电脑或手机上安装 Tailscale，并登录同一账户。
3. 在群晖 Tailscale 页面查看 NAS 的 IPv4 地址，或通过 SSH 执行：

```bash
/var/packages/Tailscale/target/bin/tailscale ip -4
```

4. 在外网设备浏览器访问：

```text
http://100.x.y.z:8791
```

DSM 7 默认允许 Tailscale 连接进入 NAS，访问本 Web 应用不需要启用 TUN。只有 NAS 上的其他应用还需要主动连接到别的 Tailscale 设备时，才需要按 Tailscale 官方说明执行 `configure-host`。

如果 DSM 防火墙已经开启，在“控制面板 → 安全性 → 防火墙”添加允许规则：

- 来源：`100.64.0.0/10`；
- 协议：TCP；
- 目标端口：`8791`；
- 规则放在拒绝规则之前。

不要在路由器上转发 8791。此时应用也仍可通过局域网 IP 访问；如果只希望 Tailscale 设备访问，可进一步用 DSM 防火墙限制来源。

## 五、可选：通过公网 IPv4 和端口访问

只有在访问者无法安装 Tailscale时才考虑此方式。先确认路由器 WAN 地址是真实公网 IPv4，而不是 `10.0.0.0/8`、`100.64.0.0/10`、`172.16.0.0/12` 或 `192.168.0.0/16`；如果运营商使用 CGNAT，端口映射不会生效，需要申请公网 IPv4 或改用 Tailscale。

在路由器中创建一条 TCP 转发：

```text
外部端口 48791  →  群晖局域网IP:8791
```

然后在 DSM 防火墙允许 TCP 8791，优先限制为你自己的固定来源 IP。外网测试地址：

```text
http://公网IPv4:48791
```

不要转发 DSM 的 `5000/5001`、SSH `22`，也不要设置 DMZ。上述 HTTP 地址没有传输加密，应用本身也没有登录验证，因此只用于短时间连通测试；长期公开服务应改用域名、HTTPS 反向代理和额外身份认证。

## 六、群晖反向代理（长期公开服务）

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

## 七、更新与备份

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

## 八、行情数据注意事项

- AKShare 会优先使用东方财富，失败时按证券类型自动回退腾讯或新浪行情；
- Yahoo Finance 可能根据网络出口限流，群晖长期运行更适合配置 AKShare 或 Tushare；
- Tushare Token 只保存在 `data/data-sources.json`，请把 `data` 目录权限限制为部署用户可读写；
- 若 NAS 使用全局代理，检查容器的 `HTTP_PROXY`、`HTTPS_PROXY` 与 `NO_PROXY`，避免国内行情域名被送入不可用代理；
- AKShare/Pandas 占用内存较高，建议至少为容器预留 1 GB，较低配置的 ARM 群晖建议预留 2 GB 并避免频繁刷新。
- 自动报告会使用当前唯一生效的数据源，并在交易日按设置时间依次处理自选池；默认 Compose 保持单个应用进程，可避免多个进程重复调度。搜索单只股票只生成页面报告，不会自动推送 Webhook。

## 九、常用排错命令

```bash
docker compose -f docker-compose.synology.yml ps
docker compose -f docker-compose.synology.yml logs -f --tail=200
docker inspect --format '{{json .State.Health}}' chanlun-visual
curl http://127.0.0.1:8791/api/health
curl http://群晖局域网IP:8791/api/health
```

如果局域网能访问、外网不能访问：Tailscale 模式检查访问设备是否登录同一账户以及 DSM 防火墙是否允许 `100.64.0.0/10`；公网模式检查是否为 CGNAT、路由器端口转发目标是否为 NAS 的固定局域网 IP，以及运营商是否封锁入站端口。

如果看到权限错误，确认 `.env` 中的 PUID/PGID 与 `data` 目录所有者一致；如果镜像在低端 NAS 上构建过慢，可在电脑上构建并推送到私有镜像仓库，再让群晖直接拉取。
