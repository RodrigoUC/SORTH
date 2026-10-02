# SORTH desktop design

## Product and audience
Spanish-first native PyQt6 application for academic timetable planning. The primary task is reviewing courses, generating a schedule, checking pending sessions and exporting the result. This palette is the first visual step in issue #4; ES/EN localization is separate work.

## Direction
Professional academic workspace with a more recognizable identity than the previous all-blue/gray surface. A navy masthead anchors the application. Teal marks the principal scheduling action and overview. Violet marks active navigation and keyboard focus. Pale reading surfaces keep dense course and schedule tables comfortable.

## Runtime source of truth
`project_root/src/gui/theme.py` owns semantic `COLORS` and the shared Qt stylesheet. Roles use English identifiers independent of displayed language. `main_window.py` assigns brandHeader/headerAction roles; schedule consultation assigns mutedText/dangerAction roles. No behavior, text, schedule allocation or exported data changes.

## Color roles
- Canvas: #EFF3F9; reading surface: #FFFFFF; alternate row: #F3F6FC
- Navy identity/table header: #183153; white text; secondary header text #D3E5FA
- Main action: #087F83; hover #066B70; pressed #055A61; white text
- Active tab/focus: #6545AD; soft accent #EFE9FA
- Body text: #1D2D44; secondary text and placeholders: #52647D
- Control boundaries: #7688A1; passive dividers: #D6DFEB
- Disabled surface/text: #E1E7F0 / #56667D
- Success: #246448 / #E3F3EA; caution: #88551A / #FFF0D5; danger: #A12D46 / #FCE8EC

## Components and behavior
Use native Segoe UI with DejaVu Sans fallback, keeping the existing 10pt desktop density. Keep existing keyboard shortcuts and native input behavior. Selection has a light violet surface; focused controls have a 2px contrasting boundary. A focused teal action uses a white inset boundary; the navy header action uses white. Destructive schedule actions retain explicit text and confirmation. Course category fills remain stable and shared with exported spreadsheets; labels and exact times carry meaning independently of color. Existing dialogs outside this palette slice retain their behavior and local status styling.

## Verification and limits
`tests/test_gui/test_theme.py` checks text ≥4.5:1, control/focus boundaries ≥3:1, schedule label contrast and packaged sorting icons. Real Qt screenshots cover list, classroom grid, course management, narrow layout, filters, pending/conflicting sessions and keyboard focus. Palette ratios are not a complete accessibility certification. Linux Qt offscreen/Fusion captures are development previews, not evidence of native Windows rendering. Confirm the Windows review workflow and native appearance before a release.
