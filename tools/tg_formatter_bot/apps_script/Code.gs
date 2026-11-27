/**
 * Content plan API for m_redactor_bot.
 * Paste into the content plan: Extensions → Apps Script. Deploy → New deployment → Web app,
 * Execute as: Me, Who has access: Anyone. Project Settings → Script properties: BOT_KEY = a long password
 * (the same value goes to the Cloudflare secret PLAN_KEY).
 *
 * Reads month tabs named like "11." / "12." / "01". Columns are found by header names:
 * DATE, STATUS, POST TOPIC, POST CATEGORY, VISUAL CATEGORY, TEXT, LINK TO VISUAL, POLL.
 * Only the bot (with the key) can call it. It reads the plan and, after publishing, can set STATUS.
 */
const MAX_FILE_BYTES = 15 * 1024 * 1024;   // larger visuals are not sent to the bot

function doPost(e) {
  let req = {};
  try { req = JSON.parse(e.postData.contents); } catch (err) { return out({ error: "bad json" }); }
  const key = PropertiesService.getScriptProperties().getProperty("BOT_KEY");
  if (!key || req.key !== key) return out({ error: "forbidden" });
  try {
    if (req.action === "list") return out(listPosts(Number(req.back || 1), Number(req.ahead || 14)));
    if (req.action === "post") return out(getPost(String(req.date || "")));
    if (req.action === "status") return out(setStatus(String(req.date || ""), String(req.value || "Posted")));
    return out({ error: "unknown action" });
  } catch (err) {
    return out({ error: String(err && err.message || err) });
  }
}

function out(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// ---------- reading the plan ----------
function monthSheets() {
  return SpreadsheetApp.getActiveSpreadsheet().getSheets()
    .map(function (sh) { const m = sh.getName().match(/^\s*(\d{1,2})\.?\s*$/); return m ? { sh: sh, month: Number(m[1]) } : null; })
    .filter(function (x) { return x && x.month >= 1 && x.month <= 12; });
}

// the plan has no year: pick the year that puts the date closest to today
function toDate(dd, mm) {
  const now = new Date();
  let best = null;
  [now.getFullYear() - 1, now.getFullYear(), now.getFullYear() + 1].forEach(function (y) {
    const d = new Date(y, mm - 1, dd);
    if (!best || Math.abs(d - now) < Math.abs(best - now)) best = d;
  });
  return best;
}

function rows() {
  const all = [];
  monthSheets().forEach(function (ms) {
    const range = ms.sh.getDataRange();
    const values = range.getValues();
    const rich = range.getRichTextValues();
    let cols = null;
    for (let r = 0; r < values.length; r++) {
      const row = values[r].map(function (v) { return typeof v === "string" ? v.trim() : v; });
      const upper = row.map(function (v) { return String(v).toUpperCase(); });
      if (upper.indexOf("TEXT") >= 0 && upper.indexOf("STATUS") >= 0) {   // header row (repeats every week)
        cols = {};
        upper.forEach(function (h, i) { if (h) cols[h] = i; });
        continue;
      }
      if (!cols) continue;
      const dm = String(row[0]).match(/^(\d{1,2})\.(\d{1,2})/);
      if (!dm) continue;
      const get = function (name) { return cols[name] === undefined ? "" : row[cols[name]]; };
      const visCol = cols["LINK TO VISUAL"] !== undefined ? cols["LINK TO VISUAL"] : cols["VISUAL"];
      let visual = "", visualLink = "", cellImage = null;
      if (visCol !== undefined) {
        const v = values[r][visCol];
        if (v && typeof v === "object" && typeof v.getContentUrl === "function") cellImage = v;   // image inside the cell
        else {
          visual = String(v || "").trim();
          const rt = rich[r][visCol];
          visualLink = (rt && rt.getLinkUrl()) || (visual.match(/https?:\/\/\S+/) || [""])[0];
        }
      }
      const dd = Number(dm[1]), mm = Number(dm[2]);
      all.push({
        sheet: ms.sh.getName(), row: r + 1, statusCol: cols["STATUS"] === undefined ? null : cols["STATUS"] + 1,
        date: ("0" + dd).slice(-2) + "." + ("0" + mm).slice(-2), when: toDate(dd, mm),
        status: String(get("STATUS")), topic: String(get("POST TOPIC")), category: String(get("POST CATEGORY")),
        visualCategory: String(get("VISUAL CATEGORY")), text: String(get("TEXT")), poll: String(get("POLL") || ""),
        visual: visual, visualLink: visualLink, cellImage: cellImage,
      });
    }
  });
  return all;
}

function brief(p) {
  return { date: p.date, status: p.status, topic: p.topic, category: p.category, hasText: !!p.text.trim(),
    hasVisual: !!(p.cellImage || p.visualLink) };
}

function listPosts(back, ahead) {
  const now = new Date(); now.setHours(0, 0, 0, 0);
  const from = new Date(now.getTime() - back * 864e5), to = new Date(now.getTime() + ahead * 864e5);
  const list = rows().filter(function (p) { return p.when >= from && p.when <= to; })
    .sort(function (a, b) { return a.when - b.when; }).map(brief);
  return { posts: list };
}

function findPost(date) {
  const m = date.match(/^(\d{1,2})\.(\d{1,2})/);
  if (!m) return null;
  const key = ("0" + Number(m[1])).slice(-2) + "." + ("0" + Number(m[2])).slice(-2);
  return rows().filter(function (p) { return p.date === key; })[0] || null;
}

function getPost(date) {
  const p = findPost(date);
  if (!p) return { found: false };
  const res = brief(p);
  res.found = true; res.text = p.text; res.poll = p.poll; res.visualNote = p.visualLink ? "" : p.visual;
  res.visualCategory = p.visualCategory;
  res.file = null;
  try {
    let blob = null, name = "";
    if (p.cellImage) {
      blob = UrlFetchApp.fetch(p.cellImage.getContentUrl()).getBlob(); name = "cell-image";
    } else if (p.visualLink) {
      const id = (p.visualLink.match(/\/d\/([\w-]{20,})/) || p.visualLink.match(/[?&]id=([\w-]{20,})/) || [])[1];
      if (id) {
        const f = DriveApp.getFileById(id); name = f.getName();
        // big pictures: take Drive's 2000px JPEG preview instead (Telegram shrinks photos to 1280px anyway)
        if (/^image\//.test(f.getMimeType()) && f.getSize() > 2 * 1024 * 1024) blob = driveThumb(id);
        if (!blob && f.getSize() <= MAX_FILE_BYTES) blob = f.getBlob();
        if (!blob) res.fileNote = "файл больше 15 МБ: " + name;
      }
      else res.fileNote = "ссылка на визуал не из Google Drive: " + p.visualLink;
    }
    if (blob) res.file = { name: name, mime: blob.getContentType(), b64: Utilities.base64Encode(blob.getBytes()) };
  } catch (err) {
    res.fileNote = "не удалось открыть визуал: " + (err && err.message || err);
  }
  return res;
}

function driveThumb(id) {
  try {
    const auth = { headers: { Authorization: "Bearer " + ScriptApp.getOAuthToken() }, muteHttpExceptions: true };
    const meta = JSON.parse(UrlFetchApp.fetch("https://www.googleapis.com/drive/v3/files/" + id + "?fields=thumbnailLink", auth).getContentText());
    if (!meta.thumbnailLink) return null;
    const r = UrlFetchApp.fetch(meta.thumbnailLink.replace(/=s\d+$/, "=s2000"), auth);
    return r.getResponseCode() === 200 ? r.getBlob().setName("visual.jpg") : null;
  } catch (err) { return null; }
}

function setStatus(date, value) {
  const p = findPost(date);
  if (!p || !p.statusCol) return { ok: false };
  SpreadsheetApp.getActiveSpreadsheet().getSheetByName(p.sheet).getRange(p.row, p.statusCol).setValue(value);
  return { ok: true };
}

// Run once from the editor (▶ testList) to grant permissions and check the output in the log.
function testList() { Logger.log(JSON.stringify(listPosts(3, 14)).slice(0, 2000)); }
