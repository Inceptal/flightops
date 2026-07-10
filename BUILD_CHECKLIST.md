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
- [x] Create first local commit

## Phase 2: Decision Cockpit UI

- [x] Build focused decision-cockpit layout
- [x] Add scenario header for typhoon risk near SGN
- [x] Add four core metrics
- [x] Add weather, NOTAM and airport-capacity risk panel
- [x] Add affected flight table with risk coloring
- [x] Add supervisor recommendation panel
- [x] Add compact specialist-agent reasoning cards
- [x] Add rejected alternatives panel
- [x] Add "Why?" explanation chain
- [ ] Review the dashboard live with the team and cut anything that slows the demo

Commit target:

```bash
git commit -m "Build decision cockpit dashboard"
```

## Phase 3: Agent Simulation

- [x] Create agent modules for weather, aircraft, crew, maintenance and cost
- [x] Create supervisor orchestration module
- [x] Have each agent return structured findings
- [x] Have supervisor rank alternatives
- [x] Feed the UI from generated agent output instead of static JSON fields

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
