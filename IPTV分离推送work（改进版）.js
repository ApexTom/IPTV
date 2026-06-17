// ==========================================
// IPTV M3U Aggregator Worker
// Multi Source Independent + Group Split + KV Cache
// Manual Refresh + Telegram Notify
// ==========================================
//
// KV Namespace:
// M3U_KV
//
// Secrets:
// ADMIN_KEY
// SOURCE_URLS
// TG_TOKEN
// TG_CHAT_ID
//
// ==========================================
//
// SOURCE_URLS 格式（每行一个，可选关键词用|分隔）
//
// https://a.com/a.m3u
// https://b.com/b.m3u|频道宝
// https://c.com/c.m3u|MyIPTV
//
// 若不指定关键词，自动从URL中提取域名关键词
//
// ==========================================
//
// 更新：https://xxx.workers.dev/update?key=你的key
// 分类列表：https://xxx.workers.dev/list
// 获取分类：https://xxx.workers.dev/关键词_all.m3u
//
// ==========================================

// ==========================================
// 工具函数（先定义，避免 ES Module 作用域问题）
// ==========================================

function sanitize(str) {
  return str
    .replace(/[^\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffefa-zA-Z0-9]/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "")
    .trim() || "Other"
}

function isValidGroup(name) {
  return name.replace(/[-_]+/g, "").length > 0
}

function toKVKey(prefix, group) {
  return prefix + "_" + group + ".m3u"
}

function extractKeyword(sourceUrl) {
  try {
    const u = new URL(sourceUrl)
    const host = u.hostname.replace(/^www\./, "")
    const parts = host.split(".")
    const kw = parts.length >= 2 ? parts[parts.length - 2] : parts[0]
    return sanitize(kw) || "source"
  } catch (e) {
    return "source"
  }
}

// ==========================================
// 拉取单个源（返回对象含状态码和错误信息）
// ==========================================

async function fetchSource(sourceUrl, keyword) {
  try {
    console.log("Fetching:", keyword, sourceUrl)
    const resp = await fetch(sourceUrl, {
      headers: { "User-Agent": "Mozilla/5.0" }
    })
    if (!resp.ok) {
      console.log("HTTP error:", resp.status, sourceUrl)
      return { text: null, status: resp.status, error: `HTTP ${resp.status}` }
    }
    return { text: await resp.text(), status: 200, error: null }
  } catch (e) {
    console.log("Fetch error:", keyword, e.message)
    return { text: null, status: 0, error: e.message }
  }
}

// ==========================================
// 解析 M3U 文本
// ==========================================

function parseM3U(text) {
  const lines = text.split(/\r?\n/)
  const groups = {}
  let channelCount = 0

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (!line.startsWith("#EXTINF")) continue

    const extinf = line
    let streamUrl = ""
    const extraLines = []  // 收集 #KODIPROP 等附加行

    for (let j = i + 1; j < lines.length; j++) {
      const next = lines[j].trim()
      if (!next) continue
      if (next.startsWith("#EXTINF")) break
      if (
        next.startsWith("http://") ||
        next.startsWith("https://") ||
        next.startsWith("rtmp://") ||
        next.startsWith("rtsp://") ||
        next.startsWith("rtp://")
      ) {
        streamUrl = next
        break
      }
      // #KODIPROP、#EXTVLCOPT 等附加行，原样保留
      if (next.startsWith("#")) {
        extraLines.push(next)
      }
    }

    if (!streamUrl) continue

    const match = extinf.match(/group-title="([^"]*)"/)
    let group = match ? match[1].trim() : "Other"
    if (!group) group = "Other"
    group = sanitize(group)
    if (!isValidGroup(group)) group = "Other"

    if (!groups[group]) groups[group] = []
    groups[group].push(extinf)
    for (const extra of extraLines) {
      groups[group].push(extra)
    }
    groups[group].push(streamUrl)
    channelCount++
  }

  return { groups, channelCount }
}

// ==========================================
// Telegram 通知
// ==========================================

async function sendTG(env, text) {
  if (!env.TG_TOKEN || !env.TG_CHAT_ID) return
  try {
    await fetch(
      `https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: env.TG_CHAT_ID, text })
      }
    )
  } catch (e) {
    console.log("TG Error:", e)
  }
}

// ==========================================
// 更新处理
// ==========================================

async function handleUpdate(request, env) {
  const url = new URL(request.url)
  const key = url.searchParams.get("key")

  if (!key || key !== env.ADMIN_KEY) {
    return new Response("Unauthorized", { status: 401 })
  }

  const baseUrl = `${url.protocol}//${url.host}`

  // 执行锁：60秒内只允许执行一次，防止浏览器/CF 重试重复触发
  const existingLock = await env.M3U_KV.get("__UPDATE_LOCK__")
  if (existingLock) {
    return new Response(
      "Update already in progress, please wait and retry.",
      { status: 429, headers: { "Content-Type": "text/plain;charset=utf-8" } }
    )
  }
  await env.M3U_KV.put("__UPDATE_LOCK__", "1", { expirationTtl: 60 })

  const startTime = Date.now()

  // 解析源列表
  const sourceList = env.SOURCE_URLS
    .split("\n")
    .map(v => v.trim())
    .filter(Boolean)
    .map(line => {
      const parts = line.split("|")
      const sourceUrl = parts[0].trim()
      const keyword = parts[1]
        ? sanitize(parts[1].trim())
        : extractKeyword(sourceUrl)
      return { sourceUrl, keyword }
    })

  if (sourceList.length === 0) {
    return new Response("No SOURCE_URLS", { status: 500 })
  }

  // 并发拉取
  const fetchResults = await Promise.allSettled(
    sourceList.map(({ sourceUrl, keyword }) => fetchSource(sourceUrl, keyword))
  )

  let loadedCount = 0
  let failedCount = 0
  let totalChannels = 0
  const allGroupFiles = []
  const sourceStats = []

  // 逐源解析写入 KV
  for (let i = 0; i < fetchResults.length; i++) {
    const result = fetchResults[i]
    const { sourceUrl, keyword } = sourceList[i]

    if (result.status === "rejected" || !result.value || !result.value.text) {
      const errMsg = result.value?.error || "未知错误"
      console.log("Source failed:", sourceUrl, errMsg)
      failedCount++
      sourceStats.push({ keyword, ok: false, channels: 0, groups: 0, groupKeys: [], error: errMsg })
      continue
    }

    const { groups, channelCount } = parseM3U(result.value.text)

    if (channelCount === 0) {
      console.log("No channels in:", sourceUrl)
      failedCount++
      sourceStats.push({ keyword, ok: false, channels: 0, groups: 0, groupKeys: [], error: "解析后0频道" })
      continue
    }

    loadedCount++
    totalChannels += channelCount
    const sourceGroupKeys = []

    for (const [groupName, lines] of Object.entries(groups)) {
      const kvKey = toKVKey(keyword, groupName)
      await env.M3U_KV.put(kvKey, "#EXTM3U\n" + lines.join("\n") + "\n")
      sourceGroupKeys.push(kvKey)
      allGroupFiles.push({ kvKey, display: groupName })
    }

    const allKey = `${keyword}_all.m3u`
    await env.M3U_KV.put(allKey, "#EXTM3U\n" + Object.values(groups).flat().join("\n") + "\n")
    allGroupFiles.push({ kvKey: allKey, display: "全部频道" })

    sourceStats.push({
      keyword,
      ok: true,
      channels: channelCount,
      groups: sourceGroupKeys.length,
      groupKeys: sourceGroupKeys
    })

    console.log(`Source OK: ${keyword} | ${channelCount} channels | ${sourceGroupKeys.length} groups`)
  }

  // 去重后保存分类列表
  const seenKeys = new Set()
  const uniqueEntries = []
  for (const entry of allGroupFiles) {
    if (!seenKeys.has(entry.kvKey)) {
      seenKeys.add(entry.kvKey)
      uniqueEntries.push(entry)
    }
  }
  await env.M3U_KV.put("__GROUP_LIST__", JSON.stringify(uniqueEntries))

  const seconds = ((Date.now() - startTime) / 1000).toFixed(2)

  // 构造 TG 通知（完整链接）
  let sourceDetail = ""
  for (const stat of sourceStats) {
    if (!stat.ok) {
      sourceDetail += `❌ ${stat.keyword}  失败原因: ${stat.error}\n\n`
      continue
    }
    const allLink = `${baseUrl}/${stat.keyword}_all.m3u`
    const groupLinks = stat.groupKeys.sort().map(k => `${baseUrl}/${k}`).join("\n")
    sourceDetail +=
      `✅ ${stat.keyword}  频道: ${stat.channels} | 分组: ${stat.groups}\n` +
      `${allLink}\n` +
      (groupLinks ? groupLinks + "\n" : "") +
      "\n"
  }

  const tgMessage =
`✅ IPTV 更新完成
成功源: ${loadedCount}/${sourceList.length}  失败源: ${failedCount}
频道总数: ${totalChannels}  耗时: ${seconds}s

${sourceDetail.trimEnd()}
`

  await sendTG(env, tgMessage)

  return new Response(tgMessage, {
    status: 200,
    headers: { "Content-Type": "text/plain;charset=utf-8" }
  })
}

// ==========================================
// 分类列表页
// ==========================================

async function handleList(env) {
  const data = await env.M3U_KV.get("__GROUP_LIST__")

  if (!data) {
    return new Response(
      "No Group List，请先访问 /update?key=xxx 更新",
      { status: 404, headers: { "Content-Type": "text/plain;charset=utf-8" } }
    )
  }

  const rawEntries = JSON.parse(data)
  const entries = rawEntries.map(e =>
    typeof e === "object" ? e : { kvKey: e, display: e }
  )

  const byKeyword = {}
  for (const entry of entries) {
    const idx = entry.kvKey.indexOf("_")
    const kw = idx !== -1 ? entry.kvKey.slice(0, idx) : "Other"
    if (!byKeyword[kw]) byKeyword[kw] = []
    byKeyword[kw].push(entry)
  }

  let sectionsHtml = ""
  for (const [kw, fileEntries] of Object.entries(byKeyword)) {
    const sorted = [
      ...fileEntries.filter(e => e.kvKey.endsWith("_all.m3u")),
      ...fileEntries.filter(e => !e.kvKey.endsWith("_all.m3u"))
    ]
    let itemsHtml = ""
    for (const entry of sorted) {
      const isAll = entry.kvKey.endsWith("_all.m3u")
      const label = isAll ? `📋 ${entry.display}（全部频道）` : `📺 ${entry.display}`
      itemsHtml += `\n        <li><a href="/${entry.kvKey}">${label}</a></li>`
    }
    sectionsHtml += `
      <section>
        <h3>📡 ${kw}</h3>
        <ul>${itemsHtml}
        </ul>
      </section>`
  }

  const html =
`<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IPTV Groups</title>
<style>
  body { background:#111; color:#e0e0e0; font-family:sans-serif; padding:24px; max-width:800px; margin:0 auto; }
  h2 { color:#fff; border-bottom:1px solid #333; padding-bottom:10px; }
  h3 { color:#4da3ff; margin-top:0; margin-bottom:8px; }
  ul { list-style:none; padding:0; margin:0; }
  li { margin:8px 0; }
  a { color:#7ec8ff; text-decoration:none; font-size:14px; }
  a:hover { color:#fff; text-decoration:underline; }
  section { background:#1a1a1a; border-radius:8px; padding:16px 20px; margin-bottom:16px; }
</style>
</head>
<body>
<h2>📺 IPTV Groups</h2>
${sectionsHtml}
</body>
</html>`

  return new Response(html, {
    headers: { "Content-Type": "text/html;charset=utf-8" }
  })
}

// ==========================================
// Worker 入口（export default 放最后）
// ==========================================

export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url)

      if (url.pathname === "/update") return await handleUpdate(request, env)
      if (url.pathname === "/list") return await handleList(env)

      if (url.pathname === "/") {
        return new Response(
`IPTV Aggregator Worker

/list               - 查看所有分类
/update?key=xxx     - 手动刷新
/关键词_all.m3u    - 获取指定源全部频道
/关键词_分组.m3u   - 获取指定分类
`,
          { status: 200, headers: { "Content-Type": "text/plain;charset=utf-8" } }
        )
      }

      // 获取 m3u 文件
      // decodeURIComponent 还原浏览器对中文路径的编码，与 KV key 对齐
      let kvKey
      try {
        kvKey = decodeURIComponent(url.pathname.replace(/^\/+/, ""))
      } catch (e) {
        kvKey = url.pathname.replace(/^\/+/, "")
      }

      const data = await env.M3U_KV.get(kvKey)
      if (!data) return new Response("M3U Not Found", { status: 404 })

      return new Response(data, {
        status: 200,
        headers: {
          "Content-Type": "application/x-mpegURL; charset=utf-8",
          "Cache-Control": "public, max-age=3600"
        }
      })

    } catch (e) {
      return new Response("Worker Error\n\n" + e.stack, { status: 500 })
    }
  }
}
