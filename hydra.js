// You can either use `@latest` or load a specific version with, for example, `@0.4.0`.
await loadScript(
    'https://cdn.jsdelivr.net/npm/hydra-midi@latest/dist/index.js'
)

// Use midi messages from all channels of all inputs.
await midi.start({ channel: '*', input: 'borderland_pandelirium' })
// Show a small midi monitor (similar to hydra's `a.show()`).
midi.show()

solid(cc(1), cc(2), cc(3)).out()