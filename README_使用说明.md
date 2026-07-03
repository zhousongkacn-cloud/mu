# 咖啡直播 GitHub 云端自动更新 M3U

这个包的作用：不用一直开电脑，让 GitHub Actions 定时运行脚本，自动生成 `coffee_live.m3u`。APTV 只需要添加一次固定订阅地址。

## 1. 创建 GitHub 仓库

1. 打开 GitHub，新建一个仓库，例如：`coffee-live-m3u`
2. 建议设为 Public，因为 APTV 读取 raw 文件更方便
3. 上传本包内全部文件，包括：
   - `generate_coffee_m3u.py`
   - `.github/workflows/update_m3u.yml`
   - `README_使用说明.md`

## 2. 打开 Actions 权限

进入仓库：

`Settings → Actions → General`

确认：

- Actions permissions：允许运行 Actions
- Workflow permissions：选择 `Read and write permissions`

## 3. 手动运行一次

进入：

`Actions → Update Coffee Live M3U → Run workflow`

运行成功后，仓库根目录会生成：

`coffee_live.m3u`

## 4. APTV 添加订阅地址

地址格式：

`https://raw.githubusercontent.com/你的用户名/coffee-live-m3u/main/coffee_live.m3u`

例如你的 GitHub 用户名是 `abc123`，仓库名是 `coffee-live-m3u`，那就是：

`https://raw.githubusercontent.com/abc123/coffee-live-m3u/main/coffee_live.m3u`

在 APTV 中添加这个 M3U URL，并开启播放列表自动刷新。

## 5. 更新频率

默认每 15 分钟运行一次：

`7,22,37,52 * * * *`

不建议改成 5 分钟，容易遇到 GitHub 调度延迟，也可能请求过于频繁。

## 6. 注意

- GitHub Actions 的定时任务不是精确秒级，可能会延迟。
- 公共仓库如果 60 天没有任何活动，定时任务可能会被 GitHub 自动停用。
- 如果当天没有比赛，生成的 M3U 可能只有 `#EXTM3U`。
- APTV 有时会缓存播放列表，看不到新比赛时手动刷新一下播放源。
