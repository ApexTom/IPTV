/**
 * Cloudflare Worker IPTV Proxy V3.1.2 (Fixed)
 *
 * 修复记录（相对 V3.1.1）：
 * 1. [Fix] URL 提取改用完整 href，不再丢失 query string（修复鉴权 token 丢失导致 403）
 * 2. [Fix] 请求头改为白名单式手动构造，清除 CF 特征头（cf-connecting-ip 等）
 * 3. [Fix] 白名单匹配改为后缀感知模式（以 . 开头的按域名后缀匹配，其余按子串匹配）
 * 4. [Fix] m3u8 判断条件补充 .m3u 后缀及 text/plain 类型的 m3u 路径
 * 5. [Fix] 首页字符串去除 Unicode 特殊字符，避免 Cloudflare 编辑器 SyntaxError
 *
 * 核心逻辑：
 * - 默认代理模式：除非域名命中 WHITE_LIST，否则所有请求强制走 BACKUP_PROXY 反代
 * - 深度 M3U/M3U8 重写：递归重写所有 URL（含 #EXT-X-KEY / #EXT-X-MAP），确保切片锁死在 Worker 中
 *
 * 环境变量：
 *   WHITE_LIST    逗号分隔，直连域名关键词或后缀（如 .cn,.xyz,cctv,fengshows）
 *   BACKUP_PROXY  反代优选 IP/域名（如 ProxyIP.US.CMLiussss.net）
 *   ADMIN_KEY     预留管理密钥（当前版本暂未启用，占位用）
 */

const SAFE_PREFIX = "/proxy";

// --- 工具函数 ---

/**
 * 后缀感知白名单匹配
 * - 关键词以 "." 开头 -> 严格后缀匹配（.cn 只匹配 xxx.cn，不匹配 xxx.cn.evil.com）
 * - 关键词不以 "." 开头 -> 子串匹配（cctv 匹配 live.cctv.com）
 */
function matchList(list, hostname) {
    var h = hostname.toLowerCase();
    return list.some(function(k) {
        var kl = k.toLowerCase();
        if (kl.startsWith(".")) {
            return h.endsWith(kl) || h === kl.slice(1);
        }
        return h.includes(kl);
    });
}

/**
 * 从完整请求 URL 中提取被代理的目标 URL 字符串
 * 保留 query string，修复 https:/// 三斜杠问题
 */
function extractTargetUrl(requestUrl) {
    var reqUrl = new URL(requestUrl);
    var prefix = reqUrl.origin + SAFE_PREFIX + "/";
    var target = reqUrl.href.substring(prefix.length);
    target = target.replace(/^(https?):\/+(?!\/)/, "$1://");
    return target;
}

/**
 * 构造安全的转发请求头（不透传 CF 特征头）
 */
function buildHeaders(targetUrl) {
    var headers = new Headers();
    headers.set("Host", targetUrl.host);
    headers.set("Origin", targetUrl.origin);
    headers.set("Referer", targetUrl.origin + "/");
    headers.set("Connection", "close");
    headers.set("User-Agent", "AppleCoreMedia/1.0.0.21E213 (iPhone; CPU OS 17_4_1 like Mac OS X)");
    return headers;
}

// --- 主逻辑 ---

export default {
    async fetch(request, env) {
        var url = new URL(request.url);
        var path = url.pathname;
        var proxyOrigin = url.origin;

        // 读取环境变量
        var BACKUP_PROXY = (env.BACKUP_PROXY || "").trim();
        var WHITE_LIST = (env.WHITE_LIST || "")
            .split(",")
            .map(function(i) { return i.trim(); })
            .filter(function(i) { return i !== ""; });

        // 1. 首页状态信息
        if (path === "/" || path === "") {
            var proxyStatus = BACKUP_PROXY
                ? "Enabled -> " + BACKUP_PROXY
                : "Disabled (direct mode)";
            var whiteInfo = WHITE_LIST.length + " rules -> [" + WHITE_LIST.join(", ") + "]";
            return new Response(
                "IPTV Proxy Engine V3.1.2\n" +
                "--------------------------\n" +
                "Proxy    : " + proxyStatus + "\n" +
                "Whitelist: " + whiteInfo + "\n" +
                "Mode     : suffix-aware match\n" +
                "Strategy : proxy-by-default, whitelist = direct",
                { headers: { "Content-Type": "text/plain; charset=utf-8" } }
            );
        }

        // 2. 代理转发路由
        if (!path.startsWith(SAFE_PREFIX + "/")) {
            return new Response("Not Found", { status: 404 });
        }

        // 提取目标 URL
        var actualUrlStr = extractTargetUrl(request.url);
        if (!actualUrlStr.startsWith("http")) {
            return new Response("Invalid Target URL: must start with http(s)://", { status: 400 });
        }

        var targetUrl;
        try {
            targetUrl = new URL(actualUrlStr);
        } catch (e) {
            return new Response("Invalid Target URL: " + e.message, { status: 400 });
        }

        // 构造安全请求头
        var newHeaders = buildHeaders(targetUrl);

        // 决定出口：命中白名单 -> 直连；否则 -> 走 BACKUP_PROXY
        var isWhiteListed = matchList(WHITE_LIST, targetUrl.hostname);
        var fetchUrl = actualUrlStr;
        if (!isWhiteListed && BACKUP_PROXY) {
            fetchUrl = "https://" + BACKUP_PROXY + targetUrl.pathname + targetUrl.search;
        }

        try {
            var response = await fetch(fetchUrl, {
                method: "GET",
                headers: newHeaders,
                redirect: "follow"
            });

            var contentType = (response.headers.get("Content-Type") || "").toLowerCase();

            // 3. M3U / M3U8 深度重写
            var isM3U =
                contentType.includes("mpegurl") ||
                contentType.includes("m3u8") ||
                targetUrl.pathname.endsWith(".m3u8") ||
                targetUrl.pathname.endsWith(".m3u") ||
                (contentType.includes("text/plain") && targetUrl.pathname.toLowerCase().includes("m3u"));

            if (isM3U && response.status === 200) {
                var text = await response.text();

                var rewritten = text.split(/\r?\n/).map(function(line) {
                    var trimmed = line.trim();

                    // 空行原样保留
                    if (!trimmed) return line;

                    // 注释行：处理携带 URI 的特殊标签
                    if (trimmed.startsWith("#")) {
                        if (trimmed.startsWith("#EXT-X-KEY") || trimmed.startsWith("#EXT-X-MAP")) {
                            return trimmed.replace(/URI="([^"]+)"/g, function(match, p1) {
                                var absUrl;
                                try {
                                    absUrl = new URL(p1, targetUrl.href).href;
                                } catch (e) {
                                    return match;
                                }
                                var inWhite = matchList(WHITE_LIST, new URL(absUrl).hostname);
                                return inWhite
                                    ? "URI=\"" + absUrl + "\""
                                    : "URI=\"" + proxyOrigin + SAFE_PREFIX + "/" + absUrl + "\"";
                            });
                        }
                        return line;
                    }

                    // URL 行：补全为绝对路径后判断分流
                    var absUrl;
                    try {
                        absUrl = new URL(trimmed, targetUrl.href).href;
                    } catch (e) {
                        return line;
                    }

                    var inWhite = matchList(WHITE_LIST, new URL(absUrl).hostname);
                    return inWhite
                        ? absUrl
                        : proxyOrigin + SAFE_PREFIX + "/" + absUrl;

                }).join("\n");

                return new Response(rewritten, {
                    status: 200,
                    headers: {
                        "Content-Type": "application/vnd.apple.mpegurl; charset=utf-8",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "no-cache"
                    }
                });
            }

            // 4. 其他资源（.ts 切片等）直接透传
            var resHeaders = new Headers(response.headers);
            resHeaders.set("Access-Control-Allow-Origin", "*");

            return new Response(response.body, {
                status: response.status,
                headers: resHeaders
            });

        } catch (e) {
            return new Response("Proxy Error: " + e.message, { status: 500 });
        }
    }
};