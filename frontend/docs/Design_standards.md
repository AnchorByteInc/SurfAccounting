# Design Standards and Decisions

This document outlines the design decisions and standards for the application. It is intended to be CSS framework-agnostic, documenting the visual language and user interface patterns that define the app's identity.

## 1. Design Philosophy

The application follows a modern, clean, and functional design language. It blends the structured patterns of Material Design 3 (MD3) with custom elements like "Pill-nav" for navigation actions. The focus is on clarity, accessibility, and high contrast for information-dense views.

### Core Principles:

- **Consistency**: Unified behavior and appearance across all views.
- **Clarity**: High-contrast text and clear visual hierarchy.
- **Efficiency**: Minimal steps for frequent actions (e.g., "Universal Create Button").
- **Adaptability**: Seamless transition between desktop and mobile layouts.

---

## 2. Design Tokens

### 2.1 Color Palette

The colors are derived from a custom implementation of Material Design 3 palettes.

| Name             | Hex                     | Usage                                                    |
| :--------------- | :---------------------- | :------------------------------------------------------- |
| **Primary**      | `#1A5F7A`               | Main brand color, primary actions, active indicators.    |
| **Secondary**    | `#2D9596`               | Accent color, secondary actions, highlights.             |
| **Error**        | `#BA191A`               | Destructive actions, error alerts, validation messages.  |
| **Background**   | `#E0F4FF`               | Global page background.                                  |
| **Surface/Card** | `#FDFDFD`               | Background for cards, modals, and container elements.    |
| **On-Surface**   | `#0F4C61`               | Standard text color for surface backgrounds (Deep Wave). |
| **Muted**        | `#0F4C61` (50% Opacity) | Tertiary text, helper text, and secondary details.       |
| **Divider**      | `#CFEBFD`               | Subtle separators between list items and table rows.     |

### 2.2 Typography

- **Primary Font Family**: `Helvetica`, `system-ui`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `Oxygen`, `Ubuntu`, `Cantarell`, `"Open Sans"`, `"Helvetica Neue"`, `sans-serif`.
- **Base Body Font Size**: `14px`.
- **Headline Medium Size**: `22px`.
- **Weight**:
  - `Normal (400)`: Standard body text.
  - `Bold (700)`: Headings, navigation labels, and table headers.

### 2.3 Shapes & Borders

- **Standard Border Radius**: `14px` (Used for cards, modals, and containers).
- **Button Radius**: `999px` (Full pill shape).
- **Small Element Radius**: `7px` to `10px` (Used for menu items and smaller inputs).
- **Pill Shape**: `50rem` or `999px` (Used for navigation "pills" and badges).

### 2.4 Spacing

- **Standard Padding (X/Y)**: `24px` (Used for cards, modals, and main content containers).
- **Internal Spacing**: `12px` to `16px` (Used between related elements like buttons in a group or list items).
- **Gaps**: `2rem` (Used between large layout sections).

---

## 3. Layout Architecture

### 3.1 Main Structure

- **Sidenav Width**: `250px`.
- **Topnav Height**: `64px`.
- **Content Area**: Dynamic width (`calc(100vw - 250px)` on desktop).

### 3.2 Layout Patterns

- **Standard List View**: A full-width card containing a hoverable table. Includes a "more_vert" menu on each row for contextual actions.
- **Categorized View (Marketplace Pattern)**:
  - **Sidebar**: Sticky sidebar (`top: 2rem`) containing an `md-list` for category selection.
  - **Content**: A grid of cards (e.g., `row g-4` with `col-md-6`) or a filtered list.
  - **Header**: Contains the view title and a search input field.
- **Detail View**: typically uses a centered layout or a split layout with key info on one side and detailed activities/logs on the other.

### 3.3 Navigation Patterns

- **Sidenav**: Sidebar navigation with `100px` radius on the active state (flush to the left).
- **Topnav**: Floating "Pill-nav" elements for view-specific actions.
- **Back Button**: A circular arrow button located in the top left, often within a "Pill-nav" container.
- **Offcanvas Drawer**: On mobile, navigation and categories move to a slide-out drawer triggered by a "menu" icon.

---

## 4. UI Components

### 4.1 Buttons

- **Primary (Filled/Tonal)**: Teal/Blue background (`#1A5F7A`), white/light-grey text.
- **Secondary**: Aqua background (`#2D9596`), white/light-grey text.
- **Error (Danger)**: Red background (`#BA191A`) or red text for outlines.
- **Pill-nav Button**: Transparent background with a `12px` blur filter (`backdrop-filter: blur(12px)`) and a subtle white/grey background color with low opacity.
- **Universal Create Button**: A specific button pattern used for global actions, typically with a plus icon.

### 4.2 Cards

- **Background**: `#FDFDFD`.
- **Border**: None (by default).
- **Border Radius**: `14px`.
- **Padding**: `24px` on all sides.
- **Shadow**: Subtle shadow on hover (`0 0.25rem 1rem rgba(0, 0, 0, 0.075)`).

### 4.3 Tables

- **Header**: `14px`, `60% opacity` text, bold font weight.
- **Rows**: `1rem` vertical padding, `14px` font size.
- **Borders**: Subtle `#CFEBFD` border between rows.
- **Hover State**: Light teal background tint (`rgba(26, 95, 122, 0.08)`).
- **Background**: Atmospheric gradient (`linear-gradient(180deg, #E0F4FF 0%, #FFFFFF 100%)`).

### 4.4 Modals / Dialogs

- **Border Radius**: `14px`.
- **Padding**: `24px`.
- **Backdrop**: Black (`#000`) with `0.32` opacity.
- **Shadow**: Elevation of `10` (Standard Material Design shadow).

### 4.5 Forms

- **Input Style**: Filled tonal background (`#E6E8E9`) with `100px` corner radius (Pill style).
- **Select Fields**: Minimum width of `100px`, matching the button style variant (Primary, Secondary, Light).
- **Switches**: Track color `#CFEBFD`, active track color `#1A5F7A`, active handle white.
- **Chips**: Used for filtering and labels with a `20px` border radius.

### 4.6 Feedback & Progress

- **Progress Indicators**:
  - **Linear**: `8px` height, `8px` radius. Track color `#F4F4F6`, active indicator primary color.
  - **Circular**: Used within buttons or as standalone loaders.
- **Toasts**: Dark background (Primary color), white text, `4px` radius, elevation of `3` to `5`.
- **Tooltips**: Rounded corners, `12px 16px` padding.
- **Badges**: Rounded pill shape (`rounded-pill`), used for status or plan levels.

---

## 5. Iconography

- **System**: Material Icons (Outlined or Filled).
- **Standard Size**: `24px`.
- **Weight**: Typically `400` weight, with specialized weights (`200` or `300`) for specific UI elements like the account icon.
- **Variation**: `filled-icon` class for fully filled Material Icons.

---

## 6. Interaction States

- **Hover**: Subtle background tinting or shadow increase.
- **Active/Pressed**: Darker shade or slight scale down (if applicable).
- **Disabled**: `50%` opacity and `pointer-events: none`.
- **Focus**: Distinct focus ring, often matching the primary color.

---

## 7. Responsive Guidelines

- **Desktop (> 991px)**: Full Sidenav and Topnav.
- **Tablet/Mobile (< 991px)**: Sidenav becomes an Offcanvas drawer (Drawer width `85%`, max `300px`).
- **Small Screens (< 768px)**: Padding reduced from `15px` to `8px` in `container-fluid`.
- **Modals**: Full-screen on very small devices (`< 575px`).

---

## 8. Accessibility and Best Practices

- **Contrast**: Maintain a high contrast ratio between text and background (e.g., On-Surface color `#0F4C61` against background `#FDFDFD`).
- **Interactive Targets**: Buttons and interactive icons should have a minimum click area (often using `md-icon-button` or explicit padding).
- **Aria Labels**: Use `aria-label` or `aria-labelledby` for icon-only buttons to ensure screen reader compatibility.
- **Keyboard Navigation**: Ensure `md-list` and `md-menu` support standard keyboard interactions (Enter to select, Esc to close).

---

## 9. Specific Design Patterns

### 9.1 Gradient Backgrounds

Gradient backgrounds are used for high-impact cards, buttons, or section transitions.

- **Deep Wave**: `linear-gradient(135deg, #0F4C61 0%, #1A5F7A 100%)` - Professional, stable.
- **Mid-Surf**: `linear-gradient(135deg, #1A5F7A 0%, #2D9596 100%)` - Primary brand transition.
- **Shallow Aqua**: `linear-gradient(135deg, #2D9596 0%, #59B4C3 100%)` - Energetic, modern.
- **Atmospheric**: `linear-gradient(180deg, #E0F4FF 0%, #FFFFFF 100%)` - Soft background for data-heavy tables.

### 9.2 Blurred Navigation ("Pill-nav")

Used for floating navigation elements to maintain readability over dynamic content.

- **Backdrop Filter**: `blur(12px)`.
- **Background Color**: `rgba(255, 255, 255, opacity)`.
- **Border Radius**: `50rem`.
