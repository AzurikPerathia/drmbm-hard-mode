<h1 align="center">Dr. Robotnik's Mean Bean Machine — New Story</h1>

<img width="1279" height="958" alt="2026-08-19_071241" src="https://github.com/user-attachments/assets/8e22164d-e2fc-4f0d-b418-880021f3e344" />

<p align="center"><strong>A configurable challenge expansion for the Sega Mega Drive / Genesis game</strong></p>

<p align="center">
  <strong>New Story mod created by <a href="https://github.com/AzurikPerathia">Azurik Perathia</a></strong>
</p>

<p align="center">
  <a href="https://github.com/AzurikPerathia/drmbm-new-story/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/AzurikPerathia/drmbm-new-story?style=for-the-badge&amp;label=Latest%20Release&amp;color=dd3b3b"></a>
  <a href="#building-from-source"><img alt="Platform" src="https://img.shields.io/badge/Platform-Mega%20Drive%20%2F%20Genesis-1f6feb?style=for-the-badge"></a>
  <a href="#hard-mode"><img alt="Hard Mode" src="https://img.shields.io/badge/Hard%20Mode-Optional-f0a020?style=for-the-badge"></a>
</p>

<p align="center">
  Built from the work-in-progress disassembly by the
  <a href="https://github.com/Scrambled-Beans/drmbm-md-disasm">Scrambled Beans team</a>.
</p>

<p align="center">
  <a href="https://github.com/AzurikPerathia/drmbm-new-story/releases/tag/v0.2"><strong>Download v0.2</strong></a>
  ·
  <a href="CHANGELOG.md">Read the changelog</a>
  ·
  <a href="https://github.com/AzurikPerathia/drmbm-new-story">Browse the source</a>
</p>

---

## About the project

This project expands *Dr. Robotnik's Mean Bean Machine* with a much more demanding CPU opponent and several gameplay enhancements, while keeping the original experience available.

The Scenario menu also includes an early **Hero Story / Dark Story** prototype. Hero Story preserves the original campaign against Robotnik's forces, while Dark Story begins a new route against Sonic's friends.

Version **0.2** adds the first playable Dark Story stage against Cream, a fully customized animated introduction, a redesigned *New Story* title screen, story-specific combo voices, and extensive visual and control fixes. See [CHANGELOG.md](CHANGELOG.md) for the complete list of changes and fixes since v0.1.

A new **HARD MODE** option appears directly above **VS.COM LEVEL** in the Options menu. It is disabled by default and saved alongside the other game settings.

- **HARD MODE: OFF** — restores the original gameplay behavior.
- **HARD MODE: ON** — enables every enhancement included in this project.

<img width="1276" height="957" alt="2026-08-18_223142" src="https://github.com/user-attachments/assets/577d6daf-7af5-4c08-9190-e2463e63338f" />

## Story modes

Choose **SCENARIO**, then **START**, to open the new route selector:

- **DARK STORY** — a new route opposing Sonic's friends. The current prototype contains one stage against Cream and returns to the menu after victory.
- **HERO STORY** — the complete original campaign against Robotnik and his villains, unchanged.

<img width="1255" height="942" alt="2026-08-19_022620" src="https://github.com/user-attachments/assets/9e52fa75-c500-49b1-a1ff-a76bda2e08cc" />


Cream now has an original animated introduction with several expressive poses. Her custom in-game portrait blinks, moves her ears, becomes visibly cheerful while winning, alternates between worried and stressed expressions near defeat, and shows a dedicated disgusted reaction after losing. The Dark Story stage card identifies **CREAM** beneath a blue **STAGE** label and a yellow stage number. The original neutral artwork and animation reference were supplied by AzurikPerathia and converted into native Mega Drive tiles, mappings, palettes, and animation scripts for this project.

<img width="1285" height="963" alt="2026-08-19_071313" src="https://github.com/user-attachments/assets/b08f51df-9027-4c9a-9ffa-57f918e4f518" />

The dialogue presentation uses explicit layering: scenery remains behind the dialogue box, while Cream—the active speaker—stays in front. Both controllers can operate the mode selector.

<img width="1278" height="958" alt="2026-08-19_072133" src="https://github.com/user-attachments/assets/64fcc33b-709d-46a0-a179-f76d8440f775" />

### New Story title screen

Version 0.2 replaces the old presentation with a native Mega Drive conversion of the *Mean Bean Machine: New Story* logo. The screen includes subtle logo movement, a blinking **PRESS START** prompt, title music, the credit **AZURIK PERATHIA - 2026**, and the final version number. Starting the game now proceeds directly to the mode selector instead of displaying the legacy second title screen.

## Hard Mode

| Feature | Hard Mode OFF | Hard Mode ON |
|---|---|---|
| CPU intelligence | Original opponent profiles | Enhanced evaluator on all 13 stages |
| Chain planning | Original plans and timing | Verified chain plans from 1 to 7 links |
| AI temperament | Original stage behavior | Random Weak, Medium, or Brutal temperament per battle |
| Obstacles | Original garbage handling | Tries compact builds elsewhere before targeting non-blocking rocks |
| Combo voices | Original assignments | **Yeehaw** for the player and **Yippee** for opponents |
| Heavy landing | Original stage-specific behavior | Player board shake and heavy landing sound in every stage |
| Score after defeat | Reset as in the original game | Current player score is preserved |

### Smarter and more aggressive AI

Each battle randomly selects one of three equally likely CPU temperaments:

- **Weak** builds chains from 1 to 3 links.
- **Medium** builds chains from 1 to 7 links.
- **Brutal** continuously prioritizes 6- and 7-link chains.

The enhanced AI uses seven verified chain plans. After completing a chain, it immediately starts preparing the next one. If a large setup is blocked by black rocks or an uneven field, it first attempts a smaller construction elsewhere instead of automatically abandoning its game to remove the obstacle.

### Score preservation

When the player is defeated in Hard Mode, the current score is carried into the retry flow. Starting a completely new game still resets the score normally.

### Combo voices

Hard Mode swaps the combo voice roles requested for this edition:

- The player receives the **Yeehaw** combo calls.
- CPU opponents receive the **Yippee** combo calls.

### Heavy landing and board shake

The player's beans trigger the heavy landing sound and board shake in every stage. The correct board is animated even when the controls are swapped. CPU opponents retain their original stage-specific behavior.

## Download and play

The latest prebuilt ROM is available from the [GitHub Releases page](https://github.com/AzurikPerathia/drmbm-new-story/releases/latest).

For version `v0.2`:

- ROM size: **1 MiB**
- SHA-256: `4D1EAEC1F93EF20DA78E681362E84E29A24F033D648878516AE0E8D78BA2454F`

Use the ROM with a compatible Sega Mega Drive / Genesis emulator or suitable original hardware setup. HARD MODE can be enabled from the in-game Options menu.

## Building from source

### Windows

1. Clone or download this repository.
2. Open `build config.asm` and adjust the desired build settings. The defaults produce the USA version.
3. Run `build rom (Windows).bat`.
4. Find the compiled ROM and assembly log in the `output` directory.

The repository includes the required Windows build tools. The main assembler command produces a 1 MiB ROM and the included utility fixes its header checksum.

## Project structure

| Path | Purpose |
|---|---|
| `drmbm.asm` | Main game disassembly and Hard Mode logic |
| `include/` | Constants, macros, RAM definitions, and supporting projects |
| `modules/` | Reusable assembly modules and default option setup |
| `resources/` | Art, mappings, palettes, text, and game data |
| `sound/` | Music, sound effects, PCM banks, and sound-driver data |
| `tools/` | Assemblers, compressors, and ROM utilities |
| `output/` | Generated ROM, listing, and build log |

## Sprite editing

Use [Flex2-Puyo](https://github.com/Nasina7/Flex2-Puyo/releases) to edit compatible sprite data. A work-in-progress editing project is available under `include/projects/Flex2-Puyo`.

## Credits and attribution

### Hard Mode author

- **[AzurikPerathia](https://github.com/AzurikPerathia)** — creator and author of the Hard Mode mod

### Original disassembly

This Hard Mode edition is based on the original
[Dr. Robotnik's Mean Bean Machine disassembly](https://github.com/Scrambled-Beans/drmbm-md-disasm).

If you use this code in another ROM hack, please preserve the upstream attribution and link to the original disassembly.

<details>
<summary><strong>Original disassembly contributors</strong></summary>

- RadioTails
- Ralakimus
- Nasina
- TomboyDragon
- Neto
- DaxKatter
- ArcaniaCQ
- Kiwami
- AdolescentSeagull
- Hivebrain
- MarkeyJester
- Totally-Not-Filter

</details>

### Tools

- [puyomdtool](https://github.com/Nasina7/puyomdtool/releases) by Nasina
- [ClownAssembler](https://github.com/Clownacy/clownassembler/releases) by Clownacy
- [ClownNemesis](https://github.com/Clownacy/clownnemesis/releases) by Clownacy
- [Enigma compression tool](https://www.romhacking.net/utilities/757/) by Kosinski

## Contributing and support

Suggestions and pull requests for this Hard Mode edition are welcome. Please use this repository's [Issues page](https://github.com/AzurikPerathia/drmbm-new-story/issues) for reproducible problems or enhancement ideas.

For general Mega Drive reverse-engineering and ROM-hacking help, these communities may also be useful:

- [Sonic Retro — Engineering / Reverse Engineering](https://forums.sonicretro.org/forums/engineering-reverse-engineering.13/)
- [Sonic Stuff Research Group](https://sonicresearch.org/community/index.php)
- [ROMhacking.net](https://www.romhacking.net)

## Disclaimer

- This repository is provided for informational and educational purposes.
- Commercial use is expressly prohibited.
- The project contributors do not claim ownership of the original game or its copyrighted assets.
- You are responsible for complying with the laws applicable in your region and for using legally obtained game data.
- The project is provided without warranty; contributors accept no responsibility for its use.

---

<p align="center"><strong>Ready for a meaner Mean Bean Machine? Enable HARD MODE and build your chain.</strong></p>
