export default async function handler(req, res) {
  const target =
    "https://php.946985.filegear-sg.me/mytv265.php?id=J";
  const started = Date.now();
  try {
    const response = await fetch(target, {
      method: "GET",
      // 关键：绝对不能自动跟随 302
      redirect: "manual",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
          "AppleWebKit/537.36 (KHTML, like Gecko) " +
          "Chrome/140.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language":
          "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
      },
    });
    const headers = {};
    for (const [key, value] of response.headers.entries()) {
      headers[key] = value;
    }
    const location = response.headers.get("location");
    const cfMitigated = response.headers.get("cf-mitigated");
    const cfRay = response.headers.get("cf-ray");
    // 只读取一小部分 body，避免 Challenge 页面过大
    let bodyPreview = "";
    if (response.status !== 302 && response.status !== 301) {
      const text = await response.text();
      bodyPreview = text.substring(0, 1000);
    }
    res.status(200).json({
      ok: response.ok,
      status: response.status,
      statusText: response.statusText,
      target,
      location,
      cloudflare: {
        mitigated: cfMitigated,
        ray: cfRay,
        server: response.headers.get("server"),
      },
      elapsed_ms: Date.now() - started,
      body_preview: bodyPreview,
      headers,
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      target,
      elapsed_ms: Date.now() - started,
      error: String(error),
      stack: error?.stack || null,
    });
  }
}
