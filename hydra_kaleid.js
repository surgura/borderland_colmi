color_r = 1.0;
color_g = 1.0;
color_b = 1.0;
color_r_target = 1.0;
color_g_target = 1.0;
color_b_target = 1.0;

kaleidval = 3.0;
kaleidval_target = 3.0;

scaleval = 1.0;
scaleval_target = 1.0;

// You can either use `@latest` or load a specific version with, for example, `@0.4.0`.
await loadScript(
    'https://cdn.jsdelivr.net/npm/hydra-midi@latest/dist/index.js'
)

// Use midi messages from all channels of all inputs.
await midi.start({ channel: '*', input: 'borderland_pandelirium' })
// Show a small midi monitor (similar to hydra's `a.show()`).
midi.show()

function vibrantColor() {
    h = Math.floor(Math.random() * 360);
    s = 100;
    l = 50;

    function hslToRgbUnit(h, s, l) {
        s /= 100;
        l /= 100;
        k = n => (n + h / 30) % 12;
        a = s * Math.min(l, 1 - l);
        f = n =>
            l - a * Math.max(-1, Math.min(Math.min(k(n) - 3, 9 - k(n)), 1));
        return [
            f(0),
            f(8),
            f(4)
        ];
    }
    return hslToRgbUnit(h, s, l);
}

function lerp(a, b, t) {
    return a + (b - a) * t;
}

setInterval(() => {
    if (cc(4)() > 0.7) {
        console.log("ok!");
        [color_r_target, color_g_target, color_b_target] = vibrantColor();
    }
    if (cc(5)() > 0.7) {
        kaleidval_target = 3 + Math.round(Math.random() * 8);
    }
    if (cc(6)() > 0.7) {
        scaleopts = [0.05, 0.20, 1.0, 5.0];
        new_scaleval_target = scaleval_target;
        while (new_scaleval_target == scaleval_target) {
            new_scaleval_target = scaleopts[Math.floor(Math.random() * scaleopts.length)];
        }
        scaleval_target = new_scaleval_target
    }

    color_r = lerp(color_r, color_r_target, 0.05);
    color_g = lerp(color_g, color_g_target, 0.05);
    color_b = lerp(color_b, color_b_target, 0.05);
    kaleidval = lerp(kaleidval, kaleidval_target, 0.1);
    scaleval = lerp(scaleval, scaleval_target, 0.1);
}, 16);

// window.addEventListener('keydown', (e) => {
// 	if (e.key === 'a') {
// 		[color_r_target, color_g_target, color_b_target] = vibrantColor();
// 	}
// 	if (e.key === 's') {
// 		kaleidval_target = 3 + Math.round(Math.random() * 8);
// 	}
// 	if (e.key === 'd') {
// 		scaleopts = [0.05, 0.20, 1.0, 5.0];
// 		new_scaleval_target = scaleval_target;
// 		while (new_scaleval_target == scaleval_target) {
// 			new_scaleval_target = scaleopts[Math.floor(Math.random() * scaleopts.length)];
// 		}
// 		scaleval_target = new_scaleval_target
// 	}
// });

voronoi(5, 0.3, () => mouse.x / width * 2 + 0)
    .repeat(2.0, 5.0, 0.0, 0.0)
    .kaleid(() => kaleidval)
    .color(() => color_r, () => color_g, () => 0.5 + 0.5 * color_b)
    .modulateScale(osc(10, -0.2, 10), 0.2)
    .kaleid(() => kaleidval)
    .scale(() => scaleval)
    .out(o0);