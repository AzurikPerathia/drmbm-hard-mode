# Changelog

All notable changes to *Dr. Robotnik's Mean Bean Machine — Hard Mode* are documented here.

## [v0.2] — 2026-08-19

Version 0.2 expands the v0.1 Hard Mode release with the first playable New Story content, a redesigned title presentation, new character animation, and a large set of visual, control, and routing fixes.

### Added since v0.1

- Added a **DARK STORY / HERO STORY** selector to Scenario mode.
- Added the first Dark Story prototype stage against **Cream the Rabbit**, while preserving the complete original campaign as Hero Story.
- Added an original animated introduction and a full set of expressive in-game reactions for Cream.
- Added a dedicated Dark Story stage card and story-specific **Yeehaw / Yippee** combo voice roles.
- Added a completely redesigned and animated *Mean Bean Machine: New Story* title screen with music, creator credit, and version information.
- Added Controller 2 support to the mode selector; either controller can navigate and confirm.

### Changed since v0.1

- Scenario mode now opens the story selector before starting a campaign.
- Dark Story now contains the new route against Sonic's friends; Hero Story contains the original route against Robotnik's forces.
- The New Story title proceeds directly to the mode selector after Start, skipping the redundant legacy title screen.
- Cream's dialogue boxes were moved upward to avoid covering her animation.
- Dialogue layering now keeps all scenery behind the box and text while leaving Cream, the active speaker, in front.
- The New Story logo was rebuilt as separate optimized art instead of replacing or stretching the original title assets.
- Project documentation now names **Azurik Perathia** as the creator and author of the mod.

### Corrections made during v0.2 development

- Fixed Hero Story opening the password screen instead of launching the original campaign.
- Fixed the Dark Story and Hero Story menu labels, alignment, selection routing, and swapped story logic.
- Fixed the mode selector becoming unresponsive after leaving the title screen.
- Fixed mode selection when Controller 2 is the active controller.
- Fixed visual corruption after completing the original story and returning to the mode selector.
- Fixed Cream's portrait shrinking after defeat.
- Fixed Cream portrait corruption during the white damage flash.
- Fixed missing tiles, holes, clipping, and incorrect mapping in Cream's dialogue sprites.
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

### Corrections related specifically to v0.1

- Corrected the creator-name formatting and mod-author attribution in the README.
- No released v0.1 gameplay system required a compatibility fix; its Hard Mode AI, score preservation, heavy landing effects, and option behavior remain unchanged in v0.2.

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
