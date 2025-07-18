// You can either use `@latest` or load a specific version with, for example, `@0.4.0`.
await loadScript(
    'https://cdn.jsdelivr.net/npm/hydra-midi@latest/dist/index.js'
)

// Use midi messages from all channels of all inputs.
await midi.start({ channel: '*', input: 'borderland_pandelirium' })
// Show a small midi monitor (similar to hydra's `a.show()`).
midi.show()

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
    .diff(shape(cc(5).range(3, 10), 0.8, .09)
        .repeat(20, 20))
    .add(
        src(o0)
            .scale(0.95)
            .rotate(cc(4).range(0, 0.2))
            .color(1, 0.5, 0.2)
            .brightness(.15), .7)
    .out(o0)

src(o0)
    .modulate(noise(0.5, 0.2))
    .fisheye(() => mouse.x / width, () => mouse.y / height, 0.01)
    .out(o1)

console.log(cc(1))

render(o1)
