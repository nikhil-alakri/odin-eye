---
trigger: always_on
---

# Rule: AI Documentation and Artifact Storage

All AI-generated documentation, plans, and walkthroughs for any feature or task must be stored under the `Raw/features/` directory in the project workspace.

## Required Naming Scheme:
* **Implementation Plans**: `Raw/features/implementation_plan_[feature_name].md`
* **Walkthroughs**: `Raw/features/walkthrough_[feature_name].md`
* **Other Generated Artifacts/Mockups**: `Raw/features/[artifact_name]_[feature_name].md`

## Required Metadata:
* **Date & Time**: Always write the current date and time (e.g. `DD-MMM-YYYY HH:MM`) at the top of the plan, walkthrough, or generated document.

## General Constraints:
* Always name files using the suffix `_[feature_name].md`.
* Never store plans, walkthroughs, or generated files in the root folder, default system artifact folders, or other custom folders.
