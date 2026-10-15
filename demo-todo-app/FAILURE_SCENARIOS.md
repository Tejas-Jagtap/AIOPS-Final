# Failure Scenarios for Testing

This document describes intentional failure scenarios built into the demo app for testing the AIOps failure prediction system.

## Automatic Failure Simulation

### Enable Simulated Failures

Edit `Jenkinsfile` and change the environment variable:

```groovy
environment {
    SIMULATE_FAILURE = 'true'  // Change from 'false' to 'true'
}
```

### Failure Pattern Schedule

When `SIMULATE_FAILURE = 'true'`, builds will fail according to this pattern:

| Build Number  | Failure Type                 | Stage                | Exit Code | Key Error Message       |
| ------------- | ---------------------------- | -------------------- | --------- | ----------------------- |
| Multiple of 3 | **Test Failure**             | Run Tests            | 1         | `npm run test:ci` fails |
| Multiple of 5 | **Dependency Install Error** | Install Dependencies | 1         | `npm install` fails     |
| Multiple of 7 | **Build Error**              | Build Application    | 1         | Simulated build error   |

**Example Timeline**:

```
Build #1  → SUCCESS
Build #2  → SUCCESS
Build #3  → FAILURE (Tests)
Build #4  → SUCCESS
Build #5  → FAILURE (Dependencies)
Build #6  → FAILURE (Tests: 3×2)
Build #7  → FAILURE (Build)
Build #8  → SUCCESS
Build #9  → FAILURE (Tests: 3×3)
Build #10 → FAILURE (Dependencies: 5×2)
Build #12 → FAILURE (Tests: 3×4)
Build #14 → FAILURE (Build: 7×2)
Build #15 → FAILURE (Tests: 3×5 & Dependencies: 5×3)
```

This creates a realistic mix of:

- **~60%** successful builds
- **~40%** failed builds (diverse error types)

---

## Manual Failure Injection

### 1. Test Failures

#### Option A: Add Failing Test

Edit `__tests__/Home.test.tsx`:

```typescript
describe("Intentional Failures", () => {
  it("should fail for testing AIOps", () => {
    expect(1 + 1).toBe(3); // Will always fail
  });

  it("should timeout for async testing", async () => {
    await new Promise((resolve) => setTimeout(resolve, 10000)); // 10s timeout
  });
});
```

#### Option B: Break Existing Test

Edit `__tests__/api-todos.test.ts`:

```typescript
it("creates a new todo successfully", async () => {
  // ... existing code ...

  // Add intentional assertion failure
  expect(data.todo.text).toBe("WRONG_VALUE"); // Will fail
});
```

**Expected Log Output**:

```
FAIL __tests__/Home.test.tsx
  ● Intentional Failures › should fail for testing AIOps

    expect(received).toBe(expected)

    Expected: 3
    Received: 2
```

### 2. Build Failures

#### Option A: Syntax Error

Edit `app/page.tsx`:

```typescript
// Add syntax error at the top
const invalidSyntax =   // Missing value - syntax error

export default function Home() {
  // ... rest of code
}
```

#### Option B: Missing Import

Edit `app/page.tsx`:

```typescript
// Remove the useState import
import { useEffect } from "react"; // useState removed
// Now useState will be undefined
```

**Expected Log Output**:

```
Failed to compile.

./app/page.tsx
Error: Unexpected token (line 5)
  3 |
  4 | const invalidSyntax =
  5 |
```

### 3. Dependency Errors

#### Option A: Invalid Package

Edit `package.json`:

```json
"dependencies": {
  "next": "14.0.4",
  "react": "18.2.0",
  "react-dom": "18.2.0",
  "nonexistent-package-xyz": "1.0.0"  // Add invalid package
}
```

#### Option B: Version Conflict

Edit `package.json`:

```json
"dependencies": {
  "react": "19.0.0",  // Incompatible with Next.js 14
  "react-dom": "19.0.0"
}
```

**Expected Log Output**:

```
npm ERR! code E404
npm ERR! 404 Not Found - GET https://registry.npmjs.org/nonexistent-package-xyz
npm ERR! 404 'nonexistent-package-xyz@1.0.0' is not in the npm registry
```

### 4. Linting Errors

Edit `.eslintrc.js`:

```javascript
module.exports = {
  extends: ["next/core-web-vitals"],
  rules: {
    "@typescript-eslint/no-unused-vars": "error", // Change to error
    "@typescript-eslint/no-explicit-any": "error",
    "no-console": "error", // Fail on console.log
  },
};
```

Then add unused variables:

```typescript
// In any file
const unusedVariable = "This will cause lint error";
console.log("This will also fail"); // With no-console rule
```

**Expected Log Output**:

```
./app/page.tsx
  5:7  error  'unusedVariable' is assigned a value but never used  @typescript-eslint/no-unused-vars
  10:3  error  Unexpected console statement  no-console
```

### 5. Docker Build Failures

#### Option A: Invalid Dockerfile Command

Edit `Dockerfile`:

```dockerfile
# Add invalid command
RUN nonexistent-command --some-flag
```

#### Option B: Missing File Reference

Edit `Dockerfile`:

```dockerfile
# Try to copy non-existent file
COPY nonexistent-file.txt ./
```

**Expected Log Output**:

```
ERROR: failed to solve: process "/bin/sh -c nonexistent-command --some-flag" did not complete successfully: exit code: 127
```

---

## Error Log Patterns

### Typical Test Failure Log

```
npm run test:ci

FAIL __tests__/Home.test.tsx
  ● Test suite failed to run

    Test failed. Exit code: 1

  ● Home Page › should fail intentionally

    expect(received).toBe(expected)

    Expected: 3
    Received: 2

----------|---------|----------|---------|---------|-------------------
File      | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
----------|---------|----------|---------|---------|-------------------
All files |   45.23 |    32.14 |   50.00 |   44.92 |
----------|---------|----------|---------|---------|-------------------

Test Suites: 1 failed, 2 passed, 3 total
Tests:       1 failed, 12 passed, 13 total

npm ERR! Test failed. See above for more details.
```

### Typical Build Failure Log

```
npm run build

> build
> next build

Creating an optimized production build ...
Failed to compile.

./app/page.tsx:4:5
Type error: Cannot find name 'invalidVariable'

  2 | import { useState } from 'react'
  3 |
> 4 | invalidVariable = 5
    | ^
  5 |
  6 | export default function Home() {

Error: Command failed with exit code 1: next build
```

### Typical Dependency Failure Log

```
npm install --legacy-peer-deps

npm WARN deprecated some-package@1.0.0: Package no longer supported
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
npm ERR!
npm ERR! While resolving: aiops-demo-todo-app@1.0.0
npm ERR! Found: react@18.2.0
npm ERR! Could not resolve dependency:
npm ERR! peer react@"^19.0.0" from react-dom@19.0.0

npm ERR! A complete log of this run can be found in:
npm ERR!     C:\Users\...\npm-cache\_logs\2024-01-01T12_00_00_000Z-debug.log
```

---

## Testing Failure Detection

### Step 1: Enable Failures

```groovy
// In Jenkinsfile
environment {
    SIMULATE_FAILURE = 'true'
}
```

Commit and push to trigger builds.

### Step 2: Generate Mixed Results

Run approximately **30 builds** to get:

- ~18 SUCCESS builds
- ~12 FAILED builds (4 test, 4 dependency, 4 build failures)

```powershell
# Trigger multiple builds manually (if not using webhooks)
# In Jenkins, click "Build Now" repeatedly, or use API:

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:YOUR_TOKEN"))
$headers = @{ Authorization = "Basic $auth" }

1..30 | ForEach-Object {
    Write-Host "Triggering build $_"
    Invoke-WebRequest -Uri "http://localhost:8080/job/aiops-demo-todo-app/build" `
        -Method POST -Headers $headers
    Start-Sleep -Seconds 60  # Wait between builds
}
```

### Step 3: Collect Logs

```powershell
cd G:\Mtech-Project\AIOPS
.\scripts\collect_jenkins_logs.ps1 -ApiToken "YOUR_TOKEN"
```

### Step 4: Verify Data Quality

Check that you have diverse failure types:

```powershell
$logs = Get-ChildItem "G:\Mtech-Project\AIOPS\data\jenkins_logs\*.log"

Write-Host "Total logs: $($logs.Count)"

$failures = $logs | Where-Object { $_.Name -match "FAILURE" }
Write-Host "Failure logs: $($failures.Count)"

$success = $logs | Where-Object { $_.Name -match "SUCCESS" }
Write-Host "Success logs: $($success.Count)"
```

---

## Resetting to Normal Operation

### Disable Automatic Failures

Edit `Jenkinsfile`:

```groovy
environment {
    SIMULATE_FAILURE = 'false'  // Back to normal
}
```

### Remove Manual Failures

1. **Revert test changes**: Remove intentional failing tests
2. **Fix syntax errors**: Remove invalid code
3. **Restore package.json**: Remove invalid dependencies
4. **Reset ESLint rules**: Return to warning-only mode

```bash
git checkout app/page.tsx
git checkout package.json
git checkout __tests__/Home.test.tsx
git commit -m "Reset to normal operation"
git push
```

---

## Best Practices for Log Collection

1. **Run at least 30 builds** for meaningful training data
2. **Mix of results**: Aim for 60% success, 40% failure
3. **Diverse failures**: Test, build, dependency errors
4. **Real timing**: Allow builds to complete naturally
5. **Stable infrastructure**: Keep Jenkins and dependencies consistent
6. **Document changes**: Note when you inject manual failures

---

## Integration with AIOps Training

After collecting logs, the training pipeline expects:

```
data/jenkins_logs/
├── build_1_2024-01-01_120000_SUCCESS.log
├── build_1_2024-01-01_120000_SUCCESS.log.meta.json
├── build_3_2024-01-01_121000_FAILURE.log
├── build_3_2024-01-01_121000_FAILURE.log.meta.json
└── collection_summary.json
```

The `jenkins_collector.py` will:

1. Read all logs and metadata
2. Extract features (error counts, warnings, duration)
3. Label builds (SUCCESS=0, FAILURE=1)
4. Generate training dataset
5. Save for XGBoost model training

---

**For more information**, see `demo-todo-app/README.md`
