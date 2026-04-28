# DeafComms

**A quick text-communication overlay for deaf and hard-of-hearing Valorant players.**

DeafComms is a lightweight accessibility tool that helps deaf and hard-of-hearing players communicate with their teammates during gameplay through fast, predefined text messages displayed as on-screen popups. It is designed to partially offset the disadvantage these players face when they cannot hear in-game audio cues such as footsteps, reloads, ability sounds, or spike audio, and when voice chat is not accessible to them.

This is a community-driven, open-source project. Contributions, translations, and feedback from deaf and hard-of-hearing players are very welcome.

---

## What it does

- Provides a hotkey-driven menu system (V, Z, F1–F5, backtick) for sending short predefined messages to teammates.
- Displays messages as large, easily readable popups on each player's own screen.
- Supports a tactical countdown ("3, 2, 1, GO!") for coordinated team pushes.
- Bilingual interface (English / Turkish), easy to extend to other languages.
- Lightweight WebSocket-based server for routing messages between teammates in the same room.

---

## What it does NOT do

This tool was deliberately designed to avoid any interaction with game clients or anti-cheat systems. Specifically, it does **not**:

- Inject any DLL or code into the game process.
- Read, scan, or modify game memory.
- Read, modify, or tamper with any game files or configuration.
- Simulate keyboard or mouse input to the game in any way.
- Use `SetWindowsHookEx` or any other low-level input-hooking mechanism.
- Communicate with the game client or any anti-cheat system in any direction.
- Display any in-game information (enemy positions, HP, timers, etc.).

It is purely a manual text-messaging tool: a teammate presses a hotkey, teammates see the text. It is functionally equivalent to typing messages in an external chat — only faster and more readable for users who rely on visual communication.

---

## How it works (technical overview)

- Standalone Python application running in its own process.
- Creates independent top-level Tkinter windows with the "always-on-top" attribute. These windows are rendered by Windows itself, **not** by the game.
- Listens for global hotkeys via `RegisterHotKey` (a standard, documented Win32 API).
- Sends short predefined text messages between teammates over a WebSocket connection.
- Recommended to be used in **windowed fullscreen** mode so the overlay windows display naturally above the game, just like Discord, Steam, or OBS overlays do.

---

## Requirements

- Windows 10 or 11
- Python 3.9+
- `pip install websockets`

---

## Usage

```bash
python deafcomms.py
```

On first launch, a setup screen will ask for:

- **Language** (English / Turkish)
- **Player name**
- **Room ID** (teammates must use the same room ID to communicate)
- **Server URL** (a WebSocket server)

### Hotkeys

| Key       | Action                                                          |
| --------- | --------------------------------------------------------------- |
| `V`       | Emergency menu — double-tap for "ENEMY HERE!"                   |
| `Z`       | Tactics / Strategy menu — double-tap for "Swing together 3,2,1" |
| `` ` ``   | Urgent menu — double-tap for "GO NOW!"                          |
| `F1`–`F5` | Direct quick messages                                           |
| `1`–`6`   | Menu navigation (only while a menu is open)                     |

---

## Notes for anti-cheat compliance

This project has been built with strong attention to anti-cheat compatibility. All input handling uses the official Windows `RegisterHotKey` API, which is the standard documented way for an application to listen for global hotkeys. There is no process injection, no memory access, no file tampering, and no input simulation directed at any game.

The author is in the process of contacting Riot Games support proactively to confirm Vanguard compatibility for this accessibility tool. Updates to this section will be added as official guidance is received.

If you are a developer or a representative of an anti-cheat team and you would like clarification about any aspect of the implementation, please open an issue on this repository.

---

## Roadmap

- [ ] More languages (Spanish, Portuguese, German, French, Russian, etc.)
- [ ] Customizable hotkeys via the setup screen
- [ ] Customizable message presets per user
- [ ] Optional Discord webhook bridge for users who prefer Discord notifications
- [ ] Visual indicator improvements based on feedback from deaf and HoH players

---

## Contributing

This tool exists for the deaf and hard-of-hearing gaming community. Feedback from real users is the most valuable thing this project can receive. If you are a deaf or HoH player and you have suggestions, please open an issue describing what would help you most.

Pull requests for new languages, bug fixes, and accessibility improvements are very welcome.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

You are free to use, modify, and distribute this software. If you build on it for your own community, a link back to this repository is appreciated but not required.

---

## Acknowledgements

Built for and with the help of deaf and hard-of-hearing players who want to compete on equal footing with their hearing teammates. Thank you to everyone who has tested early versions and shared feedback.
