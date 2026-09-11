export default async function handler(req, res) {
  const url =
    "https://php.946985.filegear-sg.me/mytv265.php?id=J";

  try {
    const r = await fetch(url, {
      redirect: "manual",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
        "Accept": "*/*",
      },
    });

    const headers = {};
    for (const [k, v] of r.headers.entries()) {
      headers[k] = v;
    }

    res.status(200).json({
      status: r.status,
      location: r.headers.get("location"),
      cf_mitigated: r.headers.get("cf-mitigated"),
      cf_ray: r.headers.get("cf-ray"),
      server: r.headers.get("server"),
      headers,
    });
  } catch (e) {
    res.status(500).json({
      error: String(e),
    });
  }
}
