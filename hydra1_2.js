setFunction({
    name: 'fisheye',
    type: 'coord',
    inputs: [{
        type: 'float',
        name: 'x',
        default: 0,
    },
    {
        type: 'float',
        name: 'y',
        default: 0,
    },
    {
        type: 'float',
        name: 'strength',
        default: 1.0,
    }
    ],
    glsl: `   vec2 center = vec2(x, y);
    vec2 offset = _st - center;
    float r = length(offset);

    float k = 1.0 + strength /r / r;
    return center + offset / k;`
})

solid(1, 1, 1)
    .diff(shape(() => Math.round(10 * mouse.y / width + 4), 0.8, .09)
        .repeat(20, 10))
    .add(
        src(o0)
            .scale(0.95)
            .rotate(() => (mouse.x - width / 2) / width / 10)
            .color(1, 0.5, 0.2)
            .brightness(.15), .7)
    .out(o0)

src(o0)
    .fisheye(0.2, 0.2, 0.01).fisheye(0.8, 0.8, 0.01).fisheye(() => mouse.x / width, () => mouse.y / height, 0.01)
    .out(o1)

render(o1)