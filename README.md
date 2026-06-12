# DoALL

A terminal TUI dashboard for doing everything — notes, clock, music, games, todos, and more. Built with [Textual](https://github.com/Textualize/textual).

## Modules

### Time & Planning
| Module | Description |
|---|---|
| Clock | Alarm (SQLite), stopwatch, and countdown timer |
| Time Zones | Compare time across multiple timezones |
| Countdown | Event countdowns with days/hours/minutes remaining |
| Job Tracker | Job application tracker with filters, statuses, and salary tracking |

### Writing & Notes
| Module | Description |
|---|---|
| Note Taker | Markdown note editor with live preview, persisted to files |
| Todos | Task manager with priorities, due dates, and status tracking (SQLite) |
| Cheat Sheets | Quick-reference cheatsheets with search, persisted to files |
| Word Counter | Character, word, sentence, and paragraph counts |

### Finance
| Module | Description |
|---|---|
| Money Tracker | Income and expense tracking with category summaries (SQLite) |
| Budget Tracker | Monthly budgeting with categories, increase/decrease impact, and progress tracking (SQLite) |

### Developer Tools
| Module | Description |
|---|---|
| JSON Tool | JSON formatter, validator, and minifier |
| Base Converter | Convert between binary, octal, decimal, and hex |
| Regex Tester | Test regular expressions against input text with match highlighting |
| CSV Viewer | View and browse CSV files in a table |
| Subnet Calc | Calculate subnet masks, CIDR ranges, and IP info |
| Port Checker | Check if a port is open on a given host |
| Changelog Gen | Generate changelogs from git commit history |
| QR Gen & Extract | Generate QR codes from text and extract data from QR images |
| Gitignore Builder | Build .gitignore files from templates for various languages/IDEs |
| Lorem Ipsum | Generate placeholder text by paragraphs, sentences, or words |

### Converters & Calc
| Module | Description |
|---|---|
| Unit Converter | Convert between common units (length, mass, temperature, etc.) |
| Color Picker | Pick, preview, and convert colors between hex, RGB, and HSL |
| Random Picker | Pick a random item from a list or generate random numbers |

### Entertainment
| Module | Description |
|---|---|
| Music | Album/track browser, playlists, queue, and playback |
| Games | Collection of terminal games |
| Typing Test | Measure typing speed and accuracy with sample texts |

### Life & Home
| Module | Description |
|---|---|
| Recipe Manager | Store and browse recipes with ingredients and instructions |
| Habit Tracker | Track daily habits with a weekly grid and streak counters (SQLite) |

## Installation & Run

### Package
**Download and Run**: 

Download the current version from the packages tab. 

Latest version might not have the acutal latest modules, if wanted then clone repository.

in Linux: Open the directory where the app is downloaded and run it using.
```bash
./doall
```

### Clone Repository
Make sure that you have uv "we don't use pip here"

1. Clone the repository:
```bash
git clone git@github.com:HuSSonO3/DoALL.git
```

2. Go to Directory:
```bash
cd DoALL
```

3. Run the application:
```bash
uv run main.py
## or
uv run python main.py 
```

## Contribution
If someone want to contribute lol.

View [Contribution](CONTRIBUTING.md).

Just be nice and I will try to be as active as possible to review PRs lol.

---

## Pictures!

<img width="1844" height="957" alt="image" src="https://github.com/user-attachments/assets/d985da9a-7c4a-4d16-8552-95538d75ab15" />


<img width="1844" height="957" alt="image" src="https://github.com/user-attachments/assets/4fafaec7-5d88-46e2-888a-f6a80c17614a" />


---

> [!NOTE]
> **AI-generated content:** This README, some modules, and portions of the codebase were generated with assistance from Claude Code (Anthropic) and the DeepSeek API "mostly me just testing how to guide the AI properly to make it make what I want while I focus on my other projects so some code might suck but it does the work ig?". 
>
> **Note:** Some modules have layout elements that require a wider terminal. If buttons or side panels appear clipped, increase your terminal width to fully view all features.

> [!CAUTION]
> **Package Issues** Even though there is a package released, I havn't tested the MacOS and Windows version myself so it might not work as intended for certain modules that don't have the same packages that are used "Mainly Music uses ffplay, mpv, aplay, or afplay so if it doesn't exist in the OS it might not work".
>
> **Data Hit/Miss:** Some modules data might be out of date / inaccurate so do take them with a grain of salt.
