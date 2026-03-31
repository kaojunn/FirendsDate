from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_HTML = ROOT / "展商导航.html"

EXCLUDED_NAMES = {
    ".DS_Store",
    "letVision2026展商清单.pdf",
    "厂商联系方式整理.md",
    "活动信息汇总.md",
    "展商目录索引.md",
    "展商导航.html",
    "生成展商导航.py",
}


@dataclass
class Exhibitor:
    name: str
    zone: str
    booth: str
    summary: str
    links: list[str]
    contact: str
    detail_path: str
    folder_path: str
    has_contact: bool
    tags: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_value(text: str, label: str) -> str:
    pattern = rf"- {re.escape(label)}：`([^`]+)`"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else "待补充"


def extract_summary(text: str) -> str:
    match = re.search(r"## 简介\s*\n\s*\n(.+?)(?:\n\s*\n## |\Z)", text, re.S)
    if not match:
        return "待补充"
    return " ".join(line.strip() for line in match.group(1).strip().splitlines()).strip()


def extract_links(text: str) -> list[str]:
    match = re.search(r"## 公开链接\s*\n\s*\n(.+?)(?:\n\s*\n## |\Z)", text, re.S)
    if not match:
        return []
    links = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if line.startswith("- "):
            links.append(line[2:].strip())
    return links


def extract_contact(text: str) -> str:
    match = re.search(r"## 已掌握联系人\s*\n\s*\n- (.+?)(?:\n\s*\n## |\Z)", text, re.S)
    if not match:
        return "待补充"
    return " ".join(line.strip() for line in match.group(1).strip().splitlines()).strip()


def infer_tags(exhibitor: Exhibitor) -> list[str]:
    text = f"{exhibitor.name} {exhibitor.summary} {exhibitor.contact}".lower()
    mapping = {
        "AI": ["ai", "agent", "大模型", "智能体"],
        "XR/MR": ["xr", "mr", "vision pro", "visionos", "空间", "沉浸", "ar"],
        "硬件": ["相机", "音箱", "椅", "望远镜", "硬件", "充电", "可穿戴"],
        "工具/效率": ["工具", "办公", "效率", "邮箱", "笔记", "知识管理"],
        "内容/创作": ["创作", "内容", "视频", "游戏", "播客", "摄影", "设计"],
        "教育/高校": ["高校", "教育", "实验室", "课堂", "学习"],
        "文旅/展馆": ["文旅", "展馆", "博物馆", "公共文化", "景区"],
        "社区/平台": ["社区", "平台", "分发", "开源", "社交", "名片"],
    }
    tags: list[str] = []
    for tag, keywords in mapping.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    if not tags:
        tags.append("其他")
    return tags


def collect_exhibitors() -> list[Exhibitor]:
    exhibitors: list[Exhibitor] = []
    for path in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
        if path.name in EXCLUDED_NAMES or not path.is_dir():
            continue
        detail = path / "介绍卡.md"
        if not detail.exists():
            continue

        text = read_text(detail)
        name_match = re.search(r"^#\s+(.+)$", text, re.M)
        name = name_match.group(1).strip() if name_match else path.name
        zone = extract_value(text, "分区")
        booth = extract_value(text, "展位")
        summary = extract_summary(text)
        links = extract_links(text)
        contact = extract_contact(text)
        has_contact = contact != "待补充" and "待补充" not in contact

        exhibitor = Exhibitor(
            name=name,
            zone=zone,
            booth=booth,
            summary=summary,
            links=links,
            contact=contact,
            detail_path=f"{path.name}/介绍卡.md",
            folder_path=path.name,
            has_contact=has_contact,
            tags=[],
        )
        exhibitor.tags = infer_tags(exhibitor)
        exhibitors.append(exhibitor)

    return exhibitors


def build_html(exhibitors: list[Exhibitor]) -> str:
    data_json = json.dumps([asdict(item) for item in exhibitors], ensure_ascii=False, indent=2)
    # Keep JSON readable in the generated HTML while avoiding accidental closing
    # of the script tag when rendered by the browser.
    safe_data_json = data_json.replace("</", "<\\/")
    zones = sorted({item.zone for item in exhibitors})
    zone_options = "\n".join(
        f'            <option value="{escape(zone)}">{escape(zone)}</option>' for zone in zones
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LET'S VISION 2026 展商导航</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --panel-soft: #f0f4ff;
      --text: #1f2937;
      --muted: #6b7280;
      --line: #dbe2ea;
      --brand: #2563eb;
      --brand-soft: rgba(37, 99, 235, 0.12);
      --ok: #0f766e;
      --warn: #92400e;
      --shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0f172a;
        --panel: #111827;
        --panel-soft: #172036;
        --text: #e5e7eb;
        --muted: #94a3b8;
        --line: #243244;
        --brand: #60a5fa;
        --brand-soft: rgba(96, 165, 250, 0.16);
        --ok: #5eead4;
        --warn: #fbbf24;
        --shadow: 0 16px 36px rgba(0, 0, 0, 0.25);
      }}
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font: 14px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}

    a {{
      color: var(--brand);
      text-decoration: none;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    .page {{
      max-width: 1360px;
      margin: 0 auto;
      padding: 24px;
    }}

    .hero {{
      background: linear-gradient(135deg, var(--panel), var(--panel-soft));
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      box-shadow: var(--shadow);
    }}

    .hero h1 {{
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.2;
    }}

    .hero p {{
      margin: 0;
      color: var(--muted);
      max-width: 900px;
    }}

    .toolbar {{
      margin-top: 20px;
      display: grid;
      grid-template-columns: 2fr repeat(3, minmax(160px, 1fr));
      gap: 12px;
    }}

    .field {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .field label {{
      font-size: 12px;
      color: var(--muted);
    }}

    .field input,
    .field select {{
      width: 100%;
      min-height: 42px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--text);
      padding: 0 12px;
      font: inherit;
    }}

    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }}

    .chip {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--text);
      border-radius: 999px;
      padding: 8px 12px;
      cursor: pointer;
      transition: 0.15s ease;
    }}

    .chip.active {{
      border-color: var(--brand);
      background: var(--brand-soft);
      color: var(--brand);
    }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 20px;
    }}

    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      box-shadow: var(--shadow);
    }}

    .stat .label {{
      color: var(--muted);
      font-size: 12px;
    }}

    .stat .value {{
      margin-top: 6px;
      font-size: 24px;
      font-weight: 700;
    }}

    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 380px;
      gap: 16px;
      margin-top: 20px;
      align-items: start;
    }}

    .results-panel,
    .detail-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: var(--shadow);
      min-height: 540px;
    }}

    .panel-header {{
      padding: 18px 20px 0;
    }}

    .panel-header h2 {{
      margin: 0;
      font-size: 18px;
    }}

    .panel-header p {{
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }}

    .results {{
      padding: 16px 20px 20px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 12px;
    }}

    .card {{
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: var(--panel);
      cursor: pointer;
      transition: 0.15s ease;
    }}

    .card:hover {{
      transform: translateY(-2px);
      border-color: var(--brand);
    }}

    .card.active {{
      border-color: var(--brand);
      background: var(--brand-soft);
    }}

    .card h3 {{
      margin: 0;
      font-size: 16px;
      line-height: 1.35;
    }}

    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 10px 0;
    }}

    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: var(--panel-soft);
    }}

    .pill.ok {{
      color: var(--ok);
    }}

    .pill.warn {{
      color: var(--warn);
    }}

    .card p {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}

    .card-hint {{
      margin-top: 10px;
      font-size: 12px;
      color: var(--muted);
    }}

    .detail-body {{
      padding: 16px 20px 20px;
    }}

    .detail-empty {{
      color: var(--muted);
      padding-top: 48px;
    }}

    .detail-section {{
      margin-top: 18px;
    }}

    .detail-section h3 {{
      margin: 0 0 8px;
      font-size: 14px;
    }}

    .detail-section p,
    .detail-section li {{
      margin: 0;
      color: var(--text);
    }}

    .detail-section ul {{
      margin: 0;
      padding-left: 18px;
    }}

    .mobile-detail {{
      display: none;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: var(--panel-soft);
      margin-top: 12px;
    }}

    .mobile-detail .detail-section:first-child {{
      margin-top: 0;
    }}

    .detail-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}

    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 0 14px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--text);
      text-decoration: none;
    }}

    .button.primary {{
      border-color: var(--brand);
      background: var(--brand);
      color: white;
    }}

    .muted {{
      color: var(--muted);
    }}

    @media (max-width: 1120px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}

      .detail-panel {{
        display: none;
      }}

      .results {{
        grid-template-columns: 1fr;
      }}

      .card.expanded .mobile-detail {{
        display: block;
      }}
    }}

    @media (max-width: 840px) {{
      .toolbar {{
        grid-template-columns: 1fr;
      }}

      .summary {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}

    @media (max-width: 520px) {{
      .page {{
        padding: 16px;
      }}

      .summary {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <h1>LET'S VISION 2026 展商导航</h1>
      <p>
        这是一个可搜索、可筛选、可点击查看详情的展商索引页。数据来自各展商文件夹内的
        <code>介绍卡.md</code>，因此后续你只需要维护介绍卡，再重新运行一次生成脚本即可同步更新页面。
      </p>

      <div class="toolbar">
        <div class="field">
          <label for="searchInput">搜索</label>
          <input id="searchInput" type="search" placeholder="输入公司名、方向、关键词、联系人">
        </div>
        <div class="field">
          <label for="zoneFilter">分区</label>
          <select id="zoneFilter">
            <option value="">全部分区</option>
{zone_options}
          </select>
        </div>
        <div class="field">
          <label for="contactFilter">联系人状态</label>
          <select id="contactFilter">
            <option value="">全部</option>
            <option value="yes">已有联系人</option>
            <option value="no">待补充联系人</option>
          </select>
        </div>
        <div class="field">
          <label for="sortSelect">排序</label>
          <select id="sortSelect">
            <option value="zone">按分区 / 展位</option>
            <option value="name">按名称</option>
            <option value="contact">按联系人状态</option>
          </select>
        </div>
      </div>

      <div class="chips" id="tagChips"></div>
    </section>

    <section class="summary">
      <div class="stat">
        <div class="label">展商总数</div>
        <div class="value" id="totalCount">0</div>
      </div>
      <div class="stat">
        <div class="label">当前结果</div>
        <div class="value" id="filteredCount">0</div>
      </div>
      <div class="stat">
        <div class="label">已有联系人</div>
        <div class="value" id="contactCount">0</div>
      </div>
      <div class="stat">
        <div class="label">待补充联系人</div>
        <div class="value" id="missingContactCount">0</div>
      </div>
    </section>

    <section class="layout">
      <div class="results-panel">
        <div class="panel-header">
          <h2>展商列表</h2>
          <p>点击任意卡片，在右侧查看详情；也可以直接打开对应的介绍卡文件。</p>
        </div>
        <div class="results" id="results"></div>
      </div>

      <aside class="detail-panel">
        <div class="panel-header">
          <h2>详情</h2>
          <p>这里会展示你选中的展商信息。</p>
        </div>
        <div class="detail-body" id="detailPanel">
          <div class="detail-empty">先从左侧选择一个展商。</div>
        </div>
      </aside>
    </section>
  </div>

  <script id="exhibitor-data" type="application/json">
{safe_data_json}
  </script>
  <script>
    const exhibitors = JSON.parse(document.getElementById("exhibitor-data").textContent);
    const state = {{
      search: "",
      zone: "",
      contact: "",
      tag: "",
      sort: "zone",
      selectedPath: "",
    }};

    const els = {{
      searchInput: document.getElementById("searchInput"),
      zoneFilter: document.getElementById("zoneFilter"),
      contactFilter: document.getElementById("contactFilter"),
      sortSelect: document.getElementById("sortSelect"),
      tagChips: document.getElementById("tagChips"),
      totalCount: document.getElementById("totalCount"),
      filteredCount: document.getElementById("filteredCount"),
      contactCount: document.getElementById("contactCount"),
      missingContactCount: document.getElementById("missingContactCount"),
      results: document.getElementById("results"),
      detailPanel: document.getElementById("detailPanel"),
    }};

    const allTags = ["全部", ...new Set(exhibitors.flatMap(item => item.tags))];
    const mobileMediaQuery = window.matchMedia("(max-width: 1120px)");

    function escapeHtml(value) {{
      return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }}

    function boothSortValue(booth) {{
      if (!booth || booth === "待补充") return 999999;
      const match = booth.match(/([A-Z])(\\d+)/i);
      if (!match) return 900000;
      const letterValue = match[1].toUpperCase().charCodeAt(0) - 64;
      const numberValue = Number(match[2]);
      return letterValue * 1000 + numberValue;
    }}

    function getFilteredData() {{
      const keyword = state.search.trim().toLowerCase();
      const filtered = exhibitors.filter(item => {{
        const haystack = [
          item.name,
          item.zone,
          item.booth,
          item.summary,
          item.contact,
          item.tags.join(" "),
        ].join(" ").toLowerCase();

        if (keyword && !haystack.includes(keyword)) return false;
        if (state.zone && item.zone !== state.zone) return false;
        if (state.contact === "yes" && !item.has_contact) return false;
        if (state.contact === "no" && item.has_contact) return false;
        if (state.tag && state.tag !== "全部" && !item.tags.includes(state.tag)) return false;
        return true;
      }});

      filtered.sort((a, b) => {{
        if (state.sort === "name") {{
          return a.name.localeCompare(b.name, "zh-CN");
        }}
        if (state.sort === "contact") {{
          if (a.has_contact !== b.has_contact) return a.has_contact ? -1 : 1;
          return a.name.localeCompare(b.name, "zh-CN");
        }}

        const zoneCompare = a.zone.localeCompare(b.zone, "zh-CN");
        if (zoneCompare !== 0) return zoneCompare;
        const boothCompare = boothSortValue(a.booth) - boothSortValue(b.booth);
        if (boothCompare !== 0) return boothCompare;
        return a.name.localeCompare(b.name, "zh-CN");
      }});

      return filtered;
    }}

    function isMobileLayout() {{
      return mobileMediaQuery.matches;
    }}

    function renderTagChips() {{
      els.tagChips.innerHTML = allTags.map(tag => {{
        const active = (state.tag || "全部") === tag ? "active" : "";
        return `<button class="chip ${{active}}" type="button" data-tag="${{escapeHtml(tag)}}">${{escapeHtml(tag)}}</button>`;
      }}).join("");

      els.tagChips.querySelectorAll("[data-tag]").forEach(button => {{
        button.addEventListener("click", () => {{
          state.tag = button.dataset.tag === "全部" ? "" : button.dataset.tag;
          render();
        }});
      }});
    }}

    function renderStats(filtered) {{
      els.totalCount.textContent = exhibitors.length;
      els.filteredCount.textContent = filtered.length;
      const contactCount = exhibitors.filter(item => item.has_contact).length;
      els.contactCount.textContent = contactCount;
      els.missingContactCount.textContent = exhibitors.length - contactCount;
    }}

    function renderDetailContent(selected, options = {{ mobile: false }}) {{
      const links = selected.links.length
        ? `<ul>${{selected.links.map(link => `<li><a href="${{escapeHtml(link)}}" target="_blank" rel="noreferrer">${{escapeHtml(link)}}</a></li>`).join("")}}</ul>`
        : '<p class="muted">待补充</p>';

      const tags = selected.tags.map(tag => `<span class="pill">${{escapeHtml(tag)}}</span>`).join("");
      const actionClass = options.mobile ? "button" : "button primary";

      return `
        <h2>${{escapeHtml(selected.name)}}</h2>
        <div class="meta">
          <span class="pill">${{escapeHtml(selected.zone)}}</span>
          <span class="pill">${{escapeHtml(selected.booth)}}</span>
          <span class="pill ${{selected.has_contact ? "ok" : "warn"}}">${{selected.has_contact ? "已有联系人" : "待补充联系人"}}</span>
        </div>
        <div class="meta">${{tags}}</div>

        <div class="detail-section">
          <h3>简介</h3>
          <p>${{escapeHtml(selected.summary)}}</p>
        </div>

        <div class="detail-section">
          <h3>联系人</h3>
          <p>${{escapeHtml(selected.contact)}}</p>
        </div>

        <div class="detail-section">
          <h3>公开链接</h3>
          ${{links}}
        </div>

        <div class="detail-actions">
          <a class="${{actionClass}}" href="${{escapeHtml(selected.detail_path)}}" target="_blank" rel="noreferrer">打开介绍卡</a>
          <a class="button" href="${{escapeHtml(selected.folder_path)}}" target="_blank" rel="noreferrer">打开文件夹</a>
        </div>
      `;
    }}

    function renderResults(filtered) {{
      if (!filtered.length) {{
        els.results.innerHTML = '<div class="muted">没有匹配结果，请换个关键词或筛选条件。</div>';
        if (!state.selectedPath) {{
          els.detailPanel.innerHTML = '<div class="detail-empty">没有可展示的展商。</div>';
        }}
        return;
      }}

      const mobile = isMobileLayout();

      if (!filtered.some(item => item.detail_path === state.selectedPath)) {{
        state.selectedPath = mobile ? "" : filtered[0].detail_path;
      }} else if (!state.selectedPath && !mobile) {{
        state.selectedPath = filtered[0].detail_path;
      }}

      els.results.innerHTML = filtered.map(item => {{
        const expanded = item.detail_path === state.selectedPath;
        const active = expanded ? "active expanded" : "";
        const contactText = item.has_contact ? "已有联系人" : "待补充联系人";
        const contactClass = item.has_contact ? "ok" : "warn";
        const tags = item.tags.map(tag => `<span class="pill">${{escapeHtml(tag)}}</span>`).join("");
        const mobileHint = mobile
          ? `<div class="card-hint">${{expanded ? "再次点击卡片可收起详情" : "点击卡片查看详情"}}</div>`
          : "";
        const mobileDetail = mobile && expanded
          ? `<div class="mobile-detail">${{renderDetailContent(item, {{ mobile: true }})}}</div>`
          : "";
        return `
          <article class="card ${{active}}" data-path="${{escapeHtml(item.detail_path)}}">
            <h3>${{escapeHtml(item.name)}}</h3>
            <div class="meta">
              <span class="pill">${{escapeHtml(item.zone)}}</span>
              <span class="pill">${{escapeHtml(item.booth)}}</span>
              <span class="pill ${{contactClass}}">${{contactText}}</span>
            </div>
            <p>${{escapeHtml(item.summary)}}</p>
            <div class="meta">${{tags}}</div>
            ${{mobileHint}}
            ${{mobileDetail}}
          </article>
        `;
      }}).join("");

      els.results.querySelectorAll("[data-path]").forEach(card => {{
        card.addEventListener("click", () => {{
          const nextPath = card.dataset.path;
          if (mobile && state.selectedPath === nextPath) {{
            state.selectedPath = "";
          }} else {{
            state.selectedPath = nextPath;
          }}
          render();
        }});
      }});
    }}

    function renderDetail(filtered) {{
      if (isMobileLayout()) {{
        els.detailPanel.innerHTML = '<div class="detail-empty">移动端请点击左侧卡片，在卡片下方查看详情。</div>';
        return;
      }}

      const selected = filtered.find(item => item.detail_path === state.selectedPath);
      if (!selected) {{
        els.detailPanel.innerHTML = '<div class="detail-empty">当前筛选结果中没有选中的展商。</div>';
        return;
      }}

      els.detailPanel.innerHTML = renderDetailContent(selected);
    }}

    function render() {{
      renderTagChips();
      const filtered = getFilteredData();
      renderStats(filtered);
      renderResults(filtered);
      renderDetail(filtered);
    }}

    els.searchInput.addEventListener("input", event => {{
      state.search = event.target.value;
      render();
    }});
    els.zoneFilter.addEventListener("change", event => {{
      state.zone = event.target.value;
      render();
    }});
    els.contactFilter.addEventListener("change", event => {{
      state.contact = event.target.value;
      render();
    }});
    els.sortSelect.addEventListener("change", event => {{
      state.sort = event.target.value;
      render();
    }});

    mobileMediaQuery.addEventListener("change", () => {{
      render();
    }});

    render();
  </script>
</body>
</html>
"""


def main() -> None:
    exhibitors = collect_exhibitors()
    OUTPUT_HTML.write_text(build_html(exhibitors), encoding="utf-8")
    print(f"generated {OUTPUT_HTML.name} with {len(exhibitors)} exhibitors")


if __name__ == "__main__":
    main()
