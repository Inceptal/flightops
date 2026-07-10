# FlightOps AI Build Checklist

## Commit Rule

Commit after every completed vertical slice. A vertical slice means the app can still run and the demo is better than before.

Recommended flow:

```bash
git status
git add .
git commit -m "Short imperative message"
```

Add the GitHub remote later:

```bash
git remote add origin <github-repo-url>
git push -u origin main
```

## Phase 1: Project Baseline

- [x] Create realistic synthetic demo dataset
- [x] Add Python web frontend scaffold
- [x] Add `.gitignore`
- [x] Add `requirements.txt`
- [ ] Create first local commit

## Phase 2: Demo UI

- [ ] Build operations dashboard layout
- [ ] Add live disruption timeline
- [ ] Add weather risk panel
- [ ] Add NOTAM and airport-capacity panel
- [ ] Add flight wave table with delay-risk coloring
- [ ] Add aircraft/crew/maintenance detail drawers
- [ ] Add supervisor recommendation panel
- [ ] Add rejected alternatives panel
- [ ] Add "Why?" explanation chain

Commit target:

```bash
git commit -m "Build operations dashboard demo"
```

## Phase 3: Agent Simulation

- [ ] Create agent modules for weather, aircraft, crew, maintenance and cost
- [ ] Create supervisor orchestration module
- [ ] Have each agent return structured findings
- [ ] Have supervisor rank alternatives
- [ ] Feed the UI from generated agent output instead of static JSON fields

Commit target:

```bash
git commit -m "Add multi-agent operations simulation"
```

## Phase 4: Judge Demo Polish

- [ ] Add one-click scenario reset
- [ ] Add animated/step-through decision sequence
- [ ] Add before/after impact metrics
- [ ] Add concise README with setup and demo script
- [ ] Add screenshots or short demo GIF if time allows

Commit target:

```bash
git commit -m "Polish hackathon demo flow"
```

## Phase 5: Submission Readiness

- [ ] Verify app starts from clean checkout
- [ ] Verify `pip install -r requirements.txt` works
- [ ] Verify all demo data loads without external services
- [ ] Verify README includes exact run commands
- [ ] Add GitHub remote
- [ ] Push repository
- [ ] Confirm submission link opens
- [ ] Complete in-person check-in before Sunday, July 12, 2026 at 9:00 AM

Commit target:

```bash
git commit -m "Prepare hackathon submission"
```
