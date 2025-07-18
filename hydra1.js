solid(1, 1, 1)
    .diff(shape(() => Math.round(10 * mouse.y / width + 4), 0.8, .09)
        .repeat(20, 10))
    .add(
        src(o0)
            .scale(0.95)
            .rotate(() => (mouse.x - width / 2) / width / 10)
            .color(1, 0.5, 0.2)
            .brightness(.15), .7)
    .pixel((uv, t) => {
        let dx = uv.x - bubbleCenter[0]
        let dy = uv.y - bubbleCenter[1]
        let dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < bubbleRadius) {
            let norm = dist / bubbleRadius
            let factor = 1.0 - bubbleStrength * (1.0 - Math.sqrt(1.0 - norm * norm))
            dx *= factor
            dy *= factor
            return [bubbleCenter[0] + dx, bubbleCenter[1] + dy]
        } else {
            return uv
        }
    })
    .out()