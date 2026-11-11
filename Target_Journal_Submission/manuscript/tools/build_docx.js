// Renders a manuscript JSON spec (produced by build_manuscript.py from machine-generated results) into DOCX.
// Usage: node build_docx.js spec.json out.docx
const fs = require("fs");
const path = require("path");
const d = require("docx");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, PageBreak, Footer, PageNumber, LineNumberRestartFormat, LevelFormat,
  Math: OMath, MathRun, MathFraction, MathSubScript, MathSuperScript, MathSubSuperScript, MathRoundBrackets,
  MathSquareBrackets, MathCurlyBrackets, TabStopType, VerticalAlign,
} = d;

const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const FONT = "Times New Roman";
const BODY = 24; // half-points (12 pt)
const LINE = 360; // 1.5 line spacing
const PAGE_W = 11906, PAGE_H = 16838, MARGIN = 1418; // A4, 2.5 cm margins
const TEXT_W = PAGE_W - 2 * MARGIN;

// ---------------------------------------------------------------- inline runs
function runs(items, base = {}) {
  return (items || []).map((r) => {
    if (typeof r === "string") r = { t: r };
    if (r.math) return new OMath({ children: mathItems(r.math) });
    return new TextRun({
      text: r.t, bold: r.b || base.bold, italics: r.i || base.italics, font: FONT,
      size: r.size || base.size || BODY, superScript: !!r.sup, subScript: !!r.sub, color: r.color || base.color,
    });
  });
}

// ---------------------------------------------------------------- equations (mini DSL)
function mathItems(items) {
  const out = [];
  for (const it of items) {
    if (typeof it === "string") { out.push(new MathRun(it)); continue; }
    if (it.sub) out.push(new MathSubScript({ children: mathItems(asArr(it.sub[0])), subScript: mathItems(asArr(it.sub[1])) }));
    else if (it.sup) out.push(new MathSuperScript({ children: mathItems(asArr(it.sup[0])), superScript: mathItems(asArr(it.sup[1])) }));
    else if (it.subsup) out.push(new MathSubSuperScript({ children: mathItems(asArr(it.subsup[0])), subScript: mathItems(asArr(it.subsup[1])), superScript: mathItems(asArr(it.subsup[2])) }));
    else if (it.frac) out.push(new MathFraction({ numerator: mathItems(asArr(it.frac[0])), denominator: mathItems(asArr(it.frac[1])) }));
    else if (it.paren) out.push(new MathRoundBrackets({ children: mathItems(asArr(it.paren)) }));
    else if (it.brack) out.push(new MathSquareBrackets({ children: mathItems(asArr(it.brack)) }));
    else if (it.curly) out.push(new MathCurlyBrackets({ children: mathItems(asArr(it.curly)) }));
  }
  return out;
}
const asArr = (x) => (Array.isArray(x) ? x : [x]);

// ---------------------------------------------------------------- blocks
const P = (children, opt = {}) => new Paragraph({
  children, alignment: opt.align || AlignmentType.JUSTIFIED, keepNext: !!opt.keepNext, keepLines: !!opt.keepLines,
  spacing: { line: opt.line || LINE, before: opt.before ?? 0, after: opt.after ?? 120 }, indent: opt.indent,
  heading: opt.heading, numbering: opt.numbering, pageBreakBefore: !!opt.pageBreakBefore,
});

const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };

function table(b) {
  const n = b.header.length;
  const w = b.col_widths ? b.col_widths.map((x) => Math.round(x * TEXT_W)) : Array(n).fill(Math.floor(TEXT_W / n));
  const diff = TEXT_W - w.reduce((a, c) => a + c, 0); w[0] += diff;
  const fs_ = b.font_size || 16;
  const cell = (txt, i, isHead, isLast) => new TableCell({
    width: { size: w[i], type: WidthType.DXA },
    borders: { top: isHead ? border : none, bottom: (isHead || isLast) ? border : none, left: none, right: none },
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, spacing: { line: 240, before: 0, after: 0 },
      children: runs(typeof txt === "string" || typeof txt === "number" ? [{ t: String(txt) }] : txt, { size: fs_, bold: isHead && b.bold_header !== false }) })],
  });
  const rows = [new TableRow({ tableHeader: true, children: b.header.map((h, i) => cell(h, i, true, false)) })];
  b.rows.forEach((r, k) => rows.push(new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false, k === b.rows.length - 1)) })));
  return new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: w, rows });
}

const children = [];
let eqNo = 0;
for (const b of spec.blocks) {
  switch (b.type) {
    case "title":
      children.push(P(runs([{ t: b.text, b: true, size: 32 }]), { align: AlignmentType.CENTER, after: 240, line: 300 })); break;
    case "center":
      children.push(P(runs(b.runs, { size: b.size }), { align: AlignmentType.CENTER, after: 80, line: 276 })); break;
    case "heading": {
      const lvl = { 1: HeadingLevel.HEADING_1, 2: HeadingLevel.HEADING_2, 3: HeadingLevel.HEADING_3 }[b.level];
      children.push(new Paragraph({ heading: lvl, keepNext: true, children: [new TextRun({ text: b.text, font: FONT })],
        spacing: { before: b.level === 1 ? 300 : 200, after: 120, line: LINE }, pageBreakBefore: !!b.pageBreakBefore }));
      break;
    }
    case "para": children.push(P(runs(b.runs), { indent: b.noindent ? undefined : { firstLine: 0 } })); break;
    case "label": children.push(P(runs(b.runs), { keepNext: true, after: 60 })); break;
    case "bullets":
      for (const it of b.items) children.push(P(runs(it), { numbering: { reference: "bullets", level: 0 }, after: 60 })); break;
    case "numbered":
      for (const it of b.items) children.push(P(runs(it), { numbering: { reference: b.ref || "numbers", level: 0 }, after: 60 })); break;
    case "equation": {
      eqNo += 1;
      children.push(new Paragraph({ tabStops: [{ type: TabStopType.CENTER, position: Math.round(TEXT_W / 2) }, { type: TabStopType.RIGHT, position: TEXT_W }],
        spacing: { line: LINE, before: 60, after: 120 }, keepLines: true,
        children: [new TextRun({ text: "\t", font: FONT }), new OMath({ children: mathItems(b.eq) }), new TextRun({ text: `\t(${eqNo})`, font: FONT, size: BODY })] }));
      break;
    }
    case "figure": {
      const img = fs.readFileSync(b.path);
      const wIn = b.width_in || 6.3; const ratio = b.ratio; // height/width
      const wpx = Math.round(wIn * 96), hpx = Math.round(wpx * ratio);
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
        children: [new ImageRun({ type: "png", data: img, transformation: { width: wpx, height: hpx },
          altText: { title: b.alt || "Figure", description: b.alt || "Figure", name: path.basename(b.path) } })] }));
      children.push(P(runs(b.caption, { size: 20 }), { after: 240, line: 276 }));
      break;
    }
    case "table":
      children.push(P(runs(b.caption, { size: 20 }), { keepNext: true, after: 60, line: 276 }));
      children.push(table(b));
      if (b.note) children.push(P(runs(b.note, { size: 18 }), { after: 240, line: 240 }));
      else children.push(P([new TextRun({ text: "", size: 12 })], { after: 120 }));
      break;
    case "refs":
      b.items.forEach((r, k) => children.push(new Paragraph({ spacing: { line: 276, after: 60 }, indent: { left: 567, hanging: 567 },
        children: [new TextRun({ text: `[${k + 1}]\t`, font: FONT, size: 22 }), ...runs(r, { size: 22 })],
        tabStops: [{ type: TabStopType.LEFT, position: 567 }] })));
      break;
    case "pagebreak": children.push(new Paragraph({ children: [new PageBreak()] })); break;
  }
}

const doc = new Document({
  creator: "Authors", title: spec.meta.title, description: spec.meta.description || "",
  styles: {
    default: { document: { run: { font: FONT, size: BODY } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true }, paragraph: { spacing: { before: 300, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true, italics: false }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, italics: true }, paragraph: { spacing: { before: 160, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 567, hanging: 283 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 567, hanging: 283 } } } }] },
    { reference: "numbers2", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 567, hanging: 283 } } } }] },
  ] },
  sections: [{
    properties: {
      page: { size: { width: PAGE_W, height: PAGE_H }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } },
      lineNumbers: spec.meta.line_numbers ? { countBy: 1, restart: LineNumberRestartFormat.CONTINUOUS, distance: 300 } : undefined,
    },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT); });
