# Outage Monitoring UI

## Overview

The Outage Monitoring UI provides a comprehensive view of cloud provider incidents with a clean, structured format that makes it easy to understand and track outages. The interface now includes enhanced timeline visualization, intelligent summary extraction, automatic status detection, external integration, and a detailed incident slider for better readability.

## UI Layout

### Tabbed Interface

The Outage Monitoring page is organized into two main tabs:

1. **Active Outages**: Shows current monitoring status and provider health
2. **Historical Outages**: Displays detailed incident history with comprehensive formatting

### Historical Outages Display Format

Each incident is displayed in a structured format that includes:

#### Header Section
- **Severity Badge**: Color-coded severity level (high, medium, low)
- **Status Badge**: **Automatically determined** - shows "resolved" if end time exists, otherwise shows original status

#### Incident Details Grid
```
Description:     [Incident Title]
ID:             [Clean ID without prefix - clickable hyperlink to Google Status Page]
Status:          [Auto-determined: resolved/ongoing]
Begin Time:      [Detection Time]
End Time:        [Resolution Time or "Ongoing"]
```

#### Service Information
```
Service:         [Primary Affected Service]
Region:          [Affected Region or "N/A"]
```

#### Intelligent Summary
- **Summary Section**: Automatically extracted key information in a highlighted blue box
- **Most Recent Update**: **Automatically extracted** from timeline or description
- **Duration**: **Calculated automatically** as End Time - Begin Time (e.g., "2 hours 5 minutes")
- **View Details Button**: **Integrated within summary** - lean, compact button design

#### Affected Resources
- **Affected Services**: List of all impacted services (if available)
- **Affected Regions**: List of all impacted regions (if available)
- Displayed as colored tags for easy identification

## Automatic Status Detection

### Smart Status Logic
The system automatically determines incident status based on available information:

- **If End Time Exists**: Status automatically shows as "resolved"
- **If No End Time**: Status shows the original status (e.g., "investigating", "monitoring")
- **Real-time Updates**: Status updates automatically when incidents are resolved
- **Consistent Display**: Status logic applied to both header badges and detail fields

### Status Badge Colors
- **🟢 Resolved**: Green badge for completed incidents
- **🔵 Investigating**: Blue badge for active investigations
- **🟡 Monitoring**: Yellow badge for ongoing monitoring
- **🔴 Active**: Red badge for active issues

## Field Mappings

### Updated Field Names
- **Start Time** → **Begin Time**: More intuitive terminology
- **Incident ID** → **ID**: Cleaner, shorter label with prefix removal
- **Status**: Automatically determined based on resolution

### ID Field Enhancement
- **Prefix Removal**: Automatically removes "historical-gcp-" prefix for cleaner display
- **Clean Display**: Shows only the unique identifier portion
- **Clickable Hyperlink**: Opens Google Cloud Status Page in new tab
- **Example**: "historical-gcp-8cY8jdUpEGGbsSMSQk7J" displays as "8cY8jdUpEGGbsSMSQk7J"
- **Correct URL**: Links to `https://status.cloud.google.com/incidents/{id}`

### Interactive Elements
- **ID Field**: Clickable hyperlink that opens Google Status Page in new tab
- **External Links**: Proper security with `rel="noopener noreferrer"`
- **Hover Effects**: Visual feedback for clickable elements

## Summary Intelligence

### Most Recent Update Extraction
The summary section now focuses on the most current information:

1. **Timeline-based**: Extracts the most recent timeline entry
2. **Pattern Matching**: Looks for update patterns in description
3. **Fallback Logic**: Uses first meaningful sentence if no specific update found
4. **Dynamic Content**: Summary adapts to incident content

### Summary Display
- **Highlighted Box**: Summary displayed in a prominent blue box
- **Single Column Layout**: Focused on most recent update
- **Duration Information**: Automatic duration calculation
- **Clean Typography**: Easy-to-read formatting with proper contrast
- **Integrated Button**: View Details button within summary section

### View Details Button
- **Compact Design**: Lean, smaller button (px-3 py-1.5)
- **Integrated Placement**: Located within summary section with border separator
- **Icon Integration**: Small external link icon (w-3 h-3)
- **Hover Effects**: Smooth transition animations

## Enhanced Timeline Features

### JSON Updates Integration
The timeline now intelligently parses structured data:

1. **JSON Detection**: Automatically detects JSON-like structures in descriptions
2. **Updates Key**: Looks for "updates" array with timestamped entries
3. **Timestamp Mapping**: Maps "modified" timestamps to timeline events
4. **Message Extraction**: Extracts "message" content for timeline descriptions

### Timeline Data Sources
- **Primary**: JSON updates with timestamps (if available)
- **Fallback**: Text-based pattern matching for unstructured descriptions
- **Hybrid**: Combines both sources for comprehensive timeline coverage

### Timeline Display
- **Chronological Order**: Automatic sorting by timestamp
- **Date/Time Format**: Human-readable date and time display
- **Event Types**: Color-coded by event category
- **Rich Descriptions**: Full update messages with context

## Detailed Incident Slider

### Overview
The detailed incident slider provides a comprehensive view of incident information in a structured, easy-to-read format.

### Slider Features
- **Full-Screen Modal**: Overlay that covers the entire screen for focused viewing
- **Close Button**: Easy dismissal with X button in top-right corner
- **Responsive Design**: Works well on all screen sizes
- **Scrollable Content**: Handles long incident descriptions gracefully

### Slider Content Sections

#### 1. Header
- **Incident Title**: Clear identification of the incident
- **Severity and Status Badges**: **Auto-determined status** with color coding
- **Close Button**: Easy dismissal

#### 2. Incident Overview
- **Structured Grid**: Title, ID (with hyperlink), Service, Region, Begin/End Times, Status
- **Clean Layout**: Organized information for quick scanning
- **Time Information**: Formatted timestamps in local timezone
- **Interactive ID**: Clickable link to Google Status Page
- **Auto-determined Status**: Status field shows resolved/ongoing automatically

#### 3. Enhanced Timeline
- **Visual Timeline**: Large, prominent timeline with color-coded events
- **JSON Updates**: **Primary data source** from structured updates
- **Timestamp Mapping**: Events mapped by "modified" timestamps
- **Event Types**: 
  - 🟢 **Start Events**: Alert times, initial detection (green dots)
  - 🟡 **Milestone Events**: Key updates, root cause analysis (yellow dots)
  - 🔵 **Resolution Events**: Fixes, recovery steps (blue dots)
- **Enhanced Display**: Larger timeline dots and event cards
- **Chronological Order**: Automatic sorting by timestamp
- **Event Details**: Rich descriptions with type labels

#### 4. Full Description
- **Complete Text**: Full incident description with HTML formatting
- **Prose Styling**: Clean, readable formatting
- **Background Highlight**: Light gray background for better readability

#### 5. Affected Resources
- **Service Tags**: Color-coded affected services
- **Region Tags**: Color-coded affected regions
- **Visual Organization**: Clear separation of different resource types

## Timeline Intelligence

### Automatic Timeline Extraction
The system automatically parses incident descriptions to extract timeline events:

1. **JSON Updates Priority**: First looks for structured updates data
2. **Timestamp Mapping**: Maps "modified" timestamps to timeline events
3. **Message Extraction**: Extracts update messages for timeline descriptions
4. **Fallback Parsing**: Uses text-based patterns if no structured data found
5. **Hybrid Approach**: Combines multiple data sources for comprehensive coverage

### Timeline Parsing Patterns
- **Primary**: JSON updates with timestamps and messages
- **Secondary**: Time-based patterns (US/Pacific, UTC, EST, etc.)
- **Tertiary**: Date ranges, alert patterns, resolution patterns
- **Fallback**: Generic timeline and impact patterns

### Visual Timeline Features
- **Connected Timeline**: Vertical line connecting all events
- **Color-coded Dots**: Different colors for different event types
- **Event Cards**: Clean, organized display of each timeline event
- **Type Labels**: Clear identification of event types
- **Chronological Order**: Automatic sorting by timestamp

## Duration Calculation

### Automatic Duration Logic
- **Automatic Calculation**: Duration = End Time - Begin Time
- **Smart Formatting**: Displays as "X hours Y minutes" or "X minutes"
- **Edge Cases**: Handles ongoing incidents and invalid timestamps
- **Precision**: Shows exact duration down to the minute

### Duration Display
- **Real-time Updates**: Duration updates automatically when incidents resolve
- **Human Readable**: Natural language formatting (e.g., "2 hours 5 minutes")
- **Accurate**: Based on actual timestamps, not extracted text

## Data Sources

### Provider Data Source
- **GCP**: Comprehensive data from [incidents.json API](https://status.cloud.google.com/incidents.json)
- **AWS**: Limited data (RSS feeds deprecated, see [Health Dashboard](https://health.aws.amazon.com/health/status))
- **Azure**: Limited data from RSS feed
- **OCI**: No public data available

### Database Data Source
- Historical incidents stored in local database
- May contain fewer incidents than provider data
- Useful for offline analysis

## Features

### Filtering Options
- **Provider Filter**: Filter by specific cloud provider
- **Time Range**: Filter by number of days (30, 90, 180, 365)
- **Data Source**: Toggle between provider data and database data

### Real-time Updates
- **Auto-refresh**: Data automatically refreshes when filters change
- **Manual Refresh**: Refresh button for immediate updates
- **Progress Tracking**: Visual progress indicator during data loading

### Timezone Support
- All timestamps displayed in browser's local timezone
- Consistent formatting across all time displays
- Clear timezone indicators

### External Integration
- **Google Cloud Status Page**: Direct links to official incident pages at `https://status.cloud.google.com/incidents/{id}`
- **New Tab Opening**: External links open in new browser tabs
- **Security**: Proper `rel` attributes for external links
- **Clean URLs**: Automatic prefix removal for better display

## Example Display

### Main View
```
[Medium] [Resolved] ← Auto-determined status

Description:     We are investigating elevated error rates with multiple products in us-east1
ID:              [8cY8jdUpEGGbsSMSQk7J] ← Clean ID, clickable hyperlink to GCP Status
Status:          resolved ← Auto-determined
Begin Time:      07/18/2025, 07:42:00 AM PDT
End Time:        07/18/2025, 09:47:00 AM PDT

Service:         AlloyDB for PostgreSQL
Region:          us-east1

Summary:
┌─────────────────────────────────────────────────────────────┐
│ 09:47 US/Pacific: Onsite technicians reconnected the      │
│ device, control plane connectivity was fully restored,     │
│ and all services were back to a stable state               │
│                                                             │
│ Duration: 2 hours 5 minutes                                │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [View Details] ← Compact button within summary         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Slider View
```
┌─────────────────────────────────────────────────────────────┐
│ Incident Details                    [X]                    │
│ [Medium] [Resolved] ← Auto-determined status              │
├─────────────────────────────────────────────────────────────┤
│ Incident Overview                                          │
│ Title: We are investigating elevated error rates...        │
│ ID: [8cY8jdUpEGGbsSMSQk7J] ← Clean ID, hyperlink to GCP Status         │
│ Service: AlloyDB for PostgreSQL                            │
│ Begin Time: 07/18/2025, 07:42:00 AM PDT                   │
│ End Time: 07/18/2025, 09:47:00 AM PDT                     │
│ Status: resolved ← Auto-determined                         │
├─────────────────────────────────────────────────────────────┤
│ Enhanced Timeline (JSON Updates)                           │
│ ● 07/18/2025, 07:42:00 AM: Initial investigation started │
│ ● 07/18/2025, 08:15:00 AM: Root cause identified         │
│ ● 07/18/2025, 09:00:00 AM: Mitigation in progress        │
│ ● 07/18/2025, 09:47:00 AM: Issue resolved                │
├─────────────────────────────────────────────────────────────┤
│ Full Description                                           │
│ [Complete incident description with formatting]            │
├─────────────────────────────────────────────────────────────┤
│ Affected Resources                                         │
│ Services: [AlloyDB] [Apigee] [Artifact Registry] ...       │
│ Regions: [us-east1] [us-east1-b]                          │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

1. **Structured Information**: Clear, organized display of incident details
2. **Intelligent Parsing**: Automatic extraction of key information and timelines
3. **Visual Timeline**: Easy-to-follow chronological progression of events
4. **Accurate Duration**: Automatic calculation from actual timestamps
5. **Smart Status Detection**: Automatic status determination based on resolution
6. **External Integration**: Direct links to official status pages
7. **Clean ID Display**: Automatic prefix removal for better readability
8. **Integrated Controls**: View Details button within summary section
9. **Enhanced Timeline**: JSON updates with timestamp mapping
10. **Comprehensive Data**: Rich metadata from GCP JSON API
11. **Easy Scanning**: Quick identification of key incident information
12. **Consistent Formatting**: Uniform display across all incidents
13. **Responsive Design**: Works well on desktop and mobile devices
14. **Accessibility**: Clear labels and proper contrast for readability
15. **Detailed View**: Full-screen slider for comprehensive incident analysis
16. **Most Recent Updates**: Summary focuses on current status information

## Technical Implementation

- **React Components**: Modular component structure with Timeline, Summary, and Detailed Slider components
- **TypeScript**: Type-safe data handling and timeline parsing
- **Tailwind CSS**: Responsive styling with timeline visualization
- **HTML Sanitization**: Safe rendering of HTML content
- **Timezone Conversion**: Automatic local timezone display
- **Intelligent Parsing**: Advanced regex patterns and JSON parsing for timeline extraction
- **Visual Timeline**: Custom timeline component with color-coded events
- **Duration Calculation**: Automatic time difference calculation with smart formatting
- **Modal Management**: State management for detailed slider overlay
- **Event Handling**: Proper click handlers for view details functionality
- **Status Logic**: Automatic status determination based on resolution timestamps
- **External Links**: Secure hyperlink handling with proper attributes
- **Dynamic Content**: Summary content adapts to incident data
- **JSON Integration**: Structured data parsing for enhanced timeline accuracy
- **Prefix Removal**: Automatic ID cleaning for better user experience
