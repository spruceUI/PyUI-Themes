# NextUI Style Light *by* Diego Mussi

The light (inverted) version of NextUI Style: off-white background, near-black text,
one flat text list with a rounded highlight, box art (or the system's icon) on the
right, and pill-shaped status and button hints. Works at every resolution spruce supports.

## Pick any accent colour

The theme ships with a black highlight. With spruceOS's **Accent Color** app (Apps → Accent Color)
you can recolour it to any colour right on the device: RGB sliders, a hex code
(on-screen keyboard) or presets, with a live preview. It recolours the highlight,
button hints, volume bar, keyboard keys and the in-game menu (`igm.json`), then spruce
reloads the menu.

The `accent/` folder holds the templates the app uses (every accent-dependent image,
plus the theme's palette). The app only touches the accent keys in `config*.json` and
`igm.json`, so other theme settings you changed are kept. Without the app, the theme
works normally in its default colour.

## Notes

- The selected top tab is near-black: PyUI uses the same colour for the on-screen
  keyboard's text, and dark text keeps typing readable with every accent.
- On dark accents the large highlight / keyboard text box uses a lighter shade of
  the accent, so both black and white text stay readable.
- The Accent Color app works with both NextUI Style and NextUI Style Light; it
  detects which version is active.
- This theme ships its own `igm.json`, so while it is active the
  "RA: in-game menu colors" setting has no visible effect.

## Credits

- **Theme design:** Diego Mussi ([@Dmussi](https://github.com/Dmussi)),
  built with the help of Claude (Anthropic).
- **Inspiration:** [NextUI](https://github.com/LoveRetro/NextUI) and
  [MinUI](https://github.com/shauninman/MinUI) by Shaun Inman. Layout inspiration only;
  no NextUI or MinUI assets are used.
- **System and menu icons, button sound:** from spruce's stock **SPRUCE** theme by
  **tenlevels** — console icons from the default OnionOS (libretro systematic) set plus
  RetroActive by baxysquare (MIT), menu icons by [Icons8](https://icons8.com/) (Forma),
  EasyRPG swirl by the EasyRPG Project. Some were recoloured for this theme.
  System names, logos and hardware designs belong to their respective owners.
- **Font:** M PLUS Rounded 1c Bold by The Rounded M+ Project Authors (based on the
  M+ Fonts), SIL Open Font License 1.1 — see `FONT-LICENSE-OFL.txt`. Subset and
  shipped as `nextui.ttf`.
- **Theme engine, in-game menu and theming hooks:** the spruceOS / PyUI team.
