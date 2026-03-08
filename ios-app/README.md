# TechNews iOS App

SwiftUI iOS client for the existing `api-server` and `ai-engine`.

## Requirements

- Xcode 16.2+
- iOS 17+
- `xcodegen` installed

## Setup

1. By default the simulator uses `http://localhost:8080`.
2. On a physical iPhone, `localhost` points to the phone itself, not your Mac. Open the app's `Profile` tab and set `Server URL` to your Mac's LAN address, for example `http://192.168.1.23:8080`.
3. You can also change the bundled default with `API_BASE_URL` in `project.yml`.
4. Generate the Xcode project:

```bash
cd ios-app
xcodegen generate
```

3. Open `TechNewsIOS.xcodeproj` and run on a simulator or device.

## Notes

- The app uses `POST /api/news/{id}/deepsearch?maxIterations=10`.
- If the phone still cannot connect, make sure `api-server` is running and your Mac firewall allows inbound connections on port `8080`.
