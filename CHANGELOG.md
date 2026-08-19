# Changelog

All notable changes to *Dr. Robotnik's Mean Bean Machine — Hard Mode* are documented here.

## [v0.2] — 2026-08-19

Version 0.2 expands the v0.1 Hard Mode release with the first playable New Story content, a redesigned title presentation, new character animation, and a large set of visual, control, and routing fixes.

### Added since v0.1

- Added a **DARK STORY / HERO STORY** selector to Scenario mode.
- Added the first Dark Story prototype stage, with Robotnik's side facing **Cream the Rabbit**.
- Preserved the complete original campaign as Hero Story, where the player faces Robotnik's villains.
- Added a dedicated Cream opponent portrait with neutral, blink, ear movement, happy, upset, stress, and defeated animation states.
- Added five Cream cutscene poses: back turned, turning, normal speaking, hand-on-chest, and shy.
- Added synchronized open- and closed-mouth frames that animate only while her dialogue box is active.
- Added Cream's original four-part English introduction:
  1. “Ohhh... But who is this?”
  2. “Oh, hello, mister! You bad guy! My mommy Vanilla always told me not to talk to strangers!”
  3. “But if you insist, I'm Cream the Rabbit! I'm polite and well-mannered, and I'm going to teach you to respect me!”
  4. “That's what Sonic told me to say, hehe...”
- Added a Dark Story stage card with a blue **STAGE** label, yellow stage number, Cream portrait, and **CREAM** name label.
- Added story-specific combo voice assignments:
  - Dark Story gives the villain player **Yeehaw** and Cream **Yippee**.
  - Hero Story gives the hero player **Yippee** and the villains **Yeehaw**.
- Added a completely redesigned *Mean Bean Machine: New Story* title screen.
- Added subtle title-logo movement and a one-second blinking **PRESS START** prompt with a quick reappearance.
- Added title music, the creator credit **AZURIK PERATHIA - 2026**, and the final **VERSION 0.2** label.
- Added native Mega Drive art, mappings, palettes, and build scripts for Cream and the New Story title logo.
- Added Controller 2 support to the mode selector; either controller can now navigate and confirm.

### Changed since v0.1

- Scenario mode now opens the story selector before starting a campaign.
- Dark Story now contains the new route against Sonic's friends; Hero Story contains the original route against Robotnik's forces.
- The New Story title proceeds directly to the mode selector after Start, skipping the redundant legacy title screen.
- Cream's dialogue boxes were moved upward to avoid covering her animation.
- Dialogue layering now keeps all scenery behind the box and text while leaving Cream, the active speaker, in front.
- The New Story logo was rebuilt as separate optimized art instead of replacing or stretching the original title assets.
- Project documentation now names **Azurik Perathia** as the creator and author of the mod.

### Corrections made after v0.1

- Fixed Hero Story opening the password screen instead of launching the original campaign.
- Fixed the Dark Story and Hero Story menu labels, alignment, selection routing, and swapped story logic.
- Fixed the mode selector becoming unresponsive after leaving the title screen.
- Fixed mode selection when Controller 2 is the active controller.
- Fixed visual corruption after completing the original story and returning to the mode selector.
- Fixed Cream's portrait shrinking after defeat.
- Fixed Cream portrait corruption during the white damage flash.
- Fixed missing tiles, holes, clipping, and incorrect mapping in Cream's dialogue sprites.
- Fixed Cream's mouth continuing to animate after the dialogue box closed.
- Fixed the talking animation failing to start while dialogue was active.
- Fixed the stage card displaying **STAGE 0** instead of **STAGE 1**.
- Fixed the Cream name label being truncated, drawn over the portrait, or positioned above the frame instead of symmetrically below it.
- Fixed incorrect stage-label font and colors; **STAGE** is blue and the number is yellow while preserving the original lettering.
- Fixed dialogue text colors that were difficult to read.
- Fixed dialogue text being covered by hats, foreground scenery, and other tall scene elements.
- Fixed Cream disappearing when dialogue priority was first adjusted.
- Fixed the title logo being stretched, duplicated, partially loaded, or replaced by corrupted tiles.
- Fixed full-screen title tilemap loading and VRAM conflicts that caused severe texture corruption.
- Fixed title-screen input handoff that could leave the following menu locked.
- Fixed title music not starting after the logo screen.
- Fixed the creator year glyph so **2026** no longer resembles **2028**.
- Fixed the displayed development version from **0.2 ALPHA** to the final **0.2**.
- Fixed creator-name formatting and attribution in the README.

### Features retained from v0.1

- Optional Hard Mode toggle with the original game restored when disabled.
- Enhanced CPU chain planning and Weak, Medium, or Brutal battle temperaments.
- Smarter obstacle handling and continued chain development after completed reactions.
- Player score preservation after defeat in Hard Mode.
- Heavy bean landing sound and board shake for the player on every stage.
- Hard Mode combo voice reassignment.

## [v0.1]

- Introduced the optional Hard Mode feature set.
- Added enhanced AI chain planning, randomized difficulty profiles, score preservation, heavy player landings, and combo voice changes.

[v0.2]: https://github.com/AzurikPerathia/drmbm-new-story/compare/v0.1...v0.2
[v0.1]: https://github.com/AzurikPerathia/drmbm-new-story/releases/tag/v0.1
