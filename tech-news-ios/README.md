# Tech News iOS App

SwiftUI-based iOS application for reading tech news.

## Requirements

- Xcode 15.0+
- iOS 16.0+
- Swift 5.9+

## Project Setup

### Option 1: Using XcodeGen (Recommended)

```bash
# Install xcodegen
brew install xcodegen

# Generate project
cd tech-news-ios
xcodegen generate

# Open in Xcode
open TechNewsApp.xcodeproj
```

### Option 2: Create Manually in Xcode

1. Open Xcode and create a new project
2. Select "App" template
3. Configure:
   - Product Name: TechNewsApp
   - Team: Your team
   - Organization Identifier: com.technews
   - Interface: SwiftUI
   - Language: Swift
4. Replace the generated files with the source files in this directory

## Features

- **Today's News**: View the latest tech news with AI-powered summaries
- **Archive**: Browse past news by date/month
- **Favorites**: Save articles for later reading
- **User Preferences**: Customize category preferences and notifications

## Project Structure

```
TechNewsApp/
├── App/
│   └── TechNewsAppApp.swift      # App entry point
├── Models/
│   ├── News.swift                # News data model
│   ├── User.swift                # User and auth models
│   └── UserPreference.swift      # User preference model
├── ViewModels/
│   ├── AuthViewModel.swift       # Authentication state
│   ├── NewsViewModel.swift       # News data management
│   └── SettingsViewModel.swift   # Settings state
├── Views/
│   ├── ContentView.swift         # Main tab view
│   ├── News/
│   │   ├── NewsListView.swift    # Today's news list
│   │   ├── NewsDetailView.swift  # Article detail
│   │   └── ArchiveView.swift     # Archive browser
│   ├── Auth/
│   │   ├── LoginView.swift       # Login screen
│   │   └── RegisterView.swift    # Registration screen
│   └── Settings/
│       └── SettingsView.swift    # Settings and preferences
├── Services/
│   ├── APIClient.swift           # Network layer
│   ├── AuthService.swift         # Auth API calls
│   └── NewsService.swift         # News API calls
├── Utils/
│   ├── Constants.swift           # App constants
│   └── Extensions.swift          # Swift extensions
└── Resources/
    └── Info.plist               # App configuration
```

## Architecture

- **UI Framework**: SwiftUI
- **Architecture Pattern**: MVVM
- **Networking**: URLSession + async/await
- **State Management**: @StateObject, @Published
- **Storage**: UserDefaults (auth tokens)

## Configuration

### API Base URL

Set the API base URL in `Constants.swift`:

```swift
static let apiBaseURL = "http://localhost:8080"  // Development
// static let apiBaseURL = "https://api.technews.com"  // Production
```

Or set via environment variable:
```bash
export API_BASE_URL=https://your-api-server.com
```

## Running the App

1. Ensure the API server is running
2. Build and run in Xcode (⌘R)
3. Select a simulator or physical device

## Testing

```bash
# Run unit tests
xcodebuild test -scheme TechNewsApp -destination 'platform=iOS Simulator,name=iPhone 15'

# Run UI tests
xcodebuild test -scheme TechNewsAppUITests -destination 'platform=iOS Simulator,name=iPhone 15'
```

## Dependencies

This project uses only native Apple frameworks:
- SwiftUI
- Combine
- Foundation
- UIKit (for sharing functionality)

## License

MIT License
