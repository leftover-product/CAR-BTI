import Foundation
import AppKit
import CoreGraphics

struct OGPJob: Decodable {
    let kind: String      // "root" | "type" | "vs"
    let out: String
    let src: String
    let code: String
    let cluster: String
    let title: String
    let subtitle: String
    let accent: [CGFloat] // [r, g, b] 0..255
}

func makeFont(_ name: String, _ size: CGFloat, _ fallbackWeight: NSFont.Weight = .bold) -> NSFont {
    if let f = NSFont(name: name, size: size) { return f }
    return NSFont.systemFont(ofSize: size, weight: fallbackWeight)
}

func color(_ r: CGFloat, _ g: CGFloat, _ b: CGFloat, _ a: CGFloat = 1.0) -> NSColor {
    return NSColor(srgbRed: r / 255.0, green: g / 255.0, blue: b / 255.0, alpha: a)
}

func drawRoundedRect(_ rect: CGRect, radius: CGFloat, fill: NSColor?, stroke: NSColor? = nil, lineWidth: CGFloat = 0) {
    let path = NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
    if let f = fill {
        f.setFill()
        path.fill()
    }
    if let s = stroke, lineWidth > 0 {
        s.setStroke()
        path.lineWidth = lineWidth
        path.stroke()
    }
}

func drawCoverImage(_ img: NSImage, in rect: CGRect) {
    let iw = img.size.width
    let ih = img.size.height
    guard iw > 0 && ih > 0 else { return }
    let scale = max(rect.width / iw, rect.height / ih)
    let dw = iw * scale
    let dh = ih * scale
    let dx = rect.minX + (rect.width - dw) / 2.0
    let dy = rect.minY + (rect.height - dh) / 2.0
    NSGraphicsContext.saveGraphicsState()
    NSBezierPath(rect: rect).addClip()
    img.draw(in: CGRect(x: dx, y: dy, width: dw, height: dh), from: .zero, operation: .sourceOver, fraction: 1.0, respectFlipped: true, hints: nil)
    NSGraphicsContext.restoreGraphicsState()
}

func drawText(_ str: String, at point: CGPoint, maxWidth: CGFloat, maxHeight: CGFloat, fontName: String, startSize: CGFloat, minSize: CGFloat = 18, color: NSColor, lineHeightMult: CGFloat = 1.24, align: NSTextAlignment = .left) -> CGFloat {
    let explicitLines = str.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)
    var sz = startSize
    while sz >= minSize {
        let f = makeFont(fontName, sz, .bold)
        let para = NSMutableParagraphStyle()
        para.lineBreakMode = .byWordWrapping
        para.lineHeightMultiple = lineHeightMult
        para.alignment = align
        let attrs: [NSAttributedString.Key: Any] = [
            .font: f,
            .foregroundColor: color,
            .paragraphStyle: para
        ]
        let maxLineW = explicitLines.map { ($0 as NSString).size(withAttributes: [.font: f]).width }.max() ?? 0
        let attrStr = NSAttributedString(string: str, attributes: attrs)
        let bounds = attrStr.boundingRect(with: CGSize(width: maxWidth, height: 1000), options: [.usesLineFragmentOrigin, .usesFontLeading])
        let fitsExplicit = explicitLines.count <= 1 || maxLineW <= maxWidth
        if (bounds.height <= maxHeight && fitsExplicit) || sz <= minSize {
            attrStr.draw(with: CGRect(x: point.x, y: point.y, width: maxWidth, height: maxHeight), options: [.usesLineFragmentOrigin, .usesFontLeading])
            return ceil(bounds.height)
        }
        sz -= 2
    }
    return maxHeight
}

func drawCenteredPill(_ text: String, rect: CGRect, radius: CGFloat, fill: NSColor, textColor: NSColor, fontName: String, fontSize: CGFloat) {
    drawRoundedRect(rect, radius: radius, fill: fill)
    let f = makeFont(fontName, fontSize, .bold)
    let sz = (text as NSString).size(withAttributes: [.font: f])
    let tx = rect.minX + (rect.width - sz.width) / 2.0
    let ty = rect.minY + (rect.height - sz.height) / 2.0 - 1.0
    (text as NSString).draw(at: CGPoint(x: tx, y: ty), withAttributes: [.font: f, .foregroundColor: textColor])
}

func renderJob(_ job: OGPJob) throws {
    let W: CGFloat = 1200
    let H: CGFloat = 630

    guard let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(W),
        pixelsHigh: Int(H),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    ) else {
        throw NSError(domain: "render_ogp", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to allocate bitmap"])
    }
    rep.size = NSSize(width: W, height: H)

    guard let ctx = NSGraphicsContext(bitmapImageRep: rep) else {
        throw NSError(domain: "render_ogp", code: 2, userInfo: [NSLocalizedDescriptionKey: "Failed to create NSGraphicsContext"])
    }

    NSGraphicsContext.saveGraphicsState()
    let cg = ctx.cgContext
    cg.translateBy(x: 0, y: H)
    cg.scaleBy(x: 1, y: -1)
    let flippedCtx = NSGraphicsContext(cgContext: cg, flipped: true)
    NSGraphicsContext.current = flippedCtx

    color(7, 11, 20).setFill()
    NSBezierPath(rect: CGRect(x: 0, y: 0, width: W, height: H)).fill()

    if let img = NSImage(contentsOfFile: job.src) {
        drawCoverImage(img, in: CGRect(x: 80, y: 0, width: W - 60, height: H))
    }

    let ar = job.accent.count >= 3 ? job.accent[0] : 56
    let ag = job.accent.count >= 3 ? job.accent[1] : 189
    let ab = job.accent.count >= 3 ? job.accent[2] : 248
    let accentColor = color(ar, ag, ab)

    if let grad = NSGradient(colorsAndLocations:
        (color(6, 10, 20, 0.96), 0.0),
        (color(6, 10, 20, 0.88), 0.42),
        (color(6, 10, 20, 0.42), 0.66),
        (color(6, 10, 20, 0.08), 1.0)
    ) {
        grad.draw(in: CGRect(x: 0, y: 0, width: W, height: H), angle: 0)
    }

    if let bgrad = NSGradient(colorsAndLocations:
        (color(6, 10, 20, 0.0), 0.0),
        (color(6, 10, 20, 0.72), 1.0)
    ) {
        bgrad.draw(in: CGRect(x: 0, y: H - 120, width: W, height: 120), angle: 90)
    }

    accentColor.setFill()
    NSBezierPath(rect: CGRect(x: 0, y: 0, width: W, height: 8)).fill()
    accentColor.withAlphaComponent(0.75).setFill()
    NSBezierPath(rect: CGRect(x: 0, y: H - 5, width: W, height: 5)).fill()

    let jpBold = "HiraginoSans-W8"
    let jpMid = "HiraginoSans-W6"
    let enBold = "HelveticaNeue-Bold"

    if job.kind == "root" {
        drawRoundedRect(CGRect(x: 60, y: 54, width: 332, height: 46), radius: 23, fill: color(14, 28, 48, 0.92), stroke: accentColor, lineWidth: 2)
        _ = drawText("CAR-BTI | 車好き16タイプ診断", at: CGPoint(x: 82, y: 65), maxWidth: 300, maxHeight: 30, fontName: jpBold, startSize: 18, minSize: 16, color: accentColor)

        _ = drawText(job.title, at: CGPoint(x: 60, y: 128), maxWidth: 680, maxHeight: 165, fontName: jpBold, startSize: 52, minSize: 36, color: .white, lineHeightMult: 1.22)
        _ = drawText(job.subtitle, at: CGPoint(x: 60, y: 310), maxWidth: 660, maxHeight: 110, fontName: jpMid, startSize: 23, minSize: 18, color: color(215, 224, 236), lineHeightMult: 1.38)

        drawCenteredPill("無料で診断スタート（全28問） ›", rect: CGRect(x: 60, y: 458, width: 380, height: 62), radius: 16, fill: accentColor, textColor: color(6, 12, 24), fontName: jpBold, fontSize: 21)
        _ = drawText("16 TYPES × 13 VEHICLES × 5 SCENES  |  car-bti.epcj.info", at: CGPoint(x: 60, y: 558), maxWidth: 720, maxHeight: 30, fontName: enBold, startSize: 17, minSize: 15, color: color(168, 182, 202))
    } else if job.kind == "vs" {
        drawRoundedRect(CGRect(x: 60, y: 52, width: 396, height: 46), radius: 23, fill: color(14, 28, 48, 0.94), stroke: accentColor, lineWidth: 2)
        _ = drawText("🤝  CAR-BTI 友達と相性診断の招待", at: CGPoint(x: 80, y: 63), maxWidth: 360, maxHeight: 30, fontName: jpBold, startSize: 19, minSize: 16, color: accentColor)

        _ = drawText("相手のタイプ：\(job.code)", at: CGPoint(x: 60, y: 120), maxWidth: 640, maxHeight: 58, fontName: jpBold, startSize: 40, minSize: 30, color: accentColor)
        let tH = drawText(job.title, at: CGPoint(x: 60, y: 184), maxWidth: 660, maxHeight: 130, fontName: jpBold, startSize: 42, minSize: 26, color: .white, lineHeightMult: 1.24)
        _ = drawText(job.subtitle, at: CGPoint(x: 60, y: 198 + tH), maxWidth: 660, maxHeight: 100, fontName: jpMid, startSize: 19, minSize: 16, color: color(226, 232, 240), lineHeightMult: 1.38)

        drawCenteredPill("診断して2人の相性％を見る ›", rect: CGRect(x: 60, y: 462, width: 400, height: 62), radius: 16, fill: accentColor, textColor: color(6, 12, 24), fontName: jpBold, fontSize: 21)
        _ = drawText("CAR-BTI 車好き16タイプ診断  |  car-bti.epcj.info", at: CGPoint(x: 60, y: 560), maxWidth: 680, maxHeight: 30, fontName: jpMid, startSize: 16, minSize: 14, color: color(168, 182, 202))
    } else {
        let badgeText = "CAR-BTI | \(job.cluster)"
        let badgeFont = makeFont(jpBold, 19, .bold)
        let bw = ceil((badgeText as NSString).size(withAttributes: [.font: badgeFont]).width) + 44
        drawRoundedRect(CGRect(x: 60, y: 52, width: max(290, bw), height: 46), radius: 23, fill: color(14, 28, 48, 0.92), stroke: accentColor, lineWidth: 2)
        _ = drawText(badgeText, at: CGPoint(x: 82, y: 63), maxWidth: 540, maxHeight: 30, fontName: jpBold, startSize: 19, minSize: 16, color: accentColor)

        _ = drawText(job.code, at: CGPoint(x: 60, y: 112), maxWidth: 560, maxHeight: 108, fontName: enBold, startSize: 96, minSize: 78, color: .white, lineHeightMult: 1.0)
        let titleH = drawText(job.title, at: CGPoint(x: 60, y: 224), maxWidth: 660, maxHeight: 120, fontName: jpBold, startSize: 38, minSize: 24, color: accentColor, lineHeightMult: 1.24)
        _ = drawText(job.subtitle, at: CGPoint(x: 60, y: 238 + titleH), maxWidth: 660, maxHeight: 100, fontName: jpMid, startSize: 19, minSize: 15, color: color(226, 232, 240), lineHeightMult: 1.38)

        drawCenteredPill("診断結果と相性を見る ›", rect: CGRect(x: 60, y: 468, width: 350, height: 60), radius: 15, fill: accentColor, textColor: color(6, 12, 24), fontName: jpBold, fontSize: 21)
        _ = drawText("CAR-BTI 車好き16タイプ診断  |  car-bti.epcj.info", at: CGPoint(x: 60, y: 560), maxWidth: 680, maxHeight: 28, fontName: jpMid, startSize: 16, minSize: 14, color: color(168, 182, 202))
    }

    NSGraphicsContext.restoreGraphicsState()

    guard let jpegData = rep.representation(using: .jpeg, properties: [.compressionFactor: 0.88]) else {
        throw NSError(domain: "render_ogp", code: 3, userInfo: [NSLocalizedDescriptionKey: "JPEG encode failed"])
    }
    let outURL = URL(fileURLWithPath: job.out)
    try FileManager.default.createDirectory(at: outURL.deletingLastPathComponent(), withIntermediateDirectories: true)
    try jpegData.write(to: outURL)
}

guard CommandLine.arguments.count >= 2 else {
    fputs("Usage: render_ogp <jobs.json>\n", stderr)
    exit(1)
}
let manifestPath = CommandLine.arguments[1]
let data = try Data(contentsOf: URL(fileURLWithPath: manifestPath))
let jobs = try JSONDecoder().decode([OGPJob].self, from: data)
for job in jobs {
    try renderJob(job)
}
print("SWIFT_OGP_OK:\(jobs.count)")
