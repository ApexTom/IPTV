# 提取 香港/台湾/新加坡/马来西亚 频道；兼容 m3u 与 txt(名称,链接 / 分组,#genre#)
BEGIN {
  region = "香港|港台|hong ?kong|台湾|台灣|taiwan|新加坡|singapore|马来西亚|馬來西亞|malaysia"
  chan = "tvb|翡翠|明珠|无线|無線|有线|有線|viutv|now ?tv|rthk|凤凰|鳳凰|tvbs|三立|东森|東森|纬来|緯來|年代|民视|民視|台视|台視|中视|中視|华视|華視|公视|公視|八大|寰宇|龙祥|龍祥|mediacorp|新传媒|新傳媒|channel 5|channel 8|channel u|8频道|8頻道|astro|八度|rtm|ntv7|tv3|tv9|8tv|欢喜|歡喜"
  print "#EXTM3U"
}
function emit(name, grp, url,    key) {
  key = tolower(grp " " name)
  if ((key ~ region || key ~ chan) && !(url in seen)) {
    seen[url] = 1
    printf "#EXTINF:-1 group-title=\"%s\",%s\n%s\n", grp, name, url
    n++
  }
}
/^#EXTINF/ {
  name = $0; sub(/^.*,/, "", name)
  grp = ""
  if (match($0, /group-title="[^"]*"/)) grp = substr($0, RSTART + 13, RLENGTH - 14)
  ismu = 1; next
}
/^#/ { next }
/^[ \t]*$/ { next }
ismu && /^[a-zA-Z]+:\/\// { emit(name, grp, $0); ismu = 0; next }
/,#genre#/ { curgrp = $0; sub(/,#genre#.*/, "", curgrp); next }
/,[a-zA-Z]+:\/\// {
  i = index($0, ",")
  emit(substr($0, 1, i - 1), curgrp, substr($0, i + 1))
}
END { print "total: " n+0 > "/dev/stderr" }
