"""Gitignore template data for common languages, IDEs, and OSes."""

TEMPLATES = {
    "Python": (
        "# Byte-compiled / optimized\n"
        "__pycache__/\n*.py[cod]\n*$py.class\n"
        "*.so\n*.egg-info/\ndist/\nbuild/\n"
        "*.egg\n.eggs/\n"
        "# Virtual environments\n"
        "venv/\n.venv/\nenv/\n"
        "# IDE\n.vscode/\n.idea/\n"
        "# Testing\n.pytest_cache/\n.coverage\nhtmlcov/\n"
        "# Jupyter\n.ipynb_checkpoints/\n"
        "# Env files\n.env\n.env.local\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "Node / JS": (
        "# Dependencies\nnode_modules/\n"
        "# Build output\ndist/\nbuild/\n*.tsbuildinfo\n"
        "# Environment\n.env\n.env.local\n.env.*.local\n"
        "# Logs\n*.log\nnpm-debug.log*\n"
        "# Package locks (choose one)\n"
        "# package-lock.json\n# yarn.lock\n"
        "# Next.js\n.next/\n"
        "# Nuxt\n.nuxt/\n.output/\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "Rust": (
        "# Build output\ntarget/\n"
        "# Dependencies\nCargo.lock\n"
        "# IDE\n.vscode/\n.idea/\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "Go": (
        "# Binaries\n*.exe\n*.exe~\n*.dll\n*.so\n*.dylib\n"
        "# Test binary\n*.test\n"
        "# Output of go coverage\n*.out\n"
        "# Vendor\nvendor/\n"
        "# IDE\n.vscode/\n.idea/\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "Java": (
        "# Compiled classes\n*.class\n"
        "# Build\nbuild/\ntarget/\n*.jar\n*.war\n"
        "# IDE\n.idea/\n*.iml\n.settings/\n.project\n.classpath\n"
        "# Gradle\n.gradle/\n"
        "# Maven\npom.xml.tag\npom.xml.releaseBackup\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "C / C++": (
        "# Compiled output\n*.o\n*.obj\n*.exe\n*.out\n*.a\n*.so\n*.dylib\n"
        "# Debug\n*.dSYM/\n"
        "# Build\nbuild/\ncmake-build-*/\n"
        "# IDE\n.vscode/\n.idea/\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    ".NET / C#": (
        "# Build\nbin/\nobj/\n*.user\n*.suo\n*.userosscache\n*.sln.docstates\n"
        "# Packages\npackages/\n*.nupkg\n"
        "# VS Code\n.vscode/\n"
        "# Rider\n.idea/\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "Ruby": (
        "# Gems\n*.gem\n.bundle/\nvendor/bundle/\n"
        "# Environment\n.env\n.env.local\n"
        "# Logs\n*.log\n"
        "# Temp\ntmp/\ncache/\n"
        "# Database\n*.sqlite3\ndb/*.sqlite3\n"
        "# IDE\n.vscode/\n.idea/\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "Rails": (
        "# Ruby gems\n*.gem\n.bundle/\nvendor/bundle/\n"
        "# Environment\n.env\n.env.local\n"
        "# Logs / temp\n*.log\ntmp/\nlog/\n"
        "# Database\n*.sqlite3\ndb/*.sqlite3\n"
        "# Assets\npublic/assets/\npublic/packs/\n"
        "# Credentials\nconfig/master.key\nconfig/credentials/*.key\n"
        "# IDE\n.vscode/\n.idea/\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "PHP": (
        "# Dependencies\nvendor/\n"
        "# Build\n*.log\n"
        "# Environment\n.env\n.env.local\n"
        "# Composer\ncomposer.phar\ncomposer.lock\n"
        "# IDE\n.vscode/\n.idea/\n"
        "# OS\n.DS_Store\nThumbs.db\n"
    ),
    "macOS": (
        "# General\n.DS_Store\n.AppleDouble\n.LSOverride\n"
        "# Icon\nIcon\r\n\r"
        "# Thumbnails\n._*\n"
        "# Files that might appear in the root\n.DocumentRevisions-V100\n"
        ".fseventsd\n.Spotlight-V100\n.TemporaryItems\n.Trashes\n.VolumeIcon.icns\n"
        ".com.apple.timemachine.donotpresent\n"
        "# Directories potentially created on remote AFP share\n"
        ".AppleDB\n.AppleDesktop\nNetwork Trash Folder\n"
        "Temporary Items\n.apdisk\n"
    ),
    "Windows": (
        "# Windows thumbnail cache\nThumbs.db\nThumbs.db:encryptable\n"
        "ehthumbs.db\nehthumbs_vista.db\n"
        "# Folder config\n[Dd]esktop.ini\n"
        "# Recycle Bin\n$RECYCLE.BIN/\n"
        "# Windows Installer\n*.cab\n*.msi\n*.msix\n*.msm\n*.msp\n"
        "# Shortcuts\n*.lnk\n"
    ),
    "Linux": (
        "# KDE\n.directory\n"
        "# Trash\n.trash-*\n"
        "# Backup files\n*~\n*.swp\n*.swo\n"
        "# Temporary\n*.tmp\n*.temp\n"
    ),
    "VS Code": (
        ".vscode/*\n!.vscode/settings.json\n!.vscode/tasks.json\n"
        "!.vscode/launch.json\n!.vscode/extensions.json\n"
        "!.vscode/*.code-snippets\n"
        "# History\n.history/\n"
        "*.vsix\n"
    ),
    "JetBrains": (
        "# Covers IntelliJ, PyCharm, GoLand, WebStorm, Rider, etc.\n"
        ".idea/\n*.iml\n*.iws\n*.ipr\n"
        "# IDE misc\nout/\n"
        "*.swp\n~$*\n"
    ),
    "Vim": (
        "# Swap\n*.swp\n*.swo\n*~\n"
        "# Session\nSession.vim\nSessionx.vim\n"
        "# Netrw\n.netrwhist\n"
        "# Tags\ntags\ntags.lock\ntags.temp\n"
    ),
    "Docker": (
        "# Docker\n.docker/\n"
        "# Build context (often large)\n"
        "# docker-compose.override.yml (if local secrets)\n"
    ),
    "Terraform": (
        "# Local .terraform directories\n**/.terraform/*\n"
        "# .tfstate files\n*.tfstate\n*.tfstate.*\n"
        "# Crash log files\ncrash.log\ncrash.*.log\n"
        "# Override files\noverride.tf\noverride.tf.json\n"
        "*_override.tf\n*_override.tf.json\n"
        "# CLI config\n.terraformrc\nterraform.rc\n"
    ),
    "Android": (
        "# Built files\n*.apk\n*.aab\n*.ap_\n*.aab\n"
        "# Generated\nbin/\ngen/\nout/\n"
        "# Gradle\n.gradle/\nbuild/\n"
        "# Local config\nlocal.properties\n"
        "# IDE\n.idea/\n*.iml\n"
        "# OS\n.DS_Store\n"
    ),
    "iOS / Swift": (
        "# Xcode\nbuild/\n*.pbxuser\n!default.pbxuser\n*.mode1v3\n!default.mode1v3\n"
        "*.mode2v3\n!default.mode2v3\n*.perspectivev3\n!default.perspectivev3\n"
        "xcuserdata/\n*.xccheckout\n*.moved-aside\nDerivedData/\n"
        "*.hmap\n*.ipa\n*.xcuserstate\n"
        "# CocoaPods\nPods/\n"
        "# Carthage\nCarthage/Build/\n"
        "# Swift Package Manager\n.build/\n.swiftpm/\n"
        "# Fastlane\nfastlane/report.xml\n"
        "# OS\n.DS_Store\n"
    ),
}

TEMPLATE_NAMES = list(TEMPLATES.keys())
